"""
Experiment Script: Normal Operational Baseline.
Runs the simulated industrial water-tank process under standard PLC hysteresis control,
logs clean baseline data, and trains the Isolation Forest ML detector.
"""

import argparse
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

import pandas as pd

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.utils.logging import setup_logger
from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.database.db import DatabaseManager
from twinguard.monitoring.collector import DataCollector
from twinguard.features.extractor import FeatureExtractor
from twinguard.detection.isolation_forest import IsolationForestDetector


def run_normal_baseline(duration_sec: float = 40.0, exp_id: str = "EXP-NORMAL-001") -> str:
    """
    Executes normal baseline simulation, records data, and trains Isolation Forest.
    """
    config = load_system_config()
    logger = setup_logger("twinguard.normal_op")
    root = get_project_root()

    db_path = config["storage"]["db_path_resolved"]
    db = DatabaseManager(db_path)
    db.create_experiment(exp_id, name="Normal Operation Baseline", attack_type="normal", notes="Clean operational baseline")

    sim_cfg = config.get("physical_process", {})
    plc_cfg = config.get("plc", {})
    mb_cfg = config.get("modbus", {})

    tank = WaterTank(
        capacity_liters=sim_cfg.get("capacity_liters", 1000.0),
        initial_level=sim_cfg.get("initial_level", 45.0),
        pump_inflow_rate=sim_cfg.get("pump_inflow_rate", 3.0),
        gravity_outflow_rate=sim_cfg.get("gravity_outflow_rate", 1.2),
        leak_outflow_rate=sim_cfg.get("leak_outflow_rate", 0.1),
        sensor_noise_std=sim_cfg.get("sensor_noise_std", 0.25),
    )

    plc = VirtualPLC(
        tank=tank,
        cycle_interval_sec=plc_cfg.get("cycle_interval_sec", 0.2),
        default_setpoint=plc_cfg.get("default_setpoint", 70.0),
        low_threshold=plc_cfg.get("low_threshold", 30.0),
        high_threshold=plc_cfg.get("high_threshold", 80.0),
        emergency_low=plc_cfg.get("emergency_low_threshold", 10.0),
        emergency_high=plc_cfg.get("emergency_high_threshold", 95.0),
    )

    server = TwinGuardModbusServer(
        host=mb_cfg.get("host", "127.0.0.1"),
        port=mb_cfg.get("port", 5020),
        unit_id=mb_cfg.get("unit_id", 1),
    )

    collector = DataCollector(
        tank=tank,
        plc=plc,
        modbus_server=server,
        db=db,
        sample_interval_sec=config.get("simulation", {}).get("time_step_sec", 0.1),
    )
    collector.set_experiment_context(experiment_id=exp_id, is_attack_active=False, attack_type="normal")

    logger.info(f"Starting Normal Baseline Experiment: {exp_id} for {duration_sec}s...")
    server.start()
    plc.start()
    collector.start()

    start_time = time.time()
    try:
        while time.time() - start_time < duration_sec:
            tank.step(dt=0.1)
            time.sleep(0.08)
    finally:
        collector.stop()
        plc.stop()
        server.stop()
        db.finish_experiment(exp_id, status="COMPLETED")

    logger.info(f"Baseline run completed. Samples collected: {collector.total_samples_collected}")

    # Fetch recorded telemetry
    df_raw = db.get_telemetry_by_experiment(exp_id)
    if df_raw.empty:
        logger.error("No telemetry was recorded in database.")
        return ""

    # Feature extraction
    extractor = FeatureExtractor(high_threshold=plc_cfg.get("high_threshold", 80.0))
    df_features = extractor.extract_from_dataframe(df_raw)

    # Save processed baseline CSV
    processed_dir = root / config["storage"].get("processed_dir", "data/processed")
    baseline_csv_path = processed_dir / "normal_baseline.csv"
    df_features.to_csv(baseline_csv_path, index=False)
    logger.info(f"Saved processed normal baseline features to: {baseline_csv_path}")

    # Train Isolation Forest
    logger.info("Training Isolation Forest ML Anomaly Detector on clean baseline...")
    detector = IsolationForestDetector(
        n_estimators=config.get("detection", {}).get("isolation_forest", {}).get("n_estimators", 100),
        contamination=config.get("detection", {}).get("isolation_forest", {}).get("contamination", 0.03),
    )
    meta = detector.fit(df_features)
    models_dir = root / config["storage"].get("models_dir", "data/models")
    model_save_path = models_dir / "isolation_forest.joblib"
    detector.save(model_save_path)
    logger.info(f"Model trained and saved to: {model_save_path} (Trained on {meta['n_samples']} samples)")

    return str(baseline_csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwinGuard-OT Normal Baseline Collector")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration in seconds (default: 30)")
    parser.add_argument("--exp-id", type=str, default="EXP-NORMAL-001", help="Experiment ID")
    args = parser.parse_args()

    run_normal_baseline(duration_sec=args.duration, exp_id=args.exp_id)
