# TwinGuard-OT: Troubleshooting Guide

## 1. Modbus Port Conflicts (Port 5020)
- **Symptom**: `OSError: [WinError 10048] Only one usage of each socket address is normally permitted`
- **Cause**: Another instance of the Modbus server or a lingering background python process is holding port `5020`.
- **Resolution**:
  - Run the reset script:
    ```bash
    python scripts/reset.py
    ```
  - In Windows PowerShell, find and terminate any process using port 5020:
    ```powershell
    Get-NetTCPConnection -LocalPort 5020 | Select-Object OwningProcess
    Stop-Process -Id <PID> -Force
    ```
  - Alternatively, edit `config/config.yaml` and set `modbus.port: 5022`.

---

## 2. Windows Console Unicode / Emoji Display
- **Symptom**: `UnicodeEncodeError: 'charmap' codec can't encode character...`
- **Cause**: Windows CMD or default PowerShell uses Code Page 1252 or 437 by default.
- **Resolution**:
  - TwinGuard-OT scripts include automatic `sys.stdout.reconfigure(encoding="utf-8")`.
  - For manual PowerShell sessions, execute:
    ```powershell
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001
    ```

---

## 3. Streamlit Dashboard Connection Issues
- **Symptom**: Dashboard shows "No telemetry data available" or metrics are blank.
- **Resolution**:
  - TwinGuard-OT does not fabricate fake metrics. If the database was recently cleared with `reset.py`, you must run either:
    ```bash
    python scripts/start_system.py
    ```
    or
    ```bash
    python experiments/run_all_experiments.py
    ```
  - Click the **"Auto Refresh"** checkbox in the sidebar or hit the `R` key inside the browser to refresh Streamlit.

---

## 4. Resetting the System to a Clean State
- To clear all generated telemetry, purge attack results, and reset the SQLite database without deleting code:
  ```bash
  python scripts/reset.py
  ```
- To verify system dependencies and storage readiness:
  ```bash
  python scripts/setup.py
  ```
- To run automated unit and integration tests:
  ```bash
  python -m pytest tests/
  ```
