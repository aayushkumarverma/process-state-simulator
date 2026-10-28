"""
ProcessLab — Advanced Operating System Process State Simulator.
Main Streamlit Application Interface.

Authors: B.Tech CSE Operating Systems Group Project
Technology Stack: Python, Streamlit, Plotly, Pandas
"""

import io
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from process import Process, ProcessState
from simulator import ProcessSimulator
from guided_demo import GuidedDemoManager
from diagram import render_svg_diagram, STATE_INFO, TRANSITION_INFO
import scheduler


# =============================================================================
# 1. STREAMLIT CONFIGURATION & CUSTOM DARK THEME CSS
# =============================================================================

st.set_page_config(
    page_title="ProcessLab — OS Process State Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Dark Developer Theme CSS
CUSTOM_CSS = """
<style>
/* Main Background and Typography */
.stApp {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Metric Cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(56, 189, 248, 0.35);
    transform: translateY(-2px);
}
div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

/* Header Container */
.header-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}

.brand-badge {
    display: inline-block;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.cpu-badge-active {
    display: inline-flex;
    align-items: center;
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}
.cpu-badge-idle {
    display: inline-flex;
    align-items: center;
    background: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.25);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}

/* Queue Column Cards */
.queue-column-header {
    padding: 10px 14px;
    border-radius: 8px 8px 0 0;
    font-weight: 700;
    font-size: 0.95rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: none;
}

.queue-column-body {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 0 0 10px 10px;
    padding: 12px;
    min-height: 240px;
}

.process-card {
    background: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    transition: all 0.2s ease;
}
.process-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.cpu-active-card {
    background: linear-gradient(135deg, rgba(6, 78, 59, 0.4) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1.5px solid #10b981;
    box-shadow: 0 0 18px rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 8px 8px 0 0;
    color: #94a3b8;
    padding: 8px 20px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(56, 189, 248, 0.12) !important;
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Subdued Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    overflow: hidden;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. SESSION STATE INITIALIZATION
# =============================================================================

if "simulator" not in st.session_state:
    st.session_state.simulator = ProcessSimulator()

if "guided_demo" not in st.session_state:
    st.session_state.guided_demo = GuidedDemoManager()

if "selected_pid" not in st.session_state:
    st.session_state.selected_pid = None

if "inspect_state" not in st.session_state:
    st.session_state.inspect_state = "READY"

simulator: ProcessSimulator = st.session_state.simulator
guided_demo: GuidedDemoManager = st.session_state.guided_demo


# =============================================================================
# 3. SIDEBAR CONTROLS & NAVIGATION
# =============================================================================

with st.sidebar:
    st.markdown("### ⚡ ProcessLab Controls")
    st.caption("OS Kernel & Process Management Suite")

    # Quick Scenario Loaders
    st.markdown("#### 📂 Presets & Scenarios")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🚀 Load 3 Tasks", use_container_width=True, help="Load WebBrowser, MusicPlayer, CodeCompiler"):
            simulator.load_sample_scenario()
            st.session_state.selected_pid = 101
            st.toast("Loaded standard 3-process OS workload!", icon="🚀")
            st.rerun()

    with col_s2:
        if st.button("🔄 Clean Reset", use_container_width=True, help="Reset all queues, step counters, and events"):
            simulator.reset()
            guided_demo.reset(simulator)
            st.session_state.selected_pid = None
            st.toast("Simulator reset to clean state.", icon="🧹")
            st.rerun()

    st.divider()

    # Create Process Quick Form
    st.markdown("#### ➕ Create New Process")
    with st.form("sidebar_create_process"):
        new_pid = st.number_input(
            "Process ID (PID)",
            min_value=1,
            max_value=99999,
            step=1,
            value=104
        )
        new_name = st.text_input("Process Name", placeholder="e.g. VideoRenderer")
        new_priority = st.slider("Priority", min_value=1, max_value=5, value=2, help="1 = Standard, 5 = Realtime")
        new_burst = st.number_input("Est. CPU Burst Units", min_value=1, max_value=50, value=5)

        submit_create = st.form_submit_button("Allocate PCB & Create", type="primary", use_container_width=True)

    if submit_create:
        if not new_name.strip():
            st.error("Process name cannot be empty.")
        elif simulator.get_process(int(new_pid)) is not None:
            st.error(f"Process PID {int(new_pid)} already exists! PIDs must be unique.")
        else:
            try:
                proc = simulator.create_process(
                    pid=int(new_pid),
                    name=new_name.strip(),
                    priority=int(new_priority),
                    burst_time=int(new_burst)
                )
                st.session_state.selected_pid = proc.pid
                st.success(f"PCB allocated for '{proc.name}' (PID #{proc.pid}) in NEW state.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.divider()

    # Simulator Telemetry
    st.markdown("#### 📈 Kernel Telemetry")
    counts = simulator.get_state_counts()
    st.write(f"**Simulation Step:** `{simulator.step_counter}`")
    st.write(f"**Total Events Logged:** `{len(simulator.get_event_log())}`")
    st.write(f"**Multiprogramming Level:** `{counts['total']}`")

    st.caption("Developed for B.Tech CSE Operating Systems Evaluation.")


# =============================================================================
# 4. DASHBOARD HEADER & LIVE METRICS (PHASE 1)
# =============================================================================

counts = simulator.get_state_counts()
running_proc = simulator.running_process

# Header Container
cpu_badge = (
    f'<div class="cpu-badge-active">⚡ CPU ACTIVE — {running_proc.name} (PID #{running_proc.pid})</div>'
    if running_proc is not None
    else '<div class="cpu-badge-idle">⚪ CPU CORE IDLE</div>'
)

header_html = f"""
<div class="header-container">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
    <div>
      <span class="brand-badge">B.Tech CSE OS Project</span>
      <h1 style="margin: 0; font-size: 2rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
        ProcessLab <span style="font-weight: 400; color: #94a3b8; font-size: 1.25rem;">— OS Process State Simulator</span>
      </h1>
      <p style="margin: 6px 0 0 0; color: #cbd5e1; font-size: 0.95rem; max-width: 760px;">
        Interactive discrete simulation of the canonical 5-State Operating System Process Lifecycle
        (NEW, READY, RUNNING, WAITING, and TERMINATED) with real-time queue synchronization and kernel event tracking.
      </p>
    </div>
    <div>
      {cpu_badge}
    </div>
  </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Dashboard Live Metrics Row
m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
with m_col1:
    st.metric(label="Total Processes", value=counts["total"], delta=f"{counts['NEW']} In Pool" if counts['NEW'] else None)
with m_col2:
    st.metric(label="Ready Queue", value=counts["READY"], delta="Awaiting CPU" if counts["READY"] else None)
with m_col3:
    st.metric(
        label="Running Core",
        value=f"PID #{running_proc.pid}" if running_proc else "IDLE",
        delta="1 Core Active" if running_proc else "Free"
    )
with m_col4:
    st.metric(label="Waiting (I/O)", value=counts["WAITING"], delta="Blocked" if counts["WAITING"] else None)
with m_col5:
    st.metric(label="Terminated", value=counts["TERMINATED"], delta="Completed" if counts["TERMINATED"] else None)

st.write("")


# =============================================================================
# 5. MAIN TABBED APPLICATION WORKSPACE
# =============================================================================

tab_sim, tab_demo, tab_sched, tab_learn = st.tabs([
    "🖥️ Live State Simulator",
    "🎓 Guided Presentation Demo",
    "📊 Advanced CPU Scheduling",
    "📖 OS Knowledge Base"
])


# =============================================================================
# TAB 1: LIVE STATE SIMULATOR (PHASES 1, 2, 3, 4, 5)
# =============================================================================

with tab_sim:
    # -------------------------------------------------------------------------
    # PHASE 2: INTERACTIVE FIVE-STATE DIAGRAM
    # -------------------------------------------------------------------------
    st.markdown("### 🔄 5-State Process Lifecycle Diagram")
    st.caption("Live graphical state diagram synchronized with simulator kernel. Highlights active state and recent transition.")

    # Synchronize selected process state
    selected_process_obj = simulator.get_process(st.session_state.selected_pid) if st.session_state.selected_pid else None
    active_state_for_diagram = selected_process_obj.current_state.value if selected_process_obj else None

    # Render High-Resolution SVG Diagram
    svg_diagram = render_svg_diagram(
        state_counts=counts,
        selected_state=active_state_for_diagram,
        last_transition=simulator.last_transition,
        selected_pid=selected_process_obj.pid if selected_process_obj else None
    )
    # Render SVG in an isolated HTML frame so Streamlit does not display its markup as text.
    st.components.v1.html(svg_diagram, height=410, scrolling=False)

    # State & Transition Interactive Inspector
    with st.expander("🔍 Interactive State & Transition Inspector", expanded=False):
        insp_col1, insp_col2 = st.columns([1, 2])
        with insp_col1:
            inspect_target = st.selectbox(
                "Select State or Transition to Inspect:",
                options=[
                    "STATE: NEW", "STATE: READY", "STATE: RUNNING", "STATE: WAITING", "STATE: TERMINATED",
                    "TRANSITION: Admit (NEW -> READY)",
                    "TRANSITION: Dispatch (READY -> RUNNING)",
                    "TRANSITION: Preempt (RUNNING -> READY)",
                    "TRANSITION: I/O Request (RUNNING -> WAITING)",
                    "TRANSITION: I/O Complete (WAITING -> READY)",
                    "TRANSITION: Terminate (RUNNING -> TERMINATED)"
                ]
            )
        with insp_col2:
            if inspect_target.startswith("STATE:"):
                state_key = inspect_target.replace("STATE: ", "").strip()
                s_data = STATE_INFO.get(state_key, {})
                st.markdown(f"#### {s_data.get('title', state_key)}")
                st.markdown(f"**Description:** {s_data.get('desc')}")
                st.markdown(f"**Managing Subsystem:** `{s_data.get('scheduler')}`")
                st.markdown(f"**Allocated Hardware Resources:** {s_data.get('resources')}")
            else:
                raw_act = inspect_target.split(":")[1].split("(")[0].strip().upper()
                act_map = {
                    "ADMIT": "ADMIT",
                    "DISPATCH": "DISPATCH",
                    "PREEMPT": "PREEMPT",
                    "I/O REQUEST": "I/O_REQUEST",
                    "I/O COMPLETE": "I/O_COMPLETE",
                    "TERMINATE": "TERMINATE"
                }
                t_key = act_map.get(raw_act, "ADMIT")
                t_data = TRANSITION_INFO.get(t_key, {})
                st.markdown(f"#### Transition: {t_data.get('label')} ({t_data.get('from')} ➔ {t_data.get('to')})")
                st.markdown(f"**Triggering Cause:** {t_data.get('trigger')}")
                st.markdown(f"**Kernel Subsystem / Actor:** `{t_data.get('actor')}`")
                st.markdown(f"**OS Concept:** {t_data.get('os_concept')}")

    st.divider()

    # -------------------------------------------------------------------------
    # PHASE 4: STATE COLUMNS & QUEUE VISUALIZATION
    # -------------------------------------------------------------------------
    st.markdown("### 🗂️ Process Queues & Execution Core")
    st.caption("Physical queue layout showing processes currently resident in each state.")

    state_lists = simulator.get_state_lists()
    qc_new, qc_ready, qc_running, qc_waiting, qc_term = st.columns(5)

    # 1. NEW POOL
    with qc_new:
        st.markdown(
            '<div class="queue-column-header" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">'
            f'<span>🆕 NEW Pool</span><span>{len(state_lists["NEW"])}</span></div>',
            unsafe_allow_html=True
        )
        with st.container():
            if state_lists["NEW"]:
                for p in state_lists["NEW"]:
                    is_sel = (selected_process_obj and selected_process_obj.pid == p.pid)
                    border = "1.5px solid #38bdf8" if is_sel else "1px solid rgba(255,255,255,0.06)"
                    st.markdown(
                        f'<div class="process-card" style="border: {border};">'
                        f'<div style="font-weight: 700; color: #f8fafc;">PID #{p.pid} — {p.name}</div>'
                        f'<div style="font-size: 0.8rem; color: #94a3b8;">Burst: {p.burst_time} | Priority: {p.priority}</div>'
                        f'<div style="font-size: 0.75rem; color: #38bdf8; margin-top: 4px;">Created: {p.created_at}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No processes in NEW pool.")

    # 2. READY QUEUE (FIFO)
    with qc_ready:
        st.markdown(
            '<div class="queue-column-header" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b;">'
            f'<span>⏳ READY Queue</span><span>{len(state_lists["READY"])}</span></div>',
            unsafe_allow_html=True
        )
        with st.container():
            if state_lists["READY"]:
                for idx, p in enumerate(state_lists["READY"]):
                    is_sel = (selected_process_obj and selected_process_obj.pid == p.pid)
                    border = "1.5px solid #f59e0b" if is_sel else "1px solid rgba(255,255,255,0.06)"
                    tag = "Next in line" if idx == 0 else f"Queue Pos #{idx+1}"
                    st.markdown(
                        f'<div class="process-card" style="border: {border};">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<span style="font-weight: 700; color: #f8fafc;">PID #{p.pid} — {p.name}</span>'
                        f'<span style="font-size: 0.7rem; background: rgba(245,158,11,0.2); color:#f59e0b; padding:2px 6px; border-radius:10px;">{tag}</span>'
                        f'</div>'
                        f'<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Burst: {p.burst_time} | Priority: {p.priority}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Ready queue is empty.")

    # 3. RUNNING (SINGLE-CPU CORE)
    with qc_running:
        st.markdown(
            '<div class="queue-column-header" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">'
            f'<span>⚡ CPU CORE</span><span>{1 if simulator.running_process else 0}/1</span></div>',
            unsafe_allow_html=True
        )
        with st.container():
            if simulator.running_process is not None:
                p = simulator.running_process
                st.markdown(
                    f'<div class="cpu-active-card">'
                    f'<div style="font-size: 0.75rem; color: #10b981; font-weight: 700; letter-spacing: 0.05em;">EXECUTING ON CPU</div>'
                    f'<div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; margin: 4px 0;">PID #{p.pid}</div>'
                    f'<div style="font-size: 0.95rem; font-weight: 600; color: #38bdf8;">{p.name}</div>'
                    f'<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px;">Est. Burst: {p.burst_time} units</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="background: #1e293b; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px; padding: 24px 12px; text-align: center;">'
                    '<div style="font-size: 1.5rem; color: #64748b;">💤</div>'
                    '<div style="font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-top: 6px;">CPU is currently IDLE</div>'
                    '<div style="font-size: 0.75rem; color: #64748b;">Dispatch a process from READY</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

    # 4. WAITING QUEUE (I/O)
    with qc_waiting:
        st.markdown(
            '<div class="queue-column-header" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">'
            f'<span>⏸️ WAITING Queue</span><span>{len(state_lists["WAITING"])}</span></div>',
            unsafe_allow_html=True
        )
        with st.container():
            if state_lists["WAITING"]:
                for p in state_lists["WAITING"]:
                    is_sel = (selected_process_obj and selected_process_obj.pid == p.pid)
                    border = "1.5px solid #818cf8" if is_sel else "1px solid rgba(255,255,255,0.06)"
                    st.markdown(
                        f'<div class="process-card" style="border: {border};">'
                        f'<div style="font-weight: 700; color: #f8fafc;">PID #{p.pid} — {p.name}</div>'
                        f'<div style="font-size: 0.8rem; color: #818cf8; margin-top: 2px;">Awaiting I/O completion...</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No processes blocked on I/O.")

    # 5. TERMINATED
    with qc_term:
        st.markdown(
            '<div class="queue-column-header" style="background: rgba(244, 63, 94, 0.15); color: #f43f5e;">'
            f'<span>🏁 TERMINATED</span><span>{len(state_lists["TERMINATED"])}</span></div>',
            unsafe_allow_html=True
        )
        with st.container():
            if state_lists["TERMINATED"]:
                for p in state_lists["TERMINATED"]:
                    is_sel = (selected_process_obj and selected_process_obj.pid == p.pid)
                    border = "1.5px solid #f43f5e" if is_sel else "1px solid rgba(255,255,255,0.06)"
                    st.markdown(
                        f'<div class="process-card" style="border: {border};">'
                        f'<div style="font-weight: 700; color: #cbd5e1; text-decoration: line-through;">PID #{p.pid} — {p.name}</div>'
                        f'<div style="font-size: 0.75rem; color: #f43f5e; margin-top: 2px;">Execution Finished</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No processes terminated.")

    st.divider()

    # -------------------------------------------------------------------------
    # PHASE 3: PROCESS SELECTION & SIMULATION CONTROLS
    # -------------------------------------------------------------------------
    st.markdown("### 🎮 Process Control Panel")
    all_procs = simulator.get_all_processes()

    if not all_procs:
        st.info("No processes exist currently in the simulator. Create a process via the sidebar or load the 3-process preset.")
    else:
        # Process Selector
        proc_options = {f"PID #{p.pid} — {p.name} (Current: {p.current_state.value})": p.pid for p in sorted(all_procs, key=lambda x: x.pid)}
        default_idx = 0
        if st.session_state.selected_pid in proc_options.values():
            default_idx = list(proc_options.values()).index(st.session_state.selected_pid)

        sel_label = st.selectbox(
            "Select Process to Manage:",
            options=list(proc_options.keys()),
            index=default_idx
        )
        selected_pid = proc_options[sel_label]
        st.session_state.selected_pid = selected_pid
        sel_proc = simulator.get_process(selected_pid)

        if sel_proc:
            ctrl_col1, ctrl_col2 = st.columns([1, 2])

            with ctrl_col1:
                # Process PCB Summary Card
                st.markdown(
                    f'<div style="background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px;">'
                    f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">SELECTED PROCESS PCB</div>'
                    f'<h3 style="margin: 4px 0; color: #f8fafc;">PID #{sel_proc.pid} — {sel_proc.name}</h3>'
                    f'<p style="margin: 0; color: #38bdf8; font-weight: 600;">State: <span style="background:rgba(56,189,248,0.15); padding:2px 8px; border-radius:6px;">{sel_proc.current_state.value}</span></p>'
                    f'<div style="margin-top: 10px; font-size: 0.85rem; color: #cbd5e1; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">'
                    f'<div>Priority: <b>{sel_proc.priority}</b></div>'
                    f'<div>Est. Burst: <b>{sel_proc.burst_time} units</b></div>'
                    f'<div>Created: <b>{sel_proc.created_at}</b></div>'
                    f'<div>Transitions: <b>{len(sel_proc.state_history)-1}</b></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with ctrl_col2:
                st.markdown("#### Permitted Kernel Actions")
                state = sel_proc.current_state

                # State-specific valid actions
                if state == ProcessState.NEW:
                    st.caption("This process is initialized in the NEW pool awaiting admission into main memory.")
                    if st.button("➡️ Admit to Ready Queue (Long-Term Scheduler)", type="primary", use_container_width=True):
                        try:
                            simulator.move_to_ready(sel_proc.pid)
                            st.toast(f"PID #{sel_proc.pid} admitted to Ready Queue!", icon="✅")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

                elif state == ProcessState.READY:
                    cpu_busy = (simulator.running_process is not None)
                    if cpu_busy:
                        r_p = simulator.running_process
                        st.warning(f"⚠️ CPU is currently busy executing PID #{r_p.pid} ('{r_p.name}'). The CPU must become free before dispatching.")

                    if st.button("▶️ Dispatch to CPU (Short-Term Scheduler)", type="primary", disabled=cpu_busy, use_container_width=True):
                        try:
                            simulator.run_process(sel_proc.pid)
                            st.toast(f"Dispatched PID #{sel_proc.pid} to CPU!", icon="⚡")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

                elif state == ProcessState.RUNNING:
                    st.caption("This process is currently running on the CPU core. Select an OS transition:")
                    act_c1, act_c2, act_c3 = st.columns(3)
                    with act_c1:
                        if st.button("⏸️ Request I/O\n(Yield to WAITING)", use_container_width=True):
                            try:
                                simulator.move_to_waiting(sel_proc.pid)
                                st.toast(f"PID #{sel_proc.pid} issued I/O wait and yielded CPU.", icon="⏸️")
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err))

                    with act_c2:
                        if st.button("🔄 Timer Interrupt\n(Preempt to READY)", use_container_width=True):
                            try:
                                simulator.move_to_ready_from_running(sel_proc.pid)
                                st.toast(f"PID #{sel_proc.pid} preempted back to Ready Queue.", icon="🔄")
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err))

                    with act_c3:
                        if st.button("⛔ Terminate\n(Finish Execution)", type="primary", use_container_width=True):
                            try:
                                simulator.terminate_process(sel_proc.pid)
                                st.toast(f"PID #{sel_proc.pid} terminated successfully.", icon="🏁")
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err))

                elif state == ProcessState.WAITING:
                    st.caption("This process is blocked in WAITING state waiting for an I/O device controller.")
                    if st.button("✅ I/O Complete Interrupt (Move to READY)", type="primary", use_container_width=True):
                        try:
                            simulator.resume_process(sel_proc.pid)
                            st.toast(f"I/O finished: PID #{sel_proc.pid} returned to Ready Queue!", icon="✅")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

                elif state == ProcessState.TERMINATED:
                    st.info("🏁 This process has completed execution. Its resources have been reclaimed. In Operating Systems, terminated processes cannot be re-executed.")

    st.divider()

    # -------------------------------------------------------------------------
    # PHASE 5: EVENT AUDIT LOG & LIFECYCLE TIMELINE
    # -------------------------------------------------------------------------
    st.markdown("### 📜 Kernel Event Log & Process Lifecycle Timeline")
    st.caption("Chronological audit log of all scheduling transitions and lifecycle milestones.")

    event_log = simulator.get_event_log()
    if not event_log:
        st.info("No kernel events recorded yet. Create or transition a process to see events populate.")
    else:
        log_df = pd.DataFrame(event_log)

        # Filters and CSV Export
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            filter_pid = st.selectbox(
                "Filter Log by Process:",
                options=["All Processes"] + [f"PID #{p.pid} ({p.name})" for p in all_procs]
            )
        with f_col2:
            display_count = st.selectbox("Show Latest Entries:", options=[10, 25, 50, "All"], index=1)
        with f_col3:
            # CSV Download Button
            csv_data = log_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Log to CSV",
                data=csv_data,
                file_name="processlab_simulation_events.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Apply PID filter
        filtered_df = log_df.copy()
        if filter_pid != "All Processes":
            selected_f_pid = int(filter_pid.split("#")[1].split(" ")[0])
            filtered_df = filtered_df[filtered_df["pid"] == selected_f_pid]

        if display_count != "All":
            filtered_df = filtered_df.tail(int(display_count))

        # Render styled event log table
        st.dataframe(
            filtered_df.rename(columns={
                "step": "Step",
                "timestamp": "Time",
                "pid": "PID",
                "name": "Process",
                "from_state": "From",
                "to_state": "To",
                "action": "Action",
                "reason": "Kernel Reason",
                "status": "Status"
            }),
            use_container_width=True,
            hide_index=True
        )

        # Visual Process Lifecycle Path
        if selected_process_obj:
            with st.expander(f"📊 Detailed Lifecycle Timeline for PID #{selected_process_obj.pid} ({selected_process_obj.name})", expanded=True):
                p_hist = selected_process_obj.get_history()
                if len(p_hist) > 1:
                    path_str = " ➔ ".join([f"**{entry['state']}**" for entry in p_hist])
                    st.markdown(f"**State Progression:** {path_str}")

                    # Plotly Step chart of state transitions
                    step_data = []
                    state_y_map = {"NEW": 1, "READY": 2, "RUNNING": 3, "WAITING": 2.5, "TERMINATED": 0}
                    for h in p_hist:
                        step_data.append({
                            "Step": h.get("step", 0),
                            "State": h["state"],
                            "StateLevel": state_y_map.get(h["state"], 1),
                            "Time": h["timestamp"],
                            "Reason": h.get("reason", "")
                        })
                    hist_df = pd.DataFrame(step_data)

                    fig_hist = px.line(
                        hist_df,
                        x="Step",
                        y="State",
                        markers=True,
                        text="State",
                        title=f"Lifecycle Transition Path: PID #{selected_process_obj.pid}",
                        template="plotly_dark"
                    )
                    fig_hist.update_traces(
                        line=dict(color="#38bdf8", width=3),
                        marker=dict(size=10, color="#f59e0b")
                    )
                    fig_hist.update_layout(
                        paper_bgcolor="#0f172a",
                        plot_bgcolor="#1e293b",
                        height=260,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.caption("Process has only been created in NEW state so far.")


# =============================================================================
# TAB 2: GUIDED DEMONSTRATION MODE (PHASE 6)
# =============================================================================

with tab_demo:
    st.markdown("### 🎓 Guided OS Presentation Demonstration")
    st.caption("Step-by-step walkthrough designed specifically for your college project evaluation and viva.")

    step_info = guided_demo.get_current_info()
    curr_step = guided_demo.step_index
    total_steps = guided_demo.total_steps

    # Progress Bar
    progress_val = curr_step / total_steps if total_steps > 0 else 0.0
    st.progress(progress_val, text=f"Presentation Progress: Step {curr_step} of {total_steps}")

    # Demo Control Buttons
    d_col1, d_col2, d_col3, d_col4 = st.columns([1.5, 1.5, 2, 2])
    with d_col1:
        if st.button("⏩ Next Step", type="primary", use_container_width=True, disabled=not guided_demo.can_advance()):
            guided_demo.advance(simulator)
            st.session_state.selected_pid = 101
            st.rerun()

    with d_col2:
        if st.button("🔄 Reset Demo", use_container_width=True):
            guided_demo.reset(simulator)
            st.session_state.selected_pid = None
            st.rerun()

    with d_col3:
        st.write(f"**Current State:** `{step_info.get('badge')}`")

    with d_col4:
        st.write(f"**Target Process:** `PID #101` or `PID #102`")

    st.write("")

    # Card Displaying the Current Step Information
    st.markdown(
        f'<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1.5px solid #38bdf8; border-radius: 12px; padding: 22px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:4px 10px; border-radius:12px; font-weight:700; font-size:0.85rem;">'
        f'STEP {curr_step} OF {total_steps}: {step_info["badge"]}</span>'
        f'<span style="color:#94a3b8; font-size:0.85rem;">Action: {step_info["action_desc"]}</span>'
        f'</div>'
        f'<h2 style="margin: 10px 0 6px 0; color: #f8fafc; font-size: 1.4rem;">{step_info["title"]}</h2>'
        f'<p style="color: #cbd5e1; font-size: 1rem; margin-bottom: 14px;">{step_info["description"]}</p>'
        f'<div style="background: rgba(15, 23, 42, 0.7); border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 4px;">'
        f'<div style="color: #10b981; font-weight: 700; font-size: 0.85rem; margin-bottom: 4px;">OPERATING SYSTEMS CONCEPT EXPLANATION:</div>'
        f'<div style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.5;">{step_info["os_concept"]}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.write("")
    st.markdown("#### Live State Snapshot During Demonstration")
    # Mini state view
    d_m1, d_m2, d_m3, d_m4, d_m5 = st.columns(5)
    d_counts = simulator.get_state_counts()
    with d_m1:
        st.metric("NEW Pool", d_counts["NEW"])
    with d_m2:
        st.metric("READY Queue", d_counts["READY"])
    with d_m3:
        st.metric("RUNNING Core", f"PID #{simulator.running_process.pid}" if simulator.running_process else "IDLE")
    with d_m4:
        st.metric("WAITING Queue", d_counts["WAITING"])
    with d_m5:
        st.metric("TERMINATED", d_counts["TERMINATED"])


# =============================================================================
# TAB 3: ADVANCED CPU SCHEDULING MODE (PHASE 8)
# =============================================================================

with tab_sched:
    st.markdown("### 📊 Advanced CPU Scheduling Simulation Engine")
    st.caption("Discrete algorithmic simulation of Short-Term CPU Scheduling algorithms (FCFS, Round Robin, SJF) with Gantt charts.")

    st.info(
        "💡 **Academic Note:** This section is a discrete algorithmic simulation of CPU scheduling. "
        "It models how the Short-Term Scheduler dispatches processes from the READY queue onto the CPU "
        "based on arrival times and burst times."
    )

    sched_col1, sched_col2 = st.columns([1, 2])

    with sched_col1:
        st.markdown("#### Simulation Parameters")
        sched_algo = st.selectbox(
            "Select Scheduling Algorithm:",
            options=["Round Robin (RR)", "First-Come, First-Served (FCFS)", "Shortest Job First (SJF - Non-Preemptive)"]
        )

        quantum = 2
        if "Round Robin" in sched_algo:
            quantum = st.slider("Time Quantum (Time Slices):", min_value=1, max_value=10, value=2)

        st.markdown("##### Process Workload Config")
        # Default process dataset
        default_workload = [
            {"pid": 1, "name": "P1 (Browser)", "arrival": 0, "burst": 5},
            {"pid": 2, "name": "P2 (Music)", "arrival": 1, "burst": 3},
            {"pid": 3, "name": "P3 (Compiler)", "arrival": 2, "burst": 8},
            {"pid": 4, "name": "P4 (Editor)", "arrival": 3, "burst": 6},
        ]

        workload_input = []
        for i, item in enumerate(default_workload):
            with st.expander(f"Config: {item['name']}", expanded=(i < 2)):
                c_arr, c_bst = st.columns(2)
                with c_arr:
                    arr = st.number_input(f"Arrival Time", min_value=0, max_value=50, value=item["arrival"], key=f"arr_{i}")
                with c_bst:
                    bst = st.number_input(f"Burst Time", min_value=1, max_value=50, value=item["burst"], key=f"bst_{i}")
                workload_input.append(
                    scheduler.ScheduledProcessInput(
                        pid=item["pid"],
                        name=item["name"],
                        arrival_time=arr,
                        burst_time=bst
                    )
                )

    with sched_col2:
        st.markdown("#### Execution Results & Gantt Chart")

        # Run selected scheduling algorithm
        if "Round Robin" in sched_algo:
            sim_output = scheduler.simulate_round_robin(workload_input, time_quantum=quantum)
        elif "First-Come" in sched_algo:
            sim_output = scheduler.simulate_fcfs(workload_input)
        else:
            sim_output = scheduler.simulate_sjf(workload_input)

        # Metrics display
        res_m1, res_m2, res_m3, res_m4 = st.columns(4)
        with res_m1:
            st.metric("Avg Waiting Time", f"{sim_output.avg_waiting_time} units")
        with res_m2:
            st.metric("Avg Turnaround Time", f"{sim_output.avg_turnaround_time} units")
        with res_m3:
            st.metric("Total Makespan", f"{sim_output.total_time} units")
        with res_m4:
            st.metric("CPU Utilization", f"{sim_output.cpu_utilization}%")

        # Plotly Gantt Chart
        gantt_records = []
        color_palette = ["#38bdf8", "#f59e0b", "#10b981", "#818cf8", "#f43f5e", "#64748b"]

        for block in sim_output.gantt_chart:
            gantt_records.append({
                "Task": "CPU Core",
                "Start": block["start"],
                "Finish": block["end"],
                "Duration": block["end"] - block["start"],
                "Process": block["name"],
                "PID": block["pid"]
            })

        if gantt_records:
            gantt_df = pd.DataFrame(gantt_records)
            fig_gantt = px.bar(
                gantt_df,
                base="Start",
                x="Duration",
                y="Task",
                color="Process",
                orientation="h",
                text="Process",
                title=f"CPU Execution Timeline (Gantt Chart) — {sim_output.algorithm}",
                template="plotly_dark",
                color_discrete_sequence=color_palette
            )
            fig_gantt.update_layout(
                paper_bgcolor="#0f172a",
                plot_bgcolor="#1e293b",
                height=220,
                xaxis_title="Time Units",
                yaxis_title="",
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=True
            )
            st.plotly_chart(fig_gantt, use_container_width=True)

        # Results Table
        st.markdown("##### Detailed Process Completion Breakdown")
        table_rows = []
        for r in sim_output.process_results:
            table_rows.append({
                "PID": r.pid,
                "Process Name": r.name,
                "Arrival Time (AT)": r.arrival_time,
                "Burst Time (BT)": r.burst_time,
                "Completion Time (CT)": r.completion_time,
                "Turnaround Time (TAT = CT - AT)": r.turnaround_time,
                "Waiting Time (WT = TAT - BT)": r.waiting_time,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 4: OPERATING SYSTEMS LEARNING SECTION (PHASE 7)
# =============================================================================

with tab_learn:
    st.markdown("### 📖 Operating Systems Process State Theory")
    st.caption("Comprehensive educational reference for 3rd semester B.Tech Computer Science examination and viva preparation.")

    edu_c1, edu_c2 = st.columns([1, 1])

    with edu_c1:
        with st.expander("1. What is a Process and Process Control Block (PCB)?", expanded=True):
            st.markdown(
                """
                - **Program vs. Process:** A *program* is a passive entity stored on disk (executable file).
                  A *process* is an active entity—a program loaded into memory and actively executing instructions.
                - **Process Control Block (PCB):** The OS kernel maintains a data structure for every active process, containing:
                  - **PID (Process Identifier):** Unique integer ID.
                  - **Process State:** Current state (NEW, READY, RUNNING, WAITING, TERMINATED).
                  - **Program Counter (PC):** Address of the next CPU instruction to execute.
                  - **CPU Registers:** Accumulators, index registers, stack pointers.
                  - **CPU-Scheduling Info:** Priority, scheduling queue pointers.
                  - **Memory-Management Info:** Page tables, segment tables, base and limit registers.
                  - **Accounting & I/O Info:** Amount of CPU used, open files list, I/O devices allocated.
                """
            )

        with st.expander("2. The Canonical 5-State Process Model", expanded=True):
            st.markdown(
                """
                In modern multitasking operating systems, a process transitions through 5 fundamental states:
                1. **NEW:** The process is being created and its PCB allocated, but it has not yet been admitted to main memory.
                2. **READY:** The process is in main memory and possesses all required resources; it is waiting only for the CPU scheduler to allocate CPU execution time.
                3. **RUNNING:** The process's instructions are actively executing on the CPU core. (In a single-core model, exactly **one** process is running at a time).
                4. **WAITING (Blocked):** The process cannot execute because it is waiting for an external event (e.g. disk I/O, network packet, keyboard input, or synchronization lock).
                5. **TERMINATED:** The process has completed execution or was killed; its resources are deallocated by the kernel.
                """
            )

        with st.expander("3. Crucial Distinction: READY vs. WAITING", expanded=True):
            st.markdown(
                """
                > **Viva Question:** *What is the difference between READY and WAITING states?*

                - **READY:** The process is completely capable of executing **right now** if given a CPU core. It has memory and all necessary data. It is only waiting for the CPU Scheduler.
                - **WAITING:** The process **cannot** run even if the CPU is 100% free! It is waiting for an external hardware device or event.
                - **Key Rule:** A process in WAITING can **never** jump straight to RUNNING. When its I/O finishes, it must return to the **READY** queue first and wait to be scheduled.
                """
            )

    with edu_c2:
        with st.expander("4. Operating System Schedulers & Dispatcher", expanded=True):
            st.markdown(
                """
                - **Long-Term Scheduler (Job Scheduler):**
                  - Controls the *degree of multiprogramming* (number of processes in memory).
                  - Decides which processes from disk/pool transition from `NEW ➔ READY`.
                - **Short-Term Scheduler (CPU Scheduler):**
                  - Executes frequently (every few milliseconds).
                  - Selects which ready process transitions from `READY ➔ RUNNING`.
                - **CPU Dispatcher:**
                  - The module that gives control of the CPU to the process selected by the short-term scheduler.
                  - Performs **Context Switching** (saving old process registers, loading new process registers).
                  - Switches to user mode and jumps to the proper location in the program.
                """
            )

        with st.expander("5. Real-World Multitasking Example", expanded=True):
            st.markdown(
                """
                **Scenario: Web Browser & Music Player**
                1. You launch your **Web Browser** (`P101`). It enters `NEW`, then gets admitted to `READY`.
                2. The CPU dispatcher runs `P101` (`RUNNING`).
                3. You click a link to download a webpage. `P101` issues a network socket `read()` system call.
                4. Since network packets take milliseconds to arrive (millions of CPU cycles!), `P101` transitions to `WAITING`.
                5. Instead of wasting CPU cycles idling, the OS scheduler dispatches your **Music Player** (`P102`) from `READY ➔ RUNNING`. Your music continues playing without any stutter.
                6. When the network card finishes receiving the webpage, it raises a hardware interrupt. The kernel moves `P101` from `WAITING ➔ READY`.
                7. When `P102`'s time slice expires (preemption), `P101` is dispatched back to `RUNNING` to render the webpage!
                """
            )

        with st.expander("6. Formal State Transition Reference Matrix", expanded=True):
            matrix_df = pd.DataFrame([
                {"Transition": "NEW ➔ READY", "Name": "Admit", "Triggering Event": "Long-Term Scheduler admits program into memory", "OS Subsystem": "Job Scheduler"},
                {"Transition": "READY ➔ RUNNING", "Name": "Dispatch", "Triggering Event": "Short-Term Scheduler chooses process; Context switch occurs", "OS Subsystem": "CPU Scheduler & Dispatcher"},
                {"Transition": "RUNNING ➔ READY", "Name": "Preempt", "Triggering Event": "Hardware timer interrupt fires (quantum expired) or priority preemption", "OS Subsystem": "Timer ISR / Kernel Scheduler"},
                {"Transition": "RUNNING ➔ WAITING", "Name": "I/O Request", "Triggering Event": "Process makes blocking system call (e.g. read(), wait())", "OS Subsystem": "Syscall Handler / Device Driver"},
                {"Transition": "WAITING ➔ READY", "Name": "I/O Complete", "Triggering Event": "I/O device finishes transfer and sends hardware interrupt", "OS Subsystem": "Device Controller & ISR"},
                {"Transition": "RUNNING ➔ TERMINATED", "Name": "Exit", "Triggering Event": "Process finishes routine, calls exit(), or receives fatal signal", "OS Subsystem": "Process Subsystem / Memory Deallocator"},
            ])
            st.dataframe(matrix_df, hide_index=True, use_container_width=True)
