"""
Virtual Programmable Logic Controller (PLC) for TwinGuard-OT.
Executes periodic control scans, maintains setpoints, and governs actuators.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from .control_logic import ProcessControlLogic, ControlDecision
from twinguard.process.tank import WaterTank


class VirtualPLC:
    """
    Virtual PLC executing industrial control loops on the simulated water tank.
    
    Can operate directly with the WaterTank simulation instance or synchronize
    with a Modbus TCP datastore.
    """

    def __init__(
        self,
        tank: WaterTank,
        cycle_interval_sec: float = 0.2,
        default_setpoint: float = 70.0,
        low_threshold: float = 30.0,
        high_threshold: float = 80.0,
        emergency_low: float = 10.0,
        emergency_high: float = 95.0,
        auto_mode: int = 1,
    ) -> None:
        self.tank = tank
        self.cycle_interval_sec = cycle_interval_sec
        self.auto_mode = auto_mode
        self.logic = ProcessControlLogic(
            setpoint=default_setpoint,
            low_threshold=low_threshold,
            high_threshold=high_threshold,
            emergency_low=emergency_low,
            emergency_high=emergency_high,
        )

        self.last_decision: Optional[ControlDecision] = None
        self.cycle_count: int = 0
        self.event_log: List[Dict[str, Any]] = []
        self._is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def scan_once(self) -> ControlDecision:
        """
        Executes a single PLC scan cycle:
        1. Read sensor inputs.
        2. Evaluate control logic.
        3. Write actuator outputs.
        4. Record operational event.
        """
        with self._lock:
            sensor_level = self.tank.level_sensor.last_measured_value
            current_pump = self.tank.pump.state
            current_valve = self.tank.valve.state

            decision = self.logic.evaluate(
                sensor_level=sensor_level,
                current_pump=current_pump,
                current_valve=current_valve,
                auto_mode=self.auto_mode,
            )

            # Enforce actuator commands on the physical process
            if decision.target_pump != current_pump:
                self.tank.set_pump(decision.target_pump)
            if decision.target_valve != current_valve:
                self.tank.set_valve(decision.target_valve)

            self.last_decision = decision
            self.cycle_count += 1

            # Log events when changes or alarms occur
            if decision.alarm_state > 0 or decision.target_pump != current_pump or decision.target_valve != current_valve:
                event = {
                    "timestamp": time.time(),
                    "cycle": self.cycle_count,
                    "sensor_level": round(sensor_level, 2),
                    "pump": decision.target_pump,
                    "valve": decision.target_valve,
                    "alarm": decision.alarm_state,
                    "reasons": decision.reasons,
                }
                self.event_log.append(event)
                # Keep event log size bounded
                if len(self.event_log) > 500:
                    self.event_log.pop(0)

            return decision

    def _run_loop(self) -> None:
        """Continuous background execution loop."""
        while self._is_running:
            start_t = time.time()
            self.scan_once()
            elapsed = time.time() - start_t
            sleep_time = max(0.01, self.cycle_interval_sec - elapsed)
            time.sleep(sleep_time)

    def start(self) -> None:
        """Starts PLC continuous scan thread."""
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._run_loop, name="VirtualPLCThread", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stops PLC continuous scan thread."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

    def set_mode(self, auto_mode: int) -> None:
        """Sets PLC operating mode: 1 = AUTO, 0 = MANUAL."""
        with self._lock:
            self.auto_mode = 1 if auto_mode >= 1 else 0

    def set_setpoint(self, setpoint: float) -> None:
        """Sets desired target setpoint."""
        with self._lock:
            self.logic.update_thresholds(setpoint=setpoint)

    def set_thresholds(self, low: float, high: float) -> None:
        """Updates hysteresis thresholds."""
        with self._lock:
            self.logic.update_thresholds(low_threshold=low, high_threshold=high)

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive PLC operational status."""
        with self._lock:
            return {
                "cycle_count": self.cycle_count,
                "auto_mode": self.auto_mode,
                "setpoint": self.logic.setpoint,
                "low_threshold": self.logic.low_threshold,
                "high_threshold": self.logic.high_threshold,
                "alarm_state": self.last_decision.alarm_state if self.last_decision else 0,
                "last_reasons": self.last_decision.reasons if self.last_decision else [],
            }
