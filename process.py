"""
Process Control Block (PCB) Representation for Operating System Process Simulation.
Part of ProcessLab — Advanced OS Process State Simulator.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Union, List, Dict, Any


class ProcessState(Enum):
    """Standard 5-State Process Model in Operating Systems."""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"        # Also referred to as BLOCKED
    TERMINATED = "TERMINATED"  # Also referred to as EXIT / DEAD


class Process:
    """
    Represents an Operating System Process and its Process Control Block (PCB).

    Attributes:
        pid (int): Unique Process Identifier.
        name (str): Human-readable name of the process.
        priority (int): Process priority level (1 = standard, higher = higher priority).
        burst_time (int): Total CPU burst execution time units required.
        arrival_time (int): Simulation arrival time unit.
        current_state (ProcessState): Current execution state.
        state_history (List[Dict[str, Any]]): Chronological log of state transitions.
        created_at (str): Human-readable real-world creation timestamp.
    """

    def __init__(
        self,
        pid: int,
        name: str,
        priority: int = 1,
        burst_time: int = 5,
        arrival_time: int = 0,
    ):
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError(f"Process PID must be a positive integer, got '{pid}'.")
        if not name or not name.strip():
            raise ValueError("Process name cannot be empty.")

        self.pid: int = pid
        self.name: str = name.strip()
        self.priority: int = max(1, int(priority))
        self.burst_time: int = max(1, int(burst_time))
        self.remaining_time: int = self.burst_time
        self.arrival_time: int = max(0, int(arrival_time))

        self.created_at: str = datetime.now().strftime("%H:%M:%S")

        # Every OS process begins its lifecycle in the NEW state
        self.current_state: ProcessState = ProcessState.NEW

        # Chronological audit trail of all state transitions
        self.state_history: List[Dict[str, Any]] = [
            {
                "state": self.current_state.value,
                "timestamp": self.created_at,
                "step": 0,
                "reason": "Process created in NEW state"
            }
        ]

    def change_state(
        self,
        new_state: Union[ProcessState, str],
        step: Optional[int] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Transitions the process into a new state and appends the event to history.

        Args:
            new_state (ProcessState | str): Target process state.
            step (int, optional): Simulation step counter.
            reason (str, optional): Cause or event triggering the transition.
        """
        if isinstance(new_state, str):
            try:
                new_state = ProcessState(new_state.upper())
            except ValueError:
                valid_states = [s.value for s in ProcessState]
                raise ValueError(
                    f"Invalid state '{new_state}'. Valid OS states: {valid_states}"
                )

        old_state = self.current_state
        self.current_state = new_state
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.state_history.append({
            "state": self.current_state.value,
            "timestamp": timestamp,
            "step": step if step is not None else len(self.state_history),
            "reason": reason or f"Transitioned from {old_state.value} to {new_state.value}"
        })

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the complete chronological state transition history."""
        return list(self.state_history)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the process PCB for UI rendering, tables, and JSON export."""
        return {
            "pid": self.pid,
            "name": self.name,
            "current_state": self.current_state.value,
            "priority": self.priority,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "arrival_time": self.arrival_time,
            "created_at": self.created_at,
            "transitions_count": max(0, len(self.state_history) - 1),
            "state_history": self.state_history,
        }

    def __repr__(self) -> str:
        return (
            f"Process(pid={self.pid}, name='{self.name}', "
            f"state='{self.current_state.value}')"
        )


if __name__ == "__main__":
    print("--- Operating System Process Simulation Demo ---")
    p = Process(pid=101, name="WebBrowser")
    print(f"Created: {p}")
    p.change_state(ProcessState.READY, step=1, reason="Admitted to Ready Queue")
    p.change_state(ProcessState.RUNNING, step=2, reason="Dispatched to CPU")
    p.change_state(ProcessState.WAITING, step=3, reason="I/O Request")
    p.change_state(ProcessState.READY, step=4, reason="I/O Complete")
    p.change_state(ProcessState.RUNNING, step=5, reason="Rescheduled to CPU")
    p.change_state(ProcessState.TERMINATED, step=6, reason="Process Finished")
    print(f"Final State: {p}")
    print("History:")
    for h in p.get_history():
        print(f"  Step {h['step']} [{h['timestamp']}] {h['state']}: {h['reason']}")
