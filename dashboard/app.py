"""
TwinGuard-OT: Process-Aware Digital Twin for Cybersecurity Testing and Anomaly Detection in ICS
Interactive Streamlit Dashboard and Experimentation Platform.
"""

import sys
import time
from pathlib import Path

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

# Streamlit Page Config
st.set_page_config(
    page_title="TwinGuard-OT | ICS Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Clean, professional academic look - NO excessive neon/hacker tropes)
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 12px; border-radius: 8px; border: 1px solid #2d3139; }
    .status-badge-normal { background-color: #1b4724; color: #7ee787; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
    .status-badge-alert { background-color: #5c1d1d; color: #ffa39e; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
    .safety-notice { background-color: #162436; border-left: 4px solid #1f6feb; padding: 10px; border-radius: 4px; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    config = load_system_config()
    db_path = config["storage"]["db_path_resolved"]
    return DatabaseManager(db_path)


db = get_db()
config = load_system_config()

# Sidebar Navigation
st.sidebar.title("🛡️ TwinGuard-OT")
st.sidebar.caption("Process-Aware Anomaly Detection for ICS")
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "🌊 Overview",
        "🔄 Digital Twin",
        "📡 Modbus Monitor",
        "🎯 Attack Simulator",
        "🛡️ Detection & Alerts",
        "📊 Analytics & Residuals",
        "📈 Evaluation & Metrics",
        "💾 Dataset & Export",
    ],
)

# Live Polling toggle
auto_refresh = st.sidebar.checkbox("Auto Refresh (every 3s)", value=False)
if auto_refresh:
    time.sleep(3.0)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="safety-notice">
    <strong>Localhost Isolation:</strong><br>
    All packets and attacks operate strictly inside virtual local memory (127.0.0.1:5020).
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 1. OVERVIEW
# ==============================================================================
if nav_choice == "🌊 Overview":
    st.title("System Overview")
    st.write("Real-time physical process telemetry and operational status of the simulated industrial water tank.")

    df_telemetry = db.get_all_telemetry()
    df_exp = db.get_experiments()

    col1, col2, col3, col4 = st.columns(4)

    latest_level = 50.0
    latest_pump = 0
    latest_valve = 0
    latest_residual = 0.0
    latest_label = 0
    active_exp = "None"

    if not df_telemetry.empty:
        latest = df_telemetry.iloc[-1]
        latest_level = latest["sensor_level"]
        latest_pump = int(latest["pump_state"])
        latest_valve = int(latest["valve_state"])
        latest_residual = latest["process_residual"]
        latest_label = int(latest["label"])
        active_exp = latest["experiment_id"]

    with col1:
        st.metric("Water Level (Sensor)", f"{latest_level:.1f} %", delta=f"{latest_level - 70.0:.1f} % to Setpoint")
    with col2:
        pump_str = "🟢 RUNNING (ON)" if latest_pump == 1 else "⚪ STOPPED (OFF)"
        st.metric("Inflow Pump", pump_str)
    with col3:
        valve_str = "🟢 OPEN (DRAINING)" if latest_valve == 1 else "⚪ CLOSED"
        st.metric("Drain Valve", valve_str)
    with col4:
        st.metric("Physical Residual", f"{latest_residual:.1f} %", delta_color="inverse")

    st.markdown("### Operational Alert Status")
    if latest_label == 1 or latest_residual > config["detection"]["residual_threshold"]:
        st.markdown(
            f'<div class="status-badge-alert">⚠️ ANOMALOUS PROCESS BEHAVIOR DETECTED | Active Experiment: {active_exp} | Residual: {latest_residual:.1f}%</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="status-badge-normal">✅ NORMAL OPERATION | Active Experiment: {active_exp} | All Safety Interlocks Clear</div>',
            unsafe_allow_html=True,
        )

    # Tank Level Gauge / Graphic
    col_gauge, col_trend = st.columns([1, 2])
    with col_gauge:
        st.subheader("Physical Tank Level")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest_level,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Tank Level (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 30], 'color': "rgba(255, 165, 0, 0.2)"},
                    {'range': [30, 80], 'color': "rgba(46, 204, 113, 0.2)"},
                    {'range': [80, 95], 'color': "rgba(255, 165, 0, 0.2)"},
                    {'range': [95, 100], 'color': "rgba(231, 76, 60, 0.3)"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95.0,
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_trend:
        st.subheader("Recent Process Trajectory")
        if not df_telemetry.empty:
            recent_df = df_telemetry.tail(100).copy()
            recent_df["Time_Sec"] = (recent_df["timestamp"] - recent_df["timestamp"].iloc[0]).round(1)
            fig_trend = px.line(
                recent_df,
                x="Time_Sec",
                y=["sensor_level", "true_level"],
                labels={"value": "Level (%)", "Time_Sec": "Elapsed (s)", "variable": "Signal"},
                color_discrete_map={"sensor_level": "#58a6ff", "true_level": "#238636"},
            )
            fig_trend.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No live telemetry recorded yet. Start system or run an experiment to stream data.")


# ==============================================================================
# 2. DIGITAL TWIN
# ==============================================================================
elif nav_choice == "🔄 Digital Twin":
    st.title("Digital Twin Comparison")
    st.write("Cross-comparison between the simulated physical process (Ground Truth) and virtual sensor measurements.")

    df_telemetry = db.get_all_telemetry()
    if df_telemetry.empty:
        st.info("No telemetry data available. Please run an experiment or start the simulation system.")
    else:
        # Experiment filter
        exp_list = list(df_telemetry["experiment_id"].unique())
        selected_exp = st.selectbox("Select Experiment Run", exp_list, index=len(exp_list) - 1)
        exp_df = df_telemetry[df_telemetry["experiment_id"] == selected_exp].copy()
        exp_df["Elapsed_Sec"] = (exp_df["timestamp"] - exp_df["timestamp"].iloc[0]).round(1)

        # Plot 1: True vs Observed
        st.subheader("1. True Physical Level vs Observed Sensor Level")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["true_level"], mode="lines", name="Ground Truth Physical Level", line=dict(color="#2ea043", width=2)))
        fig1.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["sensor_level"], mode="lines", name="Observed Sensor Level", line=dict(color="#58a6ff", width=2, dash="dot")))
        fig1.add_hline(y=config["plc"]["high_threshold"], line_dash="dash", line_color="#d29922", annotation_text="High Hysteresis (80%)")
        fig1.add_hline(y=config["plc"]["low_threshold"], line_dash="dash", line_color="#d29922", annotation_text="Low Hysteresis (30%)")
        fig1.update_layout(height=350, xaxis_title="Elapsed Time (seconds)", yaxis_title="Water Level (%)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)

        # Plot 2: Physical Residual
        st.subheader("2. Physical Residual: |Observed - Expected|")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["process_residual"], mode="lines", name="Process Residual", line=dict(color="#f85149", width=2)))
        fig2.add_hline(y=config["detection"]["residual_threshold"], line_dash="dash", line_color="red", annotation_text=f"Anomaly Threshold ({config['detection']['residual_threshold']}%)")
        fig2.update_layout(height=260, xaxis_title="Elapsed Time (seconds)", yaxis_title="Residual (%)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

        # Plot 3: Actuator Activity
        st.subheader("3. Actuator States")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["pump_state"], mode="lines", name="Pump State (1=ON)", line=dict(color="#a371f7", width=2)))
        fig3.add_trace(go.Scatter(x=exp_df["Elapsed_Sec"], y=exp_df["valve_state"], mode="lines", name="Valve State (1=OPEN)", line=dict(color="#39c5bb", width=2, dash="dash")))
        fig3.update_layout(height=220, xaxis_title="Elapsed Time (seconds)", yaxis_title="State (Binary)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)


# ==============================================================================
# 3. MODBUS MONITOR
# ==============================================================================
elif nav_choice == "📡 Modbus Monitor":
    st.title("Modbus TCP Communication Monitor")
    st.write("Real-time inspection of industrial packets, register accesses, and request rates.")

    df_events = db.get_modbus_events()
    if df_events.empty:
        st.info("No Modbus events recorded yet. Connect a client or run traffic generation.")
    else:
        col_m1, col_m2 = st.columns([2, 1])

        with col_m1:
            st.subheader("Modbus Request Rate (req/s)")
            df_events["Time"] = pd.to_datetime(df_events["timestamp"], unit="s")
            fig_rate = px.line(
                df_events.tail(100),
                x="Time",
                y="request_rate",
                labels={"request_rate": "Requests / sec", "Time": "Timestamp"},
                color_discrete_sequence=["#58a6ff"],
            )
            fig_rate.add_hline(y=config["detection"]["request_rate_flood_threshold"], line_dash="dash", line_color="red", annotation_text="Flood Threshold (30 req/s)")
            fig_rate.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_rate, use_container_width=True)

        with col_m2:
            st.subheader("Function Code Distribution")
            fc_counts = df_events["function_name"].value_counts().reset_index()
            fc_counts.columns = ["Function", "Count"]
            fig_pie = px.pie(fc_counts, values="Count", names="Function", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Recent Modbus Transactions")
        st.dataframe(
            df_events[["timestamp", "client_ip", "function_name", "register_address", "register_name", "value", "is_write", "request_rate"]].tail(50),
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# 4. ATTACK SIMULATOR
# ==============================================================================
elif nav_choice == "🎯 Attack Simulator":
    st.title("ICS Cyberattack Simulator")
    st.write("Safely inject controlled cybersecurity attack scenarios into the local simulation environment.")

    st.markdown("""
    <div class="safety-notice">
        <strong>SAFETY ASSURANCE:</strong> This attack injector binds exclusively to the local loopback simulation
        port (<code>127.0.0.1:5020</code>). Network generation outside localhost is strictly prevented by software guardrails.
    </div><br>
    """, unsafe_allow_html=True)

    attack_type = st.selectbox(
        "Select Attack Scenario",
        [
            "Sensor Spoofing",
            "Unauthorized Register Write",
            "Replay Attack",
            "Command Flooding",
            "Abnormal Setpoint Manipulation",
        ],
    )

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        duration = st.slider("Attack Duration (seconds)", min_value=5, max_value=30, value=12)

    with col_cfg2:
        if attack_type == "Sensor Spoofing":
            spoof_val = st.slider("Falsified Tank Level (%)", min_value=0.0, max_value=100.0, value=20.0)
            st.caption("Description: Reports low level (e.g. 20%) while true level is high, causing pump to overfill.")
        elif attack_type == "Unauthorized Register Write":
            target_reg = st.selectbox("Target Control Register", ["PUMP_COMMAND (40003)", "VALVE_COMMAND (40004)"])
            st.caption("Description: Rogue external client directly alters actuator output coils.")
        elif attack_type == "Command Flooding":
            flood_rate = st.slider("Target Request Rate (req/s)", min_value=50, max_value=300, value=150)
            st.caption("Description: Floods local Modbus server with rapid queries.")
        elif attack_type == "Abnormal Setpoint Manipulation":
            setpoint_val = st.slider("Abnormal Target Setpoint (%)", min_value=5.0, max_value=99.0, value=98.0)
            st.caption("Description: Unsafe operational setpoint forcing PLC into boundary condition.")
        else:
            st.caption("Description: Replays recorded previous telemetry out of context.")

    st.markdown("---")
    if st.button("🚀 Execute Attack Scenario", type="primary"):
        st.info(f"Injecting {attack_type} against local virtual environment...")
        mb_port = config["modbus"]["port"]

        attack_key_map = {
            "Sensor Spoofing": "sensor_spoofing",
            "Unauthorized Register Write": "unauthorized_write",
            "Replay Attack": "replay",
            "Command Flooding": "command_flood",
            "Abnormal Setpoint Manipulation": "setpoint_manipulation",
        }
        internal_name = attack_key_map[attack_type]

        with st.spinner(f"Executing {attack_type} for {duration} seconds..."):
            from experiments.run_attack import run_attack_experiment
            csv_path = run_attack_experiment(
                attack_name=internal_name,
                warmup_sec=3.0,
                attack_duration_sec=float(duration),
                cooldown_sec=3.0,
            )
            st.success(f"Attack execution completed! Telemetry recorded and exported to: {csv_path}")


# ==============================================================================
# 5. DETECTION & ALERTS
# ==============================================================================
elif nav_choice == "🛡️ Detection & Alerts":
    st.title("Process-Aware Anomaly Detection")
    st.write("Explainable domain rules and Machine Learning anomaly correlation results.")

    df_detections = db.get_detections()
    if df_detections.empty:
        st.info("No detection alerts generated yet. Run an experiment or attack scenario.")
    else:
        anom_only = df_detections[df_detections["is_anomaly"] == 1]

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("Total Detections Logged", len(df_detections))
        with col_d2:
            st.metric("Confirmed Anomalies", len(anom_only))
        with col_d3:
            cyber_phys_count = len(df_detections[df_detections["correlation_category"] == "CYBER_PHYSICAL_ATTACK"])
            st.metric("Cyber-Physical Incidents", cyber_phys_count)

        st.subheader("Correlation Category Breakdown")
        cat_counts = df_detections["correlation_category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_cat = px.bar(cat_counts, x="Category", y="Count", color="Category", color_discrete_map={
            "NORMAL": "#2ea043",
            "CYBER_ONLY": "#58a6ff",
            "PROCESS_ONLY": "#d29922",
            "CYBER_PHYSICAL_ATTACK": "#f85149",
        })
        fig_cat.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_cat, use_container_width=True)

        st.subheader("Explainable Incident Log")
        if not anom_only.empty:
            for _, alert in anom_only.tail(10).iterrows():
                with st.expander(f"🚨 [{alert['severity']}] {alert['correlation_category']} - Rule {alert['rule_id']}"):
                    st.write(f"**Explanation:** {alert['explanation']}")
                    st.write(f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert['timestamp']))}")
                    st.write(f"**ML Outlier Score:** {alert['anomaly_score']:.3f}")
        else:
            st.success("No anomalies detected in the recorded period.")


# ==============================================================================
# 6. ANALYTICS & RESIDUALS
# ==============================================================================
elif nav_choice == "📊 Analytics & Residuals":
    st.title("Process Analytics & Residual Deep-Dive")
    st.write("Detailed physical residual distributions and telemetry feature correlations.")

    df_telemetry = db.get_all_telemetry()
    if df_telemetry.empty:
        st.info("No data available for analytics.")
    else:
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.subheader("Process Residual Distribution")
            fig_hist = px.histogram(
                df_telemetry,
                x="process_residual",
                color="attack_type",
                nbins=30,
                labels={"process_residual": "Residual (%)", "count": "Frequency"},
            )
            fig_hist.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_a2:
            st.subheader("True Level vs Observed Sensor Level")
            fig_scatter = px.scatter(
                df_telemetry,
                x="true_level",
                y="sensor_level",
                color="attack_type",
                labels={"true_level": "True Physical Level (%)", "sensor_level": "Reported Sensor (%)"},
            )
            fig_scatter.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_scatter, use_container_width=True)


# ==============================================================================
# 7. EVALUATION & METRICS
# ==============================================================================
elif nav_choice == "📈 Evaluation & Metrics":
    st.title("Empirical Model Evaluation & Benchmarks")
    st.write("Mathematical verification of detection performance against actual ground-truth labels. (No fabricated metrics).")

    if st.button("🔄 Recompute Evaluation Metrics Now"):
        with st.spinner("Calculating actual evaluation metrics from recorded database..."):
            evaluate_experiment()
            st.success("Evaluation complete! Reloading metrics...")

    df_eval = db.get_evaluations()
    if df_eval.empty:
        st.warning("No evaluation metrics calculated yet. Please run an experiment or click 'Recompute Evaluation Metrics Now'.")
    else:
        latest_eval = df_eval.head(3)  # Latest 3 models evaluated

        st.subheader("Comparative Benchmark Performance Table")
        st.dataframe(
            df_eval[["model_name", "total_samples", "true_positives", "false_positives", "true_negatives", "false_negatives", "accuracy", "precision", "recall", "f1_score", "false_positive_rate"]].drop_duplicates(subset=["model_name"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("F1-Score and Accuracy Comparison")
        latest_unique = df_eval.drop_duplicates(subset=["model_name"])
        fig_bar = px.bar(
            latest_unique,
            x="model_name",
            y=["accuracy", "precision", "recall", "f1_score"],
            barmode="group",
            labels={"value": "Score (0.0 to 1.0)", "model_name": "Detection Approach"},
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_bar.update_layout(height=350, yaxis_range=[0, 1.05], paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)


# ==============================================================================
# 8. DATASET & EXPORT
# ==============================================================================
elif nav_choice == "💾 Dataset & Export":
    st.title("Experiment Datasets & Report Export")
    st.write("Inspect recorded experimental data and download CSV datasets for inclusion in project reports.")

    df_telemetry = db.get_all_telemetry()
    if df_telemetry.empty:
        st.info("No experiment datasets found in database.")
    else:
        exp_list = ["ALL"] + list(df_telemetry["experiment_id"].unique())
        selected = st.selectbox("Filter by Experiment Run", exp_list)

        filtered_df = df_telemetry if selected == "ALL" else df_telemetry[df_telemetry["experiment_id"] == selected]

        st.write(f"Showing **{len(filtered_df)}** records:")
        st.dataframe(filtered_df.tail(200), use_container_width=True, hide_index=True)

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Dataset (CSV)",
            data=csv_data,
            file_name=f"twinguard_dataset_{selected}.csv",
            mime="text/csv",
        )
