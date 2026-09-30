"""
Attack Scenario 4: Command Flooding.
Simulates high-frequency request flooding against the simulated Modbus TCP environment.
Strictly confined to localhost simulation.
"""

import time
from .base import BaseAttack
from twinguard.modbus.client import TwinGuardModbusClient


class CommandFloodAttack(BaseAttack):
    """
    Floods the local Modbus TCP server with rapid read/write requests
    to induce resource contention, communication delays, and high request-rate anomalies.
    """

    def __init__(
        self,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        requests_per_sec: int = 150,
        duration_sec: float = 8.0,
    ) -> None:
        super().__init__(
            name="command_flood",
            description="Generates high-frequency Modbus queries against local virtual PLC.",
            target_host=target_host,
            target_port=target_port,
            duration_sec=duration_sec,
        )
        self.requests_per_sec = requests_per_sec

    def execute(self) -> None:
        client = TwinGuardModbusClient(host=self.target_host, port=self.target_port, timeout=0.5)
        if not client.connect():
            self.metrics["error"] = "Failed to connect to simulation Modbus server"
            return

        end_time = time.time() + self.duration_sec
        delay = 1.0 / max(1, self.requests_per_sec)

        start_t = time.time()
        try:
            while not self._stop_event.is_set() and time.time() < end_time:
                try:
                    # Rapid holding register reads
                    client.read_holding_registers(address=0, count=4)
                    self.events_injected += 1
                except Exception:
                    pass
                time.sleep(delay)
        finally:
            elapsed = max(0.001, time.time() - start_t)
            client.close()
            actual_rate = round(self.events_injected / elapsed, 2)
            self.metrics["total_requests"] = self.events_injected
            self.metrics["achieved_rate_rps"] = actual_rate
            self.metrics["flood_duration_sec"] = round(elapsed, 2)
