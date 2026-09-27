"""
Feature extraction pipeline for Process-Aware ICS Anomaly Detection.
Processes physical telemetry and network traffic variables into numerical feature vectors.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class FeatureExtractor:
    """
    Extracts informative cyber-physical features for Machine Learning
    and Process-Aware Rule Evaluation.
    """

    FEATURE_NAMES: List[str] = [
        "sensor_level",
        "level_rate",
        "process_residual",
        "inflow_rate",
        "outflow_rate",
        "net_flow",
        "pump_state",
        "valve_state",
        "setpoint",
        "setpoint_error",
        "request_rate",
        "actuator_inconsistency",
        "physical_impossibility",
    ]

    def __init__(
        self,
        high_threshold: float = 80.0,
        max_physical_rate: float = 5.0,
    ) -> None:
        self.high_threshold = high_threshold
        self.max_physical_rate = max_physical_rate
        self._last_sample: Optional[Dict[str, Any]] = None

    def get_feature_names(self) -> List[str]:
        return list(self.FEATURE_NAMES)

    def extract_from_row(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Extracts feature dictionary from an instantaneous sample and its predecessor.
        """
        prev = previous or self._last_sample

        sensor_level = float(current.get("sensor_level", 50.0))
        true_level = float(current.get("true_level", sensor_level))
        residual = float(current.get("process_residual", abs(true_level - sensor_level)))
        inflow = float(current.get("inflow_rate", 0.0))
        outflow = float(current.get("outflow_rate", 0.0))
        pump = float(current.get("pump_state", 0))
        valve = float(current.get("valve_state", 0))
        setpoint = float(current.get("setpoint", 70.0))
        request_rate = float(current.get("request_rate", 0.0))

        # 1. Rate of level change
        level_rate = 0.0
        if prev is not None:
            dt = max(0.01, float(current.get("timestamp", 0.0)) - float(prev.get("timestamp", 0.0)))
            d_level = sensor_level - float(prev.get("sensor_level", sensor_level))
            level_rate = round(d_level / dt, 3)

        # 2. Net Flow
        net_flow = round(inflow - outflow, 3)

        # 3. Setpoint Error
        setpoint_error = round(sensor_level - setpoint, 2)

        # 4. Actuator Inconsistency: Pump ON when tank level already high
        actuator_inconsistency = 1.0 if (pump == 1.0 and sensor_level >= self.high_threshold) else 0.0

        # 5. Physical Impossibility: Level jump exceeds max pump capacity
        physical_impossibility = 1.0 if abs(level_rate) > self.max_physical_rate else 0.0

        self._last_sample = current

        return {
            "sensor_level": sensor_level,
            "level_rate": level_rate,
            "process_residual": residual,
            "inflow_rate": inflow,
            "outflow_rate": outflow,
            "net_flow": net_flow,
            "pump_state": pump,
            "valve_state": valve,
            "setpoint": setpoint,
            "setpoint_error": setpoint_error,
            "request_rate": request_rate,
            "actuator_inconsistency": actuator_inconsistency,
            "physical_impossibility": physical_impossibility,
        }

    def extract_from_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts features across an entire historical DataFrame.
        Computes rolling derivatives and temporal differences cleanly.
        """
        if df.empty:
            return pd.DataFrame(columns=self.FEATURE_NAMES)

        out = pd.DataFrame(index=df.index)

        out["sensor_level"] = df["sensor_level"].astype(float)
        
        # Calculate level rate: d(sensor_level) / dt
        dt = df["timestamp"].diff().fillna(0.1)
        dt = dt.apply(lambda x: 0.1 if x <= 0 else x)
        out["level_rate"] = (df["sensor_level"].diff().fillna(0.0) / dt).round(3)

        # Residual
        if "process_residual" in df.columns:
            out["process_residual"] = df["process_residual"].astype(float)
        elif "true_level" in df.columns:
            out["process_residual"] = (df["true_level"] - df["sensor_level"]).abs().round(2)
        else:
            out["process_residual"] = 0.0

        out["inflow_rate"] = df.get("inflow_rate", 0.0).astype(float)
        out["outflow_rate"] = df.get("outflow_rate", 0.0).astype(float)
        out["net_flow"] = (out["inflow_rate"] - out["outflow_rate"]).round(3)
        out["pump_state"] = df.get("pump_state", 0).astype(float)
        out["valve_state"] = df.get("valve_state", 0).astype(float)
        out["setpoint"] = df.get("setpoint", 70.0).astype(float)
        out["setpoint_error"] = (out["sensor_level"] - out["setpoint"]).round(2)
        out["request_rate"] = df.get("request_rate", 0.0).astype(float)

        out["actuator_inconsistency"] = (
            (out["pump_state"] == 1.0) & (out["sensor_level"] >= self.high_threshold)
        ).astype(float)

        out["physical_impossibility"] = (out["level_rate"].abs() > self.max_physical_rate).astype(float)

        # Preserve label if present
        if "label" in df.columns:
            out["label"] = df["label"].astype(int)
        if "attack_type" in df.columns:
            out["attack_type"] = df["attack_type"]

        return out[self.FEATURE_NAMES + ([col for col in ["label", "attack_type"] if col in out.columns])]
