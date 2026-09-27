"""
SQLite Database Layer for TwinGuard-OT.
Provides thread-safe persistence and querying for experiments, telemetry, events, detections, and metrics.
"""

import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd


class DatabaseManager:
    """
    Manages SQLite storage for TwinGuard-OT.
    Thread-safe connection handling using threading.local().
    """

    def __init__(self, db_path: str | Path = "data/twinguard.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=20.0)
            conn.row_factory = sqlite3.Row
            # Enable write-ahead logging (WAL) for concurrent reads and writes
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._local.conn = conn
        return self._local.conn

    def init_schema(self) -> None:
        """Initializes normalized relational schema and performance indexes."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Experiments Metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                attack_type TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                duration_sec REAL,
                status TEXT NOT NULL,
                notes TEXT
            );
        """)

        # 2. Physical & Sensor Telemetry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                true_level REAL NOT NULL,
                sensor_level REAL NOT NULL,
                inflow_rate REAL NOT NULL,
                outflow_rate REAL NOT NULL,
                pump_state INTEGER NOT NULL,
                valve_state INTEGER NOT NULL,
                setpoint REAL NOT NULL,
                process_residual REAL NOT NULL,
                is_overflow INTEGER NOT NULL,
                is_dry_run INTEGER NOT NULL,
                label INTEGER NOT NULL,
                attack_type TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)

        # 3. Modbus Network Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modbus_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                client_ip TEXT NOT NULL,
                function_code INTEGER NOT NULL,
                function_name TEXT NOT NULL,
                register_address INTEGER NOT NULL,
                register_name TEXT NOT NULL,
                value INTEGER NOT NULL,
                is_write INTEGER NOT NULL,
                request_rate REAL NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)

        # 4. Anomaly Detections & Alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                engine TEXT NOT NULL,
                rule_id TEXT,
                rule_name TEXT,
                severity TEXT NOT NULL,
                is_anomaly INTEGER NOT NULL,
                anomaly_score REAL NOT NULL,
                cyber_anomaly INTEGER NOT NULL,
                physical_anomaly INTEGER NOT NULL,
                correlation_category TEXT NOT NULL,
                explanation TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)

        # 5. Model Evaluation Metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                total_samples INTEGER NOT NULL,
                true_positives INTEGER NOT NULL,
                false_positives INTEGER NOT NULL,
                true_negatives INTEGER NOT NULL,
                false_negatives INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                precision REAL NOT NULL,
                recall REAL NOT NULL,
                f1_score REAL NOT NULL,
                false_positive_rate REAL NOT NULL,
                detection_latency_sec REAL,
                computed_at REAL NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)

        # Indexes for fast querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_exp ON process_telemetry(experiment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON process_telemetry(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_modbus_exp ON modbus_events(experiment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_exp ON detections(experiment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_exp ON evaluation_results(experiment_id);")

        conn.commit()

    # --- Experiment Lifecycle ---

    def create_experiment(
        self,
        exp_id: str,
        name: str,
        attack_type: str = "normal",
        notes: str = "",
    ) -> None:
        conn = self.get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO experiments (id, name, attack_type, start_time, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exp_id, name, attack_type, time.time(), "RUNNING", notes),
        )
        conn.commit()

    def finish_experiment(self, exp_id: str, status: str = "COMPLETED") -> None:
        conn = self.get_connection()
        row = conn.execute("SELECT start_time FROM experiments WHERE id = ?", (exp_id,)).fetchone()
        now = time.time()
        start_time = row["start_time"] if row else now
        duration = max(0.0, now - start_time)

        conn.execute(
            """
            UPDATE experiments
            SET end_time = ?, duration_sec = ?, status = ?
            WHERE id = ?
            """,
            (now, round(duration, 2), status, exp_id),
        )
        conn.commit()

    # --- Telemetry Logging ---

    def log_process_telemetry(self, data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        conn.execute(
            """
            INSERT INTO process_telemetry (
                experiment_id, timestamp, true_level, sensor_level,
                inflow_rate, outflow_rate, pump_state, valve_state,
                setpoint, process_residual, is_overflow, is_dry_run,
                label, attack_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["experiment_id"],
                data["timestamp"],
                data["true_level"],
                data["sensor_level"],
                data.get("inflow_rate", 0.0),
                data.get("outflow_rate", 0.0),
                int(data.get("pump_state", 0)),
                int(data.get("valve_state", 0)),
                data.get("setpoint", 70.0),
                data.get("process_residual", 0.0),
                int(data.get("is_overflow", 0)),
                int(data.get("is_dry_run", 0)),
                int(data.get("label", 0)),
                data.get("attack_type", "normal"),
            ),
        )
        conn.commit()

    def log_process_telemetry_batch(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        conn = self.get_connection()
        conn.executemany(
            """
            INSERT INTO process_telemetry (
                experiment_id, timestamp, true_level, sensor_level,
                inflow_rate, outflow_rate, pump_state, valve_state,
                setpoint, process_residual, is_overflow, is_dry_run,
                label, attack_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r["experiment_id"],
                    r["timestamp"],
                    r["true_level"],
                    r["sensor_level"],
                    r.get("inflow_rate", 0.0),
                    r.get("outflow_rate", 0.0),
                    int(r.get("pump_state", 0)),
                    int(r.get("valve_state", 0)),
                    r.get("setpoint", 70.0),
                    r.get("process_residual", 0.0),
                    int(r.get("is_overflow", 0)),
                    int(r.get("is_dry_run", 0)),
                    int(r.get("label", 0)),
                    r.get("attack_type", "normal"),
                )
                for r in records
            ],
        )
        conn.commit()

    # --- Modbus Event Logging ---

    def log_modbus_event(self, data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        conn.execute(
            """
            INSERT INTO modbus_events (
                experiment_id, timestamp, client_ip, function_code,
                function_name, register_address, register_name,
                value, is_write, request_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["experiment_id"],
                data["timestamp"],
                data.get("client_ip", "127.0.0.1"),
                data.get("function_code", 3),
                data.get("function_name", "ReadHoldingRegisters"),
                data.get("register_address", 40001),
                data.get("register_name", "TANK_LEVEL_SENSOR"),
                int(data.get("value", 0)),
                int(data.get("is_write", 0)),
                float(data.get("request_rate", 0.0)),
            ),
        )
        conn.commit()

    # --- Detections & Alerts ---

    def log_detection(self, data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        conn.execute(
            """
            INSERT INTO detections (
                experiment_id, timestamp, engine, rule_id,
                rule_name, severity, is_anomaly, anomaly_score,
                cyber_anomaly, physical_anomaly, correlation_category,
                explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["experiment_id"],
                data["timestamp"],
                data.get("engine", "RULE"),
                data.get("rule_id", "N/A"),
                data.get("rule_name", "N/A"),
                data.get("severity", "INFO"),
                int(data.get("is_anomaly", 0)),
                float(data.get("anomaly_score", 0.0)),
                int(data.get("cyber_anomaly", 0)),
                int(data.get("physical_anomaly", 0)),
                data.get("correlation_category", "NORMAL"),
                data.get("explanation", ""),
            ),
        )
        conn.commit()

    # --- Evaluation Results ---

    def log_evaluation_result(self, data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        conn.execute(
            """
            INSERT INTO evaluation_results (
                experiment_id, model_name, total_samples,
                true_positives, false_positives, true_negatives,
                false_negatives, accuracy, precision, recall,
                f1_score, false_positive_rate, detection_latency_sec,
                computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["experiment_id"],
                data["model_name"],
                int(data.get("total_samples", 0)),
                int(data.get("true_positives", 0)),
                int(data.get("false_positives", 0)),
                int(data.get("true_negatives", 0)),
                int(data.get("false_negatives", 0)),
                float(data.get("accuracy", 0.0)),
                float(data.get("precision", 0.0)),
                float(data.get("recall", 0.0)),
                float(data.get("f1_score", 0.0)),
                float(data.get("false_positive_rate", 0.0)),
                float(data["detection_latency_sec"]) if data.get("detection_latency_sec") is not None else None,
                time.time(),
            ),
        )
        conn.commit()

    # --- Query Methods ---

    def get_experiments(self) -> pd.DataFrame:
        conn = self.get_connection()
        return pd.read_sql_query("SELECT * FROM experiments ORDER BY start_time DESC", conn)

    def get_telemetry_by_experiment(self, experiment_id: str) -> pd.DataFrame:
        conn = self.get_connection()
        return pd.read_sql_query(
            "SELECT * FROM process_telemetry WHERE experiment_id = ? ORDER BY timestamp ASC",
            conn,
            params=(experiment_id,),
        )

    def get_all_telemetry(self) -> pd.DataFrame:
        conn = self.get_connection()
        return pd.read_sql_query("SELECT * FROM process_telemetry ORDER BY timestamp ASC", conn)

    def get_modbus_events(self, experiment_id: Optional[str] = None) -> pd.DataFrame:
        conn = self.get_connection()
        if experiment_id:
            return pd.read_sql_query(
                "SELECT * FROM modbus_events WHERE experiment_id = ? ORDER BY timestamp ASC",
                conn,
                params=(experiment_id,),
            )
        return pd.read_sql_query("SELECT * FROM modbus_events ORDER BY timestamp DESC LIMIT 500", conn)

    def get_detections(self, experiment_id: Optional[str] = None) -> pd.DataFrame:
        conn = self.get_connection()
        if experiment_id:
            return pd.read_sql_query(
                "SELECT * FROM detections WHERE experiment_id = ? ORDER BY timestamp ASC",
                conn,
                params=(experiment_id,),
            )
        return pd.read_sql_query("SELECT * FROM detections ORDER BY timestamp DESC LIMIT 500", conn)

    def get_evaluations(self, experiment_id: Optional[str] = None) -> pd.DataFrame:
        conn = self.get_connection()
        if experiment_id:
            return pd.read_sql_query(
                "SELECT * FROM evaluation_results WHERE experiment_id = ? ORDER BY id ASC",
                conn,
                params=(experiment_id,),
            )
        return pd.read_sql_query("SELECT * FROM evaluation_results ORDER BY computed_at DESC", conn)

    def reset_all_data(self) -> None:
        """Truncates all tables while preserving schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        for table in ["evaluation_results", "detections", "modbus_events", "process_telemetry", "experiments"]:
            cursor.execute(f"DELETE FROM {table};")
        conn.commit()
