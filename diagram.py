"""
Interactive Five-State Process Diagram Renderer.
Part of ProcessLab — Advanced OS Process State Simulator (Phase 2).

Renders a high-resolution, responsive SVG diagram of the 5-state model
with active node highlighting, transition arrow glowing, badge counts,
and OS event annotations.
"""

from typing import Dict, Any, Optional, List
from process import ProcessState


STATE_INFO: Dict[str, Dict[str, str]] = {
    "NEW": {
        "title": "NEW State",
        "color": "#38bdf8",
        "badge_bg": "rgba(56, 189, 248, 0.15)",
        "desc": "The process is being created and its Process Control Block (PCB) is being initialized in kernel memory.",
        "scheduler": "Long-Term (Job) Scheduler",
        "resources": "PCB created, not yet loaded into RAM"
    },
    "READY": {
        "title": "READY State",
        "color": "#f59e0b",
        "badge_bg": "rgba(245, 158, 11, 0.15)",
        "desc": "The process is loaded into main memory and is awaiting allocation of CPU time by the Short-Term Scheduler.",
        "scheduler": "Short-Term (CPU) Scheduler",
        "resources": "Memory, registers, and resources allocated; waiting only for CPU core"
    },
    "RUNNING": {
        "title": "RUNNING State",
        "color": "#10b981",
        "badge_bg": "rgba(16, 185, 129, 0.15)",
        "desc": "The process's instructions are currently being executed by the CPU core.",
        "scheduler": "CPU Dispatcher",
        "resources": "Actively occupies CPU register set, ALU, and Program Counter"
    },
    "WAITING": {
        "title": "WAITING (Blocked) State",
        "color": "#6366f1",
        "badge_bg": "rgba(99, 102, 241, 0.15)",
        "desc": "The process cannot execute because it is waiting for an external event, such as I/O completion or signal.",
        "scheduler": "I/O Device Controller / Interrupt Handler",
        "resources": "Relinquished CPU; queued in device wait queue"
    },
    "TERMINATED": {
        "title": "TERMINATED State",
        "color": "#f43f5e",
        "badge_bg": "rgba(244, 63, 94, 0.15)",
        "desc": "The process has finished execution or was killed; OS reclaims memory and closes open descriptors.",
        "scheduler": "OS Memory Manager / Process Subsystem",
        "resources": "Resources freed; exit status held until parent reads it"
    }
}

TRANSITION_INFO: Dict[str, Dict[str, str]] = {
    "ADMIT": {
        "from": "NEW",
        "to": "READY",
        "label": "Admit",
        "actor": "Long-Term Scheduler",
        "trigger": "System admits newly created program into main memory ready queue.",
        "os_concept": "Degree of multiprogramming control. Ensures memory is not overcommitted."
    },
    "DISPATCH": {
        "from": "READY",
        "to": "RUNNING",
        "label": "Dispatch",
        "actor": "Short-Term Scheduler & Dispatcher",
        "trigger": "Scheduler selects process based on algorithm; Dispatcher performs context switch.",
        "os_concept": "Context switch loads program counter, registers, and memory page tables."
    },
    "PREEMPT": {
        "from": "RUNNING",
        "to": "READY",
        "label": "Interrupt / Preempt",
        "actor": "Timer Hardware & Kernel Interrupt",
        "trigger": "Timer tick expires time quantum, or higher priority process arrives.",
        "os_concept": "Prevents CPU monopolization; enables fair time-sharing across multiple processes."
    },
    "I/O_REQUEST": {
        "from": "RUNNING",
        "to": "WAITING",
        "label": "I/O Request / Wait",
        "actor": "Process System Call",
        "trigger": "Process issues blocking system call (e.g. read(), recv(), sleep()).",
        "os_concept": "Synchronous I/O yields CPU so another ready process can execute instead of idling."
    },
    "I/O_COMPLETE": {
        "from": "WAITING",
        "to": "READY",
        "label": "I/O Complete",
        "actor": "Device Controller Interrupt",
        "trigger": "Hardware device finishes operation and issues hardware interrupt to CPU.",
        "os_concept": "Interrupt Service Routine (ISR) moves process from wait queue back to Ready queue."
    },
    "TERMINATE": {
        "from": "RUNNING",
        "to": "TERMINATED",
        "label": "Exit / Terminate",
        "actor": "Exit System Call / Exception",
        "trigger": "Process completes its main routine, calls exit(), or receives kill signal.",
        "os_concept": "OS closes open files, frees memory pages, and notifies parent process."
    }
}


def render_svg_diagram(
    state_counts: Dict[str, int],
    selected_state: Optional[str] = None,
    last_transition: Optional[Dict[str, Any]] = None,
    selected_pid: Optional[int] = None
) -> str:
    """
    Renders a responsive SVG diagram representing the 5-state process model.
    Highlights current active state of selected process and last triggered transition.
    """
    # Coordinates for the 5 states
    nodes = {
        "NEW": {"x": 100, "y": 140, "color": "#38bdf8", "icon": "✨"},
        "READY": {"x": 320, "y": 140, "color": "#f59e0b", "icon": "⏳"},
        "RUNNING": {"x": 580, "y": 140, "color": "#10b981", "icon": "⚡"},
        "TERMINATED": {"x": 840, "y": 140, "color": "#f43f5e", "icon": "🏁"},
        "WAITING": {"x": 450, "y": 280, "color": "#818cf8", "icon": "⏸️"}
    }

    # Determine which transition to highlight
    active_trans_key = None
    if last_transition:
        action = last_transition.get("action", "")
        if action in TRANSITION_INFO:
            active_trans_key = action

    # Helper for arrow stroke & dash styling
    def arrow_style(trans_key: str, default_color: str = "#475569") -> str:
        is_active = (active_trans_key == trans_key)
        stroke = "#38bdf8" if is_active else default_color
        width = "3.5" if is_active else "2"
        dash = 'stroke-dasharray="6,4" class="pulsing-arrow"' if is_active else ""
        glow = 'filter="url(#arrow-glow)"' if is_active else ""
        marker = 'url(#arrow-head-active)' if is_active else 'url(#arrow-head)'
        return f'stroke="{stroke}" stroke-width="{width}" {dash} {glow} marker-end="{marker}"'

    def label_style(trans_key: str) -> str:
        is_active = (active_trans_key == trans_key)
        fill = "#38bdf8" if is_active else "#94a3b8"
        weight = "bold" if is_active else "500"
        return f'fill="{fill}" font-weight="{weight}"'

    svg = f"""
    <div style="width:100%; box-sizing:border-box; overflow-x:auto; padding:12px; background:#101827; border:1px solid #263449; border-radius:14px;">
    <svg viewBox="0 0 940 370" xmlns="http://www.w3.org/2000/svg" style="display:block; width:100%; height:auto; min-width:720px; font-family:Inter, system-ui, -apple-system, sans-serif;">
      <defs>
        <!-- Gradients -->
        <linearGradient id="bg-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#1e293b" stop-opacity="0.9" />
          <stop offset="100%" stop-color="#0f172a" stop-opacity="0.95" />
        </linearGradient>

        <linearGradient id="grad-NEW" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#0284c7" />
          <stop offset="100%" stop-color="#0369a1" />
        </linearGradient>
        <linearGradient id="grad-READY" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#d97706" />
          <stop offset="100%" stop-color="#b45309" />
        </linearGradient>
        <linearGradient id="grad-RUNNING" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#059669" />
          <stop offset="100%" stop-color="#047857" />
        </linearGradient>
        <linearGradient id="grad-WAITING" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#4f46e5" />
          <stop offset="100%" stop-color="#3730a3" />
        </linearGradient>
        <linearGradient id="grad-TERMINATED" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#e11d48" />
          <stop offset="100%" stop-color="#be123c" />
        </linearGradient>

        <!-- Glow Filters -->
        <filter id="node-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#38bdf8" flood-opacity="0.8" />
        </filter>
        <filter id="cpu-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="7" flood-color="#10b981" flood-opacity="0.75" />
        </filter>
        <filter id="arrow-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#38bdf8" flood-opacity="0.9" />
        </filter>

        <!-- Arrow Markers -->
        <marker id="arrow-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />
        </marker>
        <marker id="arrow-head-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8" />
        </marker>
      </defs>

      <style>
        .state-box {{ cursor: pointer; transition: all 0.3s ease; }}
        .state-box:hover {{ filter: brightness(1.15); }}
        .pulsing-ring {{
          animation: pulse 1.8s infinite ease-in-out;
        }}
        .pulsing-arrow {{
          animation: dashflow 1.2s linear infinite;
        }}
        @keyframes pulse {{
          0% {{ opacity: 0.9; stroke-width: 3px; }}
          50% {{ opacity: 0.3; stroke-width: 7px; }}
          100% {{ opacity: 0.9; stroke-width: 3px; }}
        }}
        @keyframes dashflow {{
          to {{ stroke-dashoffset: -20; }}
        }}
      </style>

      <!-- Background Grid Subdued Lines -->
      <line x1="50" y1="140" x2="890" y2="140" stroke="#1e293b" stroke-width="1" stroke-dasharray="4,4" />

      <!-- ================= TRANSITION ARROWS ================= -->

      <!-- 1. NEW -> READY (Admit) -->
      <path d="M 160 140 L 250 140" fill="none" {arrow_style("ADMIT")} />
      <text x="205" y="128" text-anchor="middle" font-size="11" {label_style("ADMIT")}>Admit</text>

      <!-- 2. READY -> RUNNING (Dispatch) -->
      <path d="M 380 130 Q 480 105 510 130" fill="none" {arrow_style("DISPATCH")} />
      <text x="450" y="105" text-anchor="middle" font-size="11" {label_style("DISPATCH")}>Dispatch</text>

      <!-- 3. RUNNING -> READY (Preempt / Interrupt) -->
      <path d="M 520 152 Q 450 180 390 152" fill="none" {arrow_style("PREEMPT")} />
      <text x="455" y="180" text-anchor="middle" font-size="11" {label_style("PREEMPT")}>Preempt / Interrupt</text>

      <!-- 4. RUNNING -> WAITING (I/O Request) -->
      <path d="M 570 190 C 560 230, 520 250, 495 260" fill="none" {arrow_style("I/O_REQUEST")} />
      <text x="560" y="240" text-anchor="middle" font-size="11" {label_style("I/O_REQUEST")}>I/O Request</text>

      <!-- 5. WAITING -> READY (I/O Complete) -->
      <path d="M 405 260 C 370 245, 335 225, 330 190" fill="none" {arrow_style("I/O_COMPLETE")} />
      <text x="340" y="240" text-anchor="middle" font-size="11" {label_style("I/O_COMPLETE")}>I/O Complete</text>

      <!-- 6. RUNNING -> TERMINATED (Exit) -->
      <path d="M 640 140 L 770 140" fill="none" {arrow_style("TERMINATE")} />
      <text x="705" y="128" text-anchor="middle" font-size="11" {label_style("TERMINATE")}>Exit / Terminate</text>

      <!-- ================= STATE NODES ================= -->
    """

    for name, data in nodes.items():
        x = data["x"]
        y = data["y"]
        color = data["color"]
        icon = data["icon"]
        count = state_counts.get(name, 0)
        is_selected = (selected_state == name)
        is_cpu = (name == "RUNNING")

        glow_filter = 'filter="url(#node-glow)"' if is_selected else ('filter="url(#cpu-glow)"' if is_cpu else "")
        border_stroke = "#38bdf8" if is_selected else (color if is_cpu else "#334155")
        border_width = "3" if is_selected else ("2.5" if is_cpu else "1.5")

        # Pulse indicator if selected
        pulse_svg = ""
        if is_selected:
            pulse_svg = f'<rect x="{x-64}" y="{y-44}" width="128" height="88" rx="14" fill="none" stroke="{color}" class="pulsing-ring" />'

        badge_text = f"{count} process" if count == 1 else f"{count} processes"
        if name == "RUNNING":
            badge_text = "CPU BUSY" if count > 0 else "CPU IDLE"

        svg += f"""
        <g class="state-box">
          {pulse_svg}
          <!-- Node Container Card -->
          <rect x="{x-60}" y="{y-40}" width="120" height="80" rx="12" fill="url(#grad-{name})"
                stroke="{border_stroke}" stroke-width="{border_width}" {glow_filter} />

          <!-- Icon & Name -->
          <text x="{x}" y="{y-12}" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="700">
            {name}
          </text>

          <!-- Divider -->
          <line x1="{x-45}" y1="{y+4}" x2="{x+45}" y2="{y+4}" stroke="rgba(255,255,255,0.2)" stroke-width="1" />

          <!-- Count Badge -->
          <rect x="{x-48}" y="{y+10}" width="96" height="20" rx="10" fill="rgba(15, 23, 42, 0.6)" />
          <text x="{x}" y="{y+24}" text-anchor="middle" fill="#f8fafc" font-size="10" font-weight="600">
            {badge_text}
          </text>
        </g>
        """

    # If selected PID is provided, render overlay badge
    if selected_pid is not None and selected_state:
        selected_node = nodes.get(selected_state)
        if selected_node:
            nx = selected_node["x"]
            ny = selected_node["y"]
            svg += f"""
            <g transform="translate({nx}, {ny-50})">
              <rect x="-55" y="-14" width="110" height="22" rx="11" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5" />
              <text x="0" y="1" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="700">
                Active PID #{selected_pid}
              </text>
            </g>
            """

    svg += """
    </svg>
    </div>
    """
    return svg
