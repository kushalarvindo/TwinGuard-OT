"""
Unit tests for the physical water tank simulation, actuators, and sensors.
"""

import pytest
from twinguard.process.physics import WaterTankPhysics
from twinguard.process.actuators import Pump, Valve
from twinguard.process.sensors import WaterLevelSensor, FlowSensor
from twinguard.process.tank import WaterTank


def test_physics_filling_and_draining():
    physics = WaterTankPhysics(pump_inflow_rate=4.0, gravity_outflow_rate=2.0, leak_outflow_rate=0.0)
    
    # Pump ON, Valve CLOSED -> Net +4.0 %/s
    level, inflow, outflow, overflow, dry_run = physics.step(current_level=50.0, pump_state=1, valve_state=0, dt=1.0)
    assert level == pytest.approx(54.0, abs=1e-2)
    assert inflow == 4.0
    assert outflow == 0.0

    # Pump OFF, Valve OPEN -> Net -2.0 %/s (with head factor)
    level2, inflow2, outflow2, _, _ = physics.step(current_level=50.0, pump_state=0, valve_state=1, dt=1.0)
    assert level2 < 50.0
    assert inflow2 == 0.0
    assert outflow2 > 0.0


def test_physics_boundaries():
    physics = WaterTankPhysics(min_level=0.0, max_level=100.0, pump_inflow_rate=10.0, gravity_outflow_rate=10.0)

    # Overflow capping
    level, _, _, overflow, _ = physics.step(current_level=98.0, pump_state=1, valve_state=0, dt=1.0)
    assert level == 100.0
    assert overflow is True

    # Underflow capping
    level, _, _, _, dry_run = physics.step(current_level=2.0, pump_state=0, valve_state=1, dt=1.0)
    assert level == 0.0
    assert dry_run is True


def test_actuator_controls():
    pump = Pump(name="TEST_PUMP", rated_flow=3.0)
    assert pump.state == 0
    assert not pump.is_on

    pump.turn_on()
    assert pump.state == 1
    assert pump.is_on
    assert pump.cycle_count == 1

    pump.turn_off()
    assert pump.state == 0

    valve = Valve(name="TEST_VALVE", rated_flow=1.5)
    assert valve.state == 0
    valve.open()
    assert valve.state == 1
    assert valve.position == 1.0
    valve.close()
    assert valve.state == 0


def test_sensor_spoofing_decoupling():
    """
    CRITICAL TEST: Verify that sensor spoofing modifies observed value
    without changing the underlying true physical state.
    """
    sensor = WaterLevelSensor(noise_std=0.0)
    true_level = 88.5
    reading = sensor.read(true_level)
    assert reading == pytest.approx(88.5, abs=1e-2)
    assert sensor.get_status()["residual"] == 0.0

    # Inject cyber spoofing: report 20.0% when true is 88.5%
    sensor.set_spoof(20.0)
    spoofed_reading = sensor.read(true_level)
    assert spoofed_reading == 20.0
    assert sensor.last_true_value == 88.5
    assert sensor.is_spoofed is True

    status = sensor.get_status()
    assert status["residual"] == pytest.approx(68.5, abs=1e-2)

    # Clear spoofing
    sensor.clear_spoof()
    restored_reading = sensor.read(true_level)
    assert restored_reading == pytest.approx(88.5, abs=1e-2)


def test_complete_tank_simulation_step():
    tank = WaterTank(initial_level=40.0, pump_inflow_rate=3.0, gravity_outflow_rate=1.0)
    tank.set_pump(1)
    tank.set_valve(0)

    # Step 1 second
    state = tank.step(dt=1.0)
    assert state["true_level"] > 40.0
    assert state["pump_state"] == 1
    assert state["valve_state"] == 0
    assert abs(state["true_level"] - state["sensor_level"]) < 2.0  # only small noise
