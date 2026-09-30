"""
TwinGuard-OT Simulation Service.
Singleton that owns and runs all core subsystems (Tank, PLC, Modbus, Collector, Detectors).
The FastAPI application talks to this service; the existing logic is unchanged.
"""

import sys
import time
import threading
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque

# Ensure the src directory is on the path
_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.utils.logging import setup_logger
from twinguard.process.tank import WaterTank
from twinguard.plc.plc import VirtualPLC
from twinguard.modbus.server import TwinGuardModbusServer
from twinguard.modbus.registers import RegisterMap, REG_TANK_LEVEL_SENSOR, REG_SETPOINT_LEVEL
from twinguard.database.db import DatabaseManager
from twinguard.monitoring.collector import DataCollector
from twinguard.features.extractor import FeatureExtractor
from twinguard.detection.rules import RuleBasedDetector
from twinguard.detection.process_residual import DigitalTwinShadowModel
from twinguard.detection.isolation_forest import IsolationForestDetector
from twinguard.detection.correlation import CyberPhysicalCorrelator

logger = setup_logger("twinguard.api")


class SimulationService:
    """
    Owns the full TwinGuard-OT simulation runtime.
    Thread-safe singleton for the FastAPI application.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = False

        # Core subsystems (initialised in start())
        self.config: Dict[str, Any] = {}
        self.tank: Optional[WaterTank] = None
        self.plc: Optional[VirtualPLC] = None
        self.modbus_server: Optional[TwinGuardModbusServer] = None
        self.db: Optional[DatabaseManager] = None
        self.collector: Optional[DataCollector] = None

        # Detection pipeline
        self.extractor: Optional[FeatureExtractor] = None
        self.rule_detector: Optional[RuleBasedDetector] = None
        self.shadow_twin: Optional[DigitalTwinShadowModel] = None
        self.ml_detector: Optional[IsolationForestDetector] = None
        self.correlator: Optional[CyberPhysicalCorrelator] = None

        # Live state buffers
        self.live_telemetry: deque = deque(maxlen=600)   # 60 s @ 10 Hz
        self.live_alerts: deque = deque(maxlen=200)
        self.last_detection: Optional[Dict[str, Any]] = None
        self._prev_sample: Optional[Dict[str, Any]] = None

        # Active experiment / attack tracking
        self.current_exp_id: str = "EXP-LIVE-0000"

        # Background simulation loop
        self._sim_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Attack job registry
        self._attack_jobs: Dict[str, Dict[str, Any]] = {}
        # Experiment job registry
        self._experiment_jobs: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return

        self.config = load_system_config()
        root = get_project_root()

        sim_cfg = self.config.get("physical_process", {})
        plc_cfg = self.config.get("plc", {})
        mb_cfg  = self.config.get("modbus", {})
        det_cfg = self.config.get("detection", {})

        # Database
        db_path = self.config["storage"]["db_path_resolved"]
        self.db = DatabaseManager(db_path)
        self.current_exp_id = f"EXP-LIVE-{int(time.time()) % 10000:04d}"
        self.db.create_experiment(
            self.current_exp_id,
            name="Live API Session",
            attack_type="normal",
            notes="FastAPI backend session",
        )

        # Tank
        self.tank = WaterTank(
            capacity_liters=sim_cfg.get("capacity_liters", 1000.0),
            initial_level=sim_cfg.get("initial_level", 45.0),
            pump_inflow_rate=sim_cfg.get("pump_inflow_rate", 3.0),
            gravity_outflow_rate=sim_cfg.get("gravity_outflow_rate", 1.2),
            leak_outflow_rate=sim_cfg.get("leak_outflow_rate", 0.1),
            sensor_noise_std=sim_cfg.get("sensor_noise_std", 0.25),
        )

        # PLC
        self.plc = VirtualPLC(
            tank=self.tank,
            cycle_interval_sec=plc_cfg.get("cycle_interval_sec", 0.2),
            default_setpoint=plc_cfg.get("default_setpoint", 70.0),
            low_threshold=plc_cfg.get("low_threshold", 30.0),
            high_threshold=plc_cfg.get("high_threshold", 80.0),
            emergency_low=plc_cfg.get("emergency_low_threshold", 10.0),
            emergency_high=plc_cfg.get("emergency_high_threshold", 95.0),
        )

        # Modbus
        self.modbus_server = TwinGuardModbusServer(
            host=mb_cfg.get("host", "127.0.0.1"),
            port=mb_cfg.get("port", 5020),
            unit_id=mb_cfg.get("unit_id", 1),
        )

        # Collector
        self.collector = DataCollector(
            tank=self.tank,
            plc=self.plc,
            modbus_server=self.modbus_server,
            db=self.db,
            sample_interval_sec=self.config.get("simulation", {}).get("time_step_sec", 0.1),
        )
        self.collector.set_experiment_context(self.current_exp_id, is_attack_active=False, attack_type="normal")

        # Detection pipeline
        self.extractor = FeatureExtractor(
            high_threshold=plc_cfg.get("high_threshold", 80.0)
        )
        self.rule_detector = RuleBasedDetector(
            residual_threshold=det_cfg.get("residual_threshold", 10.0),
            flood_request_rate=det_cfg.get("request_rate_flood_threshold", 30.0),
        )
        self.shadow_twin = DigitalTwinShadowModel(
            initial_level=sim_cfg.get("initial_level", 50.0),
            residual_threshold=det_cfg.get("residual_threshold", 10.0),
        )
        self.ml_detector = IsolationForestDetector()
        model_path = root / self.config["storage"].get("models_dir", "data/models") / "isolation_forest.joblib"
        loaded = self.ml_detector.load(model_path)
        if loaded:
            logger.info("[TwinGuard] Isolation Forest model loaded from disk.")
        else:
            logger.warning("[TwinGuard] No trained model found; ML detection will be skipped until trained.")

        self.correlator = CyberPhysicalCorrelator()

        # Start subsystems
        self.modbus_server.start()
        self.plc.start()
        self.collector.start()

        # Background physics loop
        self._stop_event.clear()
        self._sim_thread = threading.Thread(
            target=self._simulation_loop,
            name="SimulationLoop",
            daemon=True,
        )
        self._sim_thread.start()

        self._started = True
        logger.info("[TwinGuard] API started — all subsystems online.")
        logger.info(f"[TwinGuard] Digital Twin initialized (level={self.tank.current_level:.1f}%)")
        logger.info(f"[TwinGuard] Modbus server listening on {self.modbus_server.host}:{self.modbus_server.port}")
        logger.info("[TwinGuard] Detection engine active.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._sim_thread and self._sim_thread.is_alive():
            self._sim_thread.join(timeout=2.0)
        if self.collector:
            self.collector.stop()
        if self.plc:
            self.plc.stop()
        if self.modbus_server:
            self.modbus_server.stop()
        if self.db and self.current_exp_id:
            self.db.finish_experiment(self.current_exp_id, status="COMPLETED")
        logger.info("[TwinGuard] System stopped cleanly.")

    # ------------------------------------------------------------------
    # Core simulation loop
    # ------------------------------------------------------------------

    def _simulation_loop(self) -> None:
        """Advances tank physics at ~10 Hz and runs the detection pipeline."""
        while not self._stop_event.is_set():
            t0 = time.time()

            if self.tank and self.plc:
                state = self.tank.step(dt=0.1)
                plc_status = self.plc.get_status()

                # Shadow twin step
                expected_lvl = state["sensor_level"]
                residual = state["residual"]
                if self.shadow_twin:
                    expected_lvl, residual, _ = self.shadow_twin.step(
                        pump_command=self.tank.pump.state,
                        valve_command=self.tank.valve.state,
                        dt=0.1,
                        observed_sensor_level=state["sensor_level"],
                    )

                curr_dict = {
                    "timestamp": state["timestamp"],
                    "sensor_level": state["sensor_level"],
                    "true_level": state["true_level"],
                    "process_residual": residual,
                    "inflow_rate": state["true_inflow"],
                    "outflow_rate": state["true_outflow"],
                    "pump_state": state["pump_state"],
                    "valve_state": state["valve_state"],
                    "setpoint": plc_status["setpoint"],
                    "request_rate": self.modbus_server.current_request_rate if self.modbus_server else 0.0,
                }

                features = {}
                if self.extractor:
                    features = self.extractor.extract_from_row(curr_dict, self._prev_sample)
                self._prev_sample = curr_dict

                # Detection
                detection_result = None
                if self.rule_detector and self.correlator:
                    rule_results = self.rule_detector.evaluate(features)
                    ml_anomaly, ml_score = False, 0.0
                    if self.ml_detector and self.ml_detector.is_trained:
                        ml_anomaly, ml_score, _ = self.ml_detector.predict_sample(features)
                    corr = self.correlator.correlate(rule_results, ml_anomaly, ml_score, features)

                    detection_result = {
                        "timestamp": state["timestamp"],
                        "is_anomaly": corr.is_anomaly,
                        "category": corr.category,
                        "severity": corr.severity,
                        "anomaly_score": corr.anomaly_score,
                        "ml_anomaly": corr.ml_anomaly,
                        "cyber_anomaly": corr.cyber_anomaly,
                        "physical_anomaly": corr.physical_anomaly,
                        "explanation": corr.explanation,
                        "active_rules": corr.active_rules,
                    }
                    self.last_detection = detection_result

                    if corr.is_anomaly:
                        alert = {
                            **detection_result,
                            "id": str(uuid.uuid4())[:8],
                        }
                        self.live_alerts.appendleft(alert)

                # Build telemetry record
                active_attack = self._get_active_attack_name()
                telemetry_record = {
                    "timestamp": state["timestamp"],
                    "true_level": state["true_level"],
                    "sensor_level": state["sensor_level"],
                    "residual": round(residual, 2),
                    "inflow": state["true_inflow"],
                    "outflow": state["true_outflow"],
                    "pump_state": state["pump_state"],
                    "valve_state": state["valve_state"],
                    "setpoint": plc_status["setpoint"],
                    "low_threshold": plc_status["low_threshold"],
                    "high_threshold": plc_status["high_threshold"],
                    "alarm_state": plc_status["alarm_state"],
                    "is_overflow": state["is_overflow"],
                    "is_dry_run": state["is_dry_run"],
                    "sensor_spoofed": state.get("sensor_spoofed", False),
                    "request_rate": curr_dict["request_rate"],
                    "anomaly_score": detection_result["anomaly_score"] if detection_result else 0.0,
                    "is_anomaly": detection_result["is_anomaly"] if detection_result else False,
                    "active_attack": active_attack,
                    "plc_mode": "AUTO" if plc_status["auto_mode"] == 1 else "MANUAL",
                }
                self.live_telemetry.append(telemetry_record)

            elapsed = time.time() - t0
            sleep_time = max(0.01, 0.1 - elapsed)
            time.sleep(sleep_time)

    def _get_active_attack_name(self) -> Optional[str]:
        for job in self._attack_jobs.values():
            if job.get("status") == "RUNNING":
                return job.get("attack_type")
        return None

    # ------------------------------------------------------------------
    # Attack job management
    # ------------------------------------------------------------------

    def start_attack_job(self, attack_type: str, params: Dict[str, Any]) -> str:
        """Creates and starts an attack as a background job. Returns job_id."""
        job_id = str(uuid.uuid4())[:12]
        job = {
            "job_id": job_id,
            "attack_type": attack_type,
            "status": "QUEUED",
            "params": params,
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
            "_attack_obj": None,
        }
        self._attack_jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_attack_job,
            args=(job_id,),
            name=f"AttackJob-{job_id}",
            daemon=True,
        )
        thread.start()
        logger.info(f"[TwinGuard] Attack job queued: {attack_type} ({job_id})")
        return job_id

    def _run_attack_job(self, job_id: str) -> None:
        job = self._attack_jobs.get(job_id)
        if not job:
            return

        attack_type = job["attack_type"]
        params = job["params"]
        duration = float(params.get("duration_sec", 12.0))

        try:
            from twinguard.attacks.unauthorized_write import UnauthorizedWriteAttack
            from twinguard.attacks.sensor_spoofing import SensorSpoofingAttack
            from twinguard.attacks.replay import ReplayAttack
            from twinguard.attacks.command_flood import CommandFloodAttack
            from twinguard.attacks.setpoint_manipulation import SetpointManipulationAttack

            mb_cfg = self.config.get("modbus", {})
            port = mb_cfg.get("port", 5020)

            if attack_type == "sensor_spoofing":
                attack_obj = SensorSpoofingAttack(
                    tank=self.tank,
                    spoofed_level=float(params.get("spoofed_level", 20.0)),
                    target_port=port,
                    duration_sec=duration,
                )
            elif attack_type == "unauthorized_write":
                attack_obj = UnauthorizedWriteAttack(
                    target_port=port,
                    duration_sec=duration,
                )
            elif attack_type == "replay":
                attack_obj = ReplayAttack(
                    tank=self.tank,
                    target_port=port,
                    duration_sec=duration,
                )
            elif attack_type == "command_flood":
                attack_obj = CommandFloodAttack(
                    target_port=port,
                    requests_per_sec=int(params.get("requests_per_sec", 150)),
                    duration_sec=duration,
                )
            elif attack_type == "setpoint_manipulation":
                attack_obj = SetpointManipulationAttack(
                    plc=self.plc,
                    malicious_setpoint=float(params.get("malicious_setpoint", 98.0)),
                    target_port=port,
                    duration_sec=duration,
                )
            else:
                raise ValueError(f"Unknown attack type: {attack_type}")

            job["_attack_obj"] = attack_obj
            job["status"] = "RUNNING"
            job["started_at"] = time.time()

            # Update collector context
            if self.collector:
                self.collector.set_experiment_context(
                    self.current_exp_id, is_attack_active=True, attack_type=attack_type
                )

            logger.info(f"[TwinGuard] Attack started: {attack_type}")
            attack_obj.start()

            # Wait for attack to complete
            while attack_obj.is_running:
                time.sleep(0.2)

            job["result"] = attack_obj.get_status()
            job["status"] = "COMPLETED"
            logger.info(f"[TwinGuard] Attack completed: {attack_type}")

        except Exception as e:
            job["status"] = "FAILED"
            job["error"] = str(e)
            logger.error(f"[TwinGuard] Attack job {job_id} failed: {e}")
        finally:
            job["finished_at"] = time.time()
            if self.collector:
                self.collector.set_experiment_context(
                    self.current_exp_id, is_attack_active=False, attack_type="normal"
                )

    def stop_attack_job(self, job_id: str) -> bool:
        job = self._attack_jobs.get(job_id)
        if not job:
            return False
        attack_obj = job.get("_attack_obj")
        if attack_obj and attack_obj.is_running:
            attack_obj.stop()
        job["status"] = "STOPPED"
        job["finished_at"] = time.time()
        logger.info(f"[TwinGuard] Attack stopped by user: {job_id}")
        return True

    def get_attack_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._attack_jobs.get(job_id)
        if not job:
            return None
        attack_obj = job.get("_attack_obj")
        elapsed = 0.0
        if job["started_at"]:
            end = job.get("finished_at") or time.time()
            elapsed = round(end - job["started_at"], 1)
        duration = float(job["params"].get("duration_sec", 12.0))
        progress = min(1.0, elapsed / duration) if duration > 0 else 0.0
        return {
            "job_id": job["job_id"],
            "attack_type": job["attack_type"],
            "status": job["status"],
            "elapsed_sec": elapsed,
            "duration_sec": duration,
            "progress": round(progress, 3),
            "events_injected": attack_obj.events_injected if attack_obj else 0,
            "metrics": attack_obj.metrics if attack_obj else {},
            "error": job.get("error"),
        }

    def list_attack_jobs(self) -> List[Dict[str, Any]]:
        return [self.get_attack_job(jid) for jid in reversed(list(self._attack_jobs.keys()))]

    # ------------------------------------------------------------------
    # Experiment job management (wraps run_all_experiments logic)
    # ------------------------------------------------------------------

    def start_experiment_job(self, experiment_type: str, params: Dict[str, Any]) -> str:
        """Runs a full attack experiment asynchronously."""
        job_id = str(uuid.uuid4())[:12]
        job = {
            "job_id": job_id,
            "experiment_type": experiment_type,
            "status": "QUEUED",
            "phase": "WAITING",
            "params": params,
            "started_at": None,
            "finished_at": None,
            "result_path": None,
            "error": None,
            "progress_log": [],
        }
        self._experiment_jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_experiment_job,
            args=(job_id,),
            name=f"ExperimentJob-{job_id}",
            daemon=True,
        )
        thread.start()
        return job_id

    def _run_experiment_job(self, job_id: str) -> None:
        job = self._experiment_jobs.get(job_id)
        if not job:
            return

        experiment_type = job["experiment_type"]
        params = job["params"]

        try:
            job["status"] = "RUNNING"
            job["started_at"] = time.time()

            sys.path.insert(0, str(_root))
            sys.path.insert(0, str(_root / "src"))

            if experiment_type == "normal":
                from experiments.normal_operation import run_normal_baseline
                job["phase"] = "RUNNING"
                job["progress_log"].append("Running normal operation baseline...")
                result = run_normal_baseline(
                    duration_sec=float(params.get("duration_sec", 25.0)),
                )
                job["result_path"] = result
            else:
                from experiments.run_attack import run_attack_experiment
                warmup = float(params.get("warmup_sec", 6.0))
                duration = float(params.get("duration_sec", 12.0))
                cooldown = float(params.get("cooldown_sec", 6.0))

                def _phase_cb(phase: str) -> None:
                    job["phase"] = phase
                    job["progress_log"].append(f"Phase: {phase}")

                _phase_cb("BASELINE")
                result = run_attack_experiment(
                    attack_name=experiment_type,
                    warmup_sec=warmup,
                    attack_duration_sec=duration,
                    cooldown_sec=cooldown,
                )
                _phase_cb("COMPLETED")
                job["result_path"] = result

            job["status"] = "COMPLETED"
            job["phase"] = "COMPLETED"

        except Exception as e:
            job["status"] = "FAILED"
            job["phase"] = "FAILED"
            job["error"] = str(e)
            logger.error(f"[TwinGuard] Experiment job {job_id} failed: {e}")
        finally:
            job["finished_at"] = time.time()

    def get_experiment_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._experiment_jobs.get(job_id)
        if not job:
            return None
        elapsed = 0.0
        if job["started_at"]:
            end = job.get("finished_at") or time.time()
            elapsed = round(end - job["started_at"], 1)
        return {
            "job_id": job["job_id"],
            "experiment_type": job["experiment_type"],
            "status": job["status"],
            "phase": job["phase"],
            "elapsed_sec": elapsed,
            "result_path": job.get("result_path"),
            "error": job.get("error"),
            "progress_log": job.get("progress_log", []),
        }

    def list_experiment_jobs(self) -> List[Dict[str, Any]]:
        return [self.get_experiment_job(jid) for jid in reversed(list(self._experiment_jobs.keys()))]

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------

    def get_system_status(self) -> Dict[str, Any]:
        modbus_ok = bool(self.modbus_server and self.modbus_server.is_running)
        plc_ok = bool(self.plc and self.plc.is_running)
        collector_ok = bool(self.collector and self.collector.is_running)
        db_ok = bool(self.db)
        ml_ready = bool(self.ml_detector and self.ml_detector.is_trained)
        return {
            "digital_twin": "ONLINE" if self.tank else "OFFLINE",
            "virtual_plc": "ONLINE" if plc_ok else "OFFLINE",
            "modbus_server": "ONLINE" if modbus_ok else "OFFLINE",
            "telemetry_collector": "ONLINE" if collector_ok else "OFFLINE",
            "detection_engine": "ACTIVE" if self.rule_detector else "OFFLINE",
            "ml_model": "READY" if ml_ready else "NOT_TRAINED",
            "database": "ONLINE" if db_ok else "OFFLINE",
            "overall": "OPERATIONAL" if (modbus_ok and plc_ok and collector_ok) else "DEGRADED",
        }

    def get_twin_state(self) -> Dict[str, Any]:
        if not self.tank:
            return {}
        state = self.tank.get_state()
        plc_status = self.plc.get_status() if self.plc else {}
        return {
            **state,
            "setpoint": plc_status.get("setpoint", 70.0),
            "low_threshold": plc_status.get("low_threshold", 30.0),
            "high_threshold": plc_status.get("high_threshold", 80.0),
            "alarm_state": plc_status.get("alarm_state", 0),
            "plc_mode": "AUTO" if plc_status.get("auto_mode", 1) == 1 else "MANUAL",
        }

    def get_plc_status(self) -> Dict[str, Any]:
        if not self.plc:
            return {}
        return {
            **self.plc.get_status(),
            "is_running": self.plc.is_running,
        }

    def get_modbus_status(self) -> Dict[str, Any]:
        if not self.modbus_server:
            return {}
        return {
            "host": self.modbus_server.host,
            "port": self.modbus_server.port,
            "is_running": self.modbus_server.is_running,
            "transaction_count": self.modbus_server.transaction_count,
            "request_rate": self.modbus_server.update_request_rate(),
        }

    def get_modbus_registers(self) -> List[Dict[str, Any]]:
        if not self.modbus_server:
            return []
        regs = []
        for offset, meta in RegisterMap.METADATA.items():
            raw = self.modbus_server.get_register(offset)
            eng = RegisterMap.to_eng(offset, raw)
            regs.append({
                "offset": offset,
                "address": meta["address"],
                "name": meta["name"],
                "raw": raw,
                "value": eng,
                "unit": meta["unit"],
                "rw": meta["rw"],
            })
        return regs

    def get_modbus_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.db:
            return []
        df = self.db.get_modbus_events()
        if df.empty:
            return []
        records = df.tail(limit).to_dict(orient="records")
        return list(reversed(records))

    def get_recent_telemetry(self, limit: int = 300) -> List[Dict[str, Any]]:
        data = list(self.live_telemetry)
        return data[-limit:]

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.live_alerts)[:limit]

    def get_detection_status(self) -> Dict[str, Any]:
        det = self.last_detection or {}
        return {
            "is_anomaly": det.get("is_anomaly", False),
            "category": det.get("category", "NORMAL"),
            "severity": det.get("severity", "INFO"),
            "anomaly_score": det.get("anomaly_score", 0.0),
            "explanation": det.get("explanation", "No detection data yet."),
            "active_rules": det.get("active_rules", []),
            "ml_trained": bool(self.ml_detector and self.ml_detector.is_trained),
        }

    def _clean_nans(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        import math
        for r in records:
            for k, v in r.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    r[k] = None
        return records

    def get_experiments_from_db(self) -> List[Dict[str, Any]]:
        if not self.db:
            return []
        df = self.db.get_experiments()
        records = df.to_dict(orient="records") if not df.empty else []
        return self._clean_nans(records)

    def get_evaluations_from_db(self) -> List[Dict[str, Any]]:
        if not self.db:
            return []
        df = self.db.get_evaluations()
        records = df.to_dict(orient="records") if not df.empty else []
        return self._clean_nans(records)

    def get_datasets(self) -> List[Dict[str, Any]]:
        root = get_project_root()
        results_dir = root / self.config.get("storage", {}).get("results_dir", "data/results")
        datasets = []
        if results_dir.exists():
            for f in sorted(results_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
                stat = f.stat()
                datasets.append({
                    "id": f.stem,
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": stat.st_size,
                    "created": stat.st_mtime,
                })
        return datasets

    def get_analytics_data(self, experiment_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.db:
            return {}
        if experiment_id:
            df = self.db.get_telemetry_by_experiment(experiment_id)
        else:
            df = self.db.get_all_telemetry()
        if df.empty:
            return {"timeseries": [], "summary": {}}

        records = df[["timestamp", "true_level", "sensor_level", "process_residual",
                       "pump_state", "valve_state", "inflow_rate", "outflow_rate",
                       "label", "attack_type"]].tail(2000).to_dict(orient="records")
        records = self._clean_nans(records)
        
        det_df = self.db.get_detections(experiment_id)
        det_records = []
        if not det_df.empty:
            if "correlation_category" in det_df.columns:
                det_df = det_df.rename(columns={"correlation_category": "category"})
            
            if "category" in det_df.columns:
                det_records = det_df[["timestamp", "anomaly_score", "is_anomaly", "severity", "category"]].to_dict(orient="records")
            else:
                det_records = det_df[["timestamp", "anomaly_score", "is_anomaly", "severity"]].to_dict(orient="records")
            
            det_records = self._clean_nans(det_records)

        return {
            "timeseries": records,
            "detections": det_records,
        }

    # ------------------------------------------------------------------
    # Singleton instance
    # ------------------------------------------------------------------


_instance: Optional["SimulationService"] = None


def get_simulation_service() -> "SimulationService":
    global _instance
    if _instance is None:
        _instance = SimulationService()
    return _instance
