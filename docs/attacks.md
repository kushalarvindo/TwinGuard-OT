# TwinGuard-OT: Cyberattack Scenarios & Threat Models

## 1. Safety Guardrails & Environment Isolation
All attack modules in TwinGuard-OT inherit from `BaseAttack`. 

Before firing any network packets or Modbus requests, `BaseAttack` validates that the target host belongs to `{"127.0.0.1", "localhost", "::1"}`. Attempting to supply external addresses, public IPs, or remote subnets immediately raises a `LocalEnvironmentSecurityError` and halts execution.

---

## 2. Attack Scenarios

### Attack 1: Unauthorized Register Write (`unauthorized_write.py`)
- **Threat Model**: An unauthenticated device on the local network connects over Modbus TCP and modifies critical control registers without PLC supervisor consent.
- **Mechanism**: Connects to port 5020 and writes to `REG_PUMP_COMMAND` (offset 2) to force the inflow pump ON while the tank is already at high capacity.
- **Physical Consequence**: Rapid tank filling towards overflow boundary ($> 95\%$) bypassing normal PLC deactivation thresholds.
- **Detection Mechanism**: 
  - Rule `R001` (Unexpected Pump Activation when level exceeds limit)
  - Cyber-Physical Correlator detects unauthorized command inconsistent with tank state.

---

### Attack 2: Sensor Spoofing (`sensor_spoofing.py`)
- **Threat Model**: A compromised sensor transmitter or Man-in-the-Middle (MitM) node falsifies sensor telemetry transmitted to the PLC.
- **Mechanism**: Injects a false reading (e.g., reports $20.0\%$ water level when the actual physical process is at $85.0\%$).
- **Physical Consequence**: The PLC logic believes the tank is low and energizes the pump, driving the true water level into physical overflow ($100\%$).
- **Detection Mechanism**:
  - Digital Twin Shadow Model predicts physical trajectory $h_{\text{expected}}(t)$.
  - Rule `R002` triggers when physical residual $|h_{\text{sensor}} - h_{\text{expected}}| > 10.0\%$.
  - Rule `R003` triggers if the level jump rate $|\Delta h/\Delta t|$ violates physical pump flow limits.

---

### Attack 3: Replay Attack (`replay.py`)
- **Threat Model**: An adversary intercepts and records legitimate Modbus sensor transmissions during a standard filling cycle, then replays those exact packets out of context during a draining or steady-state phase.
- **Mechanism**: Injects previously recorded sequence $[25.0\%, 27.5\%, 30.0\%, 32.5\%, \dots]$ when the actual water tank is discharging.
- **Physical Consequence**: Misleads operators and automated supervisory systems into believing the tank is filling normally while water is actually draining.
- **Detection Mechanism**:
  - Temporal and physical mismatch between expected pump status and reported level trend.
  - Isolation Forest flags multi-variable correlation divergence.

---

### Attack 4: Command Flooding (`command_flood.py`)
- **Threat Model**: High-frequency Modbus transaction flooding designed to exhaust virtual PLC communication buffers or cause denial of service.
- **Mechanism**: Dispatches rapid holding register read/write requests ($150 - 300\text{ req/s}$) against the local Modbus server port.
- **Physical Consequence**: Network latency spikes and communication delay between HMI and PLC.
- **Detection Mechanism**:
  - Rule `R004` (High Request Rate Flood) triggers when requests/sec $> 30\text{ req/s}$.
  - Classified by Cyber-Physical Correlator as `CYBER_ONLY` anomaly if physical process remains unperturbed.

---

### Attack 5: Abnormal Setpoint Manipulation (`setpoint_manipulation.py`)
- **Threat Model**: An adversary alters the operating setpoint register (`REG_SETPOINT_LEVEL`, offset 1) to an extreme or unsafe value.
- **Mechanism**: Modifies the setpoint to $98.0\%$ (near tank brim) or $5.0\%$ (near dry run).
- **Physical Consequence**: Forces the PLC to maintain water level in an unsafe physical regime with minimal safety margin.
- **Detection Mechanism**:
  - Rule `R005` (Abnormal Setpoint Manipulation) triggers when setpoint is outside the safe envelope $[15\%, 90\%]$.
  - Isolation Forest flags setpoint error and actuator state shifts.
