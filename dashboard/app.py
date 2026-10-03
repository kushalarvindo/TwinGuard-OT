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
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
if "refresh_speed" not in st.session_state:
    st.session_state.refresh_speed = 3.0
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "nav_choice" not in st.session_state:
    st.session_state.nav_choice = "🌊 Process SCADA Overview"

# ==============================================================================
# ==============================================================================
# MATERIAL DESIGN 3 (MD3) ENTERPRISE SCADA SYSTEM STYLES
# Design System Foundations derived from bergside/awesome-design-skills (Material/Enterprise)
# Reference: https://github.com/bergside/awesome-design-skills & https://m3.material.io/develop/web
# ==============================================================================
st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<style>
    /* ==========================================================================
       MATERIAL DESIGN 3 DESIGN SYSTEM TOKENS (MD3 Dark Tonal Hierarchy)
       ========================================================================== */
    :root {
        /* MD3 Tonal Surfaces (Progressive Dark Elevation) */
        --md-sys-color-surface: #0a0e17;
        --md-sys-color-surface-dim: #070a10;
        --md-sys-color-surface-container-lowest: #0c101b;
        --md-sys-color-surface-container-low: #101624;
        --md-sys-color-surface-container: #141c2d;
        --md-sys-color-surface-container-high: #1a243a;
        --md-sys-color-surface-container-highest: #212d46;

        /* MD3 Outline & Borders */
        --md-sys-color-outline: rgba(255, 255, 255, 0.08);
        --md-sys-color-outline-variant: rgba(255, 255, 255, 0.04);
        --md-sys-color-outline-focus: rgba(56, 189, 248, 0.45);

        /* MD3 Primary & Semantic Palette */
        --md-sys-color-primary: #38bdf8;
        --md-sys-color-on-primary: #042338;
        --md-sys-color-primary-container: rgba(56, 189, 248, 0.12);
        --md-sys-color-on-primary-container: #7dd3fc;

        --md-sys-color-secondary: #818cf8;
        --md-sys-color-secondary-container: rgba(129, 140, 248, 0.12);

        --md-sys-color-success: #34d399;
        --md-sys-color-success-container: rgba(52, 211, 153, 0.12);

        --md-sys-color-warning: #fbbf24;
        --md-sys-color-warning-container: rgba(251, 191, 36, 0.12);

        --md-sys-color-error: #f87171;
        --md-sys-color-error-container: rgba(248, 113, 113, 0.14);

        --md-sys-color-on-surface: #f8fafc;
        --md-sys-color-on-surface-variant: #94a3b8;
        --md-sys-color-on-surface-muted: #64748b;

        /* MD3 Shape Scales */
        --md-sys-shape-corner-xs: 4px;
        --md-sys-shape-corner-s: 8px;
        --md-sys-shape-corner-m: 12px;
        --md-sys-shape-corner-l: 16px;
        --md-sys-shape-corner-full: 9999px;

        /* MD3 Motion & Easing */
        --md-sys-motion-easing-standard: cubic-bezier(0.2, 0.0, 0, 1.0);
        --md-sys-motion-duration-short: 150ms;
        --md-sys-motion-duration-medium: 250ms;
    }

    /* Global Typography & Telemetry Canvas */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* Enterprise Deep Matte Canvas with Subtle MD3 Ambient Radial Lighting */
    .stApp {
        background-color: var(--md-sys-color-surface) !important;
        background-image: radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.03) 0%, transparent 60%) !important;
        color: var(--md-sys-color-on-surface) !important;
    }

    /* Generous Layout Spacing & Breathing Room (Strict 8pt Grid Rhythm) */
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 2.8rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.8rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 1.20rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 1.25rem !important;
    }

    /* MD3 Expressive Surface Cards (Level 1 Elevation) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--md-sys-color-surface-container) !important;
        border: 1px solid var(--md-sys-color-outline) !important;
        border-radius: var(--md-sys-shape-corner-l) !important;
        padding: 20px 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
        margin-bottom: 14px !important;
        transition: border-color var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard),
                    box-shadow var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--md-sys-color-outline-focus) !important;
        box-shadow: 0 6px 28px rgba(0, 0, 0, 0.5) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: none !important;
    }

    /* Header Icon Box */
    .header-icon-box {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        width: 40px;
        height: 40px;
        border-radius: var(--md-sys-shape-corner-m);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 12px rgba(2, 132, 199, 0.35);
        flex-shrink: 0;
    }

    /* Navigation Drawer & Section Titles */
    section[data-testid="stSidebar"] {
        background: var(--md-sys-color-surface-container-lowest) !important;
        border-right: 1px solid var(--md-sys-color-outline) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.45) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-left: 0.95rem !important;
        padding-right: 0.95rem !important;
    }
    .nav-section-title {
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: var(--md-sys-color-on-surface-muted);
        padding: 14px 6px 4px 6px;
        border-top: 1px solid var(--md-sys-color-outline);
        margin-top: 6px;
    }

    /* Navigation Buttons (MD3 Expressive Pill Hierarchy) */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 14px !important;
        border-radius: var(--md-sys-shape-corner-s) !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        margin-bottom: 3px !important;
        letter-spacing: -0.01em !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        transition: all var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: var(--md-sys-color-on-surface-variant) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: var(--md-sys-color-surface-container-high) !important;
        border-color: var(--md-sys-color-outline) !important;
        color: var(--md-sys-color-on-surface) !important;
        transform: translateX(3px) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--md-sys-color-primary-container) !important;
        border: 1px solid var(--md-sys-color-outline-focus) !important;
        border-left: 4px solid var(--md-sys-color-primary) !important;
        color: var(--md-sys-color-primary) !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 12px rgba(2, 132, 199, 0.25) !important;
        transform: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(56, 189, 248, 0.20) !important;
        color: #7dd3fc !important;
    }

    /* Standard Action Buttons (MD3 Filled & Tonal) */
    .stButton > button {
        border-radius: var(--md-sys-shape-corner-s) !important;
        padding: 7px 16px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        border: 1px solid var(--md-sys-color-outline) !important;
        background: var(--md-sys-color-surface-container-low) !important;
        color: var(--md-sys-color-on-surface) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        transition: all var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard) !important;
    }
    .stButton > button:hover {
        background: var(--md-sys-color-surface-container-high) !important;
        border-color: rgba(255, 255, 255, 0.16) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--md-sys-color-primary) !important;
        outline-offset: 2px !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid var(--md-sys-color-primary) !important;
        box-shadow: 0 2px 12px rgba(2, 132, 199, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
        border-color: #7dd3fc !important;
        color: #ffffff !important;
    }

    /* Custom 4-Card Telemetry Instrumentation Grid (MD3 Surfaces) */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin: 12px 0 16px 0;
    }
    @media (max-width: 900px) {
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 550px) {
        .metrics-grid {
            grid-template-columns: 1fr;
        }
    }
    .telemetry-card {
        background: var(--md-sys-color-surface-container-low);
        border: 1px solid var(--md-sys-color-outline);
        border-radius: var(--md-sys-shape-corner-m);
        padding: 16px 18px 18px 18px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.30);
        transition: all var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard);
        min-height: 116px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .telemetry-card:hover {
        border-color: var(--md-sys-color-outline-focus);
        background: var(--md-sys-color-surface-container-high);
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.45);
        transform: translateY(-2px);
    }
    .telemetry-card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .telemetry-icon {
        width: 24px;
        height: 24px;
        border-radius: var(--md-sys-shape-corner-xs);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
    }
    .icon-cyan { background: var(--md-sys-color-primary-container); color: var(--md-sys-color-primary); }
    .icon-indigo { background: var(--md-sys-color-secondary-container); color: var(--md-sys-color-secondary); }
    .icon-emerald { background: var(--md-sys-color-success-container); color: var(--md-sys-color-success); }
    .icon-amber { background: var(--md-sys-color-warning-container); color: var(--md-sys-color-warning); }
    .icon-red { background: var(--md-sys-color-error-container); color: var(--md-sys-color-error); }
    .icon-muted { background: rgba(255, 255, 255, 0.05); color: var(--md-sys-color-on-surface-muted); }

    .telemetry-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--md-sys-color-on-surface-variant);
    }
    .telemetry-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--md-sys-color-on-surface);
        line-height: 1.15;
        margin-bottom: 6px;
        font-variant-numeric: tabular-nums;
    }
    .telemetry-unit {
        font-size: 0.92rem;
        color: var(--md-sys-color-on-surface-muted);
        font-weight: 500;
    }
    .text-cyan { color: var(--md-sys-color-primary) !important; }
    .text-emerald { color: var(--md-sys-color-success) !important; }
    .text-red { color: var(--md-sys-color-error) !important; }
    .text-white { color: var(--md-sys-color-on-surface) !important; }
    .text-muted { color: var(--md-sys-color-on-surface-muted) !important; }

    .telemetry-footer {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .telemetry-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: var(--md-sys-shape-corner-xs);
    }
    .pill-cyan { background: var(--md-sys-color-primary-container); color: var(--md-sys-color-primary); border: 1px solid rgba(56, 189, 248, 0.25); }
    .pill-emerald { background: var(--md-sys-color-success-container); color: var(--md-sys-color-success); border: 1px solid rgba(52, 211, 153, 0.25); }
    .pill-amber { background: var(--md-sys-color-warning-container); color: var(--md-sys-color-warning); border: 1px solid rgba(251, 191, 36, 0.25); }
    .pill-red { background: var(--md-sys-color-error-container); color: var(--md-sys-color-error); border: 1px solid rgba(248, 113, 113, 0.3); }
    .pill-muted { background: rgba(255, 255, 255, 0.04); color: var(--md-sys-color-on-surface-variant); border: 1px solid var(--md-sys-color-outline); }

    .telemetry-progress-track {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: rgba(255, 255, 255, 0.06);
    }
    .telemetry-progress-bar {
        height: 100%;
        transition: width var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-standard);
    }

    /* Panel Headers */
    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .panel-title {
        font-size: 0.76rem;
        font-weight: 800;
        color: var(--md-sys-color-on-surface-variant);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .panel-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 700;
        color: var(--md-sys-color-primary);
        background: var(--md-sys-color-primary-container);
        border: 1px solid rgba(56, 189, 248, 0.25);
        padding: 2px 7px;
        border-radius: var(--md-sys-shape-corner-xs);
        letter-spacing: 0.05em;
    }

    /* SCADA Dual-Tank Rig (Industrial Telemetry Glass & MD3 Surface) */
    .scada-rig-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
        padding: 16px 20px;
        background: var(--md-sys-color-surface-container-lowest);
        border-radius: var(--md-sys-shape-corner-m);
        border: 1px solid var(--md-sys-color-outline);
        position: relative;
    }
    .scale-column {
        position: relative;
        height: 190px;
        width: 38px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: var(--md-sys-color-on-surface-muted);
        text-align: right;
        padding-right: 6px;
        border-right: 1px dashed rgba(255, 255, 255, 0.14);
        margin-top: 22px;
        margin-bottom: 48px;
        flex-shrink: 0;
    }
    .scale-tick {
        position: absolute;
        right: 6px;
        transform: translateY(50%);
        line-height: 1;
        white-space: nowrap;
    }
    .scale-tick::after {
        content: "";
        position: absolute;
        right: -6px;
        top: 50%;
        width: 4px;
        height: 1px;
        background: rgba(255, 255, 255, 0.28);
    }
    .tank-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        flex: 1;
        max-width: 120px;
    }
    .tank-vessel {
        width: 100%;
        height: 190px;
        border: 2px solid rgba(255, 255, 255, 0.20);
        border-top: 1px solid rgba(255, 255, 255, 0.30);
        border-radius: 4px 4px var(--md-sys-shape-corner-m) var(--md-sys-shape-corner-m);
        position: relative;
        background: var(--md-sys-color-surface-dim);
        overflow: hidden;
        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8), 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    .tank-glass-sheen {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 20%, transparent 60%, rgba(255,255,255,0.06) 100%);
        pointer-events: none;
        z-index: 12;
    }
    .liquid-wave-surface {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        transition: height 0.4s var(--md-sys-motion-easing-standard);
        border-top: 2px solid rgba(255, 255, 255, 0.85);
    }
    .wave-glow-true {
        background: linear-gradient(180deg, #38bdf8 0%, #0284c7 60%, #034f75 100%);
        box-shadow: 0 -2px 16px rgba(56, 189, 248, 0.45);
    }
    .wave-glow-sensor {
        background: linear-gradient(180deg, #34d399 0%, #059669 60%, #064e3b 100%);
        box-shadow: 0 -2px 16px rgba(52, 211, 153, 0.45);
    }
    .wave-glow-spoofed {
        background: linear-gradient(180deg, #f87171 0%, #dc2626 60%, #7f1d1d 100%) !important;
        box-shadow: 0 -2px 20px rgba(239, 68, 68, 0.65) !important;
        animation: pulseSpoofed 1.8s infinite ease-in-out;
    }
    @keyframes pulseSpoofed {
        0%, 100% { opacity: 0.92; }
        50% { opacity: 1; }
    }
    .interlock-line {
        position: absolute;
        left: 0;
        right: 0;
        height: 1px;
        border-top: 1px dashed rgba(251, 191, 36, 0.75);
        z-index: 10;
        pointer-events: none;
    }
    .tank-readout-tile {
        background: var(--md-sys-color-surface-container-low);
        border: 1px solid var(--md-sys-color-outline);
        border-radius: var(--md-sys-shape-corner-s);
        padding: 4px 8px;
        text-align: center;
        width: 100%;
    }
    .tank-readout-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.15rem;
        font-weight: 800;
        line-height: 1;
    }
    .tank-readout-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.64rem;
        color: var(--md-sys-color-on-surface-muted);
        margin-top: 2px;
    }

    /* MD3 Status Chips & Indicator Dots */
    .chip-green {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: var(--md-sys-color-success-container);
        color: var(--md-sys-color-success);
        border: 1px solid rgba(52, 211, 153, 0.35);
        padding: 4px 12px;
        border-radius: var(--md-sys-shape-corner-full);
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
    }
    .chip-red {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: var(--md-sys-color-error-container);
        color: var(--md-sys-color-error);
        border: 1px solid rgba(248, 113, 113, 0.40);
        padding: 4px 12px;
        border-radius: var(--md-sys-shape-corner-full);
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        animation: pulseAlertDark 2s infinite ease-in-out;
    }
    @keyframes pulseAlertDark {
        0%, 100% { box-shadow: 0 0 0 rgba(248, 113, 113, 0); }
        50% { box-shadow: 0 0 16px rgba(248, 113, 113, 0.35); }
    }
    .dot-live {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--md-sys-color-success);
        box-shadow: 0 0 8px var(--md-sys-color-success);
        animation: pulseRing 1.8s infinite;
    }
    @keyframes pulseRing {
        0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }
        100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }
    .dot-danger {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--md-sys-color-error);
        box-shadow: 0 0 8px var(--md-sys-color-error);
        animation: pulseRingRed 1.8s infinite;
    }
    @keyframes pulseRingRed {
        0% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.8); }
        70% { box-shadow: 0 0 0 6px rgba(248, 113, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0); }
    }

    .tech-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        background: var(--md-sys-color-primary-container);
        border: 1px solid rgba(56, 189, 248, 0.22);
        padding: 3px 10px;
        border-radius: var(--md-sys-shape-corner-full);
        color: var(--md-sys-color-primary);
        font-weight: 600;
    }

    /* Sidebar Diagnostics Dock */
    .sidebar-diagnostics {
        background: var(--md-sys-color-surface-dim);
        padding: 10px 12px;
        border-radius: var(--md-sys-shape-corner-s);
        border: 1px solid var(--md-sys-color-outline);
        font-size: 0.70rem;
        color: var(--md-sys-color-on-surface-variant);
        line-height: 1.6;
        margin-top: 8px;
    }
    .diag-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2px;
    }
    .diag-row code {
        font-family: 'JetBrains Mono', monospace;
        color: var(--md-sys-color-on-surface);
        font-weight: 600;
    }

    /* MD3 Segmented Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--md-sys-color-surface-container-lowest) !important;
        padding: 4px;
        border-radius: var(--md-sys-shape-corner-s) !important;
        border: 1px solid var(--md-sys-color-outline) !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        padding: 6px 14px !important;
        border-radius: var(--md-sys-shape-corner-s) !important;
        color: var(--md-sys-color-on-surface-variant) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        transition: all var(--md-sys-motion-duration-short) ease !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--md-sys-color-surface-container-high) !important;
        color: var(--md-sys-color-primary) !important;
        font-weight: 700 !important;
        border: 1px solid var(--md-sys-color-outline-focus) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }

    /* MD3 Dialog Modal (Level 3 Elevation) */
    div[data-testid="stDialog"] div[role="dialog"] {
        background: var(--md-sys-color-surface-container-highest) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: var(--md-sys-shape-corner-l) !important;
        box-shadow: 0 25px 60px -10px rgba(0, 0, 0, 0.8) !important;
        color: var(--md-sys-color-on-surface) !important;
        max-width: 94vw !important;
        width: 1040px !important;
        padding: 24px 28px !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] h2 {
        color: var(--md-sys-color-on-surface) !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"] {
        color: var(--md-sys-color-on-surface-variant) !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"]:hover {
        color: var(--md-sys-color-on-surface) !important;
    }

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
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline);
        border-radius: var(--md-sys-shape-corner-m);
        padding: 14px 16px;
        transition: all var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard);
    }
    .onboarding-card:hover {
        border-color: var(--md-sys-color-primary);
        background: var(--md-sys-color-surface-container-high);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }
    .onboarding-card-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--md-sys-color-on-surface);
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
        border-radius: var(--md-sys-shape-corner-xs);
        background: var(--md-sys-color-primary-container);
        color: var(--md-sys-color-primary);
        border: 1px solid rgba(56, 189, 248, 0.25);
    }
    .onboarding-card-desc {
        font-size: 0.80rem;
        color: var(--md-sys-color-on-surface-variant);
        line-height: 1.45;
        margin: 0 0 8px 0;
    }
    .onboarding-card-tip {
        font-size: 0.74rem;
        color: #7dd3fc;
        background: var(--md-sys-color-primary-container);
        border-left: 3px solid var(--md-sys-color-primary);
        padding: 5px 8px;
        border-radius: var(--md-sys-shape-corner-xs);
        margin: 0;
    }

    .onboarding-step {
        display: flex;
        gap: 14px;
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline);
        border-radius: var(--md-sys-shape-corner-m);
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
df_telemetry = db.get_all_telemetry()


# ==============================================================================
# SIDEBAR NAVIGATION & SYSTEM TELEMETRY DOCK
# Subdivided Navigation Drawer with High-Performance Telemetry Hierarchy
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 11px; margin: 2px 0 14px 2px; padding-bottom: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
        <div class="header-icon-box">
            <span style="font-size: 1.25rem; line-height: 1;">🛡️</span>
        </div>
        <div>
            <div style="font-size: 1.05rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">TwinGuard-OT</div>
            <div style="font-size: 0.65rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">ICS DIGITAL TWIN v2.2</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # SECTION 01: SCADA OPERATIONS
    # -------------------------------------------------------------
    st.markdown('<div class="nav-section-title">SCADA OPERATIONS</div>', unsafe_allow_html=True)

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
    # SECTION 02: THREAT INTELLIGENCE
    # -------------------------------------------------------------
    st.markdown('<div class="nav-section-title">THREAT INTELLIGENCE</div>', unsafe_allow_html=True)

    is_attacks_active = (st.session_state.nav_choice == "🎯 Cyberattack Laboratory")
    if st.button("🎯  Cyberattack Laboratory", key="nav_attacks", use_container_width=True, type="primary" if is_attacks_active else "secondary"):
        st.session_state.nav_choice = "🎯 Cyberattack Laboratory"
        st.rerun()

    is_soc_active = (st.session_state.nav_choice == "🛡️ Multi-Tier Anomaly Detection")
    if st.button("🛡️  Multi-Tier Anomaly Detection", key="nav_soc", use_container_width=True, type="primary" if is_soc_active else "secondary"):
        st.session_state.nav_choice = "🛡️ Multi-Tier Anomaly Detection"
        st.rerun()

    # -------------------------------------------------------------
    # SECTION 03: ANALYTICS & BENCHMARKS
    # -------------------------------------------------------------
    st.markdown('<div class="nav-section-title">ANALYTICS & BENCHMARKS</div>', unsafe_allow_html=True)

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
    # SYSTEM CONTROLS & DIAGNOSTICS DOCK
    # -------------------------------------------------------------
    st.markdown('<div class="nav-section-title">PLATFORM CONTROL</div>', unsafe_allow_html=True)

    col_sb_a, col_sb_b = st.columns(2)
    with col_sb_a:
        if st.button("⚙️ Settings", key="sb_btn_settings", use_container_width=True):
            st.session_state.show_settings = True
            st.rerun()
    with col_sb_b:
        if st.button("🧭 Tour", key="sb_btn_tour", use_container_width=True):
            st.session_state.show_onboarding = True
            st.rerun()

    # System Status Diagnostics Dock
    st.markdown("""
    <div class="sidebar-diagnostics">
        <div class="diag-row">
            <span>MODBUS:</span>
            <code>127.0.0.1:5020</code>
        </div>
        <div class="diag-row">
            <span>PLC RATE:</span>
            <span style="color: #4ade80; font-weight: 700;">5.0 Hz (200ms)</span>
        </div>
        <div class="diag-row">
            <span>STORAGE:</span>
            <span style="color: #38bdf8; font-weight: 600;">SQLite (WAL Active)</span>
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
# SETTINGS & SAFETY CONTROLS MODAL (Centralized Platform Configuration)
# Includes all parameters, safety notices, and controls from earlier versions
# ==============================================================================
def on_settings_dismiss():
    st.session_state.show_settings = False


@st.dialog("⚙️ Platform Settings & Safety Controls", width="large", on_dismiss=on_settings_dismiss)
def show_settings_modal():
    st.markdown("""
    <div style="margin-bottom: 14px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.28); padding: 4px 12px; border-radius: 9999px; font-size: 0.72rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
            <span>🛡️ CONTROL & CONFIGURATION</span>
        </div>
        <h3 style="font-size: 1.25rem; font-weight: 800; margin: 0 0 4px 0; color: #f8fafc;">
            Platform Settings & Operational Parameters
        </h3>
        <p style="color: #94a3b8; font-size: 0.84rem; margin: 0; line-height: 1.45;">
            Configure real-time telemetry streaming, plant safety thresholds, physical process setpoints, and view the localhost safety enclosure.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_telemetry, tab_process, tab_detect, tab_safety = st.tabs([
        "⚡ Telemetry & Polling",
        "🎛️ Process Setpoints",
        "🛡️ Anomaly Thresholds",
        "🔒 Localhost Isolation",
    ])

    with tab_telemetry:
        st.markdown("##### ⚡ Real-Time Polling & Ingestion Cadence")
        st.caption("Control live dashboard synchronization with the industrial SQLite database and virtual PLC.")

        c_sync1, c_sync2 = st.columns([1.5, 1])
        with c_sync1:
            auto_sync = st.toggle("Auto-Refresh Telemetry Stream", value=st.session_state.auto_refresh, key="dlg_autorefresh")
            st.session_state.auto_refresh = auto_sync
        with c_sync2:
            current_cadence_label = "3s (Standard)"
            if st.session_state.refresh_speed == 1.0:
                current_cadence_label = "1s (Fast)"
            elif st.session_state.refresh_speed == 5.0:
                current_cadence_label = "5s (Relaxed)"

            speed_choice = st.select_slider(
                "Polling Cadence",
                options=["1s (Fast)", "3s (Standard)", "5s (Relaxed)"],
                value=current_cadence_label,
                key="dlg_cadence_rate",
            )
            speed_map = {"1s (Fast)": 1.0, "3s (Standard)": 3.0, "5s (Relaxed)": 5.0}
            st.session_state.refresh_speed = speed_map[speed_choice]

        c_f1, c_f2 = st.columns([1, 1])
        with c_f1:
            if st.button("⚡ Force Immediate Resync", key="dlg_force_sync", use_container_width=True):
                st.session_state.show_settings = False
                st.rerun()
        with c_f2:
            if st.button("🧹 Clear Streamlit Cache", key="dlg_clear_cache", use_container_width=True):
                st.cache_resource.clear()
                st.success("Cache invalidated.")

    with tab_process:
        st.markdown("##### 🎛️ Plant Physical Setpoints & Limits")
        st.caption("Configured hysteresis thresholds governing virtual PLC automated pump and valve sequencing.")

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Target Setpoint", f"{config.get('plc', {}).get('default_setpoint', 70.0):.1f}%", help="Holding register 40003")
        with col_p2:
            st.metric("High-Level Cutoff", f"{config.get('plc', {}).get('high_threshold', 80.0):.1f}%", help="Pump auto-trips above this level")
        with col_p3:
            st.metric("Low-Level Refill", f"{config.get('plc', {}).get('low_threshold', 30.0):.1f}%", help="Pump energizes below this level")

        st.markdown("""
        <div style="background: #090e18; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px; margin-top: 10px; font-size: 0.80rem; color: #94a3b8;">
            <div style="font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Tank Physical Model Constants (Hydrodynamic Equations):</div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                <div>• Max Height: <code>100.0 cm</code></div>
                <div>• Tank Area: <code>1.20 m²</code></div>
                <div>• Inflow Rate: <code>15.0 L/s</code></div>
                <div>• Outflow Coeff: <code>0.60</code></div>
                <div>• Sensor Noise σ: <code>0.15%</code></div>
                <div>• Gravity g: <code>9.81 m/s²</code></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab_detect:
        st.markdown("##### 🛡️ Anomaly Detection & Invariant Thresholds")
        st.caption("Deterministic residual bounds and Machine Learning contamination parameters.")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.metric("Residual Alarm Threshold", f"{config.get('detection', {}).get('residual_threshold', 5.0):.1f}%", help="R03: |h_sensor - h_shadow| > 5%")
            st.metric("Command Flood Limit", f"{config.get('detection', {}).get('flood_threshold', 30)} req/s", help="R05: Packet frequency > 30 req/s")
        with col_d2:
            st.metric("Critical Deviation Threshold", "10.0%", help="Emergency physical divergence trip")
            st.metric("Isolation Forest Contamination", "0.10", help="scikit-learn outlier fraction")

        st.markdown("---")
        st.markdown("**Empirical Benchmark Verification:**")
        if st.button("🔄 Recompute Evaluation Metrics Now", key="dlg_recompute_eval", type="primary", use_container_width=True):
            with st.spinner("Calculating actual evaluation metrics from recorded database..."):
                try:
                    evaluate_experiment()
                    st.success("Evaluation recalculation completed! Metrics refreshed.")
                    time.sleep(1.0)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error computing evaluation metrics: {e}")

    with tab_safety:
        st.markdown("""
        <div style="background: rgba(30, 58, 138, 0.25); border: 1px solid rgba(56, 189, 248, 0.35); border-left: 4px solid #38bdf8; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;">
            <div style="font-size: 0.90rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                <span>🛡️ Localhost Isolation Safety Notice (Shivam Requirement)</span>
            </div>
            <div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.5;">
                All packets, Modbus TCP transactions, red team attacks, and telemetry operate strictly inside virtual local memory (<code>127.0.0.1:5020</code>). 
                External industrial systems, physical PLCs, SCADA networks, and remote hosts are completely isolated and will never be targeted.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("""
            <div class="sidebar-diagnostics" style="margin-top: 0;">
                <div class="diag-row"><span>MODBUS HOST:</span> <code>127.0.0.1</code></div>
                <div class="diag-row"><span>MODBUS PORT:</span> <code>5020</code></div>
                <div class="diag-row"><span>SLAVE / UNIT ID:</span> <code>1</code></div>
                <div class="diag-row"><span>PLC SCAN RATE:</span> <span style="color: #4ade80; font-weight: 700;">5.0 Hz (200ms)</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="sidebar-diagnostics" style="margin-top: 0;">
                <div class="diag-row"><span>DATABASE:</span> <span style="color: #38bdf8; font-weight: 600;">SQLite (WAL Mode)</span></div>
                <div class="diag-row"><span>TELEMETRY ROWS:</span> <code>{len(df_telemetry):,}</code></div>
                <div class="diag-row"><span>ENVIRONMENT:</span> <span style="color: #a78bfa; font-weight: 600;">Local Sandbox</span></div>
                <div class="diag-row"><span>SAFETY STATUS:</span> <span style="color: #4ade80; font-weight: 700;">ENCLOSED</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Done & Close Settings", type="primary", use_container_width=True, key="dlg_close_settings"):
        st.session_state.show_settings = False
        st.rerun()


# Trigger Settings Dialog when Requested
if st.session_state.get("show_settings", False):
    show_settings_modal()


# ==============================================================================
# TOP APP BAR (Uncluttered, Sleek MD3 Industrial Header with Settings & Tour)
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

view_headers = {
    "🌊 Process SCADA Overview": (
        "Process Overview & HMI",
        "Live water tank level, pump/valve telemetry, and closed-loop hysteresis control.",
    ),
    "🔄 Digital Twin Shadow Model": (
        "Digital Twin Shadow Model",
        "Hydrodynamic mass-balance model and continuous residual r(t) = |h_sensor - h_shadow|.",
    ),
    "📡 Modbus Protocol Inspector": (
        "Modbus TCP Inspector",
        "Transaction logging, register memory map, and packet arrival rate tracking (port 5020).",
    ),
    "🎯 Cyberattack Laboratory": (
        "Cyberattack Laboratory",
        "Isolated localhost threat injection and red team attack scenarios against virtual PLC.",
    ),
    "🛡️ Multi-Tier Anomaly Detection": (
        "Multi-Tier Anomaly Detection",
        "Domain invariant rules, hydrodynamic shadow model, and Isolation Forest ML.",
    ),
    "📊 Statistical Process Analytics": (
        "Process Dynamics & Analytics",
        "Sensor drift, residual error distributions, and physical actuator correlation.",
    ),
    "🏆 Empirical Evaluation Metrics": (
        "Empirical Model Benchmarks",
        "Precision, Recall, F1-Score, and FPR verification against ground-truth datasets.",
    ),
    "💾 Datasets & Research Artifacts": (
        "Datasets & Export",
        "Recorded telemetry logs, experiment filtering, and CSV export for research reports.",
    ),
}

current_title, current_desc = view_headers.get(nav_choice, ("TwinGuard-OT SCADA", "Industrial Cyber-Physical Platform"))

with st.container(border=True):
    col_tb_title, col_tb_status, col_tb_tour, col_tb_settings = st.columns([3.6, 2.2, 0.8, 0.9], vertical_alignment="center")
    with col_tb_title:
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; gap: 2px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.68rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">TWINGUARD-OT</span>
                <span style="color: rgba(255,255,255,0.2); font-size: 0.72rem;">/</span>
                <span style="font-size: 1.08rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.01em;">{current_title}</span>
            </div>
            <div style="font-size: 0.76rem; color: #94a3b8; line-height: 1.3;">{current_desc}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_tb_status:
        if is_anomaly:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap;">
                <span class="chip-red"><span class="dot-danger"></span> ALERT</span>
                <span class="tech-pill">{active_exp}</span>
                <span style="font-size: 0.76rem; color: #f87171; font-weight: 600; font-family: 'JetBrains Mono', monospace;">|r| = {latest_residual:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap;">
                <span class="chip-green"><span class="dot-live"></span> NORMAL</span>
                <span class="tech-pill">{active_exp}</span>
                <span style="font-size: 0.76rem; color: #4ade80; font-weight: 600; font-family: 'JetBrains Mono', monospace;">|r| = {latest_residual:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
    with col_tb_tour:
        if st.button("🧭 Tour", key="top_bar_tour", use_container_width=True):
            st.session_state.show_onboarding = True
            st.rerun()
    with col_tb_settings:
        if st.button("⚙️ Settings", key="top_bar_settings", use_container_width=True):
            st.session_state.show_settings = True
            st.rerun()


# ==============================================================================
# 1. PROCESS SCADA OVERVIEW
# ==============================================================================
if nav_choice == "🌊 Process SCADA Overview":
    # 4-Card Telemetry Instrumentation Grid
    sp_delta = latest_level - config['plc']['default_setpoint']
    delta_str = f"{sp_delta:+.1f}% to Setpoint"
    sp_pill_cls = "pill-cyan" if abs(sp_delta) <= 15.0 else ("pill-amber" if abs(sp_delta) <= 25.0 else "pill-red")

    pump_status_text = "ENERGIZED" if latest_pump == 1 else "IDLE"
    pump_val_cls = "text-emerald" if latest_pump == 1 else "text-muted"
    pump_icon_cls = "icon-emerald" if latest_pump == 1 else "icon-muted"
    pump_pill_cls = "pill-emerald" if latest_pump == 1 else "pill-muted"
    pump_sub = "PLC AUTO-HYSTERESIS" if latest_pump == 1 else "CUTOFF ACTIVE (>80%)"

    valve_status_text = "OPEN" if latest_valve == 1 else "CLOSED"
    valve_val_cls = "text-emerald" if latest_valve == 1 else "text-muted"
    valve_icon_cls = "icon-emerald" if latest_valve == 1 else "icon-muted"
    valve_pill_cls = "pill-emerald" if latest_valve == 1 else "pill-muted"
    valve_sub = "GRAVITY DISCHARGE" if latest_valve == 1 else "DRAIN SEALED"

    res_threshold = config['detection']['residual_threshold']
    res_violated = latest_residual > res_threshold
    res_val_cls = "text-red" if res_violated else ("text-cyan" if latest_residual < 2.0 else "text-white")
    res_icon_cls = "icon-red" if res_violated else "icon-indigo"
    res_pill_cls = "pill-red" if res_violated else "pill-emerald"
    res_sub = f"THRESHOLD < {res_threshold:.1f}%" if not res_violated else f"VIOLATION > {res_threshold:.1f}%"

    level_pct = min(100.0, max(0.0, latest_level))
    res_pct = min(100.0, (latest_residual / res_threshold) * 50.0)

    st.markdown(f"""
    <div class="metrics-grid">
        <div class="telemetry-card">
            <div class="telemetry-card-header">
                <div class="telemetry-icon icon-cyan">
                    <span class="material-symbols-outlined" style="font-size: 16px;">water_drop</span>
                </div>
                <span class="telemetry-label">REPORTED TANK LEVEL</span>
            </div>
            <div class="telemetry-value text-cyan">{latest_level:.1f} <span class="telemetry-unit">%</span></div>
            <div class="telemetry-footer">
                <span class="telemetry-pill {sp_pill_cls}">{delta_str}</span>
            </div>
            <div class="telemetry-progress-track">
                <div class="telemetry-progress-bar" style="width: {level_pct}%; background: linear-gradient(90deg, #0284c7, #38bdf8);"></div>
            </div>
        </div>
        <div class="telemetry-card">
            <div class="telemetry-card-header">
                <div class="telemetry-icon {pump_icon_cls}">
                    <span class="material-symbols-outlined" style="font-size: 16px;">electric_bolt</span>
                </div>
                <span class="telemetry-label">INFLOW PUMP (COIL 40003)</span>
            </div>
            <div class="telemetry-value {pump_val_cls}">{pump_status_text}</div>
            <div class="telemetry-footer">
                <span class="telemetry-pill {pump_pill_cls}">{pump_sub}</span>
            </div>
            <div class="telemetry-progress-track">
                <div class="telemetry-progress-bar" style="width: {'100%' if latest_pump == 1 else '0%'}; background: #34d399;"></div>
            </div>
        </div>
        <div class="telemetry-card">
            <div class="telemetry-card-header">
                <div class="telemetry-icon {valve_icon_cls}">
                    <span class="material-symbols-outlined" style="font-size: 16px;">tune</span>
                </div>
                <span class="telemetry-label">DISCHARGE VALVE (COIL 40004)</span>
            </div>
            <div class="telemetry-value {valve_val_cls}">{valve_status_text}</div>
            <div class="telemetry-footer">
                <span class="telemetry-pill {valve_pill_cls}">{valve_sub}</span>
            </div>
            <div class="telemetry-progress-track">
                <div class="telemetry-progress-bar" style="width: {'100%' if latest_valve == 1 else '0%'}; background: #34d399;"></div>
            </div>
        </div>
        <div class="telemetry-card">
            <div class="telemetry-card-header">
                <div class="telemetry-icon {res_icon_cls}">
                    <span class="material-symbols-outlined" style="font-size: 16px;">verified_user</span>
                </div>
                <span class="telemetry-label">PHYSICAL RESIDUAL |r(t)|</span>
            </div>
            <div class="telemetry-value {res_val_cls}">{latest_residual:.2f} <span class="telemetry-unit">%</span></div>
            <div class="telemetry-footer">
                <span class="telemetry-pill {res_pill_cls}">{res_sub}</span>
            </div>
            <div class="telemetry-progress-track">
                <div class="telemetry-progress-bar" style="width: {res_pct}%; background: {'#ef4444' if res_violated else '#818cf8'};"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_scada1, col_scada2 = st.columns([1, 2])

    with col_scada1:
        with st.container(border=True):
            st.markdown("""
            <div class="panel-header">
                <span class="panel-title">Cyber-Physical Tank Rig</span>
                <span class="panel-badge">TORRICELLI TWIN</span>
            </div>
            """, unsafe_allow_html=True)

            is_spoofed = abs(latest_level - latest_true) > 4.0
            sensor_wave_cls = "liquid-wave-surface wave-glow-spoofed" if is_spoofed else "liquid-wave-surface wave-glow-sensor"
            high_line = config['plc']['high_threshold']
            low_line = config['plc']['low_threshold']

            st.markdown(f"""
            <div class="scada-rig-container">
                <div class="scale-column">
                    <div class="scale-tick" style="bottom: 100%;">100%</div>
                    <div class="scale-tick" style="bottom: 80%; color: #f59e0b; font-weight: 700;">80%</div>
                    <div class="scale-tick" style="bottom: 60%;">60%</div>
                    <div class="scale-tick" style="bottom: 40%;">40%</div>
                    <div class="scale-tick" style="bottom: 30%; color: #f59e0b; font-weight: 700;">30%</div>
                    <div class="scale-tick" style="bottom: 0%;">0%</div>
                </div>
                <div class="tank-column">
                    <span style="font-size: 0.68rem; color: #38bdf8; font-weight: 800; letter-spacing: 0.05em;">GROUND TRUTH</span>
                    <div class="tank-vessel">
                        <div class="tank-glass-sheen"></div>
                        <div class="interlock-line" style="bottom: {high_line}%;"></div>
                        <div class="interlock-line" style="bottom: {low_line}%;"></div>
                        <div class="liquid-wave-surface wave-glow-true" style="height: {latest_true}%;"></div>
                    </div>
                    <div class="tank-readout-tile">
                        <div class="tank-readout-val" style="color: #38bdf8;">{latest_true:.1f}%</div>
                        <div class="tank-readout-sub">PHYSICS REFERENCE</div>
                    </div>
                </div>
                <div class="tank-column">
                    <span style="font-size: 0.68rem; color: {'#f87171' if is_spoofed else '#34d399'}; font-weight: 800; letter-spacing: 0.05em;">
                        {('⚠️ SPOOFED' if is_spoofed else 'REPORTED SENSOR')}
                    </span>
                    <div class="tank-vessel">
                        <div class="tank-glass-sheen"></div>
                        <div class="interlock-line" style="bottom: {high_line}%;"></div>
                        <div class="interlock-line" style="bottom: {low_line}%;"></div>
                        <div class="{sensor_wave_cls}" style="height: {latest_level}%;"></div>
                    </div>
                    <div class="tank-readout-tile">
                        <div class="tank-readout-val" style="color: {'#f87171' if is_spoofed else '#34d399'};">{latest_level:.1f}%</div>
                        <div class="tank-readout-sub">{'SPOOFED SIGNAL' if is_spoofed else 'MODBUS TELEMETRY'}</div>
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.68rem; color: #64748b; margin-top: 8px; font-family: 'JetBrains Mono', monospace; padding: 4px 8px; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                <span>CUTOFF: <strong style="color: #f59e0b;">{high_line:.0f}%</strong></span>
                <span>REFILL: <strong style="color: #f59e0b;">{low_line:.0f}%</strong></span>
                <span style="color: {'#f87171' if is_spoofed else '#34d399'}; font-weight: 700; background: {'rgba(239,68,68,0.14)' if is_spoofed else 'rgba(52,211,153,0.14)'}; padding: 2px 7px; border-radius: 4px; border: 1px solid {'rgba(239,68,68,0.25)' if is_spoofed else 'rgba(52,211,153,0.25)'};">
                    {'⚠️ SENSOR SPOOFED' if is_spoofed else '✓ SYNCHRONIZED'} (Δ {abs(latest_level - latest_true):.2f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)

    with col_scada2:
        with st.container(border=True):
            st.markdown("""
            <div class="panel-header">
                <span class="panel-title">Real-Time Hydrodynamic Trajectory</span>
                <span class="panel-badge">120-SAMPLE WINDOW</span>
            </div>
            """, unsafe_allow_html=True)

            if not df_telemetry.empty:
                recent_df = df_telemetry.tail(120).copy()
                recent_df["Time_Sec"] = (recent_df["timestamp"] - recent_df["timestamp"].iloc[0]).round(1)

                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=recent_df["Time_Sec"],
                    y=recent_df["true_level"],
                    mode="lines",
                    name="Ground Truth Level",
                    line=dict(color="#38bdf8", width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(56, 189, 248, 0.07)"
                ))
                fig_trend.add_trace(go.Scatter(
                    x=recent_df["Time_Sec"],
                    y=recent_df["sensor_level"],
                    mode="lines",
                    name="Reported Sensor Signal",
                    line=dict(color="#f87171" if is_spoofed else "#34d399", width=2, dash="dot" if is_spoofed else "solid"),
                ))
                fig_trend.add_hline(
                    y=high_line,
                    line_dash="dash",
                    line_color="#f59e0b",
                    line_width=1.5,
                    annotation_text=f"Cutoff ({high_line:.0f}%)",
                    annotation_position="top right",
                    annotation_font=dict(color="#f59e0b", size=9, family="JetBrains Mono"),
                    annotation_bgcolor="rgba(15, 23, 42, 0.85)",
                )
                fig_trend.add_hline(
                    y=low_line,
                    line_dash="dash",
                    line_color="#f59e0b",
                    line_width=1.5,
                    annotation_text=f"Refill ({low_line:.0f}%)",
                    annotation_position="bottom right",
                    annotation_font=dict(color="#f59e0b", size=9, family="JetBrains Mono"),
                    annotation_bgcolor="rgba(15, 23, 42, 0.85)",
                )

                fig_trend.update_layout(
                    height=265,
                    margin=dict(l=8, r=12, t=10, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1", family="Plus Jakarta Sans"),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.06)",
                        tickfont=dict(color="#94a3b8", family="JetBrains Mono", size=10),
                        title=dict(text="Elapsed Time (s)", font=dict(color="#64748b", size=11)),
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.06)",
                        range=[0, 105],
                        tickfont=dict(color="#94a3b8", family="JetBrains Mono", size=10),
                        title=dict(text="Water Level (%)", font=dict(color="#64748b", size=11)),
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(color="#cbd5e1", size=11),
                    ),
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("System initializing... telemetry stream will populate automatically.")


# ==============================================================================
# 2. DIGITAL TWIN RESIDUAL ANALYSIS
# ==============================================================================
elif nav_choice == "🔄 Digital Twin Shadow Model":
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
if st.session_state.auto_refresh and not st.session_state.get("show_onboarding", False) and not st.session_state.get("show_settings", False):
    time.sleep(float(st.session_state.refresh_speed))
    st.rerun()
