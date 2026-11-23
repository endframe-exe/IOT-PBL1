"""
AgriSense: Smart Irrigation Monitoring System
==============================================
Streamlit Interactive Dashboard & Control Center
Academic Context: First-Year B.Tech PBL (DEC0101/DEC0151 - Group 11).

Strict Architectural Rules:
- UI components DO NOT duplicate control logic; all decisions originate from digital_core.py.
- Widget keys are completely separated from engine state to prevent session_state collisions.
- Clear educational simulation labeling on all pages and exports.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from pathlib import Path

from digital_core import (
    DigitalCoreEngine,
    FSMState,
    ZoneId,
    quantize_4bit,
    to_binary_4bit,
    magnitude_comparator_4bit,
    generate_truth_table,
    StepSnapshot,
)
from database import DatabaseManager, default_db
from reports import export_csv_bytes, export_pdf_bytes, DISCLAIMER_TEXT

# ============================================================================
# PAGE CONFIG & AGTECH STYLING
# ============================================================================

st.set_page_config(
    page_title="AgriSense | Smart Irrigation System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for AgTech Green theme and status cards
st.markdown(
    """
    <style>
    :root {
        --primary-green: #1B5E20;
        --accent-green: #2E7D32;
        --light-bg: #F8F9FA;
        --border-color: #E0E0E0;
    }
    .main-header {
        background: linear-gradient(135deg, #1B5E20, #2E7D32);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .sim-banner {
        background-color: #FFF3CD;
        color: #856404;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid #FFEEBA;
        margin-bottom: 14px;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #616161;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1B5E20;
    }
    .badge-normal {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background-color: #FFF3E0;
        color: #E65100;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-danger {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .truth-table-highlight {
        background-color: #C8E6C9 !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# SESSION STATE INITIALIZATION (AVOIDING PRD 18.3 CRASHES)
# ============================================================================

if "engine" not in st.session_state:
    st.session_state.engine = DigitalCoreEngine()

if "db" not in st.session_state:
    st.session_state.db = default_db

if "latest_snapshot" not in st.session_state:
    # Initialize with baseline step
    comb = st.session_state.engine.evaluate_combinational()
    st.session_state.latest_snapshot = None

if "auto_clock" not in st.session_state:
    st.session_state.auto_clock = False

# Ensure widget state keys exist with defaults
if "ui_z1" not in st.session_state:
    st.session_state.ui_z1 = 50.0
if "ui_z2" not in st.session_state:
    st.session_state.ui_z2 = 50.0
if "ui_tank" not in st.session_state:
    st.session_state.ui_tank = 80.0
if "ui_rain" not in st.session_state:
    st.session_state.ui_rain = False
if "ui_manual" not in st.session_state:
    st.session_state.ui_manual = False
if "ui_target" not in st.session_state:
    st.session_state.ui_target = "ZONE_1"
if "ui_pipe_burst" not in st.session_state:
    st.session_state.ui_pipe_burst = False
if "ui_evaporation" not in st.session_state:
    st.session_state.ui_evaporation = False


def sync_ui_to_engine():
    """Pushes current widget values to the digital core model."""
    st.session_state.engine.set_inputs(
        zone1_moisture=float(st.session_state.ui_z1),
        zone2_moisture=float(st.session_state.ui_z2),
        tank_level=float(st.session_state.ui_tank),
        rain_detected=bool(st.session_state.ui_rain),
        manual_override=bool(st.session_state.ui_manual),
        manual_target_zone=ZoneId(st.session_state.ui_target),
        pipe_burst_fault=bool(st.session_state.ui_pipe_burst),
        auto_evaporation=bool(st.session_state.ui_evaporation),
    )


def sync_engine_to_ui():
    """Pulls current engine state into widget keys (e.g. after a simulation step)."""
    st.session_state.ui_z1 = round(float(st.session_state.engine.state.zone1_moisture), 1)
    st.session_state.ui_z2 = round(float(st.session_state.engine.state.zone2_moisture), 1)
    st.session_state.ui_tank = round(float(st.session_state.engine.state.tank_level), 1)
    st.session_state.ui_rain = bool(st.session_state.engine.state.rain_detected)
    st.session_state.ui_manual = bool(st.session_state.engine.state.manual_override)
    st.session_state.ui_target = st.session_state.engine.state.manual_target_zone.value
    st.session_state.ui_pipe_burst = bool(st.session_state.engine.state.pipe_burst_fault)
    st.session_state.ui_evaporation = bool(st.session_state.engine.state.auto_evaporation)


# ============================================================================
# HEADER & EDUCATIONAL DISCLAIMER BANNER
# ============================================================================

st.markdown(
    """
    <div class="main-header">
        <h2 style="margin: 0; padding: 0;">🌱 AgriSense | Smart Irrigation Monitoring System</h2>
        <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 0.95rem;">
            DEC0101 / DEC0151 Digital Electronics & IoT Systems PBL Prototype • Group 11
        </p>
    </div>
    <div class="sim-banner">
        ⚠️ <b>SIMULATION MODE:</b> All sensor inputs, hydraulic parameters, and actuator relays are 
        deterministic software simulation models for academic evaluation. No physical sensor accuracy or crop yield claims are made.
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar System Health & Controller Mode
with st.sidebar:
    st.image("https://img.icons8.com/color/96/field.png", width=64)
    st.markdown("### Controller Core")
    
    current_fsm = st.session_state.engine.state.fsm_state
    if current_fsm == FSMState.FAULT_LOCK:
        st.markdown('<span class="badge-danger">STATE: FAULT_LOCK (11)</span>', unsafe_allow_html=True)
    elif current_fsm in (FSMState.ZONE_1_ACTIVE, FSMState.ZONE_2_ACTIVE):
        st.markdown(f'<span class="badge-normal">STATE: {current_fsm.value} ({current_fsm.binary_code})</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-normal">STATE: IDLE (00)</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Quick Preset Demos:**")

    if st.button("1. Normal Dry Zone 1", use_container_width=True):
        st.session_state.ui_z1 = 20.0
        st.session_state.ui_z2 = 65.0
        st.session_state.ui_tank = 90.0
        st.session_state.ui_rain = False
        st.session_state.ui_manual = False
        st.session_state.ui_pipe_burst = False
        sync_ui_to_engine()
        st.rerun()

    if st.button("2. Rain Interlock Stop", use_container_width=True):
        st.session_state.ui_rain = True
        sync_ui_to_engine()
        st.rerun()

    if st.button("3. Low Tank Safety Trip", use_container_width=True):
        st.session_state.ui_tank = 10.0
        sync_ui_to_engine()
        st.rerun()

    if st.button("4. Run to Fertigation (Count 4)", use_container_width=True):
        st.session_state.ui_z1 = 20.0
        st.session_state.ui_tank = 90.0
        st.session_state.ui_pipe_burst = True
        sync_ui_to_engine()
        for _ in range(4):
            snap = st.session_state.engine.step_clock()
            st.session_state.db.log_event(snap)
            st.session_state.latest_snapshot = snap
        sync_engine_to_ui()
        st.rerun()

    if st.button("5. Pipe Burst Watchdog (Count 15)", use_container_width=True):
        st.session_state.ui_z1 = 20.0
        st.session_state.ui_tank = 90.0
        st.session_state.ui_pipe_burst = True
        sync_ui_to_engine()
        for _ in range(15):
            snap = st.session_state.engine.step_clock()
            st.session_state.db.log_event(snap)
            st.session_state.latest_snapshot = snap
        sync_engine_to_ui()
        st.rerun()

    st.markdown("---")
    st.markdown("DEC0101 Syllabus Modules 1-5 Verified.")


# ============================================================================
# PRIMARY NAVIGATION TABS
# ============================================================================

tabs = st.tabs([
    "🌐 3D Virtual Farm Twin",
    "📊 Overview",
    "🚜 Farm Simulator",
    "⚡ Logic Control (Viva View)",
    "📈 Analytics & Reports",
])

# ----------------------------------------------------------------------------
# TAB 0: 3D VIRTUAL FARM TWIN
# ----------------------------------------------------------------------------
with tabs[0]:
    col_tw1, col_tw2 = st.columns([0.7, 0.3])
    with col_tw1:
        st.subheader("🌾 3D Blender-Shaded Virtual Farm Digital Twin")
        st.caption("Interactive Cyber-Physical Canvas • Synchronized with Digital Core & FSM Equations")
    with col_tw2:
        st.link_button(
            "⚡ Open Wokwi Hardware Twin (Uno)",
            "https://wokwi.com/projects/new/arduino-uno",
            type="primary",
            use_container_width=True,
        )

    twin_html_path = Path("assets/virtual_farm_twin.html")
    if twin_html_path.exists():
        twin_code = twin_html_path.read_text(encoding="utf-8")
        components.html(twin_code, height=760, scrolling=True)
    else:
        st.error("Digital Twin asset 'assets/virtual_farm_twin.html' not found.")

# ----------------------------------------------------------------------------
# TAB 1: OVERVIEW
# ----------------------------------------------------------------------------
with tabs[1]:
    engine = st.session_state.engine
    state = engine.state
    snap = st.session_state.latest_snapshot

    st.subheader("Field Telemetry & Controller Metrics")

    # Metric Row 1: Primary Hydraulic Readings
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        z1_val = state.zone1_moisture
        badge = "badge-danger" if z1_val < 30 else ("badge-warning" if z1_val < 45 else "badge-normal")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Zone 1 Soil Moisture</div>
                <div class="metric-val">{z1_val:.1f}%</div>
                <span class="{badge}">{'DRY DEMAND' if state.zone1_dry_demand else 'ADEQUATE'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col2:
        z2_val = state.zone2_moisture
        badge2 = "badge-danger" if z2_val < 30 else ("badge-warning" if z2_val < 45 else "badge-normal")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Zone 2 Soil Moisture</div>
                <div class="metric-val">{z2_val:.1f}%</div>
                <span class="{badge2}">{'DRY DEMAND' if state.zone2_dry_demand else 'ADEQUATE'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col3:
        tank_val = state.tank_level
        badge_tank = "badge-danger" if tank_val < 20 else ("badge-warning" if tank_val < 40 else "badge-normal")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Reservoir Water Level</div>
                <div class="metric-val">{tank_val:.1f}%</div>
                <span class="{badge_tank}">{'LOW TANK INTERLOCK' if tank_val < 20 else 'SAFE LEVEL'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col4:
        rain_val = state.rain_detected
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Rainfall Interlock</div>
                <div class="metric-val">{'RAIN ON' if rain_val else 'DRY'}</div>
                <span class="{'badge-warning' if rain_val else 'badge-normal'}">{'PUMP SUPPRESSED' if rain_val else 'NORMAL'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Metric Row 2: Digital Actuators & Controller State
    c_col1, c_col2, c_col3, c_col4 = st.columns(4)
    with c_col1:
        fsm_val = state.fsm_state
        pump_on = (fsm_val in (FSMState.ZONE_1_ACTIVE, FSMState.ZONE_2_ACTIVE))
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Main Pump Relay</div>
                <div class="metric-val">{'ENERGIZED' if pump_on else 'OFF'}</div>
                <span class="{'badge-normal' if pump_on else 'badge-warning'}">RELAY {1 if pump_on else 0}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_col2:
        active_z = "ZONE 1" if fsm_val == FSMState.ZONE_1_ACTIVE else ("ZONE 2" if fsm_val == FSMState.ZONE_2_ACTIVE else "NONE")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Active Solenoid Valve</div>
                <div class="metric-val">{active_z}</div>
                <span class="badge-normal">ROUTING</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Irrigation FSM (2-Bit)</div>
                <div class="metric-val">{fsm_val.value}</div>
                <span class="{'badge-danger' if fsm_val == FSMState.FAULT_LOCK else 'badge-normal'}">CODE: {fsm_val.binary_code}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_col4:
        cnt = state.counter
        cnt_bin = to_binary_4bit(cnt)
        badge_cnt = "badge-warning" if cnt == 4 else ("badge-danger" if cnt == 15 else "badge-normal")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">MOD-16 Counter</div>
                <div class="metric-val">{cnt} <span style="font-size: 1rem; color: #555;">[{cnt_bin}]</span></div>
                <span class="{badge_cnt}">{'FERTIGATION (4)' if cnt == 4 else ('WATCHDOG LOCK (15)' if cnt == 15 else 'NORMAL RUN')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Live Recommendation Banner
    st.markdown("<br>", unsafe_allow_html=True)
    recs = engine.generate_recommendations()
    if recs:
        rec_html = "".join([f"<li>{r}</li>" for r in recs])
        st.markdown(
            f"""
            <div style="background-color: #E8F5E9; border-left: 5px solid #2E7D32; padding: 12px 18px; border-radius: 4px;">
                <b style="color: #1B5E20; font-size: 1rem;">Rule-Based Controller Advisories:</b>
                <ul style="margin: 6px 0 0 0; padding-left: 20px; color: #2E7D32;">{rec_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Historical Trend Chart
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Real-Time Simulation Trajectory")
    events_df = st.session_state.db.fetch_events(limit=50)
    if not events_df.empty and len(events_df) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=events_df["id"], y=events_df["zone1"], name="Zone 1 Moisture (%)", line=dict(color="#2E7D32", width=2)))
        fig.add_trace(go.Scatter(x=events_df["id"], y=events_df["zone2"], name="Zone 2 Moisture (%)", line=dict(color="#66BB6A", width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=events_df["id"], y=events_df["tank"], name="Tank Level (%)", line=dict(color="#0288D1", width=2)))
        fig.add_hline(y=30, line_dash="dash", line_color="#E65100", annotation_text="Dry Trip (30%)")
        fig.add_hline(y=45, line_dash="dash", line_color="#2E7D32", annotation_text="Wet Clear (45%)")
        fig.add_hline(y=20, line_dash="dash", line_color="#C62828", annotation_text="Min Tank Safe (20%)")
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Simulation Clock Step",
            yaxis_title="Percentage (%)",
            plot_bgcolor="#FAFAFA",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No multi-step history recorded yet. Advance simulation clock pulses in the Farm Simulator tab to view live trends.")


# ----------------------------------------------------------------------------
# TAB 2: FARM SIMULATOR
# ----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Virtual Field Simulator & Actuator Controls")

    col_sim_left, col_sim_right = st.columns([1.1, 0.9])

    with col_sim_left:
        st.markdown("##### Environmental Input Controls")

        st.slider("Zone 1 Soil Moisture (%)", 0.0, 100.0, key="ui_z1", step=1.0, on_change=sync_ui_to_engine)
        st.slider("Zone 2 Soil Moisture (%)", 0.0, 100.0, key="ui_z2", step=1.0, on_change=sync_ui_to_engine)
        st.slider("Water Reservoir Capacity (%)", 0.0, 100.0, key="ui_tank", step=1.0, on_change=sync_ui_to_engine)

        col_tog1, col_tog2 = st.columns(2)
        with col_tog1:
            st.toggle("🌧️ Rainfall Sensor Active", key="ui_rain", on_change=sync_ui_to_engine)
            st.toggle("💧 Simulate Ambient Evaporation", key="ui_evaporation", on_change=sync_ui_to_engine)
        with col_tog2:
            st.toggle("🕹️ Manual Override Switch", key="ui_manual", on_change=sync_ui_to_engine)
            st.toggle("⚠️ Simulate Pipe Burst / Stuck Sensor", key="ui_pipe_burst", on_change=sync_ui_to_engine)

        st.selectbox("Manual Target Routing Zone", ["ZONE_1", "ZONE_2"], key="ui_target", on_change=sync_ui_to_engine)

    with col_sim_right:
        st.markdown("##### Clock Pulse & State Engine Triggers")
        sync_ui_to_engine()

        btn_pulse, btn_eval = st.columns(2)
        with btn_pulse:
            if st.button("⏱️ Next Clock Pulse", type="primary", use_container_width=True):
                snap = st.session_state.engine.step_clock()
                st.session_state.db.log_event(snap)
                st.session_state.latest_snapshot = snap
                sync_engine_to_ui()
                st.rerun()

        with btn_eval:
            if st.button("🔍 Evaluate Combinational", use_container_width=True):
                comb = st.session_state.engine.evaluate_combinational()
                st.success(f"Evaluated: P={comb['p']}, A={comb['a']} (M={comb['m']}, W={comb['w']}, R={comb['r']}, O={comb['o']})")

        btn_rst_sim, btn_rst_flt = st.columns(2)
        with btn_rst_sim:
            if st.button("🔄 Reset Simulation RAM", use_container_width=True):
                st.session_state.engine.reset_simulation()
                sync_engine_to_ui()
                st.info("Simulation RAM reset to clean baseline (50/50/80). Event database preserved.")
                st.rerun()

        with btn_rst_flt:
            is_fault = (st.session_state.engine.state.fsm_state == FSMState.FAULT_LOCK)
            if st.button("🛡️ Reset Fault Lock", disabled=not is_fault, use_container_width=True):
                success, msg = st.session_state.engine.reset_fault()
                if success:
                    st.success(msg)
                    sync_engine_to_ui()
                    st.rerun()
                else:
                    st.error(msg)

        # Autonomous Clock Mode Fragment
        st.markdown("---")
        st.markdown("##### Autonomous Clock Execution")
        auto_toggle = st.toggle("🚀 Enable Autonomous Clock Execution", key="ui_auto_clock")

        @st.fragment(run_every="1.5s")
        def autonomous_clock_runner(enabled: bool):
            if enabled:
                st.session_state.engine.set_inputs(auto_evaporation=True)
                snap_auto = st.session_state.engine.step_clock()
                st.session_state.db.log_event(snap_auto)
                st.session_state.latest_snapshot = snap_auto
                sync_engine_to_ui()
                st.caption(f"⚡ Auto Step #{snap_auto.step_id}: {snap_auto.message}")

        if auto_toggle:
            autonomous_clock_runner(True)
        else:
            st.caption("Auto-clock is paused. Step manually with 'Next Clock Pulse'.")


# ----------------------------------------------------------------------------
# TAB 3: LOGIC CONTROL (VIVA VIEW - MODULES 1 TO 4)
# ----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Digital Logic & Theoretical Viva Verification (DEC0101)")

    comb_eval = st.session_state.engine.evaluate_combinational()
    m_val = comb_eval["m"]
    w_val = comb_eval["w"]
    r_val = comb_eval["r"]
    o_val = comb_eval["o"]
    p_val = comb_eval["p"]
    a_val = comb_eval["a"]

    # 1. Binary Input Quantization & 74LS85 Comparator Model
    st.markdown("#### 1. Input Quantization & 74LS85 4-Bit Magnitude Comparator")
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        z1_q = quantize_4bit(st.session_state.engine.state.zone1_moisture)
        st.markdown(f"**Zone 1 Quantized (A):** `{z1_q}` (`{to_binary_4bit(z1_q)}`)")
    with col_q2:
        dry_thresh_q = quantize_4bit(30.0)
        st.markdown(f"**Dry Threshold Word (B):** `{dry_thresh_q}` (`{to_binary_4bit(dry_thresh_q)}`)")
    with col_q3:
        comp = magnitude_comparator_4bit(z1_q, dry_thresh_q)
        st.markdown(f"**Comparator Output:** `A<B={comp.a_lt_b}`, `A=B={comp.a_eq_b}`, `A>B={comp.a_gt_b}`")

    # 2. Combinational Safety Logic
    st.markdown("#### 2. Combinational Safety Equations & Binary Inputs")
    eq_col1, eq_col2 = st.columns(2)
    with eq_col1:
        st.latex(r"P = W \cdot \overline{R} \cdot (O + M)")
        st.markdown(f"**Current Pump Output (P):** `{p_val}` ({'ENERGIZED' if p_val else 'CUT-OFF'})")
    with eq_col2:
        st.latex(r"A = \overline{W}")
        st.markdown(f"**Low-Level Alarm (A):** `{a_val}` ({'ACTIVE' if a_val else 'INACTIVE'})")

    # Display 4 binary inputs
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.metric("M (Moisture Demand)", m_val, "M1 or M2 Dry")
    b_col2.metric("W (Water Safe >=20%)", w_val, "Interlock" if not w_val else "Safe")
    b_col3.metric("R (Rainfall)", r_val, "Rain Hold" if r_val else "Dry")
    b_col4.metric("O (Manual Override)", o_val, "Active" if o_val else "Off")

    # 3. Complete 16-Row Truth Table with Active Minterm Highlight
    st.markdown("#### 3. Complete 16-Row Truth Table (M-W-R-O)")
    truth_table_rows = generate_truth_table()
    current_minterm_idx = (m_val << 3) | (w_val << 2) | (r_val << 1) | o_val

    tt_data = []
    for r in truth_table_rows:
        is_active = (r.row == current_minterm_idx)
        prefix = "👉 " if is_active else ""
        tt_data.append({
            "Minterm": f"{prefix}{r.minterm}",
            "M (Demand)": r.m,
            "W (Water)": r.w,
            "R (Rain)": r.r,
            "O (Manual)": r.o,
            "P (Pump)": r.p,
            "A (Alarm)": r.a,
            "Operational Description": r.description + (" [CURRENT STATE]" if is_active else ""),
        })

    tt_df = pd.DataFrame(tt_data)
    st.dataframe(
        tt_df,
        use_container_width=True,
        hide_index=True,
    )

    # 4. Sequential FSM & PIPO Register Bus
    st.markdown("#### 4. Sequential State Machine & 4-Bit PIPO Register")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("**2-Bit D Flip-Flop State Machine:**")
        fsm = st.session_state.engine.state.fsm_state
        q1, q0 = fsm.bit_tuple
        st.markdown(f"- State: **`{fsm.value}`**")
        st.markdown(f"- Latched Flip-Flop Vector: `Q1={q1}`, `Q0={q0}` (`{fsm.binary_code}`)")
        st.markdown("- Transition Model: $Q_{n+1} = D$ (evaluated synchronously on clock pulse)")

    with s_col2:
        st.markdown("**4-Bit PIPO (Parallel-In Parallel-Out) Status Bus:**")
        pipo = st.session_state.engine.state.pipo
        st.markdown(f"- `Q3 (Zone 1 Valve):` **`{pipo.q3_valve1}`**")
        st.markdown(f"- `Q2 (Zone 2 Valve):` **`{pipo.q2_valve2}`**")
        st.markdown(f"- `Q1 (Fertigation Solenoid):` **`{pipo.q1_fertigation}`**")
        st.markdown(f"- `Q0 (Low Tank / Watchdog Alarm):` **`{pipo.q0_alarm}`**")
        st.markdown(f"- Word: **`{pipo.binary_str}`** (`{pipo.hex_str}`)")


# ----------------------------------------------------------------------------
# TAB 4: ANALYTICS & REPORTS
# ----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Historical Analytics, Audit Logs & Report Exports")

    metrics = st.session_state.db.fetch_summary_metrics()

    # Metric KPI cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Events Logged", metrics["total_events"])
    kpi2.metric("Pump Active Pulses", metrics["pump_active_events"])
    kpi3.metric("Fault / Safety Lockouts", metrics["fault_events"])
    kpi4.metric("Rain Interlock Holds", metrics["rain_events"])

    st.markdown("---")

    # Export Action Buttons
    df_all = st.session_state.db.fetch_events(ascending=True)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_bytes = export_csv_bytes(df_all)
        st.download_button(
            label="📥 Download Event History (CSV)",
            data=csv_bytes,
            file_name=f"agrisense_events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_exp2:
        pdf_bytes = export_pdf_bytes(st.session_state.latest_snapshot, df_all)
        st.download_button(
            label="📄 Download Formal PDF Audit Report",
            data=pdf_bytes,
            file_name=f"agrisense_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Searchable Simulation Event Log")
    st.dataframe(
        df_all.sort_values(by="id", ascending=False) if not df_all.empty else df_all,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Administrative Database Maintenance"):
        st.warning("⚠️ Purging event history is irreversible. Normal simulation reset does NOT clear this table.")
        if st.button("🗑️ Clear All Historical Database Records"):
            st.session_state.db.clear_all_history()
            st.success("Historical SQLite event database cleared.")
            st.rerun()
