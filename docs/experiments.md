# TwinGuard-OT: Experiments & Benchmark Suite

## 1. Experimental Methodology
TwinGuard-OT features an automated, reproducible research experiment runner. Every experiment runs inside the local software-only testbed without external hardware dependencies.

Each experiment adheres to a three-phase timeline:
1. **Warmup Phase (Normal Baseline)**: Process starts from known baseline conditions under standard PLC control ($h \approx 50.0\%$, hysteresis $[30\%, 80\%]$). Ground truth label is recorded as `label = 0` (`attack_type = "normal"`).
2. **Attack Phase (Controlled Injection)**: The designated attack vector is injected. Ground truth label transitions to `label = 1` (`attack_type = "<name>"`). Real-time telemetry, Modbus transactions, and detection outputs are recorded synchronously.
3. **Cooldown Phase (Recovery)**: Attack ceases; system recovers under normal PLC logic (`label = 0`).

---

## 2. Standard Experiment Suite

| Experiment ID | Scenario | Duration | Ground-Truth Attack Labels | Primary Detection Signals |
|:---|:---|:---:|:---:|:---|
| `EXP-NORMAL-001` | Normal Operation Baseline | 25s | 0 (0%) | Clean cyclical hysteresis; trains Isolation Forest. |
| `EXP-UNAUTH-002` | Unauthorized Register Write | 18s | ~10s (55%) | Rule `R001` (Pump active above high threshold). |
| `EXP-SPOOF-003` | Sensor Spoofing | 18s | ~10s (55%) | Rule `R002` (Physical residual $> 10\%$), Rule `R003`. |
| `EXP-REPLAY-004` | Replay Attack | 18s | ~10s (55%) | Multidimensional outlier via Isolation Forest. |
| `EXP-FLOOD-005` | Command Flooding | 16s | ~8s (50%) | Rule `R004` (Request rate $> 30\text{ req/s}$). |
| `EXP-SETPOINT-006` | Abnormal Setpoint Manipulation | 18s | ~10s (55%) | Rule `R005` (Setpoint outside safe envelope). |

---

## 3. How to Run Experiments

### Running the Entire Benchmark Suite:
```bash
python experiments/run_all_experiments.py
```
This single command executes all 6 experiments sequentially, generates labelled CSV datasets, trains the machine learning model, computes confusion matrices and performance metrics, and logs everything to SQLite.

### Running Individual Attack Scenarios:
```bash
# 1. Sensor Spoofing (e.g. 12 seconds)
python experiments/run_attack.py --attack sensor_spoofing --duration 12

# 2. Unauthorized Register Write
python experiments/run_attack.py --attack unauthorized_write --duration 12

# 3. Replay Attack
python experiments/run_attack.py --attack replay --duration 12

# 4. Command Flooding
python experiments/run_attack.py --attack command_flood --duration 8

# 5. Abnormal Setpoint Manipulation
python experiments/run_attack.py --attack setpoint_manipulation --duration 12
```

### Running Normal Baseline Collection:
```bash
python experiments/normal_operation.py --duration 30 --exp-id EXP-NORMAL-001
```

### Recomputing Empirical Evaluation Metrics:
```bash
# Evaluate all recorded data
python experiments/evaluate.py

# Evaluate a specific experiment ID
python experiments/evaluate.py --exp-id EXP-SPOOF-003
```

---

## 4. Empirical Evaluation Output
Evaluation metrics are calculated from actual labelled data using scikit-learn metrics:
- **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$
- **Precision**: $\frac{TP}{TP + FP}$
- **Recall (TPR)**: $\frac{TP}{TP + FN}$
- **F1-Score**: $\frac{2 \cdot P \cdot R}{P + R}$
- **False Positive Rate (FPR)**: $\frac{FP}{FP + TN}$
- **Detection Latency**: Time elapsed from first attack sample to first positive alarm.

Results are printed to stdout, persisted to SQLite (`evaluation_results` table), and exported to `data/results/evaluation_ALL_EXPERIMENTS.json`.
