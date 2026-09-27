"""
Modbus TCP Client Implementation for TwinGuard-OT.
Provides high-level OT methods for HMI, attacks, and telemetry polling.
"""

import time
from typing import Dict, Any, Optional, List
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from pymodbus.client import ModbusTcpClient

from .registers import (
    RegisterMap,
    REG_TANK_LEVEL_SENSOR,
    REG_SETPOINT_LEVEL,
    REG_PUMP_COMMAND,
    REG_VALVE_COMMAND,
    REG_INFLOW_RATE,
    REG_OUTFLOW_RATE,
    REG_ALARM_STATE,
    REG_LOW_THRESHOLD,
    REG_HIGH_THRESHOLD,
    REG_CONTROL_MODE,
    REG_TRUE_TANK_LEVEL,
    REG_PHYSICAL_RESIDUAL,
)


class TwinGuardModbusClient:
    """
    Client for interacting with the TwinGuard-OT Virtual PLC over Modbus TCP.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5020, unit_id: int = 1, timeout: float = 2.0) -> None:
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: Optional[ModbusTcpClient] = None

        # Telemetry statistics
        self.request_count: int = 0
        self.error_count: int = 0
        self.last_latency_ms: float = 0.0

    def connect(self) -> bool:
        """Establishes Modbus TCP connection."""
        if self._client is None:
            self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)
        return self._client.connect()

    def close(self) -> None:
        """Closes connection."""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.connected

    def ensure_connected(self) -> bool:
        """Reconnects if connection is dropped."""
        if not self.is_connected:
            return self.connect()
        return True

    def read_process_state(self) -> Dict[str, Any]:
        """
        Reads all active process registers (40001 - 40012) in a single transaction.
        Uses 0-based offset address=0, count=12.
        """
        if not self.ensure_connected():
            raise ConnectionError(f"Cannot connect to Modbus server at {self.host}:{self.port}")

        start_t = time.time()
        self.request_count += 1
        response = self._client.read_holding_registers(address=0, count=12, device_id=self.unit_id)
        self.last_latency_ms = round((time.time() - start_t) * 1000.0, 2)

        if response.isError():
            self.error_count += 1
            raise RuntimeError(f"Modbus read error: {response}")

        regs = response.registers
        return {
            "timestamp": time.time(),
            "sensor_level": RegisterMap.to_eng(REG_TANK_LEVEL_SENSOR, regs[REG_TANK_LEVEL_SENSOR]),
            "setpoint": RegisterMap.to_eng(REG_SETPOINT_LEVEL, regs[REG_SETPOINT_LEVEL]),
            "pump_command": regs[REG_PUMP_COMMAND],
            "valve_command": regs[REG_VALVE_COMMAND],
            "inflow_rate": RegisterMap.to_eng(REG_INFLOW_RATE, regs[REG_INFLOW_RATE]),
            "outflow_rate": RegisterMap.to_eng(REG_OUTFLOW_RATE, regs[REG_OUTFLOW_RATE]),
            "alarm_state": regs[REG_ALARM_STATE],
            "low_threshold": RegisterMap.to_eng(REG_LOW_THRESHOLD, regs[REG_LOW_THRESHOLD]),
            "high_threshold": RegisterMap.to_eng(REG_HIGH_THRESHOLD, regs[REG_HIGH_THRESHOLD]),
            "control_mode": regs[REG_CONTROL_MODE],
            "true_level": RegisterMap.to_eng(REG_TRUE_TANK_LEVEL, regs[REG_TRUE_TANK_LEVEL]),
            "physical_residual": RegisterMap.to_eng(REG_PHYSICAL_RESIDUAL, regs[REG_PHYSICAL_RESIDUAL]),
            "latency_ms": self.last_latency_ms,
        }

    def write_pump(self, state: int) -> bool:
        """Writes pump command register (40003, address=2)."""
        return self.write_register_raw(REG_PUMP_COMMAND, int(state))

    def write_valve(self, state: int) -> bool:
        """Writes valve command register (40004, address=3)."""
        return self.write_register_raw(REG_VALVE_COMMAND, int(state))

    def write_setpoint(self, setpoint: float) -> bool:
        """Writes target setpoint register (40002, address=1)."""
        raw_val = RegisterMap.to_raw(REG_SETPOINT_LEVEL, setpoint)
        return self.write_register_raw(REG_SETPOINT_LEVEL, raw_val)

    def write_thresholds(self, low: float, high: float) -> bool:
        """Writes hysteresis threshold registers."""
        raw_low = RegisterMap.to_raw(REG_LOW_THRESHOLD, low)
        raw_high = RegisterMap.to_raw(REG_HIGH_THRESHOLD, high)
        r1 = self.write_register_raw(REG_LOW_THRESHOLD, raw_low)
        r2 = self.write_register_raw(REG_HIGH_THRESHOLD, raw_high)
        return r1 and r2

    def write_mode(self, auto_mode: int) -> bool:
        """Writes control mode register (40010, address=9)."""
        return self.write_register_raw(REG_CONTROL_MODE, int(auto_mode))

    def write_register_raw(self, address: int, value: int) -> bool:
        """Direct raw register write at given address offset."""
        if not self.ensure_connected():
            raise ConnectionError(f"Cannot connect to Modbus server at {self.host}:{self.port}")

        start_t = time.time()
        self.request_count += 1
        response = self._client.write_register(address=address, value=int(value), device_id=self.unit_id)
        self.last_latency_ms = round((time.time() - start_t) * 1000.0, 2)

        if response.isError():
            self.error_count += 1
            return False
        return True

    def read_holding_registers(self, address: int, count: int) -> List[int]:
        """Low-level register read."""
        if not self.ensure_connected():
            raise ConnectionError(f"Cannot connect to Modbus server at {self.host}:{self.port}")

        self.request_count += 1
        response = self._client.read_holding_registers(address=address, count=count, device_id=self.unit_id)
        if response.isError():
            self.error_count += 1
            raise RuntimeError(f"Modbus read error: {response}")
        return response.registers
