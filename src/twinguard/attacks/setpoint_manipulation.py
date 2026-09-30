"""
Attack Scenario 5: Abnormal Setpoint Manipulation.
Modifies the operational target setpoint to an unsafe or out-of-spec extreme
(e.g., setpoint 98% risking overflow, or setpoint 5% causing dry running).
"""

import time
from typing import Optional
from .base import BaseAttack
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.modbus.registers import REG_SETPOINT_LEVEL, RegisterMap


class SetpointManipulationAttack(BaseAttack):
    """
    Overwrites the PLC setpoint holding register to an abnormal value.
    """

    def __init__(
        self,
        plc: Optional[VirtualPLC] = None,
        malicious_setpoint: float = 98.0,
        original_setpoint: float = 70.0,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        duration_sec: float = 12.0,
    ) -> None:
        super().__init__(
            name="setpoint_manipulation",
            description="Forces operational setpoint to unsafe extreme value.",
            target_host=target_host,
            target_port=target_port,
            duration_sec=duration_sec,
        )
        self.plc = plc
        self.malicious_setpoint = float(malicious_setpoint)
        self.original_setpoint = float(original_setpoint)

    def execute(self) -> None:
        end_time = time.time() + self.duration_sec

        # Apply malicious setpoint
        if self.plc is not None:
            self.plc.set_setpoint(self.malicious_setpoint)
            self.events_injected += 1
        else:
            client = TwinGuardModbusClient(host=self.target_host, port=self.target_port)
            if client.connect():
                client.write_setpoint(self.malicious_setpoint)
                self.events_injected += 1
                client.close()

        self.metrics["malicious_setpoint"] = self.malicious_setpoint
        self.metrics["original_setpoint"] = self.original_setpoint

        try:
            while not self._stop_event.is_set() and time.time() < end_time:
                time.sleep(0.5)
        finally:
            # Restore original setpoint on completion
            if self.plc is not None:
                self.plc.set_setpoint(self.original_setpoint)
            else:
                client = TwinGuardModbusClient(host=self.target_host, port=self.target_port)
                if client.connect():
                    client.write_setpoint(self.original_setpoint)
                    client.close()
            self.metrics["restored"] = True
