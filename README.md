# ⚡ ProcessLab — Advanced Operating System Process State Simulator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![License](https://img.shields.io/badge/Project-B.Tech%20CSE%20OS-emerald.svg)]()

**ProcessLab** is an interactive, developer-grade Operating System Process State Simulator designed for B.Tech Computer Science and Engineering students and educators. It provides real-time discrete simulation and visual telemetry of the canonical **5-State Process Model**, queue management, single-core CPU execution constraints, context switches, interrupts, and CPU scheduling algorithms.

---

## 🌟 Key Features

### 1. 🖥️ Interactive 5-State Lifecycle Diagram
- Live graphical SVG state diagram synchronized with the kernel simulation engine.
- Represents the 5 standard OS states: **NEW**, **READY**, **RUNNING**, **WAITING (Blocked)**, and **TERMINATED**.
- Highlights the current active state of the selected process with animated glowing rings.
- Dynamic arrow transitions with glowing indicators reflecting the most recent kernel event:
  - `Admit` (`NEW ➔ READY`)
  - `Dispatch` (`READY ➔ RUNNING`)
  - `Preempt / Interrupt` (`RUNNING ➔ READY`)
  - `I/O Request / Wait` (`RUNNING ➔ WAITING`)
  - `I/O Complete` (`WAITING ➔ READY`)
  - `Exit / Terminate` (`RUNNING ➔ TERMINATED`)
- Integrated **State & Transition Inspector** detailing scheduling actors, hardware interrupts, and resource allocations.

### 2. 🗂️ Process Queues & Single-CPU Core Visualization
- Physical visualization of OS process queues:
  - **NEW Pool:** Unadmitted processes initialized in memory.
  - **READY Queue (FIFO):** Processes ordered awaiting CPU dispatch.
  - **CPU Core (RUNNING):** Enforces single-CPU invariant; active instruction visualization.
  - **WAITING Queue:** Processes blocked awaiting asynchronous I/O devices.
  - **TERMINATED List:** Completed processes with reclaimed PCBs.

### 3. 🎮 Process Management & Interactive Controls
- Create processes with custom **PID**, **Name**, **Priority**, and **Estimated Burst Time**.
- Validates PID uniqueness and rejects empty or non-positive identifiers.
- Dynamically shows only valid OS transitions permitted for the process's current state.
- Strict backend invariant enforcement:
  - Prevents illegal jumps (e.g., `NEW ➔ RUNNING` or `WAITING ➔ RUNNING`).
  - Enforces single-CPU occupancy (disallowing simultaneous execution on single core).
  - Preserves system state consistency upon invalid operations.

### 4. 📜 Kernel Event Audit Log & Lifecycle Timeline
- Complete chronological audit log recording `Step`, `Time`, `PID`, `Process`, `From State`, `To State`, `Action`, and `Kernel Reason`.
- Interactive filtering by PID and entry limits.
- **CSV Export:** One-click download of simulation telemetry (`processlab_simulation_events.csv`).
- **Lifecycle Timeline:** Plotly step chart plotting the state progression of any process.

### 5. 🎓 Guided Presentation Demonstration Mode
- Built specifically for college viva, lab evaluations, and project presentations.
- 11-step walkthrough demonstrating:
  1. Process creation and PCB initialization.
  2. Long-term scheduler admission to memory.
  3. Short-term scheduler dispatch and context switch.
  4. Multiprogramming (queuing second process).
  5. Blocking I/O system calls and CPU yielding.
  6. CPU reallocation to prevent CPU idle time.
  7. I/O controller hardware interrupt handling.
  8. Timer interrupt and Round Robin preemption.
  9. Resumed execution from saved context.
  10. Resource reclamation and process termination.
- Explains the exact OS concept at each step while mutating the real backend simulation.

### 6. 📊 Advanced CPU Scheduling Mode
- Discrete algorithmic scheduling engine implementing:
  - **First-Come, First-Served (FCFS)**
  - **Round Robin (RR)** with user-configurable Time Quantum
  - **Shortest Job First (SJF - Non-Preemptive)**
- Generates interactive **Plotly Gantt Charts** of CPU time slices.
- Computes **Completion Time (CT)**, **Turnaround Time (TAT)**, **Waiting Time (WT)**, **Average TAT**, **Average WT**, and **CPU Utilization**.

### 7. 📖 OS Knowledge Base & Exam Reference
- Academic notes on Program vs. Process, PCB anatomy, and schedulers.
- Crucial distinction: **READY vs. WAITING**.
- Real-world multitasking walkthrough (browser streaming while typing in editor).
- Complete state transition matrix reference.

---

## 🏗️ Project Architecture & Folder Structure

```text
process-state-simulator/
│
├── app.py               # Main Streamlit web application & UI presentation layer
├── process.py           # Process Control Block (PCB) & ProcessState enum
├── simulator.py         # Kernel simulation engine, queue manager & event logger
├── scheduler.py         # Discrete CPU scheduling algorithms (FCFS, RR, SJF) & Gantt generator
├── guided_demo.py       # Step-by-step presentation demonstration driver
├── diagram.py           # SVG state diagram renderer & OS metadata definitions
├── test_simulator.py    # Automated test suite (pytest)
├── requirements.txt     # Python project dependencies
└── README.md            # Comprehensive project documentation
```

---

## 🛠️ Installation & Setup Guide

### Prerequisites
- Python **3.10** or higher installed on your system.
- Git (optional, for cloning).

### Step 1: Clone or Navigate to the Project
```powershell
cd "c:\Users\Akshat\Desktop\os visualisation\process-state-simulator"
```

### Step 2: Set Up Virtual Environment on Windows (Recommended)
Open PowerShell or Command Prompt in the project directory:

```powershell
# Create a virtual environment named 'venv'
py -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# (If PowerShell execution policy blocks activation, run:)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### Step 3: Install Dependencies
```powershell
py -m pip install -r requirements.txt
```
*(Dependencies installed: `streamlit`, `pandas`, `plotly`, `pytest`)*

---

## 🚀 Running the Application

Launch the Streamlit interactive dashboard with the following command:

```powershell
py -m streamlit run app.py
```

Once started, the application will automatically open in your default browser at:
👉 **`http://localhost:8501`**

---

## 🧪 Running Automated Unit Tests

To verify code correctness, queue logic, single-CPU invariants, and scheduling calculations, run `pytest`:

```powershell
py -m pytest -v test_simulator.py
```

Expected output:
```text
============================= test session starts =============================
collected 15 items

test_simulator.py::test_process_creation PASSED                          [  6%]
test_simulator.py::test_process_invalid_creation PASSED                  [ 13%]
test_simulator.py::test_process_state_transitions PASSED                 [ 20%]
test_simulator.py::test_simulator_creation_and_duplicate_pid PASSED      [ 26%]
test_simulator.py::test_simulator_valid_lifecycle PASSED                 [ 33%]
test_simulator.py::test_simulator_single_cpu_invariant PASSED            [ 40%]
test_simulator.py::test_simulator_illegal_transitions PASSED             [ 46%]
test_simulator.py::test_simulator_state_after_failed_operations PASSED   [ 53%]
test_simulator.py::test_simulator_event_logging_and_telemetry PASSED     [ 60%]
test_simulator.py::test_simulator_reset_and_sample_scenario PASSED       [ 66%]
test_simulator.py::test_guided_demo_workflow PASSED                      [ 73%]
test_simulator.py::test_fcfs_scheduling PASSED                           [ 80%]
test_simulator.py::test_round_robin_scheduling PASSED                    [ 86%]
test_simulator.py::test_sjf_scheduling PASSED                            [ 93%]
test_simulator.py::test_svg_diagram_rendering PASSED                     [100%]

============================= 15 passed in 0.07s ==============================
```

---

## 🎤 How to Use in a College Viva / Presentation

1. **Start the App:** Run `py -m streamlit run app.py`.
2. **Quick Overview:** Point out the dark developer interface, the live CPU status badge in the header, and the metric counters.
3. **Switch to '🎓 Guided Presentation Demo' Tab:**
   - Click **`Next Step`** to walk through the 11 steps sequentially.
   - Explain how `P101` (WebBrowser) gets created, dispatched, blocks on I/O, allows `P102` to run, completes I/O via hardware interrupt, gets preempted by timer interrupt, and finally terminates.
4. **Switch to '🖥️ Live State Simulator' Tab:**
   - Click **`Load 3 Tasks`** to demonstrate manual control.
   - Dispatch `P101`, and show that attempting to dispatch `P102` triggers an immediate **CPU Conflict Warning** explaining the single-core constraint.
   - Move `P101` to `WAITING` (I/O request), then dispatch `P102`.
   - Scroll down to the **Event Audit Log** and demonstrate filtering and the **Export to CSV** button.
5. **Switch to '📊 Advanced CPU Scheduling' Tab:**
   - Select **Round Robin**, adjust the **Time Quantum**, and show the **Plotly Gantt Chart** and the mathematical formulas for Turnaround Time and Waiting Time.
6. **Switch to '📖 OS Knowledge Base' Tab:**
   - Review the **State Transition Reference Matrix** to answer any theoretical question posed by the evaluator.

---

## 📌 Limitations & Future Enhancements
- **Single-Core Model:** Current implementation models a uniprocessor system. Future releases could support multi-core CPU scheduling (dual/quad-core dispatch pools).
- **Virtual Memory Paging:** Adding page fault interrupt simulations (e.g. `WAITING ➔ READY` on swap-in).
- **Priority Inversion & Deadlock:** Visualizing resource allocation graphs (RAG) and mutex contention between waiting processes.

---

## 👥 Credits
- Developed for **3rd Semester B.Tech CSE — Operating Systems Evaluation**.
- Designed and built with Python, Streamlit, Plotly, and modern OS pedagogical standards.
