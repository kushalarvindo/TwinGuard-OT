"""
Modbus TCP Server, Client, and Register definitions for TwinGuard-OT.
"""

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
from .server import TwinGuardModbusServer
from .client import TwinGuardModbusClient

__all__ = [
    "RegisterMap",
    "REG_TANK_LEVEL_SENSOR",
    "REG_SETPOINT_LEVEL",
    "REG_PUMP_COMMAND",
    "REG_VALVE_COMMAND",
    "REG_INFLOW_RATE",
    "REG_OUTFLOW_RATE",
    "REG_ALARM_STATE",
    "REG_LOW_THRESHOLD",
    "REG_HIGH_THRESHOLD",
    "REG_CONTROL_MODE",
    "REG_TRUE_TANK_LEVEL",
    "REG_PHYSICAL_RESIDUAL",
    "TwinGuardModbusServer",
    "TwinGuardModbusClient",
]
