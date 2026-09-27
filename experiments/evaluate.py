"""
Comprehensive Evaluation Pipeline for TwinGuard-OT.
Calculates actual mathematical metrics (Accuracy, Precision, Recall, F1, FPR, Latency)
comparing Rule-Based, Isolation Forest (ML), and Hybrid Cyber-Physical Correlation.
NEVER emits hard-coded or fabricated metrics.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

import numpy as np
import pandas as pd

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.utils.logging import setup_logger
from twinguard.database.db import DatabaseManager
from twinguard.features.extractor import FeatureExtractor
from twinguard.detection.rules import RuleBasedDetector
from twinguard.detection.isolation_forest import IsolationForestDetector
from twinguard.detection.correlation import CyberPhysicalCorrelator


def compute_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray, timestamps: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Computes confusion matrix and performance statistics from actual labels.
    """
    if len(y_true) == 0:
        return {
            "status": "No data available",
            "total_samples": 0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "false_positive_rate": 0.0,
            "detection_latency_sec": None,
        }

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    total = len(y_true)

    accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0

    # Detection Latency: time from first actual attack sample to first detection
    latency_sec = None
    if timestamps is not None and np.any(y_true == 1) and np.any((y_true == 1) & (y_pred == 1)):
        first_attack_t = timestamps[y_true == 1][0]
        detected_indices = np.where((y_true == 1) & (y_pred == 1))[0]
        first_detect_t = timestamps[detected_indices[0]]
        latency_sec = round(max(0.0, float(first_detect_t - first_attack_t)), 3)

    return {
        "status": "Evaluated",
        "total_samples": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "detection_latency_sec": latency_sec,
    }


def evaluate_experiment(experiment_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates detection engines on recorded experiment data.
    """
    config = load_system_config()
    logger = setup_logger("twinguard.evaluate")
    root = get_project_root()
    db = DatabaseManager(config["storage"]["db_path_resolved"])

    # Load recorded telemetry
    if experiment_id:
        df_raw = db.get_telemetry_by_experiment(experiment_id)
        target_name = experiment_id
    else:
        df_raw = db.get_all_telemetry()
        target_name = "ALL_EXPERIMENTS"

    if df_raw.empty:
        logger.warning(f"No experiment data found for {target_name}.")
        return {"status": "No experiment data available"}

    logger.info(f"Evaluating {len(df_raw)} samples for {target_name}...")

    # Extract features
    extractor = FeatureExtractor(high_threshold=config.get("plc", {}).get("high_threshold", 80.0))
    df_features = extractor.extract_from_dataframe(df_raw)

    y_true = df_raw["label"].values.astype(int)
    timestamps = df_raw["timestamp"].values

    # 1. Rule-Based Evaluation
    rule_detector = RuleBasedDetector(residual_threshold=config.get("detection", {}).get("residual_threshold", 10.0))
    y_pred_rule = np.zeros(len(df_features), dtype=int)
    for i in range(len(df_features)):
        row_feat = df_features.iloc[i].to_dict()
        active = rule_detector.get_active_alerts(row_feat)
        y_pred_rule[i] = 1 if len(active) > 0 else 0

    metrics_rule = compute_binary_metrics(y_true, y_pred_rule, timestamps)

    # 2. Isolation Forest ML Evaluation
    ml_detector = IsolationForestDetector()
    model_path = root / config["storage"].get("models_dir", "data/models") / "isolation_forest.joblib"
    if ml_detector.load(model_path):
        y_pred_ml = ml_detector.predict(df_features)
        ml_scores = ml_detector.decision_function(df_features)
    else:
        logger.warning("Isolation Forest model not found on disk. Training temporary baseline...")
        # Train on whatever normal data exists
        normal_subset = df_features[y_true == 0]
        if len(normal_subset) >= 10:
            ml_detector.fit(normal_subset)
            y_pred_ml = ml_detector.predict(df_features)
            ml_scores = ml_detector.decision_function(df_features)
        else:
            y_pred_ml = np.zeros(len(df_features), dtype=int)
            ml_scores = np.zeros(len(df_features))

    metrics_ml = compute_binary_metrics(y_true, y_pred_ml, timestamps)

    # 3. Hybrid Cyber-Physical Correlation Evaluation
    correlator = CyberPhysicalCorrelator()
    y_pred_hybrid = np.zeros(len(df_features), dtype=int)
    for i in range(len(df_features)):
        row_feat = df_features.iloc[i].to_dict()
        rules = rule_detector.evaluate(row_feat)
        ml_anom = bool(y_pred_ml[i] == 1)
        ml_score = float(ml_scores[i])
        det = correlator.correlate(rules, ml_anom, ml_score, row_feat)
        y_pred_hybrid[i] = 1 if det.is_anomaly else 0

    metrics_hybrid = compute_binary_metrics(y_true, y_pred_hybrid, timestamps)

    # Log results to SQLite
    exp_log_id = experiment_id or "EXP-ALL-SUMMARY"
    for name, m in [("Rule-Based", metrics_rule), ("Isolation Forest", metrics_ml), ("Hybrid Correlation", metrics_hybrid)]:
        if m.get("status") == "Evaluated":
            db.log_evaluation_result({
                "experiment_id": exp_log_id,
                "model_name": name,
                "total_samples": m["total_samples"],
                "true_positives": m["true_positives"],
                "false_positives": m["false_positives"],
                "true_negatives": m["true_negatives"],
                "false_negatives": m["false_negatives"],
                "accuracy": m["accuracy"],
                "precision": m["precision"],
                "recall": m["recall"],
                "f1_score": m["f1_score"],
                "false_positive_rate": m["false_positive_rate"],
                "detection_latency_sec": m["detection_latency_sec"],
            })

    output = {
        "experiment_id": target_name,
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": len(df_raw),
        "attack_samples": int(np.sum(y_true == 1)),
        "normal_samples": int(np.sum(y_true == 0)),
        "models": {
            "Rule-Based": metrics_rule,
            "Isolation Forest": metrics_ml,
            "Hybrid Correlation": metrics_hybrid,
        }
    }

    # Save to JSON
    results_dir = root / config["storage"].get("results_dir", "data/results")
    out_file = results_dir / f"evaluation_{target_name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Evaluation report written to: {out_file}")
    print("\n" + "=" * 65)
    print(f"TwinGuard-OT Evaluation Results: {target_name}")
    print("=" * 65)
    print(f"Total Samples: {output['total_samples']} (Normal: {output['normal_samples']}, Attack: {output['attack_samples']})")
    print("-" * 65)
    print(f"{'Model':<22} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<6} | {'F1':<6} | {'FPR':<6}")
    print("-" * 65)
    for m_name, m in output["models"].items():
        print(f"{m_name:<22} | {m['accuracy']:<8.3f} | {m['precision']:<9.3f} | {m['recall']:<6.3f} | {m['f1_score']:<6.3f} | {m['false_positive_rate']:<6.3f}")
    print("=" * 65 + "\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwinGuard-OT Evaluation Pipeline")
    parser.add_argument("--exp-id", type=str, default=None, help="Specific experiment ID to evaluate (or all if omitted)")
    args = parser.parse_args()

    evaluate_experiment(experiment_id=args.exp_id)
