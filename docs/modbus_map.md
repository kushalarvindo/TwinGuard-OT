# TwinGuard-OT: Modbus TCP Register Specification

## 1. Protocol Parameters
- **Protocol**: Modbus TCP over IPv4
- **Transport**: TCP
- **Default Port**: `5020` (Non-privileged port avoiding root/admin constraints)
- **Host Binding**: `127.0.0.1` (Strict local simulation isolation)
- **Unit / Device ID**: `1`
- **Supported Function Codes**:
  - `03 (0x03)`: Read Holding Registers
  - `06 (0x06)`: Write Single Register
  - `16 (0x10)`: Write Multiple Registers

---

## 2. Holding Register Map

The simulated PLC and Digital Twin registers are organized as 16-bit Holding Registers. In 0-based offset notation (standard PyModbus address):

| Offset | PLC Address (1-based) | Register Name | Data Type | Engineering Scale | Engineering Unit | Access | Description |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|
| `0` | `40001` | `TANK_LEVEL_SENSOR` | UINT16 | $\times 10.0$ | % | RO | Reported water level from virtual level transmitter ($0.0 - 100.0\%$). |
| `1` | `40002` | `SETPOINT_LEVEL` | UINT16 | $\times 10.0$ | % | RW | Target process water level (Default: $70.0\%$). |
| `2` | `40003` | `PUMP_COMMAND` | UINT16 | $\times 1.0$ | State | RW | Inflow pump command and status ($0 = \text{OFF}, 1 = \text{ON}$). |
| `3` | `40004` | `VALVE_COMMAND` | UINT16 | $\times 1.0$ | State | RW | Drain valve command and status ($0 = \text{CLOSED}, 1 = \text{OPEN}$). |
| `4` | `40005` | `INFLOW_RATE` | UINT16 | $\times 10.0$ | %/s | RO | Measured inflow delivery rate ($0.0 - 5.0\%/\text{s}$). |
| `5` | `40006` | `OUTFLOW_RATE` | UINT16 | $\times 10.0$ | %/s | RO | Measured discharge outflow rate ($0.0 - 3.0\%/\text{s}$). |
| `6` | `40007` | `ALARM_STATE` | UINT16 | $\times 1.0$ | Enum | RO | Operational alarm code: `0=Normal`, `1=Low Alarm`, `2=High Alarm`, `3=Emergency Interlock`. |
| `7` | `40008` | `LOW_THRESHOLD` | UINT16 | $\times 10.0$ | % | RW | Low level hysteresis pump activation limit (Default: $30.0\%$). |
| `8` | `40009` | `HIGH_THRESHOLD` | UINT16 | $\times 10.0$ | % | RW | High level hysteresis pump deactivation limit (Default: $80.0\%$). |
| `9` | `40010` | `CONTROL_MODE` | UINT16 | $\times 1.0$ | State | RW | PLC Control Mode: `1 = Automatic`, `0 = Manual Operator Override`. |
| `10` | `40011` | `TRUE_TANK_LEVEL` | UINT16 | $\times 10.0$ | % | RO | Ground-truth physical level from Digital Twin physics engine. |
| `11` | `40012` | `PHYSICAL_RESIDUAL` | UINT16 | $\times 10.0$ | % | RO | Instantaneous residual discrepancy: $\|h_{\text{sensor}} - h_{\text{true}}\|$. |

---

## 3. Register Conversion Formulas

### Converting Engineering Values to Modbus Raw Values:
$$\text{Raw Integer} = \text{int}\Big(\text{round}\big(\text{Value} \times \text{Scale}\big)\Big)$$
*Example:* Tank Level of $74.2\%$ with scale $10.0$ $\rightarrow \text{Raw} = 742$.

### Converting Modbus Raw Values to Engineering Values:
$$\text{Engineering Float} = \frac{\text{Raw Integer}}{\text{Scale}}$$
*Example:* Raw register value $850$ on Setpoint register $\rightarrow 850 / 10.0 = 85.0\%$.

---

## 4. Security Audit & Transaction Tracing
Every Modbus request is audited by the `TwinGuardModbusServer` transaction interceptor:
- Client IP address and transaction timestamp
- Modbus Function code and name
- Target register address
- Transferred value
- Instantaneous request frequency (requests/sec)
These features feed directly into the **Feature Extractor** and **Rule Engine**.
