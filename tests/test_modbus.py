"""
Unit tests for Modbus TCP Server, Client, and Register mapping.
"""

import time
import pytest
from twinguard.modbus.registers import RegisterMap, REG_TANK_LEVEL_SENSOR, REG_SETPOINT_LEVEL, REG_PUMP_COMMAND
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.modbus.client import TwinGuardModbusClient


def test_register_scaling():
    # Engineering float to raw integer
    raw_level = RegisterMap.to_raw(REG_TANK_LEVEL_SENSOR, 74.2)
    assert raw_level == 742

    # Raw integer to engineering float
    eng_level = RegisterMap.to_eng(REG_TANK_LEVEL_SENSOR, 742)
    assert eng_level == 74.2

    # Discrete pump state
    raw_pump = RegisterMap.to_raw(REG_PUMP_COMMAND, 1.0)
    assert raw_pump == 1
    assert RegisterMap.to_eng(REG_PUMP_COMMAND, 1) == 1.0


def test_modbus_server_and_client_roundtrip():
    # Use dedicated test port to prevent collision
    test_port = 5025
    server = TwinGuardModbusServer(host="127.0.0.1", port=test_port)
    server.start()

    try:
        # Sync initial state into server
        tank_state = {
            "sensor_level": 65.5,
            "pump_state": 1,
            "valve_state": 0,
            "sensor_inflow": 3.0,
            "sensor_outflow": 0.0,
            "true_level": 65.2,
            "residual": 0.3,
        }
        server.sync_from_process(
            tank_state=tank_state,
            setpoint=70.0,
            low_thresh=30.0,
            high_thresh=80.0,
            control_mode=1,
            alarm_state=0,
        )

        client = TwinGuardModbusClient(host="127.0.0.1", port=test_port)
        assert client.connect() is True

        # Read process state
        state = client.read_process_state()
        assert state["sensor_level"] == 65.5
        assert state["setpoint"] == 70.0
        assert state["pump_command"] == 1
        assert state["valve_command"] == 0

        # Test writing setpoint
        assert client.write_setpoint(85.0) is True
        # Read back
        updated_state = client.read_process_state()
        assert updated_state["setpoint"] == 85.0

        # Test writing pump command
        assert client.write_pump(0) is True
        updated_state2 = client.read_process_state()
        assert updated_state2["pump_command"] == 0

        client.close()
    finally:
        server.stop()
