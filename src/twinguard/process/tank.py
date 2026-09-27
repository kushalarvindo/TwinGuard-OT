"""
Complete Water Tank Digital Twin physical process module.
Integrates physics model, pump, valve, and level/flow sensors.
"""

import time
from typing import Dict, Any
from .physics import WaterTankPhysics
from .actuators import Pump, Valve
from .sensors import WaterLevelSensor, FlowSensor


class WaterTank:
    """
    Industrial Water Tank Process Simulator.
    Maintains the ground-truth physical state of the process while
    virtual sensors report measurements to the virtual PLC.
    """

    def __init__(
        self,
        capacity_liters: float = 1000.0,
        initial_level: float = 50.0,
        pump_inflow_rate: float = 3.0,
        gravity_outflow_rate: float = 1.2,
        leak_outflow_rate: float = 0.1,
        sensor_noise_std: float = 0.25,
        flow_noise_std: float = 0.05,
    ) -> None:
        self.capacity_liters = capacity_liters
        self.initial_level = initial_level
        self.current_level: float = initial_level
        
        # Sub-components
        self.physics = WaterTankPhysics(
            capacity_liters=capacity_liters,
            min_level=0.0,
            max_level=100.0,
            pump_inflow_rate=pump_inflow_rate,
            gravity_outflow_rate=gravity_outflow_rate,
            leak_outflow_rate=leak_outflow_rate,
        )
        self.pump = Pump(name="PUMP_101", rated_flow=pump_inflow_rate)
        self.valve = Valve(name="VALVE_101", rated_flow=gravity_outflow_rate)
        self.level_sensor = WaterLevelSensor(name="LT_101", noise_std=sensor_noise_std)
        self.inflow_sensor = FlowSensor(name="FIT_101", unit="%/s", noise_std=flow_noise_std)
        self.outflow_sensor = FlowSensor(name="FIT_102", unit="%/s", noise_std=flow_noise_std)

        # Operational telemetry
        self.current_inflow: float = 0.0
        self.current_outflow: float = 0.0
        self.is_overflow: bool = False
        self.is_dry_run: bool = False
        self.overflow_time_sec: float = 0.0
        self.dry_run_time_sec: float = 0.0
        self.simulated_time_sec: float = 0.0
        self.last_step_time: float = time.time()

        # Initial measurement
        self.level_sensor.read(self.current_level)
        self.inflow_sensor.read(0.0)
        self.outflow_sensor.read(0.0)

    def step(self, dt: float = 0.1) -> Dict[str, Any]:
        """
        Advances the physical process simulation by dt seconds.
        
        1. Updates physical level via differential mass-balance.
        2. Updates actuator runtime.
        3. Virtual sensors read physical state (adding noise or spoofing).
        4. Returns full telemetry state dictionary.
        """
        new_level, inflow, outflow, overflow, dry_run = self.physics.step(
            current_level=self.current_level,
            pump_state=self.pump.state,
            valve_state=self.valve.state,
            dt=dt,
        )

        self.current_level = new_level
        self.current_inflow = inflow
        self.current_outflow = outflow
        self.is_overflow = overflow
        self.is_dry_run = dry_run

        if overflow:
            self.overflow_time_sec += dt
        if dry_run:
            self.dry_run_time_sec += dt

        self.simulated_time_sec += dt
        self.pump.update_runtime(dt)

        # Update virtual sensors
        measured_level = self.level_sensor.read(self.current_level)
        measured_inflow = self.inflow_sensor.read(self.current_inflow)
        measured_outflow = self.outflow_sensor.read(self.current_outflow)

        self.last_step_time = time.time()

        return self.get_state()

    def set_pump(self, state: int) -> None:
        """Sets pump state (1=ON, 0=OFF)."""
        self.pump.set_state(state)

    def set_valve(self, state: int) -> None:
        """Sets valve state (1=OPEN, 0=CLOSED)."""
        self.valve.set_state(state)

    def get_state(self) -> Dict[str, Any]:
        """Returns instantaneous snapshot of physical and sensor states."""
        return {
            "timestamp": time.time(),
            "simulated_time_sec": round(self.simulated_time_sec, 2),
            "true_level": round(self.current_level, 2),
            "sensor_level": round(self.level_sensor.last_measured_value, 2),
            "residual": round(abs(self.current_level - self.level_sensor.last_measured_value), 2),
            "pump_state": self.pump.state,
            "valve_state": self.valve.state,
            "true_inflow": round(self.current_inflow, 2),
            "sensor_inflow": round(self.inflow_sensor.last_measured_value, 2),
            "true_outflow": round(self.current_outflow, 2),
            "sensor_outflow": round(self.outflow_sensor.last_measured_value, 2),
            "is_overflow": self.is_overflow,
            "is_dry_run": self.is_dry_run,
            "overflow_time_sec": round(self.overflow_time_sec, 2),
            "sensor_spoofed": self.level_sensor.is_spoofed,
        }

    def reset(self, initial_level: float | None = None) -> None:
        """Resets the process to its initial baseline condition."""
        if initial_level is not None:
            self.initial_level = initial_level
        self.current_level = self.initial_level
        self.pump.reset()
        self.valve.reset()
        self.level_sensor.clear_spoof()
        self.inflow_sensor.clear_spoof()
        self.outflow_sensor.clear_spoof()
        self.current_inflow = 0.0
        self.current_outflow = 0.0
        self.is_overflow = False
        self.is_dry_run = False
        self.overflow_time_sec = 0.0
        self.dry_run_time_sec = 0.0
        self.simulated_time_sec = 0.0
        self.level_sensor.read(self.current_level)
