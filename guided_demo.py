"""
Guided Demonstration Sequence and OS Educational Walkthrough.
Part of ProcessLab — Advanced OS Process State Simulator (Phase 6).

Drives step-by-step presentation scenarios that invoke real ProcessSimulator
backend methods while explaining corresponding Operating Systems concepts.
"""

from typing import Dict, Any, List, Optional
from simulator import ProcessSimulator
from process import ProcessState


GUIDED_STEPS: List[Dict[str, Any]] = [
    {
        "step_num": 0,
        "title": "Welcome to ProcessLab Demonstration",
        "badge": "Intro",
        "description": "Ready to begin the step-by-step presentation of the 5-State Process Model.",
        "os_concept": (
            "An Operating System manages active programs as 'Processes'. "
            "To maximize CPU utilization and enable multitasking, the OS tracks each process "
            "through five formal states: NEW, READY, RUNNING, WAITING, and TERMINATED."
        ),
        "action_desc": "Click 'Start / Next Step' to begin the lifecycle demonstration."
    },
    {
        "step_num": 1,
        "title": "Step 1: Process Creation (NEW State)",
        "badge": "NEW",
        "description": "Creating Process P101 ('WebBrowser').",
        "os_concept": (
            "When a program is launched, the OS creates a Process Control Block (PCB) "
            "and assigns a unique Process ID (PID). At this stage, the process is in the NEW state; "
            "it is defined in the system but not yet loaded into main memory."
        ),
        "action_desc": "Instantiating P101 in the NEW pool."
    },
    {
        "step_num": 2,
        "title": "Step 2: Admission to Memory (NEW → READY)",
        "badge": "Admit",
        "description": "Admitting P101 into the READY Queue.",
        "os_concept": (
            "The Long-Term (Job) Scheduler determines which processes from the pool are admitted "
            "into main memory. Once admitted, the process enters the READY state, meaning it has "
            "all necessary resources allocated and is simply waiting for CPU execution time."
        ),
        "action_desc": "Calling simulator.move_to_ready(101)."
    },
    {
        "step_num": 3,
        "title": "Step 3: CPU Dispatch (READY → RUNNING)",
        "badge": "Dispatch",
        "description": "Dispatching P101 onto the CPU.",
        "os_concept": (
            "The Short-Term (CPU) Scheduler selects P101 from the Ready Queue, and the Dispatcher "
            "performs a Context Switch (loading program counter, registers, and memory mappings). "
            "P101 is now in the RUNNING state, actively executing instructions on the CPU core."
        ),
        "action_desc": "Calling simulator.run_process(101)."
    },
    {
        "step_num": 4,
        "title": "Step 4: Multiprogramming (Create P102)",
        "badge": "Multitasking",
        "description": "Creating and admitting Process P102 ('MusicPlayer').",
        "os_concept": (
            "Modern Operating Systems are multiprogrammed. While P101 is executing on the CPU, "
            "another application P102 ('MusicPlayer') is loaded into memory and queued in the "
            "READY queue, waiting for its turn on the CPU."
        ),
        "action_desc": "Creating P102 and calling simulator.move_to_ready(102)."
    },
    {
        "step_num": 5,
        "title": "Step 5: I/O System Call (RUNNING → WAITING)",
        "badge": "I/O Wait",
        "description": "P101 ('WebBrowser') issues a network socket read request.",
        "os_concept": (
            "I/O devices (disk, network, keyboard) are thousands of times slower than the CPU. "
            "When P101 issues an I/O system call, it cannot continue until data arrives. "
            "Rather than letting the CPU idle, the OS moves P101 to the WAITING (Blocked) state and yields the CPU."
        ),
        "action_desc": "Calling simulator.move_to_waiting(101)."
    },
    {
        "step_num": 6,
        "title": "Step 6: CPU Reallocation (READY → RUNNING)",
        "badge": "Dispatch P102",
        "description": "Dispatching P102 ('MusicPlayer') to the newly freed CPU.",
        "os_concept": (
            "This demonstrates the core benefit of the 5-state model: CPU efficiency. "
            "Because P101 voluntarily yielded the CPU for I/O, the scheduler immediately dispatches P102, "
            "keeping CPU utilization near 100% without lag."
        ),
        "action_desc": "Calling simulator.run_process(102)."
    },
    {
        "step_num": 7,
        "title": "Step 7: I/O Completion Interrupt (WAITING → READY)",
        "badge": "I/O Complete",
        "description": "Network data arrives for P101 ('WebBrowser').",
        "os_concept": (
            "The network device controller signals hardware interrupt to the CPU. The OS interrupt handler "
            "processes the incoming packet and transitions P101 from WAITING back to the READY queue. "
            "Note: A process cannot jump directly from WAITING to RUNNING; it must wait in READY for scheduling."
        ),
        "action_desc": "Calling simulator.resume_process(101)."
    },
    {
        "step_num": 8,
        "title": "Step 8: Timer Interrupt Preemption (RUNNING → READY)",
        "badge": "Preempt",
        "description": "P102's time slice expires; preempted back to READY.",
        "os_concept": (
            "In preemptive multitasking (e.g. Round Robin), a hardware timer fires at fixed intervals. "
            "If a process uses its entire quantum, the OS preempts it: its state is saved, it is moved from "
            "RUNNING back to READY, allowing other waiting processes a turn."
        ),
        "action_desc": "Calling simulator.move_to_ready_from_running(102)."
    },
    {
        "step_num": 9,
        "title": "Step 9: P101 Resumes Execution (READY → RUNNING)",
        "badge": "Dispatch P101",
        "description": "Dispatching P101 back to RUNNING to process downloaded web content.",
        "os_concept": (
            "The dispatcher restores P101's execution context right from where it blocked. "
            "P101 now finishes parsing the webpage and rendering the DOM."
        ),
        "action_desc": "Calling simulator.run_process(101)."
    },
    {
        "step_num": 10,
        "title": "Step 10: Process Completion (RUNNING → TERMINATED)",
        "badge": "Exit",
        "description": "P101 completes all tasks and calls exit().",
        "os_concept": (
            "When a process finishes execution or encounters a fatal error, it transitions to TERMINATED. "
            "The OS closes open file descriptors, deallocates virtual memory pages, and records exit status for the parent process."
        ),
        "action_desc": "Calling simulator.terminate_process(101)."
    },
    {
        "step_num": 11,
        "title": "Step 11: Cleanup & Conclusion",
        "badge": "Finish",
        "description": "Dispatching and terminating P102 ('MusicPlayer').",
        "os_concept": (
            "Demonstration successfully completed! Every key transition in the classic 5-state process model "
            "has been demonstrated using real simulator kernel data."
        ),
        "action_desc": "Dispatching P102 and terminating it."
    }
]


class GuidedDemoManager:
    """Manages playback of the interactive college presentation demonstration."""

    def __init__(self):
        self.step_index: int = 0
        self.total_steps: int = len(GUIDED_STEPS) - 1

    def get_current_info(self) -> Dict[str, Any]:
        """Returns metadata for the active demonstration step."""
        return GUIDED_STEPS[min(self.step_index, len(GUIDED_STEPS) - 1)]

    def can_advance(self) -> bool:
        """Checks if there is a next step."""
        return self.step_index < self.total_steps

    def can_reverse(self) -> bool:
        """Checks if we can go back."""
        return self.step_index > 0

    def advance(self, simulator: ProcessSimulator) -> Dict[str, Any]:
        """
        Executes the actual state changes on the simulator for the next step.
        """
        if self.step_index >= self.total_steps:
            return self.get_current_info()

        self.step_index += 1
        step = self.step_index

        if step == 1:
            # Step 1: Create P101 (clean slate)
            simulator.reset()
            simulator.create_process(101, "WebBrowser", priority=2, burst_time=6)

        elif step == 2:
            # Step 2: Admit P101 to READY
            simulator.move_to_ready(101)

        elif step == 3:
            # Step 3: Dispatch P101 to RUNNING
            simulator.run_process(101)

        elif step == 4:
            # Step 4: Create & Admit P102 to READY
            simulator.create_process(102, "MusicPlayer", priority=1, burst_time=4)
            simulator.move_to_ready(102)

        elif step == 5:
            # Step 5: P101 Requests I/O -> WAITING
            simulator.move_to_waiting(101)

        elif step == 6:
            # Step 6: Dispatch P102 to RUNNING
            simulator.run_process(102)

        elif step == 7:
            # Step 7: P101 I/O Complete -> READY
            simulator.resume_process(101)

        elif step == 8:
            # Step 8: Preempt P102 -> READY
            simulator.move_to_ready_from_running(102)

        elif step == 9:
            # Step 9: Dispatch P101 -> RUNNING
            simulator.run_process(101)

        elif step == 10:
            # Step 10: Terminate P101
            simulator.terminate_process(101)

        elif step == 11:
            # Step 11: Dispatch P102 and Terminate
            simulator.run_process(102)
            simulator.terminate_process(102)

        return self.get_current_info()

    def reset(self, simulator: ProcessSimulator) -> None:
        """Resets the demo to step 0 and clears the simulator."""
        self.step_index = 0
        simulator.reset()
