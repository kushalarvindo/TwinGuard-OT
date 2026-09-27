"""
Central Telemetry and OT Event Collector for TwinGuard-OT.
Aggregates cyber and physical signals, manages ground-truth labels, and streams to database.
"""

import threading
import time
from collections import deque
from typing import Dict, Any, List, Optional

from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.database.db import DatabaseManager
from .events import ProcessEvent, ModbusEvent


class DataCollector:
    """
    Subsystem responsible for real-time sampling and logging of
    physical state, PLC variables, and Modbus communication.
    """

    def __init__(
        self,
        tank: WaterTank,
        plc: VirtualPLC,
        modbus_server: TwinGuardModbusServer,
        db: DatabaseManager,
        sample_interval_sec: float = 0.1,
    ) -> None:
        self.tank = tank
        self.plc = plc
        self.modbus_server = modbus_server
        self.db = db
        self.sample_interval_sec = sample_interval_sec

        # Experiment context for automated ground-truth labelling
        self.experiment_id: str = "EXP-BASELINE"
        self.is_attack_active: bool = False
        self.current_attack_type: str = "normal"

        # Rolling in-memory window for fast dashboard updates
        self.recent_telemetry: deque = deque(maxlen=500)
        self.recent_events: deque = deque(maxlen=200)

        self._is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.total_samples_collected: int = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_experiment_context(
        self,
        experiment_id: str,
        is_attack_active: bool = False,
        attack_type: str = "normal",
    ) -> None:
        """Sets current experiment metadata for ground-truth labelling."""
        with self._lock:
            self.experiment_id = experiment_id
            self.is_attack_active = is_attack_active
            self.current_attack_type = attack_type

    def sample_once(self) -> ProcessEvent:
        """Collects a single synchronized telemetry snapshot."""
        with self._lock:
            state = self.tank.get_state()
            plc_status = self.plc.get_status()
            now = time.time()

            label = 1 if self.is_attack_active else 0
            attack_type = self.current_attack_type if self.is_attack_active else "normal"

            event = ProcessEvent(
                experiment_id=self.experiment_id,
                timestamp=now,
                true_level=state["true_level"],
                sensor_level=state["sensor_level"],
                inflow_rate=state["true_inflow"],
                outflow_rate=state["true_outflow"],
                pump_state=state["pump_state"],
                valve_state=state["valve_state"],
                setpoint=plc_status["setpoint"],
                process_residual=state["residual"],
                is_overflow=1 if state["is_overflow"] else 0,
                is_dry_run=1 if state["is_dry_run"] else 0,
                label=label,
                attack_type=attack_type,
            )

            # Store in DB and local buffer
            self.db.log_process_telemetry(event.to_dict())
            self.recent_telemetry.append(event.to_dict())
            self.total_samples_collected += 1

            # Sync with Modbus holding registers
            self.modbus_server.sync_from_process(
                tank_state=state,
                setpoint=plc_status["setpoint"],
                low_thresh=plc_status["low_threshold"],
                high_thresh=plc_status["high_threshold"],
                control_mode=plc_status["auto_mode"],
                alarm_state=plc_status["alarm_state"],
            )

            # Collect any recent Modbus server events into DB
            while self.modbus_server.event_buffer:
                trans = self.modbus_server.event_buffer.pop(0)
                mb_ev = ModbusEvent(
                    experiment_id=self.experiment_id,
                    timestamp=trans.timestamp,
                    client_ip=trans.client_ip,
                    function_code=trans.function_code,
                    function_name=trans.function_name,
                    register_address=trans.register_address,
                    register_name=trans.register_name,
                    value=trans.value,
                    is_write=1 if trans.is_write else 0,
                    request_rate=self.modbus_server.current_request_rate,
                )
                self.db.log_modbus_event(mb_ev.to_dict())
                self.recent_events.append(mb_ev.to_dict())

            return event

    def _loop(self) -> None:
        """Background sampling loop."""
        while self._is_running:
            t0 = time.time()
            self.sample_once()
            dt = time.time() - t0
            sleep_time = max(0.01, self.sample_interval_sec - dt)
            time.sleep(sleep_time)

    def start(self) -> None:
        """Starts collector background sampling thread."""
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._loop, name="DataCollectorThread", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stops collector background sampling thread."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None
