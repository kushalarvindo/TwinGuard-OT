"""
Event definitions and data transfer objects for TwinGuard-OT monitoring.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class ProcessEvent:
    experiment_id: str
    timestamp: float
    true_level: float
    sensor_level: float
    inflow_rate: float
    outflow_rate: float
    pump_state: int
    valve_state: int
    setpoint: float
    process_residual: float
    is_overflow: int
    is_dry_run: int
    label: int                  # 0 = Normal, 1 = Attack
    attack_type: str            # "normal", "sensor_spoofing", "unauthorized_write", etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModbusEvent:
    experiment_id: str
    timestamp: float
    client_ip: str
    function_code: int
    function_name: str
    register_address: int
    register_name: str
    value: int
    is_write: int
    request_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnomalyAlert:
    experiment_id: str
    timestamp: float
    engine: str                 # "RULE", "ML", "HYBRID"
    rule_id: Optional[str]
    rule_name: Optional[str]
    severity: str               # "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    is_anomaly: int             # 0 or 1
    anomaly_score: float
    cyber_anomaly: int          # 0 or 1
    physical_anomaly: int       # 0 or 1
    correlation_category: str   # "NORMAL", "CYBER_ONLY", "PROCESS_ONLY", "CYBER_PHYSICAL_ATTACK"
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
