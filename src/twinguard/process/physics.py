"""
Deterministic hydrodynamic physics model for a continuous-level water tank.
Governed by conservation of mass:
    dh/dt = (Q_in - Q_out) / Area
"""

from typing import Tuple


class WaterTankPhysics:
    """
    Simulates the true hydrodynamic behavior of the industrial water tank.
    
    Attributes:
        capacity_liters: Total tank fluid capacity (L).
        min_level: Minimum physical level (0.0%).
        max_level: Maximum physical capacity level (100.0%).
        pump_inflow_rate: Nominal filling rate (% per second when pump is ON).
        gravity_outflow_rate: Nominal draining rate (% per second when outlet valve is OPEN).
        leak_outflow_rate: Baseline passive loss rate (% per second).
    """

    def __init__(
        self,
        capacity_liters: float = 1000.0,
        min_level: float = 0.0,
        max_level: float = 100.0,
        pump_inflow_rate: float = 3.0,
        gravity_outflow_rate: float = 1.2,
        leak_outflow_rate: float = 0.1,
    ) -> None:
        self.capacity_liters = capacity_liters
        self.min_level = min_level
        self.max_level = max_level
        self.pump_inflow_rate = pump_inflow_rate
        self.gravity_outflow_rate = gravity_outflow_rate
        self.leak_outflow_rate = leak_outflow_rate

    def calculate_flows(self, pump_state: int, valve_state: int, current_level: float) -> Tuple[float, float]:
        """
        Calculates instantaneous physical inflow and outflow rates.
        
        Args:
            pump_state: 1 if pump is energized, 0 if off.
            valve_state: 1 if valve is open (or float 0.0 to 1.0), 0 if closed.
            current_level: Current water level in percentage.
            
        Returns:
            Tuple of (inflow_rate, outflow_rate) in % per second.
        """
        # Inflow exists only if pump is ON
        inflow = self.pump_inflow_rate if pump_state == 1 else 0.0

        # Outflow occurs if valve is OPEN (plus tiny gravity pressure scaling with height)
        # Torricelli-like influence: outflow increases slightly with head pressure
        head_factor = max(0.0, current_level / 100.0)
        valve_flow = (self.gravity_outflow_rate * float(valve_state)) * (0.8 + 0.4 * head_factor)
        
        # Leakage occurs only if water is present in tank
        passive_loss = self.leak_outflow_rate if current_level > 0.0 else 0.0
        
        outflow = valve_flow + passive_loss
        return inflow, outflow

    def step(
        self,
        current_level: float,
        pump_state: int,
        valve_state: int,
        dt: float,
    ) -> Tuple[float, float, float, bool, bool]:
        """
        Advances the physical simulation by dt seconds.
        
        Returns:
            Tuple of (new_level, inflow, outflow, is_overflow, is_dry_run).
        """
        inflow, outflow = self.calculate_flows(pump_state, valve_state, current_level)
        net_flow_rate = inflow - outflow
        delta_h = net_flow_rate * dt

        raw_level = current_level + delta_h

        is_overflow = raw_level > self.max_level
        is_dry_run = raw_level < self.min_level

        # Clamp to physical boundaries
        clamped_level = max(self.min_level, min(self.max_level, raw_level))

        return clamped_level, inflow, outflow, is_overflow, is_dry_run
