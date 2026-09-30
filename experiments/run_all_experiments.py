"""
Master Experiment Suite Runner for TwinGuard-OT.
Sequentially runs:
1. Normal Operation Baseline (EXP-NORMAL-001) -> trains ML detector
2. Unauthorized Register Write (EXP-UNAUTH-002)
3. Sensor Spoofing Attack (EXP-SPOOF-003)
4. Replay Attack (EXP-REPLAY-004)
5. Command Flooding Attack (EXP-FLOOD-005)
6. Abnormal Setpoint Manipulation (EXP-SETPOINT-006)
Followed by global multi-model evaluation and metric calculation.
"""

import sys
import time
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))

from twinguard.utils.logging import setup_logger
from experiments.normal_operation import run_normal_baseline
from experiments.run_attack import run_attack_experiment
from experiments.evaluate import evaluate_experiment


def run_all():
    logger = setup_logger("twinguard.all_experiments")
    logger.info("=================================================================")
    logger.info("  TWINGUARD-OT: STARTING COMPREHENSIVE EXPERIMENT BENCHMARK")
    logger.info("=================================================================")

    start_total = time.time()

    # 1. Normal Baseline
    logger.info("\n>>> [1/6] Running Normal Operation Baseline...")
    run_normal_baseline(duration_sec=25.0, exp_id="EXP-NORMAL-001")
    time.sleep(1.0)

    # 2. Unauthorized Register Write
    logger.info("\n>>> [2/6] Running Unauthorized Write Attack...")
    run_attack_experiment(attack_name="unauthorized_write", exp_id="EXP-UNAUTH-002", warmup_sec=4.0, attack_duration_sec=10.0, cooldown_sec=4.0)
    time.sleep(1.0)

    # 3. Sensor Spoofing
    logger.info("\n>>> [3/6] Running Sensor Spoofing Attack...")
    run_attack_experiment(attack_name="sensor_spoofing", exp_id="EXP-SPOOF-003", warmup_sec=4.0, attack_duration_sec=10.0, cooldown_sec=4.0)
    time.sleep(1.0)

    # 4. Replay Attack
    logger.info("\n>>> [4/6] Running Replay Attack...")
    run_attack_experiment(attack_name="replay", exp_id="EXP-REPLAY-004", warmup_sec=4.0, attack_duration_sec=10.0, cooldown_sec=4.0)
    time.sleep(1.0)

    # 5. Command Flooding
    logger.info("\n>>> [5/6] Running Command Flooding Attack...")
    run_attack_experiment(attack_name="command_flood", exp_id="EXP-FLOOD-005", warmup_sec=4.0, attack_duration_sec=8.0, cooldown_sec=4.0)
    time.sleep(1.0)

    # 6. Abnormal Setpoint Manipulation
    logger.info("\n>>> [6/6] Running Abnormal Setpoint Manipulation Attack...")
    run_attack_experiment(attack_name="setpoint_manipulation", exp_id="EXP-SETPOINT-006", warmup_sec=4.0, attack_duration_sec=10.0, cooldown_sec=4.0)
    time.sleep(1.0)

    # 7. Global Evaluation
    logger.info("\n>>> [EVALUATION] Calculating mathematical benchmark metrics across all experiments...")
    results = evaluate_experiment()

    elapsed = round(time.time() - start_total, 2)
    logger.info(f"\n=================================================================")
    logger.info(f"  EXPERIMENT SUITE FINISHED IN {elapsed}s")
    logger.info("=================================================================")
    return results


if __name__ == "__main__":
    run_all()
