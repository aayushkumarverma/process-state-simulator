import pandas as pd
import streamlit as st

from process import ProcessState
from simulator import ProcessSimulator


# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------

st.set_page_config(
    page_title="Process State Simulator",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Process State Simulator")

st.caption(
    "Interactive simulation of the standard 5-state process model "
    "in Operating Systems"
)


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "simulator" not in st.session_state:
    st.session_state.simulator = ProcessSimulator()

simulator = st.session_state.simulator


# -------------------------------------------------
# INFORMATION
# -------------------------------------------------

with st.expander("📘 About the 5-State Process Model"):

    st.markdown(
        """
A process can move through five main states:

**NEW → READY → RUNNING → WAITING → READY → RUNNING → TERMINATED**

- **NEW** — Process has just been created.
- **READY** — Process is waiting for CPU time.
- **RUNNING** — Process is currently executing.
- **WAITING** — Process is waiting for I/O or another event.
- **TERMINATED** — Process has completed execution.
"""
    )


# -------------------------------------------------
# CREATE PROCESS
# -------------------------------------------------

st.subheader("➕ Create Process")

with st.form("create_process_form"):

    col1, col2 = st.columns(2)

    with col1:

        pid = st.number_input(
            "Process ID (PID)",
            min_value=1,
            step=1,
            value=101,
        )

    with col2:

        process_name = st.text_input(
            "Process Name",
            placeholder="Example: WebBrowser",
        )

    create_button = st.form_submit_button(
        "Create Process",
        type="primary",
    )


if create_button:

    if not process_name.strip():

        st.warning("Please enter a process name.")

    else:

        try:

            simulator.create_process(
                int(pid),
                process_name.strip(),
            )

            st.success(
                f"{process_name.strip()} created successfully "
                f"with PID {int(pid)}."
            )

        except ValueError as error:

            st.error(str(error))


# -------------------------------------------------
# CURRENT STATES
# -------------------------------------------------

st.divider()

st.subheader("📊 Current Process States")

state_lists = simulator.get_state_lists()

state_names = [
    "NEW",
    "READY",
    "RUNNING",
    "WAITING",
    "TERMINATED",
]

state_icons = {
    "NEW": "🆕",
    "READY": "🟡",
    "RUNNING": "🟢",
    "WAITING": "🔵",
    "TERMINATED": "🔴",
}

columns = st.columns(5)

for column, state_name in zip(columns, state_names):

    with column:

        st.markdown(
            f"### {state_icons[state_name]} {state_name}"
        )

        processes = state_lists[state_name]

        if processes:

            for process in processes:

                st.info(
                    f"**{process.name}**\n\n"
                    f"PID: {process.pid}"
                )

        else:

            st.caption("No processes")


# -------------------------------------------------
# PROCESS CONTROL
# -------------------------------------------------

st.divider()

st.subheader("🎮 Process Control")

all_processes = sorted(
    simulator.get_all_processes(),
    key=lambda process: process.pid,
)


if not all_processes:

    st.info(
        "Create a process first to start the simulation."
    )

else:

    process_options = {
        f"PID {process.pid} — {process.name}": process
        for process in all_processes
    }

    selected_label = st.selectbox(
        "Select Process",
        list(process_options.keys()),
    )

    selected_process = process_options[selected_label]

    st.write(
        f"**Current State:** "
        f"`{selected_process.current_state.value}`"
    )

    st.write("### Available Actions")


    # -------------------------------------------------
    # NEW
    # -------------------------------------------------

    if selected_process.current_state == ProcessState.NEW:

        if st.button(
            "➡️ Admit to Ready Queue",
            type="primary",
        ):

            try:

                simulator.move_to_ready(
                    selected_process.pid
                )

                st.rerun()

            except ValueError as error:

                st.error(str(error))


    # -------------------------------------------------
    # READY
    # -------------------------------------------------

    elif selected_process.current_state == ProcessState.READY:

        cpu_busy = simulator.running_process is not None

        if cpu_busy:

            running = simulator.running_process

            st.warning(
                f"CPU is currently occupied by "
                f"{running.name} (PID {running.pid})."
            )

        if st.button(
            "▶️ Dispatch to CPU",
            type="primary",
            disabled=cpu_busy,
        ):

            try:

                simulator.run_process(
                    selected_process.pid
                )

                st.rerun()

            except ValueError as error:

                st.error(str(error))


    # -------------------------------------------------
    # RUNNING
    # -------------------------------------------------

    elif selected_process.current_state == ProcessState.RUNNING:

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "⏸️ Request I/O",
                use_container_width=True,
            ):

                try:

                    simulator.move_to_waiting(
                        selected_process.pid
                    )

                    st.rerun()

                except ValueError as error:

                    st.error(str(error))


        with col2:

            if st.button(
                "🔄 Interrupt / Preempt",
                use_container_width=True,
            ):

                try:

                    simulator.move_to_ready_from_running(
                        selected_process.pid
                    )

                    st.rerun()

                except ValueError as error:

                    st.error(str(error))


        with col3:

            if st.button(
                "⛔ Terminate",
                use_container_width=True,
            ):

                try:

                    simulator.terminate_process(
                        selected_process.pid
                    )

                    st.rerun()

                except ValueError as error:

                    st.error(str(error))


    # -------------------------------------------------
    # WAITING
    # -------------------------------------------------

    elif selected_process.current_state == ProcessState.WAITING:

        if st.button(
            "✅ I/O Complete",
            type="primary",
        ):

            try:

                simulator.resume_process(
                    selected_process.pid
                )

                st.rerun()

            except ValueError as error:

                st.error(str(error))


    # -------------------------------------------------
    # TERMINATED
    # -------------------------------------------------

    elif selected_process.current_state == ProcessState.TERMINATED:

        st.info(
            "This process has finished execution. "
            "No further transitions are possible."
        )


    # -------------------------------------------------
    # HISTORY
    # -------------------------------------------------

    st.divider()

    st.subheader("📜 State History")

    history = selected_process.get_history()

    history_path = " → ".join(
        entry["state"]
        for entry in history
    )

    st.markdown(
        f"### {history_path}"
    )

    history_df = pd.DataFrame(history)

    history_df = history_df.rename(
        columns={
            "state": "State",
            "timestamp": "Time",
        }
    )

    st.dataframe(
        history_df,
        hide_index=True,
        use_container_width=True,
    )


# -------------------------------------------------
# ALL PROCESSES
# -------------------------------------------------

all_processes = sorted(
    simulator.get_all_processes(),
    key=lambda process: process.pid,
)

if all_processes:

    st.divider()

    st.subheader("📋 All Processes")

    process_data = []

    for process in all_processes:

        process_data.append(
            {
                "PID": process.pid,
                "Process Name": process.name,
                "Current State": process.current_state.value,
                "Transitions": len(process.state_history) - 1,
            }
        )

    process_df = pd.DataFrame(process_data)

    st.dataframe(
        process_df,
        hide_index=True,
        use_container_width=True,
    )


# -------------------------------------------------
# CPU STATUS
# -------------------------------------------------

st.divider()

st.subheader("🖥️ CPU Status")

if simulator.running_process is not None:

    running = simulator.running_process

    st.success(
        f"CPU currently executing: "
        f"**{running.name} (PID {running.pid})**"
    )

else:

    st.warning(
        "CPU is currently IDLE."
    )


# -------------------------------------------------
# RESET
# -------------------------------------------------

st.divider()

if st.button("🔄 Reset Simulation"):

    st.session_state.simulator = ProcessSimulator()

    st.rerun()
