# TwinGuard-OT: System Architecture Documentation

## 1. Overview
**TwinGuard-OT** is a software-defined Industrial Control System (ICS) Digital Twin and cybersecurity experimentation platform. It reproduces the dynamics of an industrial water storage process, its physical sensors and actuators, its Programmable Logic Controller (PLC), and its local Operational Technology (OT) communication network over Modbus TCP.

The core motivation of the architecture is **Process-Aware Anomaly Detection**: traditional IT Network Intrusion Detection Systems (NIDS) inspect packet syntax and request frequencies, but cannot determine whether a syntactically valid control command is safe for the physical process. TwinGuard-OT bridges the cyber domain with physical dynamics to identify both cyber and physical discrepancies.

---

## 2. Core Architecture Topology

```
                  ┌────────────────────────┐
                  │ Modern React/Vite HMI  │
                  │   (Port 5173 Web UI)   │
                  └───────────┬────────────┘
                              │ REST & WebSocket
                              ▼
                  ┌────────────────────────┐
                  │  FastAPI Backend Core  │
                  │   (Port 8000 Server)   │
                  └───────────┬────────────┘
                              │
                              ▼
                  ┌────────────────────────┐
                  │ Modbus TCP Client (HMI)│
                  └───────────┬────────────┘
                              │ Modbus TCP (Port 5020)
                              ▼
                  ┌────────────────────────┐
                  │  Modbus TCP Server     │
                  │  (SimData Registers)   │
                  └───────────┬────────────┘
                              │
                  ┌───────────┴────────────┐
                  ▼                        ▼
       ┌─────────────────────┐  ┌─────────────────────┐
       │     Virtual PLC     │  │  Telemetry & Event  │
       │ Hysteresis & Safety │  │      Collector      │
       └──────────┬──────────┘  └──────────┬──────────┘
                  │                        │
       Control    │                        │
       Commands   ▼                        │
       ┌─────────────────────┐             │
       │  Virtual Actuators  │             │
       │    Pump & Valve     │             │
       └──────────┬──────────┘             │
                  │                        │
       Physical   │                        │
       Flows      ▼                        │
       ┌─────────────────────┐             │
       │ Simulated Water Tank│             │
       │ Hydrodynamic Physics│             │
       └──────────┬──────────┘             │
                  │                        │
       Physical   │                        │
       State      ▼                        │
       ┌─────────────────────┐             │
       │   Virtual Sensors   │             │
       │ Level & Flow Meters │             │
       └──────────┬──────────┘             │
                  │                        │
                  └────────────────────────┴──────┐
                                                  ▼
                                       ┌───────────────────────┐
                                       │   Feature Extractor   │
                                       └──────────┬────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │   Detection & Correlation     │
                                  ├───────────────┬───────────────┤
                                  │  Rule Engine  │  Isolation    │
                                  │ (Deterministic│    Forest     │
                                  │ ICS Policies) │ (ML Outliers) │
                                  ├───────────────┴───────────────┤
                                  │  Digital Twin Shadow Model    │
                                  │      (Physical Residuals)     │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                       ┌───────────────────────┐
                                       │ Cyber-Physical Fusion │
                                       └──────────┬────────────┘
                                                  │
                                                  ▼
                                       ┌───────────────────────┐
                                       │   SQLite Database     │
                                       │   (data/twinguard.db) │
                                       └───────────────────────┘
```

---

## 3. Subsystem Descriptions

### 3.1 Simulated Physical Process (`twinguard.process`)
- **Hydrodynamic Model (`physics.py`)**: Models conservation of mass via differential equations:
  $$\frac{dh}{dt} = \frac{Q_{in} - Q_{out}}{\text{Area}}$$
  Where inflow $Q_{in} = \text{pump\_rate} \times \text{pump\_state}$ and outflow $Q_{out}$ accounts for valve opening and Torricelli gravity head pressure.
- **Actuators (`actuators.py`)**: Includes a virtual inflow pump (`Pump`) and discharge valve (`Valve`) with operational cycle counters and runtime metrics.
- **Sensors (`sensors.py`)**: Crucially decouples **True Physical State** from **Observed Sensor Value**. Virtual sensors inject realistic Gaussian measurement noise ($\mathcal{N}(0, \sigma^2)$) and support cyber spoofing, bias, and freezing.

### 3.2 Virtual PLC (`twinguard.plc`)
- **Control Logic (`control_logic.py`)**: Executes hysteresis setpoint maintenance:
  - If level falls below $30.0\%$, the pump is energized (ON) and the valve closed.
  - If level reaches $80.0\%$, the pump is de-energized (OFF) and the valve opened.
  - **Safety Interlocks**: If level exceeds emergency threshold ($95.0\%$), the pump is forcibly locked out regardless of auto/manual modes to prevent physical rupture or tank overflow.

### 3.3 Modbus TCP Communications (`twinguard.modbus`)
- Exposes industrial registers on `127.0.0.1:5020` using PyModbus.
- Maps tank level, setpoint, pump state, valve state, flow rates, and alarms onto standard Holding Registers (40001–40012).
- Includes transaction tracing to monitor function codes, source IPs, and request frequencies.

### 3.4 Data Collector & SQLite Layer (`twinguard.monitoring` & `twinguard.database`)
- Continuously aggregates cyber and physical features at 10 Hz.
- Maintains ground-truth experiment labels (`label: 0` for normal baseline, `label: 1` during attacks).
- Persists data to SQLite tables with indexes for fast retrieval and CSV export.

### 3.5 Process-Aware Detection Pipeline (`twinguard.detection`)
- **Rule-Based Engine (`rules.py`)**: Evaluates explainable ICS rules (e.g., unexpected pump activation near maximum level, impossible level jump rates, request floods).
- **Digital Twin Shadow Reference (`process_residual.py`)**: Runs a parallel predictive model of the water tank and computes the physical residual:
  $$\text{residual}(t) = |h_{\text{observed}}(t) - h_{\text{expected}}(t)|$$
- **Machine Learning Detector (`isolation_forest.py`)**: An unsupervised Isolation Forest trained on normal operational data to identify multi-dimensional outliers.
- **Cyber-Physical Correlator (`correlation.py`)**: Correlates cyber anomalies with physical inconsistencies, classifying each incident into `NORMAL`, `CYBER_ONLY`, `PROCESS_ONLY`, or `CYBER_PHYSICAL_ATTACK`.
