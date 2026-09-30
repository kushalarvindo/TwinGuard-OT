# TwinGuard-OT: Process-Aware Detection Architecture

## 1. Multi-Tier Detection Methodology

TwinGuard-OT integrates three complementary detection paradigms into a unified Cyber-Physical Correlator:

```
┌──────────────────────────────────────────────────────────────┐
│                    HYBRID DETECTION LAYERS                   │
├───────────────────────────────┬──────────────────────────────┤
│ 1. Explainable Rule Engine    │ Deterministic ICS physics,   │
│    (Domain Policies)          │ safety limits, network rates │
├───────────────────────────────┼──────────────────────────────┤
│ 2. Digital Twin Shadow Model  │ Differential hydrodynamic    │
│    (Physical Residuals)       │ golden reference trajectory  │
├───────────────────────────────┼──────────────────────────────┤
│ 3. Isolation Forest ML        │ Unsupervised outlier         │
│    (Multivariate Patterns)    │ isolation on normal baseline │
└───────────────────────────────┴──────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               CYBER-PHYSICAL CORRELATOR                      │
│                                                              │
│ Categorizes every event into:                                │
│ • NORMAL: Baseline steady-state operation                    │
│ • CYBER_ONLY: Network anomaly without physical distortion    │
│ • PROCESS_ONLY: Physical deviation without cyber traffic     │
│ • CYBER_PHYSICAL_ATTACK: Correlated cyber-induced disruption │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Deterministic Rule Engine (`rules.py`)

| Rule ID | Rule Name | Category | Severity | Threshold Condition | Engineering Rationale |
|:---:|:---|:---:|:---:|:---|:---|
| `R001` | `UNEXPECTED_PUMP_ACTIVATION` | PHYSICAL | HIGH | Pump energized while level $> 80.0\%$ | Violates upper operational bound; risks overflow. |
| `R002` | `PROCESS_RESIDUAL_VIOLATION` | HYBRID | CRITICAL | $\|h_{\text{sensor}} - h_{\text{expected}}\| > 10.0\%$ | Falsified sensor reading decoupling from physics model. |
| `R003` | `IMPOSSIBLE_LEVEL_RATE` | PHYSICAL | HIGH | $\|\Delta h/\Delta t\| > 5.0\%/\text{s}$ | Level jump exceeds rated delivery rate of physical pump. |
| `R004` | `HIGH_REQUEST_RATE_FLOOD` | CYBER | MEDIUM | Request Rate $> 30.0\text{ req/s}$ | Network traffic surge indicative of DoS or command flood. |
| `R005` | `ABNORMAL_SETPOINT_MANIPULATION` | HYBRID | HIGH | Setpoint $< 15.0\%$ or $> 90.0\%$ | Setpoint outside safe operational envelope. |
| `R006` | `FROZEN_SENSOR_DETECTION` | PHYSICAL | MEDIUM | Level unchanged for $> 1.5\text{s}$ while pump active | Sensor transmitter freeze or replay of flat line. |

---

## 3. Physical Residual & Shadow Model (`process_residual.py`)

The Digital Twin maintains an internal hydrodynamic predictive model:
$$h_{\text{expected}}(t + \Delta t) = h_{\text{expected}}(t) + \frac{Q_{in}(u_{\text{pump}}) - Q_{out}(u_{\text{valve}})}{\text{Area}} \Delta t$$

The instantaneous physical residual is computed as:
$$r(t) = \big| h_{\text{sensor}}(t) - h_{\text{expected}}(t) \big|$$

- Under normal conditions, $r(t)$ remains bounded by sensor noise ($\le 1.5\%$).
- Under **sensor spoofing** attacks (e.g. reported level forced to $20\%$ while actual is $85\%$), $r(t)$ surges to $65\%$, providing an immediate, explainable detection signal.

---

## 4. Machine Learning Anomaly Detection (`isolation_forest.py`)

- **Algorithm**: `sklearn.ensemble.IsolationForest`
- **Training Strategy**: Unsupervised training strictly on clean baseline normal telemetry (`EXP-NORMAL-001`).
- **Feature Space**:
  1. `sensor_level`
  2. `level_rate`
  3. `process_residual`
  4. `inflow_rate`
  5. `outflow_rate`
  6. `net_flow`
  7. `pump_state`
  8. `valve_state`
  9. `setpoint`
  10. `setpoint_error`
  11. `request_rate`
  12. `actuator_inconsistency`
  13. `physical_impossibility`
- **Standardization**: `StandardScaler` fitted on normal distribution.
- **Model Persistence**: Serialized via `joblib` to `data/models/isolation_forest.joblib` with full metadata.

---

## 5. Cyber-Physical Correlation Matrix (`correlation.py`)

| Cyber Anomaly Detected? | Physical Inconsistency Detected? | Categorized Incident | Severity | Action |
|:---:|:---:|:---|:---:|:---|
| **NO** | **NO** | `NORMAL` | INFO | None. Operating within expected bounds. |
| **YES** | **NO** | `CYBER_ONLY` | MEDIUM | Alert operator to network flood / probe. Process is stable. |
| **NO** | **YES** | `PROCESS_ONLY` | HIGH | Alert operator to physical fault, leak, or mechanical wear. |
| **YES** | **YES** | `CYBER_PHYSICAL_ATTACK` | CRITICAL | Active cyberattack causing physical divergence. Immediate interlock. |
