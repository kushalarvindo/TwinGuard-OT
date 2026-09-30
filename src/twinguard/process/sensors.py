"""
Virtual Industrial Sensors for TwinGuard-OT.
Crucially distinguishes between TRUE PHYSICAL PROCESS STATE and OBSERVED SENSOR VALUE.
Allows simulation of sensor noise, calibration drift, and cyber spoofing attacks.
"""

import time
import numpy as np
from typing import Dict, Any, Optional


class BaseSensor:
    """Base class for virtual ICS sensors."""

    def __init__(self, name: str, unit: str, noise_std: float = 0.0) -> None:
        self.name = name
        self.unit = unit
        self.noise_std = noise_std
        self.last_true_value: float = 0.0
        self.last_measured_value: float = 0.0
        self.last_timestamp: float = time.time()
        
        # Cyber-attack injection parameters
        self._spoofed_value: Optional[float] = None
        self._bias: float = 0.0
        self._is_frozen: bool = False
        self._frozen_value: Optional[float] = None

    @property
    def is_spoofed(self) -> bool:
        return self._spoofed_value is not None or self._bias != 0.0 or self._is_frozen

    def set_spoof(self, value: float) -> None:
        """Injects a hard spoofed value override."""
        self._spoofed_value = float(value)

    def clear_spoof(self) -> None:
        """Restores normal sensor operation."""
        self._spoofed_value = None
        self._bias = 0.0
        self._is_frozen = False
        self._frozen_value = None

    def set_bias(self, bias: float) -> None:
        """Applies a persistent additive measurement bias."""
        self._bias = float(bias)

    def freeze(self) -> None:
        """Freezes the sensor measurement to its current observation."""
        self._is_frozen = True
        self._frozen_value = self.last_measured_value

    def unfreeze(self) -> None:
        """Unfreezes sensor output."""
        self._is_frozen = False
        self._frozen_value = None


class WaterLevelSensor(BaseSensor):
    """
    Virtual Continuous Tank Water Level Sensor (0.0% to 100.0%).
    Reads the true physical water level and yields the observed sensor reading.
    """

    def __init__(self, name: str = "LT_101", noise_std: float = 0.25) -> None:
        super().__init__(name=name, unit="%", noise_std=noise_std)

    def read(self, true_level: float) -> float:
        """
        Samples the physical level and computes the reported measurement.
        
        Args:
            true_level: True physical water level from the simulation.
            
        Returns:
            Observed/reported sensor reading.
        """
        self.last_true_value = float(true_level)
        self.last_timestamp = time.time()

        if self._spoofed_value is not None:
            # Attacker overwriting the sensor reading
            measured = self._spoofed_value
        elif self._is_frozen and self._frozen_value is not None:
            # Attacker or fault freezing the sensor reading
            measured = self._frozen_value
        else:
            # Normal physical observation with Gaussian sensor noise and optional calibration bias
            noise = np.random.normal(0.0, self.noise_std) if self.noise_std > 0 else 0.0
            measured = true_level + self._bias + noise

        # Clamp reported level to physical transmitter limits [0.0, 100.0]
        clamped_measured = max(0.0, min(100.0, measured))
        self.last_measured_value = clamped_measured
        return clamped_measured

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "true_value": round(self.last_true_value, 2),
            "measured_value": round(self.last_measured_value, 2),
            "residual": round(abs(self.last_true_value - self.last_measured_value), 2),
            "is_spoofed": self.is_spoofed,
            "noise_std": self.noise_std,
            "timestamp": self.last_timestamp,
        }


class FlowSensor(BaseSensor):
    """
    Virtual Flow Rate Meter (measures Inflow or Outflow).
    """

    def __init__(self, name: str = "FT_101", unit: str = "%/s", noise_std: float = 0.05) -> None:
        super().__init__(name=name, unit=unit, noise_std=noise_std)

    def read(self, true_flow: float) -> float:
        self.last_true_value = float(true_flow)
        self.last_timestamp = time.time()

        if self._spoofed_value is not None:
            measured = self._spoofed_value
        elif self._is_frozen and self._frozen_value is not None:
            measured = self._frozen_value
        else:
            noise = np.random.normal(0.0, self.noise_std) if self.noise_std > 0 else 0.0
            measured = max(0.0, true_flow + self._bias + noise)

        self.last_measured_value = measured
        return measured

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "true_flow": round(self.last_true_value, 3),
            "measured_flow": round(self.last_measured_value, 3),
            "is_spoofed": self.is_spoofed,
        }
