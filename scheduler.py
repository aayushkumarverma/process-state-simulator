"""
Discrete CPU Scheduling Simulation Engine.
Part of ProcessLab — Advanced OS Process State Simulator (Phase 8).

Implements standard OS scheduling algorithms:
- First-Come, First-Served (FCFS)
- Round Robin (RR) with configurable Time Quantum
- Shortest Job First (SJF - Non-Preemptive)

Computes turnaround time, waiting time, completion time, and generates
Gantt chart execution timelines.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class ScheduledProcessInput:
    """Input definition for scheduling simulation."""
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    priority: int = 1


@dataclass
class ProcessSchedulingResult:
    """Computed metrics for a scheduled process."""
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    completion_time: int
    turnaround_time: int
    waiting_time: int


@dataclass
class SchedulingSimulationOutput:
    """Overall results of a scheduling simulation."""
    algorithm: str
    process_results: List[ProcessSchedulingResult]
    gantt_chart: List[Dict[str, Any]]  # List of {pid, name, start, end}
    avg_turnaround_time: float
    avg_waiting_time: float
    total_time: int
    cpu_utilization: float


def simulate_fcfs(processes: List[ScheduledProcessInput]) -> SchedulingSimulationOutput:
    """
    First-Come, First-Served (FCFS) Scheduling.
    Executes processes non-preemptively strictly in order of arrival time.
    """
    if not processes:
        return _empty_output("First-Come, First-Served (FCFS)")

    # Sort by arrival time, breaking ties by PID
    sorted_procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    gantt_chart: List[Dict[str, Any]] = []
    results: List[ProcessSchedulingResult] = []

    for proc in sorted_procs:
        # If CPU is idle until process arrives
        if current_time < proc.arrival_time:
            gantt_chart.append({
                "pid": 0,
                "name": "IDLE",
                "start": current_time,
                "end": proc.arrival_time,
                "is_idle": True
            })
            current_time = proc.arrival_time

        start_time = current_time
        end_time = start_time + proc.burst_time
        current_time = end_time

        gantt_chart.append({
            "pid": proc.pid,
            "name": proc.name,
            "start": start_time,
            "end": end_time,
            "is_idle": False
        })

        completion_time = end_time
        turnaround_time = completion_time - proc.arrival_time
        waiting_time = turnaround_time - proc.burst_time

        results.append(
            ProcessSchedulingResult(
                pid=proc.pid,
                name=proc.name,
                arrival_time=proc.arrival_time,
                burst_time=proc.burst_time,
                completion_time=completion_time,
                turnaround_time=turnaround_time,
                waiting_time=waiting_time
            )
        )

    return _build_summary("First-Come, First-Served (FCFS)", results, gantt_chart, current_time)


def simulate_round_robin(
    processes: List[ScheduledProcessInput],
    time_quantum: int = 2
) -> SchedulingSimulationOutput:
    """
    Round Robin (RR) Preemptive Scheduling with Time Slicing.
    Processes are allocated CPU time slices equal to the quantum.
    """
    if not processes:
        return _empty_output("Round Robin (RR)")

    time_quantum = max(1, int(time_quantum))
    sorted_procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    # Track remaining burst times and completion times
    remaining_burst = {p.pid: p.burst_time for p in sorted_procs}
    proc_map = {p.pid: p for p in sorted_procs}
    completion_times: Dict[int, int] = {}

    current_time = 0
    ready_queue: List[int] = []
    arrived_indices = 0
    total_procs = len(sorted_procs)

    gantt_chart: List[Dict[str, Any]] = []

    # Advance to first arrival
    if sorted_procs[0].arrival_time > 0:
        gantt_chart.append({
            "pid": 0,
            "name": "IDLE",
            "start": 0,
            "end": sorted_procs[0].arrival_time,
            "is_idle": True
        })
        current_time = sorted_procs[0].arrival_time

    # Admit initially arrived processes
    while arrived_indices < total_procs and sorted_procs[arrived_indices].arrival_time <= current_time:
        ready_queue.append(sorted_procs[arrived_indices].pid)
        arrived_indices += 1

    while ready_queue or arrived_indices < total_procs:
        if not ready_queue:
            # CPU is idle waiting for next process
            next_proc = sorted_procs[arrived_indices]
            gantt_chart.append({
                "pid": 0,
                "name": "IDLE",
                "start": current_time,
                "end": next_proc.arrival_time,
                "is_idle": True
            })
            current_time = next_proc.arrival_time
            while arrived_indices < total_procs and sorted_procs[arrived_indices].arrival_time <= current_time:
                ready_queue.append(sorted_procs[arrived_indices].pid)
                arrived_indices += 1

        curr_pid = ready_queue.pop(0)
        curr_proc = proc_map[curr_pid]

        run_slice = min(time_quantum, remaining_burst[curr_pid])
        start_time = current_time
        end_time = current_time + run_slice
        current_time = end_time
        remaining_burst[curr_pid] -= run_slice

        gantt_chart.append({
            "pid": curr_proc.pid,
            "name": curr_proc.name,
            "start": start_time,
            "end": end_time,
            "is_idle": False
        })

        # Check for newly arrived processes during this time slice
        while arrived_indices < total_procs and sorted_procs[arrived_indices].arrival_time <= current_time:
            ready_queue.append(sorted_procs[arrived_indices].pid)
            arrived_indices += 1

        # If process still has remaining time, requeue it
        if remaining_burst[curr_pid] > 0:
            ready_queue.append(curr_pid)
        else:
            completion_times[curr_pid] = current_time

    # Compile results
    results: List[ProcessSchedulingResult] = []
    for proc in sorted_procs:
        ct = completion_times[proc.pid]
        tat = ct - proc.arrival_time
        wt = tat - proc.burst_time
        results.append(
            ProcessSchedulingResult(
                pid=proc.pid,
                name=proc.name,
                arrival_time=proc.arrival_time,
                burst_time=proc.burst_time,
                completion_time=ct,
                turnaround_time=tat,
                waiting_time=wt
            )
        )

    return _build_summary(f"Round Robin (RR, Quantum={time_quantum})", results, gantt_chart, current_time)


def simulate_sjf(processes: List[ScheduledProcessInput]) -> SchedulingSimulationOutput:
    """
    Shortest Job First (SJF - Non-Preemptive) Scheduling.
    Selects the process with the smallest CPU burst from the ready pool.
    """
    if not processes:
        return _empty_output("Shortest Job First (SJF)")

    sorted_procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    total_procs = len(sorted_procs)
    completed: List[ProcessSchedulingResult] = []
    gantt_chart: List[Dict[str, Any]] = []

    current_time = 0
    arrived: List[ScheduledProcessInput] = []
    proc_idx = 0

    while len(completed) < total_procs:
        # Admit all processes that have arrived by current_time
        while proc_idx < total_procs and sorted_procs[proc_idx].arrival_time <= current_time:
            arrived.append(sorted_procs[proc_idx])
            proc_idx += 1

        if not arrived:
            # CPU is idle
            next_arrival = sorted_procs[proc_idx].arrival_time
            gantt_chart.append({
                "pid": 0,
                "name": "IDLE",
                "start": current_time,
                "end": next_arrival,
                "is_idle": True
            })
            current_time = next_arrival
            continue

        # Pick shortest burst time
        arrived.sort(key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        selected = arrived.pop(0)

        start_time = current_time
        end_time = start_time + selected.burst_time
        current_time = end_time

        gantt_chart.append({
            "pid": selected.pid,
            "name": selected.name,
            "start": start_time,
            "end": end_time,
            "is_idle": False
        })

        ct = end_time
        tat = ct - selected.arrival_time
        wt = tat - selected.burst_time
        completed.append(
            ProcessSchedulingResult(
                pid=selected.pid,
                name=selected.name,
                arrival_time=selected.arrival_time,
                burst_time=selected.burst_time,
                completion_time=ct,
                turnaround_time=tat,
                waiting_time=wt
            )
        )

    # Sort results by PID
    completed.sort(key=lambda r: r.pid)
    return _build_summary("Shortest Job First (SJF)", completed, gantt_chart, current_time)


# Helper functions
def _empty_output(algorithm: str) -> SchedulingSimulationOutput:
    return SchedulingSimulationOutput(
        algorithm=algorithm,
        process_results=[],
        gantt_chart=[],
        avg_turnaround_time=0.0,
        avg_waiting_time=0.0,
        total_time=0,
        cpu_utilization=0.0
    )


def _build_summary(
    algorithm: str,
    results: List[ProcessSchedulingResult],
    gantt_chart: List[Dict[str, Any]],
    total_time: int
) -> SchedulingSimulationOutput:
    n = len(results)
    avg_tat = round(sum(r.turnaround_time for r in results) / n, 2) if n > 0 else 0.0
    avg_wt = round(sum(r.waiting_time for r in results) / n, 2) if n > 0 else 0.0

    busy_time = sum(
        block["end"] - block["start"]
        for block in gantt_chart
        if not block.get("is_idle", False)
    )
    cpu_util = round((busy_time / total_time * 100.0), 1) if total_time > 0 else 0.0

    return SchedulingSimulationOutput(
        algorithm=algorithm,
        process_results=results,
        gantt_chart=gantt_chart,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        total_time=total_time,
        cpu_utilization=cpu_util
    )
