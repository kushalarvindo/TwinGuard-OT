"""
Process-Aware Rule-Based ICS Detection Engine.
Evaluates deterministic engineering safety rules against cyber and physical parameters.
Returns rich, human-explainable detection explanations.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class RuleResult:
    """Outcome of evaluating an individual detection rule."""
    rule_id: str
    rule_name: str
    triggered: bool
    severity: str        # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    category: str        # "CYBER", "PHYSICAL", "HYBRID"
    explanation: str
    metric_value: float
    threshold_value: float


class RuleBasedDetector:
    """
    Deterministic domain rule engine for water tank ICS monitoring.
    """

    def __init__(
        self,
        residual_threshold: float = 10.0,
        max_level_rate: float = 5.0,
        high_threshold: float = 80.0,
        low_threshold: float = 30.0,
        min_safe_setpoint: float = 15.0,
        max_safe_setpoint: float = 90.0,
        flood_request_rate: float = 30.0,
    ) -> None:
        self.residual_threshold = residual_threshold
        self.max_level_rate = max_level_rate
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.min_safe_setpoint = min_safe_setpoint
        self.max_safe_setpoint = max_safe_setpoint
        self.flood_request_rate = flood_request_rate

        self._consecutive_static_sensor_counts: int = 0
        self._last_sensor_level: Optional[float] = None

    def evaluate(self, features: Dict[str, Any]) -> List[RuleResult]:
        """
        Evaluates all rules on the given feature vector.
        Returns list of all evaluated rules (both triggered and non-triggered).
        """
        results: List[RuleResult] = []

        sensor_level = float(features.get("sensor_level", 50.0))
        level_rate = float(features.get("level_rate", 0.0))
        residual = float(features.get("process_residual", 0.0))
        pump = int(features.get("pump_state", 0))
        setpoint = float(features.get("setpoint", 70.0))
        request_rate = float(features.get("request_rate", 0.0))

        # -------------------------------------------------------------
        # R001: UNEXPECTED_PUMP_ACTIVATION (Process Anomaly)
        # -------------------------------------------------------------
        r1_triggered = (pump == 1) and (sensor_level >= self.high_threshold)
        results.append(RuleResult(
            rule_id="R001",
            rule_name="UNEXPECTED_PUMP_ACTIVATION",
            triggered=r1_triggered,
            severity="HIGH" if r1_triggered else "INFO",
            category="PHYSICAL",
            explanation=(
                f"Pump energized ({pump}) while reported water level ({sensor_level:.1f}%) "
                f"exceeds high threshold ({self.high_threshold:.1f}%)."
            ) if r1_triggered else "Pump state consistent with water level.",
            metric_value=sensor_level if pump == 1 else 0.0,
            threshold_value=self.high_threshold,
        ))

        # -------------------------------------------------------------
        # R002: PROCESS_RESIDUAL_VIOLATION (Digital Twin Residual Anomaly)
        # -------------------------------------------------------------
        r2_triggered = residual > self.residual_threshold
        results.append(RuleResult(
            rule_id="R002",
            rule_name="PROCESS_RESIDUAL_VIOLATION",
            triggered=r2_triggered,
            severity="CRITICAL" if r2_triggered else "INFO",
            category="HYBRID",
            explanation=(
                f"Process residual discrepancy ({residual:.1f}%) exceeds safety limit ({self.residual_threshold:.1f}%). "
                "Reported sensor decouples from Digital Twin reference physics."
            ) if r2_triggered else "Process residual within normal tolerance.",
            metric_value=residual,
            threshold_value=self.residual_threshold,
        ))

        # -------------------------------------------------------------
        # R003: IMPOSSIBLE_LEVEL_RATE (Physical Rate of Change Violation)
        # -------------------------------------------------------------
        r3_triggered = abs(level_rate) > self.max_level_rate
        results.append(RuleResult(
            rule_id="R003",
            rule_name="IMPOSSIBLE_LEVEL_RATE",
            triggered=r3_triggered,
            severity="HIGH" if r3_triggered else "INFO",
            category="PHYSICAL",
            explanation=(
                f"Rate of level change ({level_rate:+.2f}%/s) violates maximum physical pump capacity ({self.max_level_rate:.2f}%/s). "
                "Indicates sensor spoofing or synthetic telemetry injection."
            ) if r3_triggered else "Level change rate complies with physical limits.",
            metric_value=abs(level_rate),
            threshold_value=self.max_level_rate,
        ))

        # -------------------------------------------------------------
        # R004: HIGH_REQUEST_RATE_FLOOD (Network / Cyber Anomaly)
        # -------------------------------------------------------------
        r4_triggered = request_rate > self.flood_request_rate
        results.append(RuleResult(
            rule_id="R004",
            rule_name="HIGH_REQUEST_RATE_FLOOD",
            triggered=r4_triggered,
            severity="MEDIUM" if r4_triggered else "INFO",
            category="CYBER",
            explanation=(
                f"Abnormally high Modbus traffic ({request_rate:.1f} req/s) exceeds threshold ({self.flood_request_rate:.1f} req/s). "
                "Suspected command flood or Denial of Service attempt."
            ) if r4_triggered else "Modbus request rate within normal boundaries.",
            metric_value=request_rate,
            threshold_value=self.flood_request_rate,
        ))

        # -------------------------------------------------------------
        # R005: ABNORMAL_SETPOINT_MANIPULATION (Cyber-Physical Configuration Anomaly)
        # -------------------------------------------------------------
        r5_triggered = (setpoint < self.min_safe_setpoint) or (setpoint > self.max_safe_setpoint)
        results.append(RuleResult(
            rule_id="R005",
            rule_name="ABNORMAL_SETPOINT_MANIPULATION",
            triggered=r5_triggered,
            severity="HIGH" if r5_triggered else "INFO",
            category="HYBRID",
            explanation=(
                f"Operational setpoint ({setpoint:.1f}%) is outside configured safety envelope "
                f"[{self.min_safe_setpoint:.1f}%, {self.max_safe_setpoint:.1f}%]."
            ) if r5_triggered else "Operating setpoint within safety envelope.",
            metric_value=setpoint,
            threshold_value=self.max_safe_setpoint if setpoint > self.max_safe_setpoint else self.min_safe_setpoint,
        ))

        # -------------------------------------------------------------
        # R006: FROZEN_SENSOR_DETECTION (Sensor Stagnation while Actuator Active)
        # -------------------------------------------------------------
        if self._last_sensor_level is not None:
            if abs(sensor_level - self._last_sensor_level) < 0.005 and pump == 1:
                self._consecutive_static_sensor_counts += 1
            else:
                self._consecutive_static_sensor_counts = 0
        self._last_sensor_level = sensor_level

        r6_triggered = self._consecutive_static_sensor_counts >= 15  # ~1.5s at 10Hz
        results.append(RuleResult(
            rule_id="R006",
            rule_name="FROZEN_SENSOR_DETECTION",
            triggered=r6_triggered,
            severity="MEDIUM" if r6_triggered else "INFO",
            category="PHYSICAL",
            explanation=(
                f"Sensor reading statically frozen at {sensor_level:.1f}% for {self._consecutive_static_sensor_counts} consecutive scans "
                "despite active pump inflow."
            ) if r6_triggered else "Sensor dynamics consistent with active actuators.",
            metric_value=float(self._consecutive_static_sensor_counts),
            threshold_value=15.0,
        ))

        return results

    def get_active_alerts(self, features: Dict[str, Any]) -> List[RuleResult]:
        """Returns only the rules that triggered an anomaly."""
        return [r for r in self.evaluate(features) if r.triggered]
