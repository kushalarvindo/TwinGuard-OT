"""
Experiment Script: Controlled Cyberattack Scenario Runner.
Runs simulated industrial process, injects a selected cyberattack with ground-truth labelling,
and executes real-time Process-Aware anomaly detection.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

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
from twinguard.detection.rules import RuleBasedDetector
from twinguard.detection.process_residual import DigitalTwinShadowModel
from twinguard.detection.isolation_forest import IsolationForestDetector
from twinguard.detection.correlation import CyberPhysicalCorrelator

from twinguard.attacks.unauthorized_write import UnauthorizedWriteAttack
from twinguard.attacks.sensor_spoofing import SensorSpoofingAttack
from twinguard.attacks.replay import ReplayAttack
from twinguard.attacks.command_flood import CommandFloodAttack
from twinguard.attacks.setpoint_manipulation import SetpointManipulationAttack


def create_attack_instance(attack_name: str, tank: WaterTank, plc: VirtualPLC, port: int, duration_sec: float):
    """Factory creating the requested attack module."""
    if attack_name == "sensor_spoofing":
        return SensorSpoofingAttack(tank=tank, spoofed_level=20.0, target_port=port, duration_sec=duration_sec)
    elif attack_name == "unauthorized_write":
        return UnauthorizedWriteAttack(target_port=port, duration_sec=duration_sec)
    elif attack_name == "replay":
        return ReplayAttack(tank=tank, target_port=port, duration_sec=duration_sec)
    elif attack_name == "command_flood":
        return CommandFloodAttack(target_port=port, requests_per_sec=150, duration_sec=duration_sec)
    elif attack_name == "setpoint_manipulation":
        return SetpointManipulationAttack(plc=plc, malicious_setpoint=98.0, target_port=port, duration_sec=duration_sec)
    else:
        raise ValueError(f"Unknown attack type: {attack_name}")


def run_attack_experiment(
    attack_name: str,
    exp_id: Optional[str] = None,
    warmup_sec: float = 6.0,
    attack_duration_sec: float = 12.0,
    cooldown_sec: float = 6.0,
) -> str:
    """
    Executes a structured attack experiment with warmup, attack, and cooldown phases.
    """
    config = load_system_config()
    logger = setup_logger(f"twinguard.attack.{attack_name}")
    root = get_project_root()

    if exp_id is None:
        timestamp_str = int(time.time())
        exp_id = f"EXP-{attack_name.upper()[:6]}-{timestamp_str % 10000:04d}"

    db_path = config["storage"]["db_path_resolved"]
    db = DatabaseManager(db_path)
    db.create_experiment(
        exp_id=exp_id,
        name=f"Attack: {attack_name}",
        attack_type=attack_name,
        notes=f"Controlled {attack_name} injection ({attack_duration_sec}s)",
    )

    sim_cfg = config.get("physical_process", {})
    plc_cfg = config.get("plc", {})
    mb_cfg = config.get("modbus", {})
    det_cfg = config.get("detection", {})

    tank = WaterTank(
        capacity_liters=sim_cfg.get("capacity_liters", 1000.0),
        initial_level=sim_cfg.get("initial_level", 50.0),
        pump_inflow_rate=sim_cfg.get("pump_inflow_rate", 3.0),
        gravity_outflow_rate=sim_cfg.get("gravity_outflow_rate", 1.2),
        sensor_noise_std=sim_cfg.get("sensor_noise_std", 0.25),
    )

    plc = VirtualPLC(
        tank=tank,
        cycle_interval_sec=plc_cfg.get("cycle_interval_sec", 0.2),
        default_setpoint=plc_cfg.get("default_setpoint", 70.0),
        low_threshold=plc_cfg.get("low_threshold", 30.0),
        high_threshold=plc_cfg.get("high_threshold", 80.0),
    )

    server = TwinGuardModbusServer(
        host=mb_cfg.get("host", "127.0.0.1"),
        port=mb_cfg.get("port", 5020),
    )

    collector = DataCollector(
        tank=tank,
        plc=plc,
        modbus_server=server,
        db=db,
        sample_interval_sec=0.1,
    )

    # Initialize detection engines
    extractor = FeatureExtractor(high_threshold=plc_cfg.get("high_threshold", 80.0))
    rule_detector = RuleBasedDetector(residual_threshold=det_cfg.get("residual_threshold", 10.0))
    shadow_twin = DigitalTwinShadowModel(
        initial_level=sim_cfg.get("initial_level", 50.0),
        residual_threshold=det_cfg.get("residual_threshold", 10.0),
    )
    ml_detector = IsolationForestDetector()
    model_path = root / config["storage"].get("models_dir", "data/models") / "isolation_forest.joblib"
    ml_detector.load(model_save_path:=model_path)

    correlator = CyberPhysicalCorrelator()

    attack = create_attack_instance(
        attack_name=attack_name,
        tank=tank,
        plc=plc,
        port=mb_cfg.get("port", 5020),
        duration_sec=attack_duration_sec,
    )

    logger.info(f"=== Starting Experiment {exp_id} ({attack_name}) ===")
    server.start()
    plc.start()
    collector.start()

    prev_sample = None
    try:
        # Phase 1: Warmup (Normal Baseline)
        logger.info(f"Phase 1: Warmup baseline ({warmup_sec}s)...")
        collector.set_experiment_context(exp_id, is_attack_active=False, attack_type="normal")
        t_start = time.time()
        while time.time() - t_start < warmup_sec:
            state = tank.step(dt=0.1)
            time.sleep(0.08)

        # Phase 2: Attack Injection
        logger.info(f"Phase 2: Injecting attack '{attack_name}' for {attack_duration_sec}s...")
        collector.set_experiment_context(exp_id, is_attack_active=True, attack_type=attack_name)
        attack.start()

        t_attack = time.time()
        while time.time() - t_attack < attack_duration_sec and attack.is_running:
            state = tank.step(dt=0.1)

            # Step shadow digital twin
            expected_lvl, residual, _ = shadow_twin.step(
                pump_command=tank.pump.state,
                valve_command=tank.valve.state,
                dt=0.1,
                observed_sensor_level=state["sensor_level"],
            )

            # Feature extraction
            curr_dict = {
                "timestamp": state["timestamp"],
                "sensor_level": state["sensor_level"],
                "true_level": state["true_level"],
                "process_residual": residual,
                "inflow_rate": state["true_inflow"],
                "outflow_rate": state["true_outflow"],
                "pump_state": state["pump_state"],
                "valve_state": state["valve_state"],
                "setpoint": plc.logic.setpoint,
                "request_rate": server.current_request_rate,
            }
            features = extractor.extract_from_row(curr_dict, prev_sample)
            prev_sample = curr_dict

            # Detection execution
            rule_results = rule_detector.evaluate(features)
            ml_anomaly, ml_score, _ = ml_detector.predict_sample(features)
            corr_detection = correlator.correlate(rule_results, ml_anomaly, ml_score, features)

            # Log detection to DB
            primary_r = corr_detection.primary_rule
            db.log_detection({
                "experiment_id": exp_id,
                "timestamp": state["timestamp"],
                "engine": "HYBRID",
                "rule_id": primary_r,
                "rule_name": primary_r,
                "severity": corr_detection.severity,
                "is_anomaly": 1 if corr_detection.is_anomaly else 0,
                "anomaly_score": corr_detection.anomaly_score,
                "cyber_anomaly": 1 if corr_detection.cyber_anomaly else 0,
                "physical_anomaly": 1 if corr_detection.physical_anomaly else 0,
                "correlation_category": corr_detection.category,
                "explanation": corr_detection.explanation,
            })

            time.sleep(0.08)

        attack.stop()

        # Phase 3: Cooldown (Normal Recovery)
        logger.info(f"Phase 3: Cooldown recovery ({cooldown_sec}s)...")
        collector.set_experiment_context(exp_id, is_attack_active=False, attack_type="normal")
        t_cool = time.time()
        while time.time() - t_cool < cooldown_sec:
            tank.step(dt=0.1)
            time.sleep(0.08)

    finally:
        collector.stop()
        plc.stop()
        server.stop()
        db.finish_experiment(exp_id, status="COMPLETED")

    logger.info(f"Experiment {exp_id} finished successfully.")

    # Export results CSV
    results_dir = root / config["storage"].get("results_dir", "data/results")
    csv_out = results_dir / f"{exp_id}.csv"
    df = db.get_telemetry_by_experiment(exp_id)
    df.to_csv(csv_out, index=False)
    logger.info(f"Exported experiment dataset ({len(df)} samples) to: {csv_out}")

    return str(csv_out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwinGuard-OT Attack Scenario Runner")
    parser.add_argument(
        "--attack",
        type=str,
        required=True,
        choices=["sensor_spoofing", "unauthorized_write", "replay", "command_flood", "setpoint_manipulation"],
        help="Attack scenario to execute",
    )
    parser.add_argument("--exp-id", type=str, default=None, help="Custom experiment ID")
    parser.add_argument("--duration", type=float, default=12.0, help="Attack duration in seconds (default: 12)")
    args = parser.parse_args()

    run_attack_experiment(attack_name=args.attack, exp_id=args.exp_id, attack_duration_sec=args.duration)
