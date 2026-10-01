"""
Physics subsystem alias module for TwinGuard-OT.
"""
from twinguard.process.tank import WaterTank
from twinguard.process.physics import WaterTankPhysics
from twinguard.process.actuators import Pump, Valve
from twinguard.process.sensors import WaterLevelSensor, FlowSensor

__all__ = ["WaterTank", "WaterTankPhysics", "Pump", "Valve", "WaterLevelSensor", "FlowSensor"]
