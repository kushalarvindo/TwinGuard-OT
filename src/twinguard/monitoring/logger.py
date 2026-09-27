"""
Specialized OT Logger for TwinGuard-OT.
Outputs human-readable and structured operational event records.
"""

import json
import logging
from typing import Dict, Any


class OTLogger:
    """Formats ICS domain operations and detection alerts for auditing."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def log_control_event(self, cycle: int, sensor_level: float, pump: int, valve: int, reasons: list[str]) -> None:
        msg = f"[PLC SCAN #{cycle}] Level={sensor_level:.1f}% | Pump={pump} | Valve={valve} | {'; '.join(reasons)}"
        self.logger.info(msg)

    def log_modbus_activity(self, client_ip: str, func_name: str, reg_name: str, value: int, is_write: bool) -> None:
        action = "WRITE" if is_write else "READ"
        msg = f"[MODBUS {action}] {client_ip} -> {func_name} on {reg_name} (Val={value})"
        self.logger.debug(msg)

    def log_security_alert(self, engine: str, severity: str, rule_id: str, explanation: str) -> None:
        msg = f"[{engine} ALERT - {severity}] Rule={rule_id} -> {explanation}"
        if severity in ("HIGH", "CRITICAL"):
            self.logger.warning(msg)
        else:
            self.logger.info(msg)
