"""
Deterministic Industrial Control Logic for Water Tank Virtual PLC.
Implements hysteresis control, setpoint tracking, and safety interlocks.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ControlDecision:
    """Represents the output decision of a PLC scan cycle."""
    target_pump: int          # 0 = OFF, 1 = ON
    target_valve: int         # 0 = CLOSED, 1 = OPEN
    alarm_state: int          # 0 = Normal, 1 = Low Level, 2 = High Level, 3 = Safety Interlock
    reasons: List[str]        # Explainable engineering decisions taken this scan


class ProcessControlLogic:
    """
    PLC Ladder Logic / Structured Text equivalent in Python.
    Controls tank filling and discharge based on sensor inputs and setpoints.
    """

    def __init__(
        self,
        setpoint: float = 70.0,
        low_threshold: float = 30.0,
        high_threshold: float = 80.0,
        emergency_low: float = 10.0,
        emergency_high: float = 95.0,
    ) -> None:
        self.setpoint = float(setpoint)
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)
        self.emergency_low = float(emergency_low)
        self.emergency_high = float(emergency_high)

    def update_thresholds(
        self,
        setpoint: float | None = None,
        low_threshold: float | None = None,
        high_threshold: float | None = None,
    ) -> None:
        """Dynamically updates operating setpoints and hysteresis bands."""
        if setpoint is not None:
            self.setpoint = float(setpoint)
        if low_threshold is not None:
            self.low_threshold = float(low_threshold)
        if high_threshold is not None:
            self.high_threshold = float(high_threshold)

    def evaluate(
        self,
        sensor_level: float,
        current_pump: int,
        current_valve: int,
        auto_mode: int = 1,
    ) -> ControlDecision:
        """
        Executes one scan of the control logic.
        
        Args:
            sensor_level: Observed water level from level transmitter (%).
            current_pump: Current pump actuator state (0 or 1).
            current_valve: Current valve actuator state (0 or 1).
            auto_mode: 1 for automatic PLC control, 0 for manual bypass.
            
        Returns:
            ControlDecision with target actuators, alarm state, and reasons.
        """
        reasons: List[str] = []
        target_pump = current_pump
        target_valve = current_valve
        alarm_state = 0  # Normal

        # 1. Safety Interlocks (Always evaluated regardless of mode)
        if sensor_level >= self.emergency_high:
            alarm_state = 3  # Emergency High Safety Interlock
            target_pump = 0  # Forced pump cutoff to prevent physical tank overflow
            target_valve = 1 # Open discharge to relieve pressure
            reasons.append(
                f"SAFETY INTERLOCK: Sensor level ({sensor_level:.1f}%) >= Emergency High ({self.emergency_high:.1f}%). "
                "Forced pump OFF, drain valve OPEN."
            )
            return ControlDecision(target_pump, target_valve, alarm_state, reasons)

        if sensor_level <= self.emergency_low:
            alarm_state = 1  # Low-Low Alarm
            reasons.append(
                f"ALARM: Sensor level ({sensor_level:.1f}%) <= Emergency Low ({self.emergency_low:.1f}%)."
            )

        # 2. Automatic Control Mode (Hysteresis setpoint maintenance)
        if auto_mode == 1:
            if sensor_level < self.low_threshold:
                # Tank level is too low: turn pump ON, close valve to replenish
                target_pump = 1
                target_valve = 0
                reasons.append(
                    f"AUTO: Level ({sensor_level:.1f}%) < Low Threshold ({self.low_threshold:.1f}%). "
                    "Commanded Pump ON, Valve CLOSED."
                )
            elif sensor_level >= self.high_threshold:
                # Tank level reached high limit: turn pump OFF, open valve to discharge
                target_pump = 0
                target_valve = 1
                alarm_state = max(alarm_state, 2)  # High warning
                reasons.append(
                    f"AUTO: Level ({sensor_level:.1f}%) >= High Threshold ({self.high_threshold:.1f}%). "
                    "Commanded Pump OFF, Valve OPEN."
                )
            else:
                # Within hysteresis band: maintain current running state
                reasons.append(
                    f"AUTO: Level ({sensor_level:.1f}%) in hysteresis band [{self.low_threshold:.1f}%, {self.high_threshold:.1f}%]. "
                    f"Maintained Pump={target_pump}, Valve={target_valve}."
                )
        else:
            # Manual Mode
            reasons.append(f"MANUAL MODE: Actuator states set by operator. Pump={target_pump}, Valve={target_valve}.")

        return ControlDecision(target_pump, target_valve, alarm_state, reasons)
