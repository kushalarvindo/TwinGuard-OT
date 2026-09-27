"""
Database module for TwinGuard-OT.
Provides SQLite storage for telemetry, Modbus events, detections, and evaluation results.
"""

from .db import DatabaseManager

__all__ = ["DatabaseManager"]
