"""
TwinGuard-OT: Process-Aware Digital Twin for Cybersecurity Testing and Anomaly Detection in ICS.
Material Design 3 (MD3) Expressive SCADA & Security Operations Center (SOC) Platform.
Designed for high-impact academic demonstration, empirical research, and industrial emulation.
Reference Architecture: Material Design 3 (https://m3.material.io/develop/web)
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
if "onboarding_completed" not in st.session_state:
    st.session_state.onboarding_completed = False
if "show_onboarding" not in st.session_state:
    st.session_state.show_onboarding = not st.session_state.onboarding_completed
if "refresh_speed" not in st.session_state:
    st.session_state.refresh_speed = 3.0
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "nav_choice" not in st.session_state:
    st.session_state.nav_choice = "🌊 Process SCADA Overview"

# ==============================================================================
# HIGH-PERFORMANCE TELEMETRY & MD3 DARK SYSTEM STYLES
# Formula 1 Telemetry & Material Design 3 Dark Theme Architecture
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Typography & Telemetry Canvas */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* Ultra-Dense Telemetry Canvas (F1 Dark Carbon Slate) */
    .stApp {
        background-color: #080c14 !important;
        background-image: radial-gradient(circle at 50% 0%, rgba(14, 165, 233, 0.05) 0%, transparent 60%) !important;
        color: #f1f5f9 !important;
    }

    /* Tighten Root Layout Spacing (Telemetry Density) */
    .block-container {
        padding-top: 0.85rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.8rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.55rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0.65rem !important;
    }

    /* MD3 Dark Container Cards (Elevation-1 Dark Carbon Surfaces) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #0f1523 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35) !important;
        margin-bottom: 6px !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(255, 255, 255, 0.14) !important;
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.45) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: none !important;
    }

    /* MD3 Dark Metric Telemetry Tiles */
    [data-testid="stMetric"] {
        background: #0f1523 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(56, 189, 248, 0.3) !important;
        background: #131a2c !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        margin-bottom: 2px !important;
    }
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-weight: 800 !important;
        font-size: 1.55rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: -0.01em !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.76rem !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Standard Interactive Buttons */
    .stButton > button {
        border-radius: 8px !important;
        padding: 7px 16px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        background: #141c2c !important;
        color: #f1f5f9 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s cubic-bezier(0.2, 0, 0, 1) !important;
    }
    .stButton > button:hover {
        background: #1a2438 !important;
        border-color: rgba(255, 255, 255, 0.18) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"] {
        background: #0284c7 !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 2px 10px rgba(2, 132, 199, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #0369a1 !important;
        border-color: #7dd3fc !important;
        color: #ffffff !important;
    }

    /* MD3 Dark Sidebar Drawer */
    section[data-testid="stSidebar"] {
        background: #090e18 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.5) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    /* Sidebar Navigation Subdivisions */
    .sidebar-section-divider {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 10px 2px 4px 2px;
        padding-top: 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .subdivision-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        font-weight: 700;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.10);
        border: 1px solid rgba(56, 189, 248, 0.22);
        padding: 1px 5px;
        border-radius: 4px;
        letter-spacing: 0.06em;
    }
    .subdivision-title {
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
    }

    /* Sidebar Navigation Button Pills */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 7px 12px !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin-bottom: 2px !important;
        letter-spacing: -0.01em !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        transition: all 0.15s ease !important;
    }

    /* Inactive Nav Item */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: #94a3b8 !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #f1f5f9 !important;
        border-color: rgba(255, 255, 255, 0.14) !important;
        transform: translateX(2px) !important;
    }

    /* Active Nav Item (F1 Telemetry Focus Pill) */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(56, 189, 248, 0.14) !important;
        border: 1px solid rgba(56, 189, 248, 0.40) !important;
        border-left: 3px solid #38bdf8 !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.15) !important;
        transform: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(56, 189, 248, 0.20) !important;
        color: #e0f2fe !important;
    }

    /* Status Badges */
    .chip-green {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(34, 197, 94, 0.12);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.32);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
    }
    .chip-red {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.40);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        animation: pulseAlertDark 2s infinite ease-in-out;
    }
    @keyframes pulseAlertDark {
        0%, 100% { box-shadow: 0 0 0 rgba(239, 68, 68, 0); }
        50% { box-shadow: 0 0 16px rgba(239, 68, 68, 0.35); }
    }
    .dot-live {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #22c55e;
        box-shadow: 0 0 8px #22c55e;
    }
    .dot-danger {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444;
    }

    .tech-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.22);
        padding: 3px 10px;
        border-radius: 9999px;
        color: #38bdf8;
        font-weight: 600;
    }

    /* Page Hero (Compact Dark Telemetry Header) */
    .page-hero {
        background: #0f1523;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #38bdf8;
        border-radius: 10px;
        padding: 9px 16px;
        margin-bottom: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
    }
    .page-hero h3 {
        margin: 0 0 2px 0;
        font-size: 1.06rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .page-hero p {
        margin: 0;
        color: #94a3b8;
        font-size: 0.80rem;
        line-height: 1.4;
    }

    /* SCADA Tank Visualizer (Dark F1 Telemetry Glass) */
    .scada-rig {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 28px;
        padding: 14px 18px;
        background: #090e18;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .scada-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
    }
    .tank-glass {
        width: 120px;
        height: 195px;
        border: 2px solid rgba(255, 255, 255, 0.18);
        border-top: none;
        border-radius: 0 0 14px 14px;
        position: relative;
        background: rgba(15, 23, 42, 0.85);
        overflow: hidden;
        box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.7);
    }
    .liquid-wave {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        transition: height 0.35s cubic-bezier(0.2, 0, 0, 1);
        border-top: 2px solid rgba(255, 255, 255, 0.85);
    }
    .liquid-true {
        background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 -2px 14px rgba(56, 189, 248, 0.35);
    }
    .liquid-sensor {
        background: linear-gradient(180deg, #34d399 0%, #059669 100%);
        box-shadow: 0 -2px 14px rgba(52, 211, 153, 0.35);
    }
    .liquid-spoofed {
        background: linear-gradient(180deg, #f87171 0%, #dc2626 100%) !important;
        box-shadow: 0 -2px 18px rgba(239, 68, 68, 0.55) !important;
    }
    .interlock-line {
        position: absolute;
        left: 0;
        right: 0;
        height: 1px;
        border-top: 1px dashed #f59e0b;
        z-index: 10;
    }

    /* M3 Dark Segmented Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #090e18 !important;
        padding: 4px;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        padding: 6px 14px !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        transition: all 0.15s ease !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #141c2c !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }

    /* MD3 Dark Dialog & Onboarding Modal */
    div[data-testid="stDialog"] div[role="dialog"] {
        background: #0d121f !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        box-shadow: 0 25px 60px -10px rgba(0, 0, 0, 0.8) !important;
        color: #f8fafc !important;
        max-width: 94vw !important;
        width: 1040px !important;
        padding: 24px 28px !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] h2 {
        color: #f8fafc !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"] {
        color: #94a3b8 !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"]:hover {
        color: #f8fafc !important;
    }

    /* Onboarding Card Grid (Dark Telemetry Cards) */
    .onboarding-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin: 14px 0;
    }
    @media (max-width: 768px) {
        .onboarding-grid {
            grid-template-columns: 1fr;
        }
    }
    .onboarding-card {
        background: #121827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 16px;
        transition: all 0.15s cubic-bezier(0.2, 0, 0, 1);
    }
    .onboarding-card:hover {
        border-color: #38bdf8;
        background: #172033;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }
    .onboarding-card-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .onboarding-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 2px 7px;
        border-radius: 4px;
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.25);
    }
    .onboarding-card-desc {
        font-size: 0.80rem;
        color: #94a3b8;
        line-height: 1.45;
        margin: 0 0 8px 0;
    }
    .onboarding-card-tip {
        font-size: 0.74rem;
        color: #7dd3fc;
        background: rgba(56, 189, 248, 0.08);
        border-left: 3px solid #38bdf8;
        padding: 5px 8px;
        border-radius: 4px;
        margin: 0;
    }

    /* Onboarding Step Cards */
    .onboarding-step {
        display: flex;
        gap: 14px;
        background: #121827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        align-items: flex-start;
    }
    .onboarding-step-num {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #0284c7;
        color: #ffffff;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.92rem;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
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
# Subdivided Navigation Drawer with High-Performance Telemetry Hierarchy
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin: 4px 0 10px 2px;">
        <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 8px; border-radius: 10px; box-shadow: 0 2px 10px rgba(2,132,199,0.35);">
            <span style="font-size: 1.3rem; display: block; line-height: 1;">🛡️</span>
        </div>
        <div>
            <div style="font-size: 1.08rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">TwinGuard-OT</div>
            <div style="font-size: 0.66rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">ICS DIGITAL TWIN v2.2</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # SUBDIVISION 01: SCADA & PHYSICAL TWIN
    # -------------------------------------------------------------
    st.markdown("""
    <div class="sidebar-section-divider">
        <span class="subdivision-tag">DIV 01</span>
        <span class="subdivision-title">SCADA & DIGITAL TWIN</span>
    </div>
    """, unsafe_allow_html=True)

    is_scada_active = (st.session_state.nav_choice == "🌊 Process SCADA Overview")
    if st.button("🌊  Process SCADA Overview", key="nav_scada", use_container_width=True, type="primary" if is_scada_active else "secondary"):
        st.session_state.nav_choice = "🌊 Process SCADA Overview"
        st.rerun()

    is_twin_active = (st.session_state.nav_choice == "🔄 Digital Twin Shadow Model")
    if st.button("🔄  Digital Twin Shadow", key="nav_twin", use_container_width=True, type="primary" if is_twin_active else "secondary"):
        st.session_state.nav_choice = "🔄 Digital Twin Shadow Model"
        st.rerun()

    is_modbus_active = (st.session_state.nav_choice == "📡 Modbus Protocol Inspector")
    if st.button("📡  Modbus Protocol Inspector", key="nav_modbus", use_container_width=True, type="primary" if is_modbus_active else "secondary"):
        st.session_state.nav_choice = "📡 Modbus Protocol Inspector"
        st.rerun()

    # -------------------------------------------------------------
    # SUBDIVISION 02: CYBER THREAT & DETECTION
    # -------------------------------------------------------------
    st.markdown("""
    <div class="sidebar-section-divider">
        <span class="subdivision-tag">DIV 02</span>
        <span class="subdivision-title">CYBER THREAT LAB</span>
    </div>
    """, unsafe_allow_html=True)

    is_attacks_active = (st.session_state.nav_choice == "🎯 Cyberattack Laboratory")
    if st.button("🎯  Cyberattack Laboratory", key="nav_attacks", use_container_width=True, type="primary" if is_attacks_active else "secondary"):
        st.session_state.nav_choice = "🎯 Cyberattack Laboratory"
        st.rerun()

    is_soc_active = (st.session_state.nav_choice == "🛡️ Multi-Tier Anomaly Detection")
    if st.button("🛡️  Multi-Tier Anomaly Detection", key="nav_soc", use_container_width=True, type="primary" if is_soc_active else "secondary"):
        st.session_state.nav_choice = "🛡️ Multi-Tier Anomaly Detection"
        st.rerun()

    # -------------------------------------------------------------
    # SUBDIVISION 03: BENCHMARKS & RESEARCH DATA
    # -------------------------------------------------------------
    st.markdown("""
    <div class="sidebar-section-divider">
        <span class="subdivision-tag">DIV 03</span>
        <span class="subdivision-title">ANALYTICS & METRICS</span>
    </div>
    """, unsafe_allow_html=True)

    is_analytics_active = (st.session_state.nav_choice == "📊 Statistical Process Analytics")
    if st.button("📊  Statistical Process Analytics", key="nav_analytics", use_container_width=True, type="primary" if is_analytics_active else "secondary"):
        st.session_state.nav_choice = "📊 Statistical Process Analytics"
        st.rerun()

    is_eval_active = (st.session_state.nav_choice == "🏆 Empirical Evaluation Metrics")
    if st.button("🏆  Empirical Evaluation Metrics", key="nav_eval", use_container_width=True, type="primary" if is_eval_active else "secondary"):
        st.session_state.nav_choice = "🏆 Empirical Evaluation Metrics"
        st.rerun()

    is_data_active = (st.session_state.nav_choice == "💾 Datasets & Research Artifacts")
    if st.button("💾  Datasets & Research Artifacts", key="nav_data", use_container_width=True, type="primary" if is_data_active else "secondary"):
        st.session_state.nav_choice = "💾 Datasets & Research Artifacts"
        st.rerun()

    # -------------------------------------------------------------
    # TELEMETRY SYNCHRONIZATION DOCK
    # -------------------------------------------------------------
    st.markdown("""
    <div class="sidebar-section-divider">
        <span class="subdivision-tag">SYNC</span>
        <span class="subdivision-title">TELEMETRY CONTROLS</span>
    </div>
    """, unsafe_allow_html=True)

    col_sync1, col_sync2 = st.columns([1, 1])
    with col_sync1:
        auto_sync = st.toggle("Auto-Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_sync
    with col_sync2:
        speed_label = st.selectbox(
            "Interval",
            ["Fast (1s)", "Standard (3s)", "Relaxed (5s)"],
            index=1,
            label_visibility="collapsed"
        )
        speed_map = {"Fast (1s)": 1.0, "Standard (3s)": 3.0, "Relaxed (5s)": 5.0}
        st.session_state.refresh_speed = speed_map[speed_label]

    if st.button("⚡ Force Manual Sync", use_container_width=True):
        st.rerun()

    # System Status Dock (Dark Telemetry)
    st.markdown(f"""
    <div style="background: #0d121f; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); font-size: 0.72rem; color: #94a3b8; line-height: 1.55; margin-top: 8px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
            <span>MODBUS HOST:</span>
            <span style="color: #f8fafc; font-family: monospace; font-weight: 600;">127.0.0.1:5020</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
            <span>PLC SCAN RATE:</span>
            <span style="color: #4ade80; font-weight: 700;">5.0 Hz (200ms)</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
            <span>DATABASE:</span>
            <span style="color: #38bdf8; font-weight: 600;">SQLite (WAL Active)</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>INSTITUTION:</span>
            <span style="color: #cbd5e1; font-weight: 500;">RVCE — III Sem EL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

nav_choice = st.session_state.nav_choice


# ==============================================================================
# ONBOARDING TUTORIAL MODAL / OVERLAY (MD3 Expressive SaaS Flow)
# ==============================================================================
def on_dialog_dismiss():
    st.session_state.onboarding_completed = True
    st.session_state.show_onboarding = False


@st.dialog("🚀 Welcome to TwinGuard-OT | Platform Onboarding", width="large", on_dismiss=on_dialog_dismiss)
def show_onboarding_tutorial():
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.28); padding: 4px 12px; border-radius: 9999px; font-size: 0.72rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
            <span>🛡️ ICS CYBERSECURITY PLATFORM</span>
        </div>
        <h2 style="font-size: 1.45rem; font-weight: 800; margin: 0 0 4px 0; color: #f8fafc;">
            TwinGuard-OT: Process-Aware Digital Twin
        </h2>
        <p style="color: #94a3b8; font-size: 0.86rem; margin: 0; line-height: 1.5;">
            Welcome to the TwinGuard-OT industrial operations & cybersecurity operations center. 
            TwinGuard-OT pairs continuous hydrodynamic physical process simulation with virtual PLC control, 
            industrial Modbus TCP networking, controlled threat injection, and hybrid physics-ML anomaly detection.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_tour, tab_steps, tab_sys = st.tabs([
        "🧭 Navigation Menu Tour (8 Core Modules)",
        "⚡ 3-Step Guided Experiment Workflow",
        "📐 System Architecture & Modbus Map"
    ])

    with tab_tour:
        st.markdown("""
        <div class="onboarding-grid">
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>🌊 1. Process SCADA Overview</span>
                    <span class="onboarding-tag">Operations & HMI</span>
                </div>
                <p class="onboarding-card-desc">
                    Primary supervisory dashboard monitoring live water tank level, pump and valve states, and automated hysteresis control.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Interactive Rig:</strong> View animated dual-column water tanks comparing ground truth against reported sensor readings.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>🔄 2. Digital Twin Shadow Model</span>
                    <span class="onboarding-tag">Physics Reference</span>
                </div>
                <p class="onboarding-card-desc">
                    First-principles mass-balance differential equation solver running continuously in parallel with the live plant.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Key Metric:</strong> Physical Residual |r(t)| = |h_sensor - h_shadow| detects deception when PLC appears normal.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>📡 3. Modbus Protocol Inspector</span>
                    <span class="onboarding-tag">OT Network Forensics</span>
                </div>
                <p class="onboarding-card-desc">
                    Deep packet inspection of raw industrial Modbus TCP communication over localhost port 5020 (Unit ID 1).
                </p>
                <p class="onboarding-card-tip">
                    <strong>Forensics:</strong> Tracks Function Codes (FC03, FC06, FC16), transaction latency, and packet request rates (req/s).
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>🎯 4. Cyberattack Laboratory</span>
                    <span class="onboarding-tag">Red Team Injection</span>
                </div>
                <p class="onboarding-card-desc">
                    Isolated experimentation suite to safely execute 5 industrial cyberattacks against local simulation in real time.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Vectors:</strong> Sensor Spoofing, Unauthorized Write, Packet Replay, Command Flooding, Setpoint Manipulation.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>🛡️ 5. Multi-Tier Anomaly Detection</span>
                    <span class="onboarding-tag">Blue Team SOC</span>
                </div>
                <p class="onboarding-card-desc">
                    Defense-in-depth correlation fusing deterministic domain rules, physics residuals, and scikit-learn Isolation Forest ML.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Correlation:</strong> Categorizes incidents into Normal, Cyber-Only, Process-Only, or Cyber-Physical Attacks.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>📊 6. Statistical Process Analytics</span>
                    <span class="onboarding-tag">Process Dynamics</span>
                </div>
                <p class="onboarding-card-desc">
                    High-resolution exploratory data analysis of sensor drift, actuator correlations, and physical distribution curves.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Analytics:</strong> Interactive Plotly residual error histograms and sensor vs ground-truth scatter plots.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>🏆 7. Empirical Evaluation Metrics</span>
                    <span class="onboarding-tag">ML Benchmarking</span>
                </div>
                <p class="onboarding-card-desc">
                    Quantitative academic verification computing Accuracy, Precision, Recall, and F1-Scores across labelled datasets.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Scientific Proof:</strong> Dynamic benchmark recalculation, confusion matrices, and model comparison charts.
                </p>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-card-title">
                    <span>💾 8. Datasets & Research Artifacts</span>
                    <span class="onboarding-tag">Data Ops & Export</span>
                </div>
                <p class="onboarding-card-desc">
                    Full time-series data table inspector with instant CSV export of timestamped, ground-truth labelled experimental runs.
                </p>
                <p class="onboarding-card-tip">
                    <strong>Publication:</strong> Export clean datasets ready for college project appendices and IEEE research papers.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab_steps:
        st.markdown("""
        <div style="margin: 14px 0;">
            <div class="onboarding-step">
                <div class="onboarding-step-num">1</div>
                <div>
                    <div style="font-weight: 700; color: #f8fafc; font-size: 0.98rem; margin-bottom: 3px;">Step 1: Observe Normal Baseline Operation</div>
                    <div style="color: #94a3b8; font-size: 0.84rem; line-height: 1.45;">
                        Navigate to <strong>🌊 Process SCADA Overview</strong>. Confirm that the simulated water level naturally cycles within hysteresis limits (refill at 30%, shutoff at 80%). The top bar displays a green <code>PLANT OPERATING NORMALLY</code> badge with near-zero physical residual (&lt; 5%).
                    </div>
                </div>
            </div>
            <div class="onboarding-step">
                <div class="onboarding-step-num">2</div>
                <div>
                    <div style="font-weight: 700; color: #f8fafc; font-size: 0.98rem; margin-bottom: 3px;">Step 2: Inject a Controlled Cyber Threat</div>
                    <div style="color: #94a3b8; font-size: 0.84rem; line-height: 1.45;">
                        Switch to <strong>🎯 Cyberattack Laboratory</strong>. Select <em>Sensor Spoofing</em> (falsified level = 20%) or <em>Command Flooding</em> (150 req/s), set duration to 12s, and click <strong>INJECT CYBERATTACK SCENARIO</strong>. The attack runs against localhost:5020 without risking physical equipment.
                    </div>
                </div>
            </div>
            <div class="onboarding-step">
                <div class="onboarding-step-num">3</div>
                <div>
                    <div style="font-weight: 700; color: #f8fafc; font-size: 0.98rem; margin-bottom: 3px;">Step 3: Analyze Multi-Tier Detection & Verification</div>
                    <div style="color: #94a3b8; font-size: 0.84rem; line-height: 1.45;">
                        Go to <strong>🛡️ Multi-Tier Anomaly Detection</strong> and <strong>🔄 Digital Twin Shadow Model</strong>. Notice how the physical residual diverges past the 5.0% threshold while the reported sensor lies, triggering the Isolation Forest and cyber-physical correlation alarm. Then inspect <strong>🏆 Empirical Evaluation Metrics</strong> for quantitative F1-scores.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab_sys:
        st.markdown("""
        <div style="background: #101625; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 16px; margin: 14px 0;">
            <h4 style="color: #f8fafc; margin-top: 0; font-size: 0.98rem;">Closed-Loop Cyber-Physical Digital Twin Architecture</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; font-size: 0.80rem;">
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #38bdf8;">
                    <div style="font-weight: 700; color: #38bdf8;">1. Physical Plant</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Continuous mass-balance dh/dt = (Qin - Qout)/A with Torricelli efflux discharge.</div>
                </div>
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #818cf8;">
                    <div style="font-weight: 700; color: #818cf8;">2. Virtual PLC</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Deterministic 5.0 Hz cyclic scan with hysteresis pump/valve control logic.</div>
                </div>
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #34d399;">
                    <div style="font-weight: 700; color: #34d399;">3. Modbus TCP</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Port 5020 slave holding registers 40001–40012 for industrial telemetry & commands.</div>
                </div>
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #fbbf24;">
                    <div style="font-weight: 700; color: #fbbf24;">4. Digital Twin</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Shadow physics reference calculating instantaneous residual |h_sensor - h_shadow|.</div>
                </div>
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #f87171;">
                    <div style="font-weight: 700; color: #f87171;">5. Threat Simulator</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Red team injector targeting Modbus registers with spoofing, writes, floods, replays.</div>
                </div>
                <div style="background: #141c2e; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.06); border-left: 3px solid #c084fc;">
                    <div style="font-weight: 700; color: #c084fc;">6. Hybrid Detection</div>
                    <div style="color: #94a3b8; margin-top: 3px;">Rule invariants + residual thresholding + scikit-learn Isolation Forest ML.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    c_btn1, c_btn2 = st.columns([2, 1])
    with c_btn1:
        st.caption("💡 Tip: You can reopen this guided tour at any time from the top navigation bar '🧭 Platform Tour' button.")
    with c_btn2:
        if st.button("🚀 Explore Dashboard & Get Started", type="primary", use_container_width=True):
            st.session_state.onboarding_completed = True
            st.session_state.show_onboarding = False
            st.rerun()


# Trigger Onboarding Dialog on Load or when Requested
if st.session_state.show_onboarding:
    show_onboarding_tutorial()


# ==============================================================================
# TOP APP BAR (Unified White Header Card with Single Tour Button)
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

with st.container(border=True):
    col_tb1, col_tb2 = st.columns([5, 1], vertical_alignment="center")
    with col_tb1:
        if is_anomaly:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <span class="chip-red"><span class="dot-danger"></span> CYBER-PHYSICAL ANOMALY DETECTED</span>
                <span class="tech-pill">ACTIVE EXP: {active_exp}</span>
                <span style="font-size: 0.82rem; color: #f87171; font-weight: 600;">Residual: {latest_residual:.2f}% &gt; {config['detection']['residual_threshold']}%</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <span class="chip-green"><span class="dot-live"></span> PLANT OPERATING NORMALLY</span>
                <span class="tech-pill">SESSION: {active_exp}</span>
                <span style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">All safety interlocks clear • Zero residual violations</span>
            </div>
            """, unsafe_allow_html=True)

    with col_tb2:
        if st.button("🧭 Platform Tour", key="top_bar_tour", use_container_width=True):
            st.session_state.show_onboarding = True
            st.rerun()


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
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.76rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; text-align: center;">Cyber-Physical Tank Rig</div>', unsafe_allow_html=True)

            is_spoofed = abs(latest_level - latest_true) > 4.0
            sensor_color_cls = "liquid-wave liquid-sensor"
            if is_spoofed:
                sensor_color_cls = "liquid-wave liquid-spoofed"

            high_line = config['plc']['high_threshold']
            low_line = config['plc']['low_threshold']

            st.markdown(f"""
            <div class="scada-rig">
                <div class="scada-column">
                    <span style="font-size: 0.68rem; color: #38bdf8; font-weight: 800; letter-spacing: 0.05em;">GROUND TRUTH</span>
                    <div class="tank-glass">
                        <div class="interlock-line" style="bottom: {high_line}%;"></div>
                        <div class="interlock-line" style="bottom: {low_line}%;"></div>
                        <div class="liquid-wave liquid-true" style="height: {latest_true}%;"></div>
                    </div>
                    <span style="font-size: 1.15rem; font-weight: 800; color: #38bdf8; font-family: 'JetBrains Mono', monospace;">{latest_true:.1f}%</span>
                </div>
                <div class="scada-column">
                    <span style="font-size: 0.68rem; color: {'#f87171' if is_spoofed else '#4ade80'}; font-weight: 800; letter-spacing: 0.05em;">
                        REPORTED SENSOR {('(SPOOFED)' if is_spoofed else '')}
                    </span>
                    <div class="tank-glass">
                        <div class="interlock-line" style="bottom: {high_line}%;"></div>
                        <div class="interlock-line" style="bottom: {low_line}%;"></div>
                        <div class="{sensor_color_cls}" style="height: {latest_level}%;"></div>
                    </div>
                    <span style="font-size: 1.15rem; font-weight: 800; color: {'#f87171' if is_spoofed else '#4ade80'}; font-family: 'JetBrains Mono', monospace;">{latest_level:.1f}%</span>
                </div>
            </div>
            <div style="font-size: 0.70rem; color: #94a3b8; margin-top: 6px; text-align: center;">
                Dashed Markers: Cutoff ({high_line}%) & Refill Trigger ({low_line}%)
            </div>
            """, unsafe_allow_html=True)

    with col_scada2:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.76rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Real-Time Hydrodynamic Trajectory</div>', unsafe_allow_html=True)

            if not df_telemetry.empty:
                recent_df = df_telemetry.tail(120).copy()
                recent_df["Time_Sec"] = (recent_df["timestamp"] - recent_df["timestamp"].iloc[0]).round(1)
                fig_trend = px.line(
                    recent_df,
                    x="Time_Sec",
                    y=["sensor_level", "true_level"],
                    labels={"value": "Level (%)", "Time_Sec": "Elapsed (s)", "variable": "Stream"},
                    color_discrete_map={"sensor_level": "#34d399", "true_level": "#38bdf8"},
                )
                fig_trend.update_layout(
                    height=255,
                    margin=dict(l=8, r=8, t=10, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", range=[0, 105], tickfont=dict(color="#94a3b8")),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("System initializing... telemetry stream will populate automatically.")


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

        with st.container(border=True):
            st.subheader("1. True Physical Level vs Observed Sensor Signal")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["true_level"], mode="lines", name="Ground Truth Level", line=dict(color="#38bdf8", width=2.5)))
            fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["sensor_level"], mode="lines", name="Reported Sensor Signal", line=dict(color="#f87171", width=2, dash="dot")))
            fig1.add_hline(y=config["plc"]["high_threshold"], line_dash="dash", line_color="#f59e0b", annotation_text="High Hysteresis (80%)")
            fig1.add_hline(y=config["plc"]["low_threshold"], line_dash="dash", line_color="#f59e0b", annotation_text="Low Hysteresis (30%)")
            fig1.update_layout(
                height=265,
                margin=dict(l=8, r=8, t=20, b=8),
                xaxis_title="Elapsed Time (s)",
                yaxis_title="Water Level (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with st.container(border=True):
            st.subheader("2. Instantaneous Physical Residual: |Observed - Expected|")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["process_residual"], mode="lines", name="Process Residual r(t)", line=dict(color="#a78bfa", width=2.5)))
            fig2.add_hline(y=config["detection"]["residual_threshold"], line_dash="dash", line_color="#ef4444", annotation_text=f"Threshold ({config['detection']['residual_threshold']}%)")
            fig2.update_layout(
                height=235,
                margin=dict(l=8, r=8, t=20, b=8),
                xaxis_title="Elapsed Time (s)",
                yaxis_title="Residual Deviation (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
            )
            st.plotly_chart(fig2, use_container_width=True)


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
            with st.container(border=True):
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
                fig_rate.update_layout(
                    height=255,
                    margin=dict(l=8, r=8, t=20, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                )
                st.plotly_chart(fig_rate, use_container_width=True)

        with col_m2:
            with st.container(border=True):
                st.subheader("Function Code Breakdown")
                fc_counts = df_events["function_name"].value_counts().reset_index()
                fc_counts.columns = ["Function", "Count"]
                fig_pie = px.pie(fc_counts, values="Count", names="Function", color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"])
                fig_pie.update_layout(
                    height=255,
                    margin=dict(l=8, r=8, t=20, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with st.container(border=True):
            st.subheader("Live Modbus Frame Transaction Table")
            st.dataframe(
                df_events[["timestamp", "client_ip", "function_name", "register_address", "register_name", "value", "is_write", "request_rate"]].tail(50),
                use_container_width=True,
                hide_index=True,
            )


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

    with st.container(border=True):
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

        with st.container(border=True):
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
            fig_cat.update_layout(
                height=250,
                margin=dict(l=8, r=8, t=20, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        with st.container(border=True):
            st.subheader("Explainable Security Incident Feed")
            if not anom_only.empty:
                for _, alert in anom_only.tail(10).iterrows():
                    with st.expander(f"🚨 [{alert['severity']}] {alert['correlation_category']} — Rule: {alert['rule_id']}"):
                        st.write(f"**Explanation:** {alert['explanation']}")
                        st.write(f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert['timestamp']))}")
                        st.write(f"**Machine Learning Anomaly Score:** `{alert['anomaly_score']:.3f}`")
            else:
                st.success("All processes running normally. No anomalies detected.")


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
            with st.container(border=True):
                st.subheader("Physical Residual Histogram")
                fig_hist = px.histogram(
                    df_telemetry,
                    x="process_residual",
                    color="attack_type",
                    nbins=35,
                    labels={"process_residual": "Residual Error (%)", "count": "Sample Count"},
                    color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"],
                )
                fig_hist.update_layout(
                    height=270,
                    margin=dict(l=8, r=8, t=20, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        with col_a2:
            with st.container(border=True):
                st.subheader("Sensor vs Ground Truth Discrepancy")
                fig_scatter = px.scatter(
                    df_telemetry,
                    x="true_level",
                    y="sensor_level",
                    color="attack_type",
                    labels={"true_level": "True Level (%)", "sensor_level": "Reported (%)"},
                    color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"],
                )
                fig_scatter.update_layout(
                    height=270,
                    margin=dict(l=8, r=8, t=20, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
                )
                st.plotly_chart(fig_scatter, use_container_width=True)


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
        with st.container(border=True):
            st.subheader("Comparative Detection Benchmark Table")
            st.dataframe(
                df_eval[["model_name", "total_samples", "true_positives", "false_positives", "true_negatives", "false_negatives", "accuracy", "precision", "recall", "f1_score", "false_positive_rate"]].drop_duplicates(subset=["model_name"]),
                use_container_width=True,
                hide_index=True,
            )

        with st.container(border=True):
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
            fig_bar.update_layout(
                height=280,
                margin=dict(l=8, r=8, t=20, b=8),
                yaxis_range=[0, 1.05],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#cbd5e1")),
            )
            st.plotly_chart(fig_bar, use_container_width=True)


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
        with st.container(border=True):
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


# ==============================================================================
# AUTO-REFRESH EXECUTION LOOP (Kept Active & Configurable)
# ==============================================================================
if st.session_state.auto_refresh:
    time.sleep(float(st.session_state.refresh_speed))
    st.rerun()
