"""
Machine Learning Anomaly Detection using Isolation Forest (and optional One-Class SVM).
Trained on baseline normal operational telemetry.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

from twinguard.features.extractor import FeatureExtractor


class IsolationForestDetector:
    """
    Unsupervised ML Anomaly Detector using Isolation Forest.
    Learns normal cyber-physical operational manifold and isolates out-of-distribution events.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.03,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.scaler = StandardScaler()
        self.is_trained: bool = False
        self.feature_names: List[str] = FeatureExtractor.FEATURE_NAMES
        self.training_metadata: Dict[str, Any] = {}

    def fit(self, df_or_array: pd.DataFrame | np.ndarray) -> Dict[str, Any]:
        """
        Trains Isolation Forest on clean baseline normal telemetry.
        """
        if isinstance(df_or_array, pd.DataFrame):
            # Select only feature columns
            feature_cols = [c for c in self.feature_names if c in df_or_array.columns]
            X = df_or_array[feature_cols].values
        else:
            X = np.asarray(df_or_array)

        if len(X) < 10:
            raise ValueError(f"Insufficient training samples: {len(X)}. Need at least 10 samples.")

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True

        scores = self.model.decision_function(X_scaled)
        self.training_metadata = {
            "n_samples": len(X),
            "n_features": X.shape[1],
            "contamination": self.contamination,
            "mean_normal_score": round(float(np.mean(scores)), 4),
            "min_normal_score": round(float(np.min(scores)), 4),
            "features_used": self.feature_names,
        }
        return self.training_metadata

    def predict(self, df_or_array: pd.DataFrame | np.ndarray) -> np.ndarray:
        """
        Predicts anomalies.
        Returns array where 1 = ANOMALY, 0 = NORMAL.
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call fit() or load() first.")

        if isinstance(df_or_array, pd.DataFrame):
            feature_cols = [c for c in self.feature_names if c in df_or_array.columns]
            X = df_or_array[feature_cols].values
        else:
            X = np.asarray(df_or_array)

        X_scaled = self.scaler.transform(X)
        raw_preds = self.model.predict(X_scaled)
        # IsolationForest returns -1 for anomaly, 1 for normal
        # Map: -1 -> 1 (Anomaly), 1 -> 0 (Normal)
        return np.where(raw_preds == -1, 1, 0)

    def decision_function(self, df_or_array: pd.DataFrame | np.ndarray) -> np.ndarray:
        """
        Returns continuous anomaly score (lower/negative values mean more anomalous).
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call fit() or load() first.")

        if isinstance(df_or_array, pd.DataFrame):
            feature_cols = [c for c in self.feature_names if c in df_or_array.columns]
            X = df_or_array[feature_cols].values
        else:
            X = np.asarray(df_or_array)

        X_scaled = self.scaler.transform(X)
        return self.model.decision_function(X_scaled)

    def predict_sample(self, features: Dict[str, float]) -> Tuple[bool, float, Dict[str, float]]:
        """
        Evaluates a single live feature sample.
        Returns: (is_anomaly, normalized_anomaly_score, feature_values).
        """
        if not self.is_trained:
            return False, 0.0, {}

        sample_vec = np.array([[float(features.get(f, 0.0)) for f in self.feature_names]])
        scaled_vec = self.scaler.transform(sample_vec)
        raw_pred = self.model.predict(scaled_vec)[0]
        score = float(self.model.decision_function(scaled_vec)[0])

        is_anomaly = bool(raw_pred == -1)
        # Normalized score: inverted so that higher = higher anomaly likelihood
        norm_score = round(max(0.0, -score), 4)

        return is_anomaly, norm_score, features

    def save(self, model_path: str | Path = "data/models/isolation_forest.joblib") -> None:
        """Saves trained model, scaler, and metadata to disk."""
        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "metadata": self.training_metadata,
            "is_trained": self.is_trained,
        }
        joblib.dump(payload, path)

    def load(self, model_path: str | Path = "data/models/isolation_forest.joblib") -> bool:
        """Loads trained model and scaler from disk."""
        path = Path(model_path)
        if not path.is_file():
            return False
        payload = joblib.load(path)
        self.model = payload["model"]
        self.scaler = payload["scaler"]
        self.feature_names = payload.get("feature_names", self.feature_names)
        self.training_metadata = payload.get("metadata", {})
        self.is_trained = payload.get("is_trained", True)
        return True


class OneClassSVMDetector:
    """
    Optional secondary ML baseline model: One-Class SVM.
    """

    def __init__(self, kernel: str = "rbf", nu: float = 0.03, gamma: str = "scale") -> None:
        self.model = OneClassSVM(kernel=kernel, nu=nu, gamma=gamma)
        self.scaler = StandardScaler()
        self.is_trained: bool = False
        self.feature_names: List[str] = FeatureExtractor.FEATURE_NAMES

    def fit(self, df_or_array: pd.DataFrame | np.ndarray) -> None:
        if isinstance(df_or_array, pd.DataFrame):
            feature_cols = [c for c in self.feature_names if c in df_or_array.columns]
            X = df_or_array[feature_cols].values
        else:
            X = np.asarray(df_or_array)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True

    def predict(self, df_or_array: pd.DataFrame | np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("OneClassSVM model is not trained.")
        if isinstance(df_or_array, pd.DataFrame):
            feature_cols = [c for c in self.feature_names if c in df_or_array.columns]
            X = df_or_array[feature_cols].values
        else:
            X = np.asarray(df_or_array)
        X_scaled = self.scaler.transform(X)
        raw_preds = self.model.predict(X_scaled)
        return np.where(raw_preds == -1, 1, 0)
