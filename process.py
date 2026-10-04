from enum import Enum
from datetime import datetime


class ProcessState(Enum):
    """Standard 5-State Process Model in Operating Systems."""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"        # Also referred to as BLOCKED
    TERMINATED = "TERMINATED"  # Also referred to as EXIT


class Process:
    """
    Represents an Operating System Process.
    
    Attributes:
        pid (int): Unique Process Identifier.
        name (str): Human-readable name of the process.
        current_state (ProcessState): Current execution state of the process.
        state_history (list): Chronological log of state transitions.
    """

    def __init__(self, pid: int, name: str):
        self.pid = pid
        self.name = name
        
        # Every process starts in the NEW state
        self.current_state = ProcessState.NEW
        
        # Track initial state in history with a timestamp
        self.state_history = [
            {
                "state": self.current_state.value,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        ]

    def change_state(self, new_state: ProcessState | str):
        """
        Changes the current state of the process and records it in the history.
        
        Args:
            new_state (ProcessState or str): The new state to transition into.
        """
        # Accept both Enum (ProcessState.READY) and String ("READY")
        if isinstance(new_state, str):
            try:
                new_state = ProcessState(new_state.upper())
            except ValueError:
                raise ValueError(f"Invalid state '{new_state}'. Valid states: {[s.value for s in ProcessState]}")
        
        old_state = self.current_state
        self.current_state = new_state
        
        # Update history
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.state_history.append({
            "state": self.current_state.value,
            "timestamp": timestamp
        })
        
        print(f"[PID {self.pid} - {self.name}] State transition: {old_state.value} -> {self.current_state.value}")

    def get_history(self) -> list:
        """Returns the full state transition history."""
        return self.state_history

    def to_dict(self) -> dict:
        """Helper method to convert process data into a dictionary (useful for UI/Visualization)."""
        return {
            "pid": self.pid,
            "name": self.name,
            "current_state": self.current_state.value,
            "state_history": self.state_history
        }

    def __repr__(self) -> str:
        return f"Process(pid={self.pid}, name='{self.name}', state='{self.current_state.value}')"


# Quick Demo / Self-test
if __name__ == "__main__":
    print("--- Operating System Process Simulation Demo ---\n")
    
    # 1. Create a new process (starts in NEW state)
    p1 = Process(pid=101, name="WebBrowser")
    print(f"Created: {p1}\n")

    # 2. Simulate standard OS state transitions
    p1.change_state(ProcessState.READY)       # Admitted to ready queue
    p1.change_state(ProcessState.RUNNING)     # Scheduled by CPU scheduler
    p1.change_state(ProcessState.WAITING)     # I/O or event wait
    p1.change_state(ProcessState.READY)       # I/O completed
    p1.change_state(ProcessState.RUNNING)     # Dispatched to CPU again
    p1.change_state(ProcessState.TERMINATED)  # Finished execution

    # 3. View state history
    print("\n--- Complete State History ---")
    for entry in p1.get_history():
        print(f"[{entry['timestamp']}] State: {entry['state']}")
