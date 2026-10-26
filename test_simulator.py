"""
Comprehensive Automated Test Suite for ProcessLab.
Part of ProcessLab — Advanced OS Process State Simulator (Phase 10).

Covers:
- Process creation and PCB initialization
- Rejection of invalid inputs and duplicate PIDs
- 5-State model transitions (Admit, Dispatch, Preempt, I/O Request, I/O Complete, Terminate)
- Single-CPU execution invariant (only 1 process running at a time)
- Rejection of illegal state transitions
- State integrity after caught exceptions
- Queue ordering and queue membership
- Event log consistency and step counter tracking
- Guided presentation demo execution
- Discrete CPU scheduling algorithms (FCFS, Round Robin, SJF)
- SVG diagram rendering
"""

import pytest
from process import Process, ProcessState
from simulator import ProcessSimulator
from guided_demo import GuidedDemoManager
import scheduler
from diagram import render_svg_diagram


# =============================================================================
# 1. PROCESS CLASS TESTS
# =============================================================================

def test_process_creation():
    """Verify process initializes in NEW state with correct PCB values."""
    p = Process(pid=101, name="WebBrowser", priority=2, burst_time=6)
    assert p.pid == 101
    assert p.name == "WebBrowser"
    assert p.priority == 2
    assert p.burst_time == 6
    assert p.current_state == ProcessState.NEW
    assert len(p.state_history) == 1
    assert p.state_history[0]["state"] == "NEW"


def test_process_invalid_creation():
    """Verify validation for non-positive PID and empty process name."""
    with pytest.raises(ValueError):
        Process(pid=0, name="Invalid")
    with pytest.raises(ValueError):
        Process(pid=-5, name="Invalid")
    with pytest.raises(ValueError):
        Process(pid=101, name="")
    with pytest.raises(ValueError):
        Process(pid=101, name="   ")


def test_process_state_transitions():
    """Verify Process.change_state updates current state and history."""
    p = Process(pid=101, name="WebBrowser")
    p.change_state(ProcessState.READY, step=1, reason="Admitted")
    assert p.current_state == ProcessState.READY
    assert len(p.state_history) == 2
    assert p.state_history[1]["state"] == "READY"
    assert p.state_history[1]["step"] == 1

    # String input support
    p.change_state("RUNNING", step=2, reason="Dispatched")
    assert p.current_state == ProcessState.RUNNING

    # Rejection of invalid state string
    with pytest.raises(ValueError):
        p.change_state("UNKNOWN_STATE")


# =============================================================================
# 2. PROCESS SIMULATOR TESTS
# =============================================================================

def test_simulator_creation_and_duplicate_pid():
    """Verify adding processes and rejecting duplicate PIDs."""
    sim = ProcessSimulator()
    p1 = sim.create_process(101, "Browser")
    assert p1.pid == 101
    assert len(sim.new_processes) == 1
    assert sim.get_process(101) is p1

    # Attempt duplicate PID
    with pytest.raises(ValueError, match="already exists"):
        sim.create_process(101, "DuplicateBrowser")
    assert len(sim.new_processes) == 1


def test_simulator_valid_lifecycle():
    """Verify complete valid 5-state lifecycle for a process."""
    sim = ProcessSimulator()
    sim.create_process(101, "WebBrowser")

    # NEW -> READY
    sim.move_to_ready(101)
    assert len(sim.new_processes) == 0
    assert len(sim.ready_processes) == 1
    assert sim.ready_processes[0].pid == 101

    # READY -> RUNNING
    sim.run_process(101)
    assert len(sim.ready_processes) == 0
    assert sim.running_process is not None
    assert sim.running_process.pid == 101

    # RUNNING -> WAITING (I/O)
    sim.move_to_waiting(101)
    assert sim.running_process is None
    assert len(sim.waiting_processes) == 1
    assert sim.waiting_processes[0].pid == 101

    # WAITING -> READY (I/O Complete)
    sim.resume_process(101)
    assert len(sim.waiting_processes) == 0
    assert len(sim.ready_processes) == 1

    # READY -> RUNNING
    sim.run_process(101)
    assert sim.running_process.pid == 101

    # RUNNING -> READY (Preemption)
    sim.move_to_ready_from_running(101)
    assert sim.running_process is None
    assert len(sim.ready_processes) == 1

    # READY -> RUNNING
    sim.run_process(101)

    # RUNNING -> TERMINATED
    sim.terminate_process(101)
    assert sim.running_process is None
    assert len(sim.terminated_processes) == 1
    assert sim.terminated_processes[0].pid == 101


def test_simulator_single_cpu_invariant():
    """Verify single-CPU model: only one process can execute on CPU."""
    sim = ProcessSimulator()
    sim.create_process(101, "P1")
    sim.create_process(102, "P2")

    sim.move_to_ready(101)
    sim.move_to_ready(102)

    # Dispatch P1 to CPU
    sim.run_process(101)
    assert sim.running_process.pid == 101

    # Attempt to dispatch P2 while P1 is running -> must raise ValueError
    with pytest.raises(ValueError, match="CPU conflict"):
        sim.run_process(102)

    # Invariants must remain intact
    assert sim.running_process.pid == 101
    assert len(sim.ready_processes) == 1
    assert sim.ready_processes[0].pid == 102


def test_simulator_illegal_transitions():
    """Verify rejection of illegal transitions according to OS theory."""
    sim = ProcessSimulator()
    sim.create_process(101, "TestProc")

    # Cannot dispatch process directly from NEW to RUNNING
    with pytest.raises(ValueError, match="Illegal transition"):
        sim.run_process(101)

    # Cannot transition process from NEW directly to WAITING
    with pytest.raises(ValueError, match="not RUNNING"):
        sim.move_to_waiting(101)

    # Move to READY
    sim.move_to_ready(101)

    # Cannot move process from READY directly to WAITING
    with pytest.raises(ValueError, match="not RUNNING"):
        sim.move_to_waiting(101)

    # Cannot preempt a non-running process
    with pytest.raises(ValueError, match="not RUNNING"):
        sim.move_to_ready_from_running(101)

    # Dispatch to RUNNING
    sim.run_process(101)

    # Terminate
    sim.terminate_process(101)

    # Terminated process cannot transition to READY or RUNNING
    with pytest.raises(ValueError):
        sim.move_to_ready(101)
    with pytest.raises(ValueError):
        sim.run_process(101)


def test_simulator_state_after_failed_operations():
    """Verify failed operations do not corrupt queue counts or state."""
    sim = ProcessSimulator()
    sim.create_process(101, "P1")
    sim.move_to_ready(101)
    sim.run_process(101)

    # Try an invalid operation (terminate non-existent process)
    with pytest.raises(ValueError):
        sim.terminate_process(999)

    # P1 is still RUNNING
    assert sim.running_process is not None
    assert sim.running_process.pid == 101
    assert len(sim.terminated_processes) == 0


def test_simulator_event_logging_and_telemetry():
    """Verify event log records every transition with proper details."""
    sim = ProcessSimulator()
    sim.create_process(101, "P1")
    sim.move_to_ready(101)
    sim.run_process(101)
    sim.terminate_process(101)

    events = sim.get_event_log()
    assert len(events) == 4
    assert events[0]["action"] == "CREATE"
    assert events[1]["action"] == "ADMIT"
    assert events[2]["action"] == "DISPATCH"
    assert events[3]["action"] == "TERMINATE"

    counts = sim.get_state_counts()
    assert counts["total"] == 1
    assert counts["TERMINATED"] == 1
    assert counts["RUNNING"] == 0
    assert counts["READY"] == 0


def test_simulator_reset_and_sample_scenario():
    """Verify simulator reset and standard 3-task scenario loader."""
    sim = ProcessSimulator()
    procs = sim.load_sample_scenario()
    assert len(procs) == 3
    assert sim.get_state_counts()["total"] == 3
    assert sim.get_state_counts()["NEW"] == 3

    sim.reset()
    assert sim.get_state_counts()["total"] == 0
    assert len(sim.get_event_log()) == 0
    assert sim.step_counter == 0


# =============================================================================
# 3. GUIDED DEMONSTRATION TESTS
# =============================================================================

def test_guided_demo_workflow():
    """Verify guided demonstration steps advance cleanly through all 11 steps."""
    sim = ProcessSimulator()
    demo = GuidedDemoManager()

    assert demo.step_index == 0
    assert demo.can_advance()

    # Step through entire presentation sequence
    while demo.can_advance():
        info = demo.advance(sim)
        assert info is not None
        assert "os_concept" in info
        assert "title" in info

    assert demo.step_index == demo.total_steps
    # After demo finishes, both demo processes should be terminated
    counts = sim.get_state_counts()
    assert counts["TERMINATED"] == 2
    assert sim.running_process is None


# =============================================================================
# 4. CPU SCHEDULING ALGORITHM TESTS
# =============================================================================

def test_fcfs_scheduling():
    """Verify First-Come, First-Served computation."""
    procs = [
        scheduler.ScheduledProcessInput(pid=1, name="P1", arrival_time=0, burst_time=4),
        scheduler.ScheduledProcessInput(pid=2, name="P2", arrival_time=1, burst_time=3),
    ]
    output = scheduler.simulate_fcfs(procs)
    assert output.algorithm == "First-Come, First-Served (FCFS)"
    assert len(output.process_results) == 2

    # P1: start=0, finish=4. TAT=4, WT=0
    r1 = output.process_results[0]
    assert r1.completion_time == 4
    assert r1.turnaround_time == 4
    assert r1.waiting_time == 0

    # P2: start=4, finish=7. TAT=6, WT=3
    r2 = output.process_results[1]
    assert r2.completion_time == 7
    assert r2.turnaround_time == 6
    assert r2.waiting_time == 3

    assert output.avg_waiting_time == 1.5
    assert output.avg_turnaround_time == 5.0
    assert output.cpu_utilization == 100.0


def test_round_robin_scheduling():
    """Verify Round Robin preemptive time slicing computation."""
    procs = [
        scheduler.ScheduledProcessInput(pid=1, name="P1", arrival_time=0, burst_time=4),
        scheduler.ScheduledProcessInput(pid=2, name="P2", arrival_time=0, burst_time=2),
    ]
    # Quantum = 2
    output = scheduler.simulate_round_robin(procs, time_quantum=2)
    assert "Round Robin" in output.algorithm

    # P1 runs 0-2 (rem: 2), P2 runs 2-4 (finishes, CT=4, TAT=4, WT=2), P1 runs 4-6 (finishes, CT=6, TAT=6, WT=2)
    p1_res = next(r for r in output.process_results if r.pid == 1)
    p2_res = next(r for r in output.process_results if r.pid == 2)

    assert p2_res.completion_time == 4
    assert p1_res.completion_time == 6
    assert output.total_time == 6
    assert output.avg_waiting_time == 2.0


def test_sjf_scheduling():
    """Verify Shortest Job First scheduling."""
    procs = [
        scheduler.ScheduledProcessInput(pid=1, name="P1", arrival_time=0, burst_time=6),
        scheduler.ScheduledProcessInput(pid=2, name="P2", arrival_time=0, burst_time=2),
    ]
    output = scheduler.simulate_sjf(procs)
    # P2 runs first since burst is 2
    r_first = output.gantt_chart[0]
    assert r_first["pid"] == 2


# =============================================================================
# 5. DIAGRAM SVG RENDERER TEST
# =============================================================================

def test_svg_diagram_rendering():
    """Verify SVG diagram renders with valid XML tags and highlights."""
    counts = {"NEW": 2, "READY": 1, "RUNNING": 1, "WAITING": 0, "TERMINATED": 3}
    svg = render_svg_diagram(
        state_counts=counts,
        selected_state="RUNNING",
        last_transition={"action": "DISPATCH"},
        selected_pid=101
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "NEW" in svg
    assert "READY" in svg
    assert "RUNNING" in svg
    assert "WAITING" in svg
    assert "TERMINATED" in svg
    assert "Active PID #101" in svg
