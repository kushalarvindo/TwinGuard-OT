# TwinGuard-OT: Process-Aware Digital Twin for Cybersecurity Testing and Anomaly Detection in Industrial Control Systems

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Protocol: Modbus TCP](https://img.shields.io/badge/protocol-Modbus%20TCP-orange.svg)](docs/modbus_map.md)
[![Tests: 21 Passed](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)](tests/)

> **TwinGuard-OT** is a software-defined Industrial Control System (ICS) Digital Twin and cybersecurity experimentation testbed. It reproduces the closed-loop behavior of an industrial water-tank process, its physical sensors and actuators, a virtual Programmable Logic Controller (PLC), and its Operational Technology (OT) communication network over Modbus TCP.
> 
> The central innovation is **Process-Aware Anomaly Detection**: combining traditional network-layer traffic inspection with physical hydrodynamic reference modeling and unsupervised Machine Learning to identify cyberattacks that are syntactically valid over the network but physically inconsistent with the industrial process.

---

## 1. Why TwinGuard-OT Exists

Operational Technology (OT) networks control critical physical infrastructure such as water treatment plants, power grids, and chemical facilities. Unlike conventional IT systems where cyber incidents compromise data confidentiality, attacks on OT systems cause physical consequences (e.g., pipe rupture, pump cavitation, overfill flooding).

Direct cybersecurity testing on real industrial hardware is prohibitive:
1. **Physical Safety**: Testing attack injection on live physical infrastructure risks equipment destruction and physical hazards.
2. **High Cost**: Physical PLCs, RTUs, high-pressure pumps, and industrial telemetry transmitters cost tens of thousands of dollars.
3. **Reproducibility**: Physical experiments are difficult to reset to identical initial thermodynamic states for benchmark comparisons.

**TwinGuard-OT solves this by providing a compact, 100% software-based, reproducible ICS testbed that runs locally on a standard student laptop without physical industrial hardware.**

---

## 2. Core Architecture

The system operates around two concurrent, real-time loops:

```
               [ HMI / Streamlit Web Dashboard ]
                              │
                              │ Modbus TCP (Port 5020)
                              ▼
               [ Modbus TCP Holding Registers ]
                              │
                              ▼
               [ Virtual PLC Control Logic ]
                 (Hysteresis 30% - 80%)
                              │
               Control Commands (Pump/Valve)
                              │
                              ▼
               [ Virtual Actuators (Pump & Valve) ]
                              │
               Physical Inflow & Outflow
                              │
                              ▼
               [ Simulated Water Tank Physics ]
                 (Conservation of Mass dh/dt)
                              │
               True Process State
                              │
                              ▼
               [ Virtual Sensors (Level & Flow) ]
                 (Decoupled from True State)
                              │
                              ▼
               [ Virtual PLC Scan Input ]
```

Simultaneously, the monitoring and detection pipeline processes cyber-physical signals:

```
    [ Telemetry & Modbus Event Collector ]
                     │
                     ▼
             [ Feature Extraction ]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [ Rule-Based Engine ]   [ Isolation Forest ML ]
  (Deterministic Rules)   (Unsupervised Outliers)
         │                       │
         └───────────┬───────────┘
                     ▼
     [ Digital Twin Shadow Model ]
       (Physical Residual r(t))
                     │
                     ▼
     [ Cyber-Physical Correlator ]
                     │
    Categorizes into:
    • NORMAL
    • CYBER_ONLY
    • PROCESS_ONLY
    • CYBER_PHYSICAL_ATTACK
                     │
                     ▼
         [ SQLite Database & Dashboard ]
```

---

## 3. Water-Tank Digital Twin & Physics Model

The hydrodynamic simulation is governed by continuous conservation of mass:
$$\frac{dh}{dt} = \frac{Q_{in} - Q_{out}}{\text{Area}}$$

- **Inflow ($Q_{in}$)**: Active when the virtual pump is energized ($3.0\%/\text{s}$).
- **Outflow ($Q_{out}$)**: Active when the discharge valve is open ($1.2\%/\text{s}$ baseline plus Torricelli gravity head factor).
- **Physical Boundaries**: Water level is strictly bounded between $0.0\%$ (empty) and $100.0\%$ (brim capacity). Overflow and dry-run events are explicitly logged.
- **Sensor Decoupling**: The system maintains an essential distinction between:
  - **True Process State**: The underlying physical water level.
  - **Observed Sensor Value**: The measurement reported to the PLC (includes Gaussian noise $\mathcal{N}(0, \sigma^2)$ or cyber spoofing overrides).

---

## 4. Virtual PLC & Control Logic

The virtual PLC operates an industrial scan cycle at 5 Hz ($200\text{ ms}$ interval):
1. **Input Scan**: Samples observed level from sensor transmitter.
2. **Logic Evaluation**: Hysteresis setpoint maintenance:
   - If level $< 30.0\% \rightarrow$ Pump ON, Valve CLOSED.
   - If level $\ge 80.0\% \rightarrow$ Pump OFF, Valve OPEN.
   - Level between $30\%$ and $80\% \rightarrow$ Maintain current operational state.
3. **Safety Interlocks**: If level $\ge 95.0\%$, the emergency interlock overrides all commands and forcibly de-energizes the pump.

---

## 5. Modbus TCP Register Map

The local Modbus TCP server exposes standard 16-bit holding registers on `127.0.0.1:5020`:

| Register Offset | Display Address | Signal Name | Scale | Unit | Access | Description |
|:---:|:---:|:---|:---:|:---:|:---:|:---|
| `0` | `40001` | `TANK_LEVEL_SENSOR` | 10.0 | % | RO | Reported water level from virtual sensor |
| `1` | `40002` | `SETPOINT_LEVEL` | 10.0 | % | RW | Desired target setpoint (Default: 70.0%) |
| `2` | `40003` | `PUMP_COMMAND` | 1.0 | State | RW | Inflow pump control (0=OFF, 1=ON) |
| `3` | `40004` | `VALVE_COMMAND` | 1.0 | State | RW | Discharge valve control (0=CLOSED, 1=OPEN) |
| `4` | `40005` | `INFLOW_RATE` | 10.0 | %/s | RO | Virtual flow meter measurement |
| `5` | `40006` | `OUTFLOW_RATE` | 10.0 | %/s | RO | Virtual outflow meter measurement |
| `6` | `40007` | `ALARM_STATE` | 1.0 | Enum | RO | 0=Normal, 1=Low, 2=High, 3=Interlock |
| `7` | `40008` | `LOW_THRESHOLD` | 10.0 | % | RW | Hysteresis lower threshold (30.0%) |
| `8` | `40009` | `HIGH_THRESHOLD` | 10.0 | % | RW | Hysteresis upper threshold (80.0%) |
| `9` | `40010` | `CONTROL_MODE` | 1.0 | State | RW | 1=Automatic, 0=Manual Override |
| `10` | `40011` | `TRUE_TANK_LEVEL` | 10.0 | % | RO | Ground-truth physical level from physics model |
| `11` | `40012` | `PHYSICAL_RESIDUAL` | 10.0 | % | RO | Instantaneous residual $\|h_{\text{sensor}} - h_{\text{expected}}\|$ |

---

## 6. Attack Scenarios (Localhost Isolated)

All attack modules strictly verify that the target host is `127.0.0.1` before execution.

1. **Unauthorized Register Write (`unauthorized_write.py`)**: Rogue client connects to Modbus TCP and overwrites actuator commands (e.g., forces Pump ON when tank is full).
2. **Sensor Spoofing (`sensor_spoofing.py`)**: Falsifies reported water level (e.g., reports 20% when tank is actually at 85%), causing the PLC to erroneously fill the tank toward overflow.
3. **Replay Attack (`replay.py`)**: Captures legitimate filling data and replays it out of context during an emptying phase.
4. **Command Flooding (`command_flood.py`)**: Generates high-frequency Modbus read/write bursts ($150 - 300\text{ req/s}$) against the virtual PLC.
5. **Abnormal Setpoint Manipulation (`setpoint_manipulation.py`)**: Modifies setpoint register to an extreme out-of-spec value (e.g., 98.0%).

---

## 7. Multi-Tier Process-Aware Detection

TwinGuard-OT integrates three complementary detection mechanisms:

1. **Rule Engine (`rules.py`)**:
   - `R001 - UNEXPECTED_PUMP_ACTIVATION`: Pump energized above $80\%$ level.
   - `R002 - PROCESS_RESIDUAL_VIOLATION`: Residual $\|h_{\text{sensor}} - h_{\text{expected}}\| > 10.0\%$.
   - `R003 - IMPOSSIBLE_LEVEL_RATE`: Rate of level change exceeds physical limits ($> 5.0\%/\text{s}$).
   - `R004 - HIGH_REQUEST_RATE_FLOOD`: Modbus request rate $> 30\text{ req/s}$.
   - `R005 - ABNORMAL_SETPOINT_MANIPULATION`: Setpoint outside safety envelope $[15\%, 90\%]$.
   - `R006 - FROZEN_SENSOR_DETECTION`: Sensor level flatline while pump is active.

2. **Digital Twin Shadow Model (`process_residual.py`)**:
   - Runs a shadow hydrodynamic equation alongside the plant.
   - Computes physical residual $r(t) = |h_{\text{observed}}(t) - h_{\text{expected}}(t)|$.

3. **Machine Learning (`isolation_forest.py`)**:
   - Unsupervised Isolation Forest trained on clean baseline normal telemetry.
   - Standardized 13-dimensional cyber-physical feature vector.

4. **Cyber-Physical Correlator (`correlation.py`)**:
   - Unifies findings into four clear contextual categories:
     - `NORMAL`: All variables within expected parameters.
     - `CYBER_ONLY`: Network anomaly without physical distortion (e.g., flood probing).
     - `PROCESS_ONLY`: Physical inconsistency without detected network intrusion.
     - `CYBER_PHYSICAL_ATTACK`: Correlated attack where cyber activity causes physical divergence.

---

## 8. Installation & Setup

### Requirements:
- Python 3.10, 3.11, 3.12, or 3.13
- Node.js (v18+) for the Frontend dashboard
- Windows, Linux, or macOS

### Installation Steps:
```bash
# 1. Clone repository or navigate to workplace directory
cd TwinGuard-OT

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify environment and initialize storage
python scripts/setup.py

# 4. Install Frontend dependencies
cd frontend
npm install
cd ..
```

---

## 9. Running the System

TwinGuard-OT uses a modern decoupled architecture: a FastAPI backend that drives the simulation, and a React/Vite frontend for the interactive HMI dashboard.

### 1. Start the Backend API & Simulation (FastAPI)
Open a terminal and run the backend server. The physical simulation, PLC, and Modbus server will automatically start with the API:
```bash
# From the project root
uvicorn backend.main:app --reload
```
The API will be available at **http://localhost:8000** (with Swagger docs at `/docs`).

### 2. Start the Frontend Dashboard (React/Vite)
Open a new terminal, and start the Vite development server:
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173** in your browser to view the interactive Digital Twin dashboard.

### (Alternative) Legacy Streamlit Launcher:
You can still run the old monolithic system with the legacy Streamlit dashboard if preferred:
```bash
python scripts/start_system.py --dashboard
```

---

## 10. Running Research Experiments

### Run the Complete Benchmark Suite (Recommended):
```bash
python experiments/run_all_experiments.py
```
This automatically runs all 6 experiments (Normal Baseline + 5 Attack Scenarios), trains the ML model, records ground-truth labelled datasets, and computes empirical evaluation metrics.

### Run an Individual Attack:
```bash
python experiments/run_attack.py --attack sensor_spoofing --duration 12
python experiments/run_attack.py --attack unauthorized_write --duration 10
python experiments/run_attack.py --attack replay --duration 10
python experiments/run_attack.py --attack command_flood --duration 8
python experiments/run_attack.py --attack setpoint_manipulation --duration 10
```

### Calculate Real Evaluation Metrics:
```bash
python experiments/evaluate.py
```

### Reset the System to a Clean State:
```bash
python scripts/reset.py
```

---

## 11. Empirical Evaluation Results

Actual metrics calculated from our local self-generated benchmark run ($N = 1133$ samples: 655 Normal, 478 Attack):

| Detection Approach | Accuracy | Precision | Recall | F1-Score | False Positive Rate (FPR) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Rule-Based Engine** | **0.764** | **0.747** | **0.667** | **0.705** | 0.165 |
| **Isolation Forest (ML)** | 0.721 | 0.793 | 0.458 | 0.581 | **0.087** |
| **Hybrid Correlation** | 0.754 | 0.727 | **0.667** | 0.696 | 0.183 |

*(Note: Never hardcoded. All values are calculated mathematically from ground-truth labelled experiment runs).*

---

## 12. Automated Testing Suite

TwinGuard-OT includes 21 automated unit and integration tests covering physics, sensors, PLC, Modbus, attacks, detection, and end-to-end integration:

```bash
python -m pytest tests/ -v
```

Output:
```text
tests/test_attacks.py ....                                               [ 19%]
tests/test_detection.py ......                                           [ 47%]
tests/test_integration.py .                                              [ 52%]
tests/test_modbus.py ..                                                  [ 61%]
tests/test_plc.py ...                                                    [ 76%]
tests/test_tank.py .....                                                 [100%]

============================= 21 passed in 6.51s ==============================
```

---

## 13. Academic Context & Literature Survey

TwinGuard-OT builds upon established research in industrial cybersecurity and digital twins:
1. **Balta et al. (2024)**: Digital Twin-based cyber-attack detection framework for manufacturing systems.
2. **Rehman & Bahşi (2024)**: Systematic review of process-aware security monitoring in ICS.
3. **Lucchese et al. (2024)**: Combining digital twins with process mining for cyber-physical attack detection.
4. **Xu et al. (2025)**: PLC-MDT — comparing digital twin predictions with field data to identify control channel anomalies.
5. **Sayghe (2025)**: Digital twin-driven intrusion detection for industrial SCADA combining residuals and machine learning.

**Target Contribution**: An accessible, fully functional, reproducible software-only testbed correlating OT network transactions with physical process dynamics.
