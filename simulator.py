from process import Process, ProcessState


class ProcessSimulator:
    """Manages processes and their transitions in the OS 5-state model."""

    def __init__(self):
        self.new_processes = []
        self.ready_processes = []
        self.waiting_processes = []
        self.terminated_processes = []
        self.running_process = None

    def add_process(self, process: Process):
        """Add a new process in the NEW state."""

        if process.current_state != ProcessState.NEW:
            raise ValueError("A new process must start in the NEW state.")

        if self.get_process(process.pid) is not None:
            raise ValueError(
                f"Process with PID {process.pid} already exists."
            )

        self.new_processes.append(process)
        return process

    def create_process(self, pid: int, name: str):
        """Create and add a new process."""
        return self.add_process(Process(pid, name))

    def get_process(self, pid: int):
        """Find a process using its PID."""

        for process in self._all_processes():
            if process.pid == pid:
                return process

        return None

    def move_to_ready(self, pid: int):
        """NEW -> READY or WAITING -> READY."""

        process = self._require_process(pid)

        if process.current_state == ProcessState.NEW:
            self.new_processes.remove(process)

        elif process.current_state == ProcessState.WAITING:
            self.waiting_processes.remove(process)

        else:
            raise ValueError(
                "Only NEW or WAITING processes can move to READY."
            )

        process.change_state(ProcessState.READY)
        self.ready_processes.append(process)

        return process

    def run_process(self, pid: int):
        """READY -> RUNNING."""

        process = self._require_process(pid)

        if process.current_state != ProcessState.READY:
            raise ValueError(
                "Only a READY process can move to RUNNING."
            )

        if self.running_process is not None:
            raise ValueError(
                f"PID {self.running_process.pid} is already RUNNING. "
                "The CPU must become free before another process can run."
            )

        self.ready_processes.remove(process)

        process.change_state(ProcessState.RUNNING)

        self.running_process = process

        return process

    def move_to_waiting(self, pid: int):
        """RUNNING -> WAITING."""

        process = self._require_running(pid)

        process.change_state(ProcessState.WAITING)

        self.running_process = None
        self.waiting_processes.append(process)

        return process

    def resume_process(self, pid: int):
        """WAITING -> READY."""

        return self.move_to_ready(pid)

    def move_to_ready_from_running(self, pid: int):
        """RUNNING -> READY due to interrupt or preemption."""

        process = self._require_running(pid)

        process.change_state(ProcessState.READY)

        self.running_process = None
        self.ready_processes.append(process)

        return process

    def terminate_process(self, pid: int):
        """RUNNING -> TERMINATED."""

        process = self._require_running(pid)

        process.change_state(ProcessState.TERMINATED)

        self.running_process = None
        self.terminated_processes.append(process)

        return process

    def get_state_lists(self):
        """Return processes grouped according to state."""

        return {
            "NEW": list(self.new_processes),
            "READY": list(self.ready_processes),
            "RUNNING": (
                [self.running_process]
                if self.running_process is not None
                else []
            ),
            "WAITING": list(self.waiting_processes),
            "TERMINATED": list(self.terminated_processes),
        }

    def get_all_processes(self):
        """Return every process in the simulator."""

        return list(self._all_processes())

    def _all_processes(self):
        """Internal method used to collect all processes."""

        processes = []

        processes.extend(self.new_processes)
        processes.extend(self.ready_processes)
        processes.extend(self.waiting_processes)
        processes.extend(self.terminated_processes)

        if self.running_process is not None:
            processes.append(self.running_process)

        return processes

    def _require_process(self, pid: int):
        """Return process or raise an error if it does not exist."""

        process = self.get_process(pid)

        if process is None:
            raise ValueError(
                f"Process with PID {pid} does not exist."
            )

        return process

    def _require_running(self, pid: int):
        """Ensure that the requested process is currently running."""

        process = self._require_process(pid)

        if (
            process.current_state != ProcessState.RUNNING
            or self.running_process is not process
        ):
            raise ValueError(
                f"Process with PID {pid} is not RUNNING."
            )

        return process


# -------------------------------------------------
# SELF TEST
# -------------------------------------------------

if __name__ == "__main__":

    simulator = ProcessSimulator()

    simulator.create_process(101, "WebBrowser")
    simulator.create_process(102, "TextEditor")

    simulator.move_to_ready(101)
    simulator.run_process(101)
    simulator.move_to_waiting(101)
    simulator.resume_process(101)
    simulator.run_process(101)
    simulator.move_to_ready_from_running(101)
    simulator.run_process(101)
    simulator.terminate_process(101)

    states = simulator.get_state_lists()

    assert states["TERMINATED"][0].pid == 101
    assert states["NEW"][0].pid == 102
    assert simulator.running_process is None

    print("\nSimulator self-test passed.")
