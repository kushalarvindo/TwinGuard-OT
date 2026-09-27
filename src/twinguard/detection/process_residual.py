"""
Digital Twin Physical Reference Model and Residual Calculator.
Maintains a real-time shadow physics simulation predicting the expected state.
Computes the physical residual r(t) = |y_observed(t) - y_expected(t)|.
"""

from typing import Dict, Any, Tuple
from twinguard.process.physics import WaterTankPhysics


class DigitalTwinShadowModel:
    """
    Parallel software reference model representing expected hydrodynamic process behavior.
    Acts as the golden reference for detecting process anomalies and sensor spoofing.
    """

    def __init__(
        self,
        initial_level: float = 50.0,
        pump_inflow_rate: float = 3.0,
        gravity_outflow_rate: float = 1.2,
        leak_outflow_rate: float = 0.1,
        residual_threshold: float = 10.0,
    ) -> None:
        self.physics = WaterTankPhysics(
            capacity_liters=1000.0,
            min_level=0.0,
            max_level=100.0,
            pump_inflow_rate=pump_inflow_rate,
            gravity_outflow_rate=gravity_outflow_rate,
            leak_outflow_rate=leak_outflow_rate,
        )
        self.expected_level: float = initial_level
        self.residual_threshold = residual_threshold
        self.current_residual: float = 0.0

    def step(
        self,
        pump_command: int,
        valve_command: int,
        dt: float,
        observed_sensor_level: float,
    ) -> Tuple[float, float, bool]:
        """
        Advances the expected Digital Twin physics model by dt and computes the residual.
        
        Args:
            pump_command: Actuator pump command (0 or 1).
            valve_command: Actuator valve command (0 or 1).
            dt: Time step duration in seconds.
            observed_sensor_level: Current reported water level from sensor (%).
            
        Returns:
            Tuple of (expected_level, residual, is_anomaly_flag).
        """
        # Step shadow physics
        new_expected, _, _, _, _ = self.physics.step(
            current_level=self.expected_level,
            pump_state=pump_command,
            valve_state=valve_command,
            dt=dt,
        )
        self.expected_level = new_expected

        # Calculate physical residual
        self.current_residual = round(abs(observed_sensor_level - self.expected_level), 2)
        is_anomaly = self.current_residual > self.residual_threshold

        return self.expected_level, self.current_residual, is_anomaly

    def reset(self, initial_level: float = 50.0) -> None:
        """Resets the shadow reference model to known initial state."""
        self.expected_level = initial_level
        self.current_residual = 0.0
