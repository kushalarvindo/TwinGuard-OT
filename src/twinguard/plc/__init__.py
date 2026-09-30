"""
Virtual Programmable Logic Controller (PLC) for TwinGuard-OT.
"""

from .control_logic import ProcessControlLogic, ControlDecision
from .plc import VirtualPLC

__all__ = ["ProcessControlLogic", "ControlDecision", "VirtualPLC"]
