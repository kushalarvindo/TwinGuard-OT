"""
Unit tests for attack simulation modules and security guardrails.
"""

import pytest
from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.attacks.base import LocalEnvironmentSecurityError
from twinguard.attacks.sensor_spoofing import SensorSpoofingAttack
from twinguard.attacks.setpoint_manipulation import SetpointManipulationAttack
from twinguard.attacks.replay import ReplayAttack


def test_attack_safety_guardrail():
    """Verify that attacking non-local IP addresses is strictly blocked."""
    with pytest.raises(LocalEnvironmentSecurityError):
        SensorSpoofingAttack(target_host="192.168.1.50")

    with pytest.raises(LocalEnvironmentSecurityError):
        SensorSpoofingAttack(target_host="8.8.8.8")


def test_sensor_spoofing_execution():
    tank = WaterTank(initial_level=80.0)
    attack = SensorSpoofingAttack(tank=tank, spoofed_level=20.0, duration_sec=0.5)

    assert tank.level_sensor.last_measured_value == pytest.approx(80.0, abs=2.0)
    
    attack.start()
    attack.stop()

    # Metrics should record the spoofed state
    assert attack.metrics.get("total_spoofs", 0) > 0
    # Sensor must be restored after attack stops
    assert tank.level_sensor.is_spoofed is False


def test_setpoint_manipulation_execution():
    tank = WaterTank(initial_level=50.0)
    plc = VirtualPLC(tank=tank, default_setpoint=70.0)

    assert plc.logic.setpoint == 70.0

    attack = SetpointManipulationAttack(
        plc=plc,
        malicious_setpoint=98.0,
        original_setpoint=70.0,
        duration_sec=0.5,
    )
    attack.start()
    attack.stop()

    assert attack.metrics["malicious_setpoint"] == 98.0
    # Setpoint must be restored after attack completes
    assert plc.logic.setpoint == 70.0


def test_replay_attack_sequence():
    tank = WaterTank(initial_level=50.0)
    recorded = [10.0, 15.0, 20.0]
    attack = ReplayAttack(tank=tank, recorded_sequence=recorded, duration_sec=0.6)

    attack.start()
    attack.stop()

    assert len(attack.replay_log) > 0
    assert attack.metrics["total_replayed"] > 0
    assert tank.level_sensor.is_spoofed is False
