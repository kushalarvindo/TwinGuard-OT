"""
Unit tests for detection engines: Rules, Digital Twin Residuals, Isolation Forest, and Correlation.
"""

import numpy as np
import pandas as pd
import pytest

from twinguard.detection.rules import RuleBasedDetector
from twinguard.detection.process_residual import DigitalTwinShadowModel
from twinguard.detection.isolation_forest import IsolationForestDetector
from twinguard.detection.correlation import CyberPhysicalCorrelator


def test_rule_unexpected_pump_activation():
    detector = RuleBasedDetector(high_threshold=80.0)
    features = {"sensor_level": 88.0, "pump_state": 1, "level_rate": 2.0, "process_residual": 0.5}
    active = detector.get_active_alerts(features)
    assert any(a.rule_id == "R001" for a in active)


def test_rule_process_residual_violation():
    detector = RuleBasedDetector(residual_threshold=10.0)
    # Residual = 35.0 (Spoofed reading)
    features = {"sensor_level": 20.0, "process_residual": 35.0, "pump_state": 0}
    active = detector.get_active_alerts(features)
    assert any(a.rule_id == "R002" for a in active)


def test_rule_flood_request_rate():
    detector = RuleBasedDetector(flood_request_rate=30.0)
    features = {"request_rate": 120.0, "sensor_level": 50.0}
    active = detector.get_active_alerts(features)
    assert any(a.rule_id == "R004" for a in active)


def test_digital_twin_shadow_model():
    dt_model = DigitalTwinShadowModel(initial_level=50.0, residual_threshold=10.0)
    
    # 1. Normal step: Pump ON for 1 sec -> expected increases from 50 to ~53%
    expected, residual, is_anomaly = dt_model.step(
        pump_command=1,
        valve_command=0,
        dt=1.0,
        observed_sensor_level=52.8, # Normal observed matches expected
    )
    assert expected > 50.0
    assert residual < 2.0
    assert not is_anomaly

    # 2. Attack step: sensor reports 15.0% (spoofed)
    _, attack_residual, is_attack_anomaly = dt_model.step(
        pump_command=1,
        valve_command=0,
        dt=1.0,
        observed_sensor_level=15.0,
    )
    assert attack_residual > 35.0
    assert is_attack_anomaly is True


def test_isolation_forest_train_and_predict():
    detector = IsolationForestDetector(n_estimators=50, contamination=0.05, random_state=42)

    # Generate synthetic clean normal training data
    n_samples = 150
    np.random.seed(42)
    normal_df = pd.DataFrame({
        "sensor_level": np.random.uniform(40.0, 70.0, n_samples),
        "level_rate": np.random.uniform(-1.0, 1.0, n_samples),
        "process_residual": np.random.uniform(0.1, 1.5, n_samples),
        "inflow_rate": np.random.uniform(0.0, 3.0, n_samples),
        "outflow_rate": np.random.uniform(0.0, 1.5, n_samples),
        "net_flow": np.random.uniform(-1.5, 1.5, n_samples),
        "pump_state": np.random.choice([0, 1], n_samples),
        "valve_state": np.random.choice([0, 1], n_samples),
        "setpoint": [70.0] * n_samples,
        "setpoint_error": np.random.uniform(-5.0, 5.0, n_samples),
        "request_rate": np.random.uniform(4.0, 6.0, n_samples),
        "actuator_inconsistency": [0.0] * n_samples,
        "physical_impossibility": [0.0] * n_samples,
    })

    detector.fit(normal_df)
    assert detector.is_trained is True

    # Test on a normal sample
    normal_sample = normal_df.iloc[0].to_dict()
    is_anom, score, _ = detector.predict_sample(normal_sample)
    assert not is_anom

    # Test on an extreme attack sample (massive residual and flood)
    attack_sample = normal_sample.copy()
    attack_sample["process_residual"] = 65.0
    attack_sample["request_rate"] = 250.0
    is_anom_atk, score_atk, _ = detector.predict_sample(attack_sample)
    assert is_anom_atk is True
    assert score_atk > score


def test_cyber_physical_correlator():
    correlator = CyberPhysicalCorrelator()
    detector = RuleBasedDetector()

    # Case 1: Normal
    features_norm = {"sensor_level": 55.0, "pump_state": 1, "request_rate": 5.0, "process_residual": 0.5}
    rules_norm = detector.evaluate(features_norm)
    det_norm = correlator.correlate(rules_norm, ml_is_anomaly=False, ml_score=0.01, features=features_norm)
    assert det_norm.category == "NORMAL"
    assert not det_norm.is_anomaly

    # Case 2: Cyber-Only (Command Flood)
    features_flood = {"sensor_level": 55.0, "pump_state": 1, "request_rate": 150.0, "process_residual": 0.5}
    rules_flood = detector.evaluate(features_flood)
    det_flood = correlator.correlate(rules_flood, ml_is_anomaly=True, ml_score=0.3, features=features_flood)
    assert det_flood.category == "CYBER_ONLY"
    assert det_flood.is_anomaly

    # Case 3: Cyber-Physical Attack (Sensor Spoofing + Residual Violation)
    features_spoof = {"sensor_level": 20.0, "pump_state": 1, "request_rate": 5.0, "process_residual": 65.0}
    rules_spoof = detector.evaluate(features_spoof)
    det_spoof = correlator.correlate(rules_spoof, ml_is_anomaly=True, ml_score=0.5, features=features_spoof)
    assert det_spoof.category == "CYBER_PHYSICAL_ATTACK"
    assert det_spoof.severity == "CRITICAL"
