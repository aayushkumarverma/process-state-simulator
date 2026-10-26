"""
Operating System Process State Simulator Engine.
Part of ProcessLab — Advanced OS Process State Simulator.

Manages process queues, transitions in the 5-state model, single-CPU execution
invariants, event logging, and simulation telemetry.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from process import Process, ProcessState


class ProcessSimulator:
    """
    Simulates an Operating System's Process Management and 5-State Lifecycle.

    Maintains:
    - NEW pool (admitted by long-term scheduler)
    - READY queue (FIFO queue awaiting CPU scheduling)
    - RUNNING slot (single-CPU core execution)
    - WAITING queue (processes blocked on I/O or events)
    - TERMINATED list (completed/killed processes)
    - Event audit trail with simulation step counter
    - Last transition tracker for visual diagram synchronization
    """

    def __init__(self):
        self.new_processes: List[Process] = []
        self.ready_processes: List[Process] = []
        self.waiting_processes: List[Process] = []
        self.terminated_processes: List[Process] = []
        self.running_process: Optional[Process] = None

        self.step_counter: int = 0
        self.event_log: List[Dict[str, Any]] = []
        self.last_transition: Optional[Dict[str, Any]] = None

    # -------------------------------------------------------------------------
    # PROCESS CREATION & LOOKUP
    # -------------------------------------------------------------------------

    def add_process(self, process: Process) -> Process:
        """
        Registers a new process into the simulator in the NEW state.

        Args:
            process (Process): Instance of Process to add.

        Raises:
            ValueError: If process is not in NEW state or PID already exists.
        """
        if process.current_state != ProcessState.NEW:
            raise ValueError(
                f"A new process must be created in the NEW state, got '{process.current_state.value}'."
            )

        if self.get_process(process.pid) is not None:
            raise ValueError(
                f"Process with PID {process.pid} already exists. PIDs must be unique."
            )

        self.step_counter += 1
        self.new_processes.append(process)

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state="NONE",
            to_state=ProcessState.NEW.value,
            action="CREATE",
            reason="Process allocated PCB and initialized in NEW state by OS job creator",
            status="SUCCESS"
        )
        self.last_transition = {
            "from": "NONE",
            "to": ProcessState.NEW.value,
            "pid": process.pid,
            "name": process.name,
            "action": "CREATE",
            "step": self.step_counter
        }
        return process

    def create_process(
        self,
        pid: int,
        name: str,
        priority: int = 1,
        burst_time: int = 5,
        arrival_time: int = 0
    ) -> Process:
        """Helper to instantiate and add a new process in a single call."""
        process = Process(
            pid=pid,
            name=name,
            priority=priority,
            burst_time=burst_time,
            arrival_time=arrival_time
        )
        return self.add_process(process)

    def get_process(self, pid: int) -> Optional[Process]:
        """Looks up a process across all state queues by PID."""
        for proc in self._all_processes():
            if proc.pid == pid:
                return proc
        return None

    # -------------------------------------------------------------------------
    # STATE TRANSITIONS
    # -------------------------------------------------------------------------

    def move_to_ready(self, pid: int) -> Process:
        """
        Transitions a process into the READY queue.
        Valid source states:
          - NEW -> READY (Admitted by Long-Term Scheduler)
          - WAITING -> READY (I/O or event completion handled by OS interrupt)

        Raises:
            ValueError: If PID does not exist or transition is illegal.
        """
        process = self._require_process(pid)
        from_state = process.current_state

        if from_state == ProcessState.NEW:
            action = "ADMIT"
            reason = "Long-Term (Job) Scheduler admitted process into main memory Ready Queue"
            self.new_processes.remove(process)
        elif from_state == ProcessState.WAITING:
            action = "I/O_COMPLETE"
            reason = "I/O device controller finished request; interrupt moved process back to Ready Queue"
            self.waiting_processes.remove(process)
        else:
            raise ValueError(
                f"Illegal transition: Cannot move PID {pid} from '{from_state.value}' to READY. "
                "Only NEW or WAITING processes can transition to READY."
            )

        self.step_counter += 1
        process.change_state(ProcessState.READY, step=self.step_counter, reason=reason)
        self.ready_processes.append(process)

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state=from_state.value,
            to_state=ProcessState.READY.value,
            action=action,
            reason=reason,
            status="SUCCESS"
        )
        self.last_transition = {
            "from": from_state.value,
            "to": ProcessState.READY.value,
            "pid": process.pid,
            "name": process.name,
            "action": action,
            "step": self.step_counter
        }
        return process

    def run_process(self, pid: int) -> Process:
        """
        Dispatches a process from the READY queue onto the single CPU (RUNNING).

        Enforces:
          - Process must currently be in the READY state.
          - Single-CPU invariant: Only ONE process may occupy RUNNING at any time.

        Raises:
            ValueError: If PID is not in READY or if CPU is already busy.
        """
        process = self._require_process(pid)

        if process.current_state != ProcessState.READY:
            raise ValueError(
                f"Illegal transition: Cannot dispatch PID {pid} from '{process.current_state.value}' to RUNNING. "
                "Only processes in the READY queue can be scheduled to run."
            )

        if self.running_process is not None:
            raise ValueError(
                f"CPU conflict: CPU is currently occupied by PID {self.running_process.pid} "
                f"('{self.running_process.name}'). In a single-CPU model, the running process must "
                "yield, block, or be preempted before another process can execute."
            )

        self.step_counter += 1
        self.ready_processes.remove(process)

        reason = "Short-Term Scheduler selected and CPU Dispatcher switched context to this process"
        process.change_state(ProcessState.RUNNING, step=self.step_counter, reason=reason)
        self.running_process = process

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state=ProcessState.READY.value,
            to_state=ProcessState.RUNNING.value,
            action="DISPATCH",
            reason=reason,
            status="SUCCESS"
        )
        self.last_transition = {
            "from": ProcessState.READY.value,
            "to": ProcessState.RUNNING.value,
            "pid": process.pid,
            "name": process.name,
            "action": "DISPATCH",
            "step": self.step_counter
        }
        return process

    def move_to_waiting(self, pid: int) -> Process:
        """
        Transitions the RUNNING process into the WAITING (Blocked) queue.
        Triggered when a process issues an I/O system call or awaits an event.

        Raises:
            ValueError: If PID is not currently RUNNING on the CPU.
        """
        process = self._require_running(pid)

        self.step_counter += 1
        self.running_process = None

        reason = "Process issued I/O system call or event wait, yielding the CPU to wait queue"
        process.change_state(ProcessState.WAITING, step=self.step_counter, reason=reason)
        self.waiting_processes.append(process)

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state=ProcessState.RUNNING.value,
            to_state=ProcessState.WAITING.value,
            action="I/O_REQUEST",
            reason=reason,
            status="SUCCESS"
        )
        self.last_transition = {
            "from": ProcessState.RUNNING.value,
            "to": ProcessState.WAITING.value,
            "pid": process.pid,
            "name": process.name,
            "action": "I/O_REQUEST",
            "step": self.step_counter
        }
        return process

    def resume_process(self, pid: int) -> Process:
        """Alias for move_to_ready(pid) specifically from WAITING."""
        return self.move_to_ready(pid)

    def move_to_ready_from_running(self, pid: int) -> Process:
        """
        Preempts the currently RUNNING process back into the READY queue.
        Triggered by timer interrupt (time slice expiration) or priority scheduling.

        Raises:
            ValueError: If PID is not currently RUNNING on the CPU.
        """
        process = self._require_running(pid)

        self.step_counter += 1
        self.running_process = None

        reason = "Timer interrupt (time-slice expired) or higher priority preemption"
        process.change_state(ProcessState.READY, step=self.step_counter, reason=reason)
        self.ready_processes.append(process)

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state=ProcessState.RUNNING.value,
            to_state=ProcessState.READY.value,
            action="PREEMPT",
            reason=reason,
            status="SUCCESS"
        )
        self.last_transition = {
            "from": ProcessState.RUNNING.value,
            "to": ProcessState.READY.value,
            "pid": process.pid,
            "name": process.name,
            "action": "PREEMPT",
            "step": self.step_counter
        }
        return process

    def terminate_process(self, pid: int) -> Process:
        """
        Terminates the currently RUNNING process and moves it to TERMINATED.
        Triggered when a process completes its instructions or exits via system call.

        Raises:
            ValueError: If PID is not currently RUNNING on the CPU.
        """
        process = self._require_running(pid)

        self.step_counter += 1
        self.running_process = None

        reason = "Process execution finished; OS deallocating memory and reclaiming PCB"
        process.change_state(ProcessState.TERMINATED, step=self.step_counter, reason=reason)
        self.terminated_processes.append(process)

        self._record_event(
            pid=process.pid,
            name=process.name,
            from_state=ProcessState.RUNNING.value,
            to_state=ProcessState.TERMINATED.value,
            action="TERMINATE",
            reason=reason,
            status="SUCCESS"
        )
        self.last_transition = {
            "from": ProcessState.RUNNING.value,
            "to": ProcessState.TERMINATED.value,
            "pid": process.pid,
            "name": process.name,
            "action": "TERMINATE",
            "step": self.step_counter
        }
        return process

    # -------------------------------------------------------------------------
    # STATE QUERIES & TELEMETRY
    # -------------------------------------------------------------------------

    def get_state_lists(self) -> Dict[str, List[Process]]:
        """Returns snapshot of processes grouped by state."""
        return {
            "NEW": list(self.new_processes),
            "READY": list(self.ready_processes),
            "RUNNING": [self.running_process] if self.running_process is not None else [],
            "WAITING": list(self.waiting_processes),
            "TERMINATED": list(self.terminated_processes),
        }

    def get_state_counts(self) -> Dict[str, int]:
        """Returns instantaneous counts of processes per state."""
        return {
            "total": len(self._all_processes()),
            "NEW": len(self.new_processes),
            "READY": len(self.ready_processes),
            "RUNNING": 1 if self.running_process is not None else 0,
            "WAITING": len(self.waiting_processes),
            "TERMINATED": len(self.terminated_processes),
        }

    def get_all_processes(self) -> List[Process]:
        """Returns all processes registered in the simulator."""
        return list(self._all_processes())

    def get_event_log(self) -> List[Dict[str, Any]]:
        """Returns complete historical event audit log."""
        return list(self.event_log)

    def reset(self) -> None:
        """Cleans all queues, resets step counter and transitions."""
        self.new_processes.clear()
        self.ready_processes.clear()
        self.waiting_processes.clear()
        self.terminated_processes.clear()
        self.running_process = None
        self.step_counter = 0
        self.event_log.clear()
        self.last_transition = None

    def load_sample_scenario(self) -> List[Process]:
        """
        Loads a standard multi-process operating system workload:
          - PID 101: WebBrowser (I/O bound)
          - PID 102: MusicPlayer (Interactive / Multimedia)
          - PID 103: CodeCompiler (CPU bound)
        """
        self.reset()
        p1 = self.create_process(101, "WebBrowser", priority=2, burst_time=6)
        p2 = self.create_process(102, "MusicPlayer", priority=3, burst_time=4)
        p3 = self.create_process(103, "CodeCompiler", priority=1, burst_time=8)
        return [p1, p2, p3]

    # -------------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------------

    def _all_processes(self) -> List[Process]:
        """Internal aggregator across all queues."""
        procs: List[Process] = []
        procs.extend(self.new_processes)
        procs.extend(self.ready_processes)
        procs.extend(self.waiting_processes)
        procs.extend(self.terminated_processes)
        if self.running_process is not None:
            procs.append(self.running_process)
        return procs

    def _require_process(self, pid: int) -> Process:
        """Returns process if found, or raises ValueError."""
        process = self.get_process(pid)
        if process is None:
            raise ValueError(f"Process with PID {pid} does not exist in the simulator.")
        return process

    def _require_running(self, pid: int) -> Process:
        """Verifies that the target process is actively on the CPU."""
        process = self._require_process(pid)
        if process.current_state != ProcessState.RUNNING or self.running_process is not process:
            current = self.running_process.pid if self.running_process else "None (CPU IDLE)"
            raise ValueError(
                f"Process PID {pid} is not RUNNING. Current CPU occupant: {current}."
            )
        return process

    def _record_event(
        self,
        pid: int,
        name: str,
        from_state: str,
        to_state: str,
        action: str,
        reason: str,
        status: str = "SUCCESS"
    ) -> None:
        """Appends an event entry to the audit log."""
        self.event_log.append({
            "step": self.step_counter,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "pid": pid,
            "name": name,
            "from_state": from_state,
            "to_state": to_state,
            "action": action,
            "reason": reason,
            "status": status
        })


if __name__ == "__main__":
    sim = ProcessSimulator()
    sim.create_process(101, "WebBrowser")
    sim.create_process(102, "TextEditor")

    sim.move_to_ready(101)
    sim.run_process(101)
    sim.move_to_waiting(101)
    sim.resume_process(101)
    sim.run_process(101)
    sim.move_to_ready_from_running(101)
    sim.run_process(101)
    sim.terminate_process(101)

    states = sim.get_state_lists()
    assert states["TERMINATED"][0].pid == 101
    assert states["NEW"][0].pid == 102
    assert sim.running_process is None
    print(f"Simulator self-test passed! Recorded {len(sim.get_event_log())} simulation events.")
