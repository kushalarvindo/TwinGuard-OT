"""
Unit tests for the Virtual PLC and Process Control Logic.
"""

from twinguard.process.tank import WaterTank
from twinguard.plc.control_logic import ProcessControlLogic
from twinguard.plc.plc import VirtualPLC


def test_control_logic_thresholds():
    logic = ProcessControlLogic(setpoint=70.0, low_threshold=30.0, high_threshold=80.0, emergency_high=95.0)

    # 1. Level below low threshold -> Pump ON
    d1 = logic.evaluate(sensor_level=25.0, current_pump=0, current_valve=1, auto_mode=1)
    assert d1.target_pump == 1
    assert d1.target_valve == 0
    assert d1.alarm_state == 0

    # 2. Level in hysteresis band -> Maintain state
    d2 = logic.evaluate(sensor_level=55.0, current_pump=1, current_valve=0, auto_mode=1)
    assert d2.target_pump == 1
    assert d2.target_valve == 0

    # 3. Level reaches high threshold -> Pump OFF, Valve OPEN
    d3 = logic.evaluate(sensor_level=82.0, current_pump=1, current_valve=0, auto_mode=1)
    assert d3.target_pump == 0
    assert d3.target_valve == 1


def test_control_logic_safety_interlock():
    logic = ProcessControlLogic(emergency_high=95.0)

    # When level >= emergency_high, pump must be forced OFF immediately
    d = logic.evaluate(sensor_level=96.5, current_pump=1, current_valve=0, auto_mode=1)
    assert d.target_pump == 0
    assert d.target_valve == 1
    assert d.alarm_state == 3
    assert any("SAFETY INTERLOCK" in r for r in d.reasons)


def test_virtual_plc_scan():
    tank = WaterTank(initial_level=20.0)
    plc = VirtualPLC(tank=tank, low_threshold=30.0, high_threshold=80.0)

    # Tank level is 20% (< 30%). Scan once.
    decision = plc.scan_once()
    assert decision.target_pump == 1
    assert tank.pump.state == 1
    assert plc.cycle_count == 1
    assert len(plc.event_log) > 0
