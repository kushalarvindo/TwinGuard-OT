"""
One-Command System Launcher for TwinGuard-OT.
Starts the Water Tank Digital Twin, Virtual PLC, Modbus TCP Server, Telemetry Collector,
and optionally the interactive Streamlit Dashboard with graceful shutdown.
"""

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from twinguard.utils.config import load_system_config
from twinguard.utils.logging import setup_logger
from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.database.db import DatabaseManager
from twinguard.monitoring.collector import DataCollector


def start_system(launch_dashboard: bool = True):
    config = load_system_config()
    logger = setup_logger("twinguard.system")

    logger.info("==========================================================")
    logger.info("  TWINGUARD-OT: STARTING INDUSTRIAL CONTROL SYSTEM TWIN")
    logger.info("==========================================================")

    # Storage & DB
    db_path = config["storage"]["db_path_resolved"]
    db = DatabaseManager(db_path)
    exp_id = f"EXP-LIVE-{int(time.time()) % 10000:04d}"
    db.create_experiment(exp_id, name="Live Digital Twin Run", attack_type="normal", notes="Interactive system session")

    # 1. Physical Simulation
    sim_cfg = config.get("physical_process", {})
    tank = WaterTank(
        capacity_liters=sim_cfg.get("capacity_liters", 1000.0),
        initial_level=sim_cfg.get("initial_level", 45.0),
        pump_inflow_rate=sim_cfg.get("pump_inflow_rate", 3.0),
        gravity_outflow_rate=sim_cfg.get("gravity_outflow_rate", 1.2),
        leak_outflow_rate=sim_cfg.get("leak_outflow_rate", 0.1),
        sensor_noise_std=sim_cfg.get("sensor_noise_std", 0.25),
    )
    logger.info(f"[1/4] Water Tank Digital Twin initialized (Initial level: {tank.current_level:.1f}%)")

    # 2. Virtual PLC
    plc_cfg = config.get("plc", {})
    plc = VirtualPLC(
        tank=tank,
        cycle_interval_sec=plc_cfg.get("cycle_interval_sec", 0.2),
        default_setpoint=plc_cfg.get("default_setpoint", 70.0),
        low_threshold=plc_cfg.get("low_threshold", 30.0),
        high_threshold=plc_cfg.get("high_threshold", 80.0),
        emergency_low=plc_cfg.get("emergency_low_threshold", 10.0),
        emergency_high=plc_cfg.get("emergency_high_threshold", 95.0),
    )
    logger.info(f"[2/4] Virtual PLC initialized (Hysteresis: [{plc.logic.low_threshold}%, {plc.logic.high_threshold}%])")

    # 3. Modbus TCP Server
    mb_cfg = config.get("modbus", {})
    server = TwinGuardModbusServer(
        host=mb_cfg.get("host", "127.0.0.1"),
        port=mb_cfg.get("port", 5020),
        unit_id=mb_cfg.get("unit_id", 1),
    )
    logger.info(f"[3/4] Modbus TCP Server listening on {server.host}:{server.port}")

    # 4. Telemetry Collector
    collector = DataCollector(
        tank=tank,
        plc=plc,
        modbus_server=server,
        db=db,
        sample_interval_sec=config.get("simulation", {}).get("time_step_sec", 0.1),
    )
    collector.set_experiment_context(exp_id, is_attack_active=False, attack_type="normal")
    logger.info("[4/4] Telemetry Collector and Database logger attached.")

    # Start all background subsystems
    server.start()
    plc.start()
    collector.start()

    dashboard_process = None
    if launch_dashboard:
        logger.info("Launching Streamlit Dashboard...")
        dashboard_app = str(root_dir / "dashboard" / "app.py")
        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_app, "--server.headless", "true"]
        dashboard_process = subprocess.Popen(cmd)
        logger.info(f"Streamlit Dashboard running at http://localhost:8501 (PID {dashboard_process.pid})")

    logger.info("\n>>> SYSTEM OPERATIONAL! Press Ctrl+C to stop cleanly. <<<\n")

    def shutdown_handler(signum, frame):
        logger.info("\nInitiating graceful shutdown...")
        collector.stop()
        plc.stop()
        server.stop()
        db.finish_experiment(exp_id, status="COMPLETED")
        if dashboard_process:
            dashboard_process.terminate()
        logger.info("TwinGuard-OT stopped cleanly. Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        while True:
            # Advance physical simulation
            tank.step(dt=0.1)
            time.sleep(0.08)
    except KeyboardInterrupt:
        shutdown_handler(None, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwinGuard-OT Master System Launcher")
    parser.add_argument("--dashboard", action="store_true", default=False, help="Launch Streamlit dashboard automatically")
    parser.add_argument("--no-dashboard", dest="dashboard", action="store_false", help="Run simulation headlessly")
    args = parser.parse_args()

    start_system(launch_dashboard=args.dashboard)
