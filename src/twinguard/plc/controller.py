"""
Virtual PLC and Controller alias module for TwinGuard-OT.
"""
from twinguard.plc.plc import VirtualPLC
from twinguard.plc.control_logic import ProcessControlLogic, ControlDecision

__all__ = ["VirtualPLC", "ProcessControlLogic", "ControlDecision"]
