"""
Modbus TCP Register Definitions and Scaling Utilities.
Implements holding register map for TwinGuard-OT.
"""

from typing import Dict, Any, Tuple

# Holding Register 0-based Offsets (corresponds to 40001 - 40012)
REG_TANK_LEVEL_SENSOR = 0  # 40001: Reported Level (% * 10)
REG_SETPOINT_LEVEL    = 1  # 40002: Target Setpoint (% * 10)
REG_PUMP_COMMAND      = 2  # 40003: Pump Command (0=OFF, 1=ON)
REG_VALVE_COMMAND     = 3  # 40004: Valve Command (0=CLOSED, 1=OPEN)
REG_INFLOW_RATE       = 4  # 40005: Inflow Rate (%/s * 10)
REG_OUTFLOW_RATE      = 5  # 40006: Outflow Rate (%/s * 10)
REG_ALARM_STATE       = 6  # 40007: Alarm Enum (0=Norm, 1=Low, 2=High, 3=Interlock)
REG_LOW_THRESHOLD     = 7  # 40008: Low Hysteresis Threshold (% * 10)
REG_HIGH_THRESHOLD    = 8  # 40009: High Hysteresis Threshold (% * 10)
REG_CONTROL_MODE      = 9  # 40010: Mode (1=AUTO, 0=MANUAL)
REG_TRUE_TANK_LEVEL   = 10 # 40011: True Physical Level (% * 10)
REG_PHYSICAL_RESIDUAL = 11 # 40012: Residual |True - Sensor| (% * 10)

TOTAL_REGISTERS = 32


class RegisterMap:
    """Register metadata and conversion helper."""

    METADATA: Dict[int, Dict[str, Any]] = {
        REG_TANK_LEVEL_SENSOR: {"name": "TANK_LEVEL_SENSOR", "address": 40001, "scale": 10.0, "unit": "%", "rw": "RO"},
        REG_SETPOINT_LEVEL:    {"name": "SETPOINT_LEVEL",    "address": 40002, "scale": 10.0, "unit": "%", "rw": "RW"},
        REG_PUMP_COMMAND:      {"name": "PUMP_COMMAND",      "address": 40003, "scale": 1.0,  "unit": "",  "rw": "RW"},
        REG_VALVE_COMMAND:     {"name": "VALVE_COMMAND",     "address": 40004, "scale": 1.0,  "unit": "",  "rw": "RW"},
        REG_INFLOW_RATE:       {"name": "INFLOW_RATE",       "address": 40005, "scale": 10.0, "unit": "%/s", "rw": "RO"},
        REG_OUTFLOW_RATE:      {"name": "OUTFLOW_RATE",      "address": 40006, "scale": 10.0, "unit": "%/s", "rw": "RO"},
        REG_ALARM_STATE:       {"name": "ALARM_STATE",       "address": 40007, "scale": 1.0,  "unit": "",  "rw": "RO"},
        REG_LOW_THRESHOLD:     {"name": "LOW_THRESHOLD",     "address": 40008, "scale": 10.0, "unit": "%", "rw": "RW"},
        REG_HIGH_THRESHOLD:    {"name": "HIGH_THRESHOLD",    "address": 40009, "scale": 10.0, "unit": "%", "rw": "RW"},
        REG_CONTROL_MODE:      {"name": "CONTROL_MODE",      "address": 40010, "scale": 1.0,  "unit": "",  "rw": "RW"},
        REG_TRUE_TANK_LEVEL:   {"name": "TRUE_TANK_LEVEL",   "address": 40011, "scale": 10.0, "unit": "%", "rw": "RO"},
        REG_PHYSICAL_RESIDUAL: {"name": "PHYSICAL_RESIDUAL", "address": 40012, "scale": 10.0, "unit": "%", "rw": "RO"},
    }

    @staticmethod
    def to_raw(register_offset: int, value: float) -> int:
        """Encodes an engineering float value into a 16-bit register raw integer."""
        meta = RegisterMap.METADATA.get(register_offset, {"scale": 1.0})
        scale = meta["scale"]
        raw = int(round(value * scale))
        return max(0, min(65535, raw))

    @staticmethod
    def to_eng(register_offset: int, raw_value: int) -> float:
        """Decodes a 16-bit register raw integer into an engineering float value."""
        meta = RegisterMap.METADATA.get(register_offset, {"scale": 1.0})
        scale = meta["scale"]
        return round(float(raw_value) / scale, 2)
