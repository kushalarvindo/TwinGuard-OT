"""
End-to-End Integration Test for TwinGuard-OT.
Validates the entire operational loop:
Physical Simulation -> Sensors -> PLC -> Modbus TCP -> Collector -> Detection -> DB.
"""

import time
import numpy as np
import pytest

from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.database.db import DatabaseManager
from twinguard.monitoring.collector import DataCollector
from twinguard.features.extractor import FeatureExtractor
from twinguard.detection.rules import RuleBasedDetector
from twinguard.detection.process_residual import DigitalTwinShadowModel
from twinguard.detection.correlation import CyberPhysicalCorrelator
from twinguard.attacks.sensor_spoofing import SensorSpoofingAttack


def test_full_system_integration_loop(tmp_path):
    test_port = 5035
    db_file = tmp_path / "test_twinguard.db"
    db = DatabaseManager(str(db_file))
    exp_id = "EXP-INTEGRATION-001"
    db.create_experiment(exp_id, name="Integration Test", attack_type="mixed")

    # 1. Initialize Components
    tank = WaterTank(initial_level=50.0, pump_inflow_rate=3.0, gravity_outflow_rate=1.2)
    plc = VirtualPLC(tank=tank, low_threshold=30.0, high_threshold=80.0)
    server = TwinGuardModbusServer(host="127.0.0.1", port=test_port)
    collector = DataCollector(tank=tank, plc=plc, modbus_server=server, db=db, sample_interval_sec=0.05)

    extractor = FeatureExtractor(high_threshold=80.0)
    rule_detector = RuleBasedDetector(residual_threshold=10.0)
    shadow_twin = DigitalTwinShadowModel(initial_level=50.0, residual_threshold=10.0)
    correlator = CyberPhysicalCorrelator()

    # 2. Start Subsystems
    server.start()
    plc.start()
    collector.start()

    client = TwinGuardModbusClient(host="127.0.0.1", port=test_port)
    assert client.connect() is True

    try:
        # 3. Normal Phase (1.5 seconds)
        collector.set_experiment_context(exp_id, is_attack_active=False, attack_type="normal")
        t0 = time.time()
        while time.time() - t0 < 1.5:
            tank.step(dt=0.05)
            time.sleep(0.04)

        # Verify normal state via Modbus client
        state = client.read_process_state()
        assert state["sensor_level"] > 0.0
        assert state["physical_residual"] < 5.0

        # 4. Attack Phase: Inject Sensor Spoofing (report 15% when actual is ~50%)
        collector.set_experiment_context(exp_id, is_attack_active=True, attack_type="sensor_spoofing")
        attack = SensorSpoofingAttack(tank=tank, spoofed_level=15.0, duration_sec=1.0)
        attack.start()

        detected_alerts = []
        t_atk = time.time()
        prev_sample = None
        while time.time() - t_atk < 1.2:
            st_dict = tank.step(dt=0.05)
            _, residual, _ = shadow_twin.step(
                pump_command=tank.pump.state,
                valve_command=tank.valve.state,
                dt=0.05,
                observed_sensor_level=st_dict["sensor_level"],
            )

            feat = extractor.extract_from_row({
                "timestamp": st_dict["timestamp"],
                "sensor_level": st_dict["sensor_level"],
                "true_level": st_dict["true_level"],
                "process_residual": residual,
                "pump_state": st_dict["pump_state"],
                "valve_state": st_dict["valve_state"],
                "request_rate": 5.0,
            }, prev_sample)
            prev_sample = feat

            rules = rule_detector.evaluate(feat)
            corr = correlator.correlate(rules, ml_is_anomaly=False, ml_score=0.0, features=feat)
            if corr.is_anomaly:
                detected_alerts.append(corr)

            time.sleep(0.04)

        attack.stop()

        # 5. Assertions:
        # A. Anomaly must have been detected
        assert len(detected_alerts) > 0
        assert any(a.category == "CYBER_PHYSICAL_ATTACK" for a in detected_alerts)

        # B. Telemetry was persisted to SQLite database
        df_telemetry = db.get_telemetry_by_experiment(exp_id)
        assert len(df_telemetry) >= 15
        assert np.any(df_telemetry["label"] == 1)
        assert np.any(df_telemetry["label"] == 0)

    finally:
        client.close()
        collector.stop()
        plc.stop()
        server.stop()
        db.finish_experiment(exp_id, status="COMPLETED")
