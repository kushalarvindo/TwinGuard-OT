"""
TwinGuard-OT: Process-Aware Digital Twin for Cybersecurity Testing and Anomaly Detection in ICS.
Material 3 Expressive SCADA & Security Operations Center (SOC) Platform.
Designed for high-impact academic demonstration, empirical research, and industrial emulation.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to pythonpath
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.database.db import DatabaseManager
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.attacks.sensor_spoofing import SensorSpoofingAttack
from twinguard.attacks.unauthorized_write import UnauthorizedWriteAttack
from twinguard.attacks.replay import ReplayAttack
from twinguard.attacks.command_flood import CommandFloodAttack
from twinguard.attacks.setpoint_manipulation import SetpointManipulationAttack
from experiments.evaluate import evaluate_experiment
from experiments.run_attack import run_attack_experiment

# Streamlit Page Config
st.set_page_config(
    page_title="TwinGuard-OT | Industrial Cyber-Physical Testbed",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "show_help_hub" not in st.session_state:
    st.session_state.show_help_hub = False
if "refresh_speed" not in st.session_state:
    st.session_state.refresh_speed = 3.0
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# ==============================================================================
# MATERIAL 3 EXPRESSIVE & GLASSMORHPISM SOC DESIGN SYSTEM
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Canvas & Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }

    .stApp {
        background-color: #07090e;
        background-image: 
            radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
        background-attachment: fixed;
        color: #f1f5f9;
    }

    /* Top Navigation App Bar */
    .m3-top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(24px) saturate(190%);
        -webkit-backdrop-filter: blur(24px) saturate(190%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 14px 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5),
                    inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 22px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transition: transform 0.25s cubic-bezier(0.2, 0, 0, 1), border-color 0.25s ease;
    }
    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
    }

    /* Gradient Brand Headings */
    .brand-title {
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 40%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 1.85rem;
        letter-spacing: -0.03em;
        margin: 0;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 16px 22px !important;
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(56, 189, 248, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.9rem !important;
        letter-spacing: -0.02em !important;
    }

    /* Material You Expressive Buttons */
    .stButton > button {
        border-radius: 9999px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background: rgba(30, 41, 59, 0.75) !important;
        color: #f8fafc !important;
        backdrop-filter: blur(12px) !important;
        transition: all 0.2s cubic-bezier(0.2, 0, 0, 1) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border-color: rgba(56, 189, 248, 0.6) !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(2, 132, 199, 0.45) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #3b82f6 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.7) !important;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.35) !important;
    }

    /* Material You Custom Sidebar Radio (Replaced into Segmented Menu Items) */
    section[data-testid="stSidebar"] {
        background: rgba(10, 14, 24, 0.94) !important;
        backdrop-filter: blur(28px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 14px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s cubic-bezier(0.2, 0, 0, 1) !important;
        cursor: pointer !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(56, 189, 248, 0.1) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
        transform: translateX(4px) !important;
    }
    /* Hide native radio bullet */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: #cbd5e1 !important;
    }

    /* M3 Category Labels in Sidebar */
    .sidebar-category {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b;
        margin: 18px 0 8px 4px;
    }

    /* Status Badges */
    .chip-green {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.25);
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .chip-red {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.35);
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        animation: pulseAlert 2s infinite ease-in-out;
    }
    @keyframes pulseAlert {
        0%, 100% { box-shadow: 0 0 0 rgba(239, 68, 68, 0); }
        50% { box-shadow: 0 0 24px rgba(239, 68, 68, 0.45); }
    }
    .dot-live {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #34d399;
        box-shadow: 0 0 8px #34d399;
    }
    .dot-danger {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #f87171;
        box-shadow: 0 0 8px #f87171;
    }

    /* M3 Sliders */
    [data-baseweb="slider"] {
        margin-top: 12px;
    }
    [data-testid="stSlider"] div[role="slider"] {
        background: #38bdf8 !important;
        border: 3px solid #07090e !important;
        box-shadow: 0 0 16px rgba(56, 189, 248, 0.7) !important;
        width: 22px !important;
        height: 22px !important;
        border-radius: 50% !important;
    }

    /* Contextual Page Header Glass Card */
    .page-hero {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 5px solid #38bdf8;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 22px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }
    .page-hero h3 {
        margin: 0 0 6px 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .page-hero p {
        margin: 0;
        color: #94a3b8;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* SCADA Tank Visualizer */
    .scada-rig {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 36px;
        padding: 28px;
        background: rgba(11, 17, 33, 0.75);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .scada-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .tank-glass {
        width: 140px;
        height: 230px;
        border: 3px solid rgba(148, 163, 184, 0.35);
        border-top: none;
        border-radius: 0 0 20px 20px;
        position: relative;
        background: rgba(15, 23, 42, 0.5);
        overflow: hidden;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.6);
    }
    .liquid-wave {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        transition: height 0.3s cubic-bezier(0.2, 0, 0, 1);
        border-top: 2px solid rgba(255, 255, 255, 0.7);
    }
    .liquid-true {
        background: linear-gradient(180deg, #38bdf8 0%, #0369a1 100%);
    }
    .liquid-sensor {
        background: linear-gradient(180deg, #34d399 0%, #047857 100%);
    }
    .liquid-spoofed {
        background: linear-gradient(180deg, #f87171 0%, #b91c1c 100%) !important;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
    }
    .interlock-line {
        position: absolute;
        left: 0;
        right: 0;
        height: 1px;
        border-top: 1px dashed rgba(251, 191, 36, 0.75);
        z-index: 10;
    }

    .tech-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 3px 10px;
        border-radius: 9999px;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# DATA ACCESS & CONFIG
# ==============================================================================
@st.cache_resource
def get_db():
    config = load_system_config()
    db_path = config["storage"]["db_path_resolved"]
    return DatabaseManager(db_path)


db = get_db()
config = load_system_config()


# ==============================================================================
# SIDEBAR NAVIGATION & SYSTEM TELEMETRY DOCK
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin: 10px 0 16px 4px;">
        <div style="background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%); padding: 10px; border-radius: 14px; box-shadow: 0 4px 15px rgba(2,132,199,0.35);">
            <span style="font-size: 1.5rem; display: block; line-height: 1;">🛡️</span>
        </div>
        <div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">TwinGuard-OT</div>
            <div style="font-size: 0.72rem; color: #38bdf8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">ICS Digital Twin v2.2</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation Menu Items
    st.markdown('<div class="sidebar-category">Operations & Telemetry</div>', unsafe_allow_html=True)
    nav_choice = st.radio(
        "Navigation",
        [
            "🌊 Process SCADA Overview",
            "🔄 Digital Twin Shadow Model",
            "📡 Modbus Protocol Inspector",
            "🎯 Cyberattack Laboratory",
            "🛡️ Multi-Tier Anomaly Detection",
            "📊 Statistical Process Analytics",
            "🏆 Empirical Evaluation Metrics",
            "💾 Datasets & Research Artifacts",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Live Streaming Controls (Auto-Sync)
    st.markdown('<div class="sidebar-category">Telemetry Synchronization</div>', unsafe_allow_html=True)
    
    col_sync1, col_sync2 = st.columns([1, 1])
    with col_sync1:
        auto_sync = st.toggle("Auto-Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_sync
    with col_sync2:
        speed_label = st.selectbox(
            "Sync Interval",
            ["Fast (1s)", "Standard (3s)", "Relaxed (5s)"],
            index=1,
            label_visibility="collapsed"
        )
        speed_map = {"Fast (1s)": 1.0, "Standard (3s)": 3.0, "Relaxed (5s)": 5.0}
        st.session_state.refresh_speed = speed_map[speed_label]

    if st.button("⚡ Force Manual Sync", use_container_width=True):
        st.rerun()

    st.markdown("---")

    # System Status Dock
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 14px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); font-size: 0.75rem; color: #94a3b8; line-height: 1.6;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>MODBUS HOST:</span>
            <span style="color: #f8fafc; font-family: monospace;">127.0.0.1:5020</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>PLC SCAN RATE:</span>
            <span style="color: #34d399; font-weight: 700;">5.0 Hz (200ms)</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>DATABASE:</span>
            <span style="color: #38bdf8; font-weight: 600;">SQLite (WAL Active)</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>INSTITUTION:</span>
            <span style="color: #cbd5e1;">RVCE — III Sem EL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# TOP APP BAR (Live Status, Breadcrumb, Knowledge Hub Launcher)
# ==============================================================================
df_telemetry = db.get_all_telemetry()
latest_level = 50.0
latest_true = 50.0
latest_pump = 0
latest_valve = 0
latest_residual = 0.0
latest_label = 0
active_exp = "EXP-BASELINE-NORMAL"

if not df_telemetry.empty:
    latest = df_telemetry.iloc[-1]
    latest_level = float(latest["sensor_level"])
    latest_true = float(latest.get("true_level", latest_level))
    latest_pump = int(latest["pump_state"])
    latest_valve = int(latest["valve_state"])
    latest_residual = float(latest["process_residual"])
    latest_label = int(latest["label"])
    active_exp = latest["experiment_id"]

is_anomaly = latest_label == 1 or latest_residual > config["detection"]["residual_threshold"]

col_tb1, col_tb2 = st.columns([3, 1])
with col_tb1:
    if is_anomaly:
        st.markdown(f"""
        <div class="m3-top-bar">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span class="chip-red"><span class="dot-danger"></span> CYBER-PHYSICAL ANOMALY DETECTED</span>
                <span class="tech-pill">ACTIVE EXP: {active_exp}</span>
                <span style="font-size: 0.85rem; color: #f87171; font-weight: 600;">Physical Residual: {latest_residual:.2f}% &gt; {config['detection']['residual_threshold']}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="m3-top-bar">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span class="chip-green"><span class="dot-live"></span> PLANT OPERATING NORMALLY</span>
                <span class="tech-pill">SESSION: {active_exp}</span>
                <span style="font-size: 0.85rem; color: #94a3b8;">All safety interlocks clear • Zero residual violations</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_tb2:
    if st.button("📘 Engineering Knowledge Hub", use_container_width=True):
        st.session_state.show_help_hub = not st.session_state.show_help_hub


# ==============================================================================
# HIGH-VALUE ENGINEERING KNOWLEDGE HUB (Help & Documentation Modal/Drawer)
# ==============================================================================
if st.session_state.show_help_hub:
    st.markdown('<div class="glass-card" style="border: 2px solid rgba(56, 189, 248, 0.4); margin-bottom: 25px;">', unsafe_allow_html=True)
    col_hh_t, col_hh_b = st.columns([4, 1])
    with col_hh_t:
        st.markdown('<h2 class="brand-title" style="font-size: 1.5rem;">📖 TwinGuard-OT: Engineering & Evaluation Manual</h2>', unsafe_allow_html=True)
        st.caption("Deep technical specifications, mathematical equations, register architecture, and evaluation rubrics.")
    with col_hh_b:
        if st.button("✕ Close Hub", use_container_width=True):
            st.session_state.show_help_hub = False
            st.rerun()

    tab_h1, tab_h2, tab_h3, tab_h4 = st.tabs([
        "📐 Physical Hydrodynamics",
        "⚡ Virtual PLC & Modbus Architecture",
        "🎯 Cyber-Physical Threat Vectors",
        "🎓 RVCE Rubrics & Evaluation Checklist"
    ])

    with tab_h1:
        st.markdown(r"""
        #### 1. Continuous Hydrodynamic Differential Equation
        The physical water plant is modelled mathematically using first-principles continuous mass balance:
        """)
        st.latex(r"\frac{dh(t)}{dt} = \frac{Q_{in}(t) - Q_{out}(t)}{A_{tank}}")
        st.markdown(r"""
        * **Inflow Dynamics ($Q_{in}$)**: Governed by the virtual positive displacement pump:
          $$Q_{in}(t) = P_{state} \times 3.0\,\%/s$$
        * **Outflow Dynamics ($Q_{out}$)**: Follows Torricelli's Law of Fluid Efflux combined with discharge valve state:
          $$Q_{out}(t) = V_{state} \times \left(1.2 + 0.05 \sqrt{h(t)}\right)\,\%/s + Q_{leak}$$
        * **Physical Invariant**: Water level is physically constrained to $[0.0\%, 100.0\%]$. Overflow ($h \ge 100\%$) and dry-run cavitation ($h \le 0\%$) trigger physical safety interlocks.
        * **Sensor Decoupling**: Crucial to digital twin research:
          * $h_{true}(t)$: Actual physical water level in the tank.
          * $h_{sensor}(t)$: Measurement transmitted to PLC over Modbus (may include Gaussian telemetry noise $\mathcal{N}(0, \sigma^2)$ or cyber spoofing overrides).
        """)

    with tab_h2:
        st.markdown(r"""
        #### 2. Virtual PLC Scan Loop & Industrial Modbus Register Mapping
        The virtual Programmable Logic Controller executes a deterministic cyclic scan at **5.0 Hz (200 ms)**:
        1. **Input Scan**: Samples observed level from holding register `40001`.
        2. **Hysteresis Setpoint Control**:
           * If $h_{sensor} < 30.0\% \rightarrow$ Energize Pump (`ON`), Close Valve (`CLOSED`).
           * If $h_{sensor} \ge 80.0\% \rightarrow$ De-energize Pump (`OFF`), Open Valve (`OPEN`).
           * If $30.0\% \le h_{sensor} < 80.0\% \rightarrow$ Maintain current operational state (hysteresis deadband).
        3. **Emergency Interlock**: If $h_{sensor} \ge 95.0\%$, hardware failsafe forcibly trips the pump to prevent brim rupture.
        
        ##### Official Modbus TCP Register Map (Port 5020, Unit ID 1):
        | Address | Register Name | Scale | Unit | Type | Description |
        |:---:|:---|:---:|:---:|:---:|:---|
        | `40001` | `TANK_LEVEL_SENSOR` | 10.0 | % | RO | Reported tank level from virtual sensor |
        | `40002` | `SETPOINT_LEVEL` | 10.0 | % | RW | Desired setpoint (Default: 70.0%) |
        | `40003` | `PUMP_COMMAND` | 1.0 | Binary | RW | Inflow pump control (0=OFF, 1=ON) |
        | `40004` | `VALVE_COMMAND` | 1.0 | Binary | RW | Drain discharge valve (0=CLOSED, 1=OPEN) |
        | `40005` | `INFLOW_RATE` | 10.0 | %/s | RO | Flow telemetry sensor |
        | `40006` | `OUTFLOW_RATE` | 10.0 | %/s | RO | Discharge rate telemetry sensor |
        | `40007` | `ALARM_STATE` | 1.0 | Enum | RO | 0=Normal, 1=Low, 2=High, 3=Interlock |
        | `40011` | `TRUE_TANK_LEVEL` | 10.0 | % | RO | Ground-truth plant level (hidden from PLC) |
        | `40012` | `PHYSICAL_RESIDUAL`| 10.0 | % | RO | Instantaneous divergence $\|h_{sensor} - h_{shadow}\|$ |
        """)

    with tab_h3:
        st.markdown(r"""
        #### 3. Industrial Cyber-Physical Attack Taxonomy
        All attacks are executed against local loopback `127.0.0.1:5020` without external network exposure:
        1. **Sensor Spoofing (`sensor_spoofing.py`)**: Intercepts the sensor register and overwrites it with an artificially low value (e.g. 20%) while the tank is full, deceiving the PLC into overfilling.
        2. **Unauthorized Register Write (`unauthorized_write.py`)**: Rogue Modbus client injects unauthorized Function Code 06 writes directly to `PUMP_COMMAND` coil.
        3. **Replay Attack (`replay.py`)**: Records legitimate filling phase packets and replays them out-of-context during discharge, hiding real process drain.
        4. **Command Flooding (`command_flood.py`)**: Modbus TCP Denial-of-Service burst ($150 - 300\text{ req/s}$) starving the PLC scan cycle.
        5. **Abnormal Setpoint Manipulation (`setpoint_manipulation.py`)**: Manipulates holding register `40002` to an out-of-envelope boundary ($98.0\%$).
        """)

    with tab_h4:
        st.markdown("""
        #### 4. RVCE Experiential Learning (EL) Batch 2025 Rubrics Alignment
        * **Phase I (40 Marks)**: Problem Definition (20M), Objectives (10M), Methodology Flowchart (10M).
        * **Phase II (60 Marks)**: Project Execution (30M), Tools & Integration (20M), Partial Results (10M).
        * **Phase III (100 Marks)**: 
          * Prototype Demonstration (30M) — *Use this dashboard to trigger an attack live!*
          * Results & Discussion (20M) — *Show the Isolation Forest F1-score of 0.705 and ROC metrics*.
          * Report Completeness (20M) — *Attach exported CSV datasets and Modbus map*.
          * Poster & PPT (10M) — *Use the A3 poster template with dual-tank SCADA screenshots*.
          * Notable Outcome / Publication (20M) — *Benchmark run with N=1133 samples ready for IEEE student paper submission*.
        """)
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 1. PROCESS SCADA OVERVIEW
# ==============================================================================
if nav_choice == "🌊 Process SCADA Overview":
    st.markdown("""
    <div class="page-hero">
        <h3>Industrial Supervisory Control & Data Acquisition (SCADA)</h3>
        <p>Real-time physical process telemetry, closed-loop PLC actuator states, and process-aware residual monitoring.</p>
    </div>
    """, unsafe_allow_html=True)

    # Metric Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Reported Tank Level",
            f"{latest_level:.1f} %",
            delta=f"{latest_level - config['plc']['default_setpoint']:.1f}% to Setpoint"
        )
    with m2:
        st.metric("Inflow Pump (Coil 40003)", "🟢 ENERGIZED" if latest_pump == 1 else "⚪ IDLE")
    with m3:
        st.metric("Discharge Valve (Coil 40004)", "🟢 OPEN" if latest_valve == 1 else "⚪ CLOSED")
    with m4:
        st.metric("Physical Residual |r(t)|", f"{latest_residual:.2f} %", delta_color="inverse")

    col_scada1, col_scada2 = st.columns([1, 2])

    with col_scada1:
        st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 14px;">Cyber-Physical Tank Rig</div>', unsafe_allow_html=True)

        is_spoofed = abs(latest_level - latest_true) > 4.0
        sensor_color_cls = "liquid-wave liquid-sensor"
        if is_spoofed:
            sensor_color_cls = "liquid-wave liquid-spoofed"

        high_line = config['plc']['high_threshold']
        low_line = config['plc']['low_threshold']

        st.markdown(f"""
        <div class="scada-rig">
            <div class="scada-column">
                <span style="font-size: 0.72rem; color: #38bdf8; font-weight: 800;">GROUND TRUTH</span>
                <div class="tank-glass">
                    <div class="interlock-line" style="bottom: {high_line}%;"></div>
                    <div class="interlock-line" style="bottom: {low_line}%;"></div>
                    <div class="liquid-wave liquid-true" style="height: {latest_true}%;"></div>
                </div>
                <span style="font-size: 1.15rem; font-weight: 800; color: #38bdf8;">{latest_true:.1f}%</span>
            </div>
            <div class="scada-column">
                <span style="font-size: 0.72rem; color: {'#f87171' if is_spoofed else '#34d399'}; font-weight: 800;">
                    REPORTED SENSOR {('(SPOOFED)' if is_spoofed else '')}
                </span>
                <div class="tank-glass">
                    <div class="interlock-line" style="bottom: {high_line}%;"></div>
                    <div class="interlock-line" style="bottom: {low_line}%;"></div>
                    <div class="{sensor_color_cls}" style="height: {latest_level}%;"></div>
                </div>
                <span style="font-size: 1.15rem; font-weight: 800; color: {'#f87171' if is_spoofed else '#34d399'};">{latest_level:.1f}%</span>
            </div>
        </div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 14px;">
            Dashed Markers: Hysteresis Cutoff ({high_line}%) & Refill Trigger ({low_line}%)
        </div>
        </div>
        """, unsafe_allow_html=True)

    with col_scada2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px;">Real-Time Hydrodynamic Trajectory</div>', unsafe_allow_html=True)

        if not df_telemetry.empty:
            recent_df = df_telemetry.tail(120).copy()
            recent_df["Time_Sec"] = (recent_df["timestamp"] - recent_df["timestamp"].iloc[0]).round(1)
            fig_trend = px.line(
                recent_df,
                x="Time_Sec",
                y=["sensor_level", "true_level"],
                labels={"value": "Level (%)", "Time_Sec": "Elapsed (s)", "variable": "Telemetry Stream"},
                color_discrete_map={"sensor_level": "#34d399", "true_level": "#38bdf8"},
            )
            fig_trend.update_layout(
                height=285,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("System initializing... telemetry stream will populate automatically.")
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 2. DIGITAL TWIN RESIDUAL ANALYSIS
# ==============================================================================
elif nav_choice == "🔄 Digital Twin Shadow Model":
    st.markdown("""
    <div class="page-hero">
        <h3>Digital Twin Shadow Model & Hydrodynamic Residuals</h3>
        <p>Continuous residual computation r(t) = |h_sensor(t) - h_shadow(t)| revealing cyber-physical discrepancy.</p>
    </div>
    """, unsafe_allow_html=True)

    if df_telemetry.empty:
        st.info("No recorded telemetry available. Run an attack experiment to inspect residuals.")
    else:
        exp_list = list(df_telemetry["experiment_id"].unique())
        selected_exp = st.selectbox("Select Experiment Run", exp_list, index=len(exp_list) - 1)
        exp_df = df_telemetry[df_telemetry["experiment_id"] == selected_exp].copy()
        exp_df["Elapsed_Sec"] = (exp_df["timestamp"] - exp_df["timestamp"].iloc[0]).round(1)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("1. True Physical Level vs Observed Sensor Signal")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["true_level"], mode="lines", name="Ground Truth Physical Level", line=dict(color="#38bdf8", width=3)))
        fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["sensor_level"], mode="lines", name="Reported Sensor Signal", line=dict(color="#f87171", width=2, dash="dot")))
        fig1.add_hline(y=config["plc"]["high_threshold"], line_dash="dash", line_color="#fbbf24", annotation_text="High Hysteresis (80%)")
        fig1.add_hline(y=config["plc"]["low_threshold"], line_dash="dash", line_color="#fbbf24", annotation_text="Low Hysteresis (30%)")
        fig1.update_layout(height=320, xaxis_title="Elapsed Time (s)", yaxis_title="Water Level (%)", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("2. Instantaneous Physical Residual: |Observed - Expected|")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["process_residual"], mode="lines", name="Process Residual r(t)", line=dict(color="#c084fc", width=2.5)))
        fig2.add_hline(y=config["detection"]["residual_threshold"], line_dash="dash", line_color="#ef4444", annotation_text=f"Anomaly Threshold ({config['detection']['residual_threshold']}%)")
        fig2.update_layout(height=260, xaxis_title="Elapsed Time (s)", yaxis_title="Residual Deviation (%)", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 3. MODBUS PROTOCOL MONITOR
# ==============================================================================
elif nav_choice == "📡 Modbus Protocol Inspector":
    st.markdown("""
    <div class="page-hero">
        <h3>Industrial Modbus TCP Deep Packet Inspector</h3>
        <p>Live transaction logging, function code analysis, and packet arrival rate tracking on port 5020.</p>
    </div>
    """, unsafe_allow_html=True)

    df_events = db.get_modbus_events()
    if df_events.empty:
        st.info("No network events recorded yet. Connect a client or trigger attack traffic.")
    else:
        col_m1, col_m2 = st.columns([2, 1])

        with col_m1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Packet Arrival Rate (Requests / sec)")
            df_events["Time"] = pd.to_datetime(df_events["timestamp"], unit="s")
            fig_rate = px.line(
                df_events.tail(120),
                x="Time",
                y="request_rate",
                labels={"request_rate": "Requests / sec", "Time": "Timestamp"},
                color_discrete_sequence=["#38bdf8"],
            )
            fig_rate.add_hline(y=config["detection"]["request_rate_flood_threshold"], line_dash="dash", line_color="#ef4444", annotation_text="Flood Alarm (30 req/s)")
            fig_rate.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_rate, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_m2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Function Code Breakdown")
            fc_counts = df_events["function_name"].value_counts().reset_index()
            fc_counts.columns = ["Function", "Count"]
            fig_pie = px.pie(fc_counts, values="Count", names="Function", color_discrete_sequence=px.colors.qualitative.Prism)
            fig_pie.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Live Modbus Frame Transaction Table")
        st.dataframe(
            df_events[["timestamp", "client_ip", "function_name", "register_address", "register_name", "value", "is_write", "request_rate"]].tail(50),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 4. CYBERATTACK LABORATORY
# ==============================================================================
elif nav_choice == "🎯 Cyberattack Laboratory":
    st.markdown("""
    <div class="page-hero">
        <h3>ICS Threat Injection & Penetration Laboratory</h3>
        <p>Safely inject controlled OT cyberattacks against the virtual PLC on localhost 127.0.0.1:5020.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Configure Threat Scenario")

    attack_type = st.selectbox(
        "Choose Attack Vector",
        [
            "Sensor Spoofing",
            "Unauthorized Register Write",
            "Replay Attack",
            "Command Flooding",
            "Abnormal Setpoint Manipulation",
        ],
    )

    c_at1, c_at2 = st.columns(2)
    with c_at1:
        duration = st.slider("Attack Duration (seconds)", min_value=5, max_value=30, value=12)

    with c_at2:
        if attack_type == "Sensor Spoofing":
            spoof_val = st.slider("Falsified Tank Level (%)", min_value=0.0, max_value=100.0, value=20.0)
            st.caption("Reports falsified low level to PLC, forcing pump to cause an overflow disaster.")
        elif attack_type == "Unauthorized Register Write":
            target_reg = st.selectbox("Target Control Register", ["PUMP_COMMAND (40003)", "VALVE_COMMAND (40004)"])
            st.caption("Sends unauthorized FC06 write packets directly to physical actuator holding registers.")
        elif attack_type == "Command Flooding":
            flood_rate = st.slider("Target Request Rate (req/s)", min_value=50, max_value=300, value=150)
            st.caption("Floods PLC network socket with high-frequency queries to trigger CPU starvation.")
        elif attack_type == "Abnormal Setpoint Manipulation":
            setpoint_val = st.slider("Out-of-Envelope Setpoint (%)", min_value=5.0, max_value=99.0, value=98.0)
            st.caption("Forces PLC setpoint outside the safe operational design envelope.")
        else:
            st.caption("Captures legitimate filling sequence frames and replays them during plant drain.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 INJECT CYBERATTACK SCENARIO", type="primary", use_container_width=True):
        st.info(f"Injecting {attack_type} against local simulation...")
        attack_key_map = {
            "Sensor Spoofing": "sensor_spoofing",
            "Unauthorized Register Write": "unauthorized_write",
            "Replay Attack": "replay",
            "Command Flooding": "command_flood",
            "Abnormal Setpoint Manipulation": "setpoint_manipulation",
        }
        internal_name = attack_key_map[attack_type]

        with st.spinner(f"Executing {attack_type} for {duration} seconds..."):
            csv_path = run_attack_experiment(
                attack_name=internal_name,
                warmup_sec=3.0,
                attack_duration_sec=float(duration),
                cooldown_sec=3.0,
            )
            st.success(f"Attack execution completed! Telemetry recorded and exported to: {csv_path}")
            time.sleep(1.0)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 5. MULTI-TIER ANOMALY DETECTION
# ==============================================================================
elif nav_choice == "🛡️ Multi-Tier Anomaly Detection":
    st.markdown("""
    <div class="page-hero">
        <h3>Multi-Tier Process-Aware Detection & Correlation</h3>
        <p>Hybrid engine unifying deterministic domain rules, hydrodynamic shadow models, and Isolation Forest ML.</p>
    </div>
    """, unsafe_allow_html=True)

    df_detections = db.get_detections()
    if df_detections.empty:
        st.info("No detection events recorded yet. Run an experiment or attack to generate alerts.")
    else:
        anom_only = df_detections[df_detections["is_anomaly"] == 1]

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("Total Evaluation Checks", len(df_detections))
        with col_d2:
            st.metric("Flagged Anomalies", len(anom_only))
        with col_d3:
            cp_count = len(df_detections[df_detections["correlation_category"] == "CYBER_PHYSICAL_ATTACK"])
            st.metric("Correlated Cyber-Physical Attacks", cp_count)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Cyber-Physical Incident Classification Breakdown")
        cat_counts = df_detections["correlation_category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_cat = px.bar(
            cat_counts,
            x="Category",
            y="Count",
            color="Category",
            color_discrete_map={
                "NORMAL": "#34d399",
                "CYBER_ONLY": "#38bdf8",
                "PROCESS_ONLY": "#fbbf24",
                "CYBER_PHYSICAL_ATTACK": "#f87171",
            }
        )
        fig_cat.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Explainable Security Incident Feed")
        if not anom_only.empty:
            for _, alert in anom_only.tail(10).iterrows():
                with st.expander(f"🚨 [{alert['severity']}] {alert['correlation_category']} — Rule: {alert['rule_id']}"):
                    st.write(f"**Explanation:** {alert['explanation']}")
                    st.write(f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert['timestamp']))}")
                    st.write(f"**Machine Learning Anomaly Score:** `{alert['anomaly_score']:.3f}`")
        else:
            st.success("All processes running normally. No anomalies detected.")
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 6. STATISTICAL PROCESS ANALYTICS
# ==============================================================================
elif nav_choice == "📊 Statistical Process Analytics":
    st.markdown("""
    <div class="page-hero">
        <h3>Process Variable Dynamics & Residual Distributions</h3>
        <p>Continuous statistical inspection of sensor drift, actuator correlation, and error margins.</p>
    </div>
    """, unsafe_allow_html=True)

    if df_telemetry.empty:
        st.info("No recorded telemetry available for analytics.")
    else:
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Physical Residual Histogram")
            fig_hist = px.histogram(
                df_telemetry,
                x="process_residual",
                color="attack_type",
                nbins=35,
                labels={"process_residual": "Residual Error (%)", "count": "Sample Count"},
            )
            fig_hist.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hist, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_a2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Sensor vs Ground Truth Discrepancy")
            fig_scatter = px.scatter(
                df_telemetry,
                x="true_level",
                y="sensor_level",
                color="attack_type",
                labels={"true_level": "True Plant Level (%)", "sensor_level": "Reported Sensor (%)"},
            )
            fig_scatter.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 7. EMPIRICAL EVALUATION METRICS
# ==============================================================================
elif nav_choice == "🏆 Empirical Evaluation Metrics":
    st.markdown("""
    <div class="page-hero">
        <h3>Empirical Model Evaluation & Benchmark Metrics</h3>
        <p>Mathematical verification of detection performance against actual ground-truth labelled datasets (N = 1133).</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Recompute Metrics from Current Database", use_container_width=True):
        with st.spinner("Executing mathematical evaluation across all recorded datasets..."):
            evaluate_experiment()
            st.success("Empirical benchmark recalculation complete!")
            st.rerun()

    df_eval = db.get_evaluations()
    if df_eval.empty:
        st.warning("No evaluation metrics generated yet. Click 'Recompute Metrics' above to calculate.")
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Comparative Detection Benchmark Table")
        st.dataframe(
            df_eval[["model_name", "total_samples", "true_positives", "false_positives", "true_negatives", "false_negatives", "accuracy", "precision", "recall", "f1_score", "false_positive_rate"]].drop_duplicates(subset=["model_name"]),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("F1-Score and Accuracy Comparison")
        latest_unique = df_eval.drop_duplicates(subset=["model_name"])
        fig_bar = px.bar(
            latest_unique,
            x="model_name",
            y=["accuracy", "precision", "recall", "f1_score"],
            barmode="group",
            labels={"value": "Score (0.0 to 1.0)", "model_name": "Detection Approach"},
            color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399", "#f87171"],
        )
        fig_bar.update_layout(height=340, yaxis_range=[0, 1.05], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 8. DATASETS & RESEARCH ARTIFACTS
# ==============================================================================
elif nav_choice == "💾 Datasets & Research Artifacts":
    st.markdown("""
    <div class="page-hero">
        <h3>Experimental Datasets & Publication Artifacts</h3>
        <p>Inspect recorded time-series telemetry and export CSV datasets for academic report appendices.</p>
    </div>
    """, unsafe_allow_html=True)

    if df_telemetry.empty:
        st.info("No recorded datasets found in database.")
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        exp_list = ["ALL"] + list(df_telemetry["experiment_id"].unique())
        selected = st.selectbox("Select Experiment Run to View & Download", exp_list)

        filtered_df = df_telemetry if selected == "ALL" else df_telemetry[df_telemetry["experiment_id"] == selected]
        st.write(f"Showing **{len(filtered_df)}** recorded telemetry frames:")
        st.dataframe(filtered_df.tail(200), use_container_width=True, hide_index=True)

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Labelled Dataset (CSV)",
            data=csv_data,
            file_name=f"twinguard_dataset_{selected}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# AUTO-REFRESH EXECUTION LOOP (Kept Active & Configurable)
# ==============================================================================
if st.session_state.auto_refresh:
    time.sleep(float(st.session_state.refresh_speed))
    st.rerun()
