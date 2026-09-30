"""
Attack simulation suite for TwinGuard-OT.
Strictly isolated to local virtual simulation environment (127.0.0.1).
"""

from .base import BaseAttack, LocalEnvironmentSecurityError
from .unauthorized_write import UnauthorizedWriteAttack
from .sensor_spoofing import SensorSpoofingAttack
from .replay import ReplayAttack
from .command_flood import CommandFloodAttack
from .setpoint_manipulation import SetpointManipulationAttack

__all__ = [
    "BaseAttack",
    "LocalEnvironmentSecurityError",
    "UnauthorizedWriteAttack",
    "SensorSpoofingAttack",
    "ReplayAttack",
    "CommandFloodAttack",
    "SetpointManipulationAttack",
]
