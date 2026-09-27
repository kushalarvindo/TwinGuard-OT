"""
Cyber-Physical Correlation Engine for TwinGuard-OT.
Unifies rule-based findings, machine-learning outlier scores, and Digital Twin physical residuals.
Classifies incidents into NORMAL, CYBER_ONLY, PROCESS_ONLY, or CYBER_PHYSICAL_ATTACK.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .rules import RuleResult


@dataclass
class CorrelatedDetection:
    """Consolidated detection outcome for a single monitoring window."""
    is_anomaly: bool
    category: str              # "NORMAL", "CYBER_ONLY", "PROCESS_ONLY", "CYBER_PHYSICAL_ATTACK"
    severity: str              # "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    cyber_anomaly: bool
    physical_anomaly: bool
    ml_anomaly: bool
    anomaly_score: float
    primary_rule: Optional[str]
    explanation: str
    active_rules: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": 1 if self.is_anomaly else 0,
            "category": self.category,
            "severity": self.severity,
            "cyber_anomaly": 1 if self.cyber_anomaly else 0,
            "physical_anomaly": 1 if self.physical_anomaly else 0,
            "ml_anomaly": 1 if self.ml_anomaly else 0,
            "anomaly_score": round(self.anomaly_score, 4),
            "primary_rule": self.primary_rule or "NONE",
            "explanation": self.explanation,
            "active_rules": self.active_rules,
        }


class CyberPhysicalCorrelator:
    """
    Context-aware correlation engine that bridges the cyber domain and physical thermodynamics.
    """

    def correlate(
        self,
        rule_results: List[RuleResult],
        ml_is_anomaly: bool,
        ml_score: float,
        features: Dict[str, Any],
    ) -> CorrelatedDetection:
        """
        Synthesizes rule triggers, ML outputs, and physical residuals into an explainable assessment.
        """
        active_rules = [r for r in rule_results if r.triggered]

        cyber_rules = [r for r in active_rules if r.category == "CYBER"]
        physical_rules = [r for r in active_rules if r.category == "PHYSICAL"]
        hybrid_rules = [r for r in active_rules if r.category == "HYBRID"]

        has_cyber = len(cyber_rules) > 0
        has_physical = len(physical_rules) > 0
        has_hybrid = len(hybrid_rules) > 0

        # If residual rule (R002) triggered, it represents physical mismatch caused by cyber manipulation
        if any(r.rule_id == "R002" for r in active_rules):
            has_physical = True
            has_cyber = True

        # ML detection consideration
        if ml_is_anomaly:
            # Check if ML anomaly is driven by cyber or physical features
            req_rate = float(features.get("request_rate", 0.0))
            residual = float(features.get("process_residual", 0.0))
            if req_rate > 20.0:
                has_cyber = True
            if residual > 8.0:
                has_physical = True

        # Determine overall classification
        is_anomaly = has_cyber or has_physical or has_hybrid or ml_is_anomaly
        active_rule_ids = [r.rule_id for r in active_rules]

        if not is_anomaly:
            return CorrelatedDetection(
                is_anomaly=False,
                category="NORMAL",
                severity="INFO",
                cyber_anomaly=False,
                physical_anomaly=False,
                ml_anomaly=False,
                anomaly_score=ml_score,
                primary_rule=None,
                explanation="Process and Modbus communication operating within normal expected baseline.",
                active_rules=[],
            )

        # Classify the incident
        if (has_cyber and has_physical) or has_hybrid:
            category = "CYBER_PHYSICAL_ATTACK"
            severity = "CRITICAL"
            primary = active_rules[0].rule_id if active_rules else "ML_CORRELATED"
            reasons = [r.explanation for r in active_rules]
            explanation = (
                f"CYBER-PHYSICAL INCIDENT: Suspicious cyber activity coincides with physical process deviation. "
                f"Residual = {features.get('process_residual', 0.0):.1f}%. "
                f"Rules triggered: {', '.join(active_rule_ids)}. Details: {' '.join(reasons[:2])}"
            )
        elif has_cyber:
            category = "CYBER_ONLY"
            severity = "MEDIUM"
            primary = cyber_rules[0].rule_id if cyber_rules else "ML_NETWORK"
            explanation = (
                f"CYBER-ONLY ANOMALY: Abnormal Modbus network activity detected without physical process distortion. "
                f"Request Rate = {features.get('request_rate', 0.0):.1f} req/s."
            )
        elif has_physical:
            category = "PROCESS_ONLY"
            severity = "HIGH"
            primary = physical_rules[0].rule_id if physical_rules else "ML_PROCESS"
            explanation = (
                f"PROCESS-ONLY ANOMALY: Physical process discrepancy observed while network traffic appears standard. "
                f"Level Rate = {features.get('level_rate', 0.0):+.2f}%/s."
            )
        else:
            category = "CYBER_PHYSICAL_ATTACK"
            severity = "MEDIUM"
            primary = "ML_ISOLATION"
            explanation = f"ML Isolation Forest flagged multidimensional anomaly (score={ml_score:.3f})."

        return CorrelatedDetection(
            is_anomaly=True,
            category=category,
            severity=severity,
            cyber_anomaly=has_cyber,
            physical_anomaly=has_physical,
            ml_anomaly=ml_is_anomaly,
            anomaly_score=ml_score,
            primary_rule=primary,
            explanation=explanation,
            active_rules=active_rule_ids,
        )
