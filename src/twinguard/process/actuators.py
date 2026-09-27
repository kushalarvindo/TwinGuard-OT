"""
Virtual ICS Actuators for TwinGuard-OT.
Implements industrial pump and motorized control valve.
"""

import time
from typing import Dict, Any


class Pump:
    """
    Virtual Industrial Water Inflow Pump.
    Controlled by PLC output coils/registers or manual commands.
    """

    def __init__(self, name: str = "PUMP_01", rated_flow: float = 3.0) -> None:
        self.name = name
        self.rated_flow = rated_flow
        self._state: int = 0  # 0 = OFF, 1 = ON
        self.total_run_time_sec: float = 0.0
        self.cycle_count: int = 0
        self.last_state_change: float = time.time()
        self.fault: bool = False

    @property
    def is_on(self) -> bool:
        return self._state == 1

    @property
    def state(self) -> int:
        return self._state

    def turn_on(self) -> None:
        """Energizes the pump."""
        if self._state == 0:
            self._state = 1
            self.cycle_count += 1
            self.last_state_change = time.time()

    def turn_off(self) -> None:
        """De-energizes the pump."""
        if self._state == 1:
            self._state = 0
            self.last_state_change = time.time()

    def set_state(self, new_state: int) -> None:
        """Sets pump state: 1 for ON, 0 for OFF."""
        if new_state not in (0, 1):
            raise ValueError(f"Invalid pump state: {new_state}. Expected 0 or 1.")
        if new_state == 1:
            self.turn_on()
        else:
            self.turn_off()

    def update_runtime(self, dt: float) -> None:
        """Accumulates operational runtime if pump is currently running."""
        if self._state == 1:
            self.total_run_time_sec += dt

    def reset(self) -> None:
        """Resets actuator state to factory default."""
        self._state = 0
        self.total_run_time_sec = 0.0
        self.cycle_count = 0
        self.fault = False
        self.last_state_change = time.time()

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self._state,
            "is_on": self.is_on,
            "cycle_count": self.cycle_count,
            "total_run_time_sec": round(self.total_run_time_sec, 2),
            "fault": self.fault,
        }


class Valve:
    """
    Virtual Motorized Drain / Discharge Valve.
    Can operate digitally (0=CLOSED, 1=OPEN) or as an analog percentage (0.0 to 1.0).
    """

    def __init__(self, name: str = "VALVE_01", rated_flow: float = 1.2) -> None:
        self.name = name
        self.rated_flow = rated_flow
        self._position: float = 0.0  # 0.0 = CLOSED, 1.0 = FULLY OPEN
        self.last_state_change: float = time.time()

    @property
    def is_open(self) -> bool:
        return self._position > 0.0

    @property
    def state(self) -> int:
        """Returns digital state representation (1 if open, 0 if closed)."""
        return 1 if self._position > 0.0 else 0

    @property
    def position(self) -> float:
        return self._position

    def open(self) -> None:
        """Fully opens the valve."""
        self.set_position(1.0)

    def close(self) -> None:
        """Fully closes the valve."""
        self.set_position(0.0)

    def set_position(self, position: float) -> None:
        """Sets valve position from 0.0 (closed) to 1.0 (open)."""
        clamped = max(0.0, min(1.0, float(position)))
        if clamped != self._position:
            self._position = clamped
            self.last_state_change = time.time()

    def set_state(self, state: int) -> None:
        """Sets digital valve state: 1 (open) or 0 (closed)."""
        self.set_position(1.0 if state >= 1 else 0.0)

    def reset(self) -> None:
        """Resets valve to default closed position."""
        self._position = 0.0
        self.last_state_change = time.time()

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "position": round(self._position, 2),
            "is_open": self.is_open,
        }
