"""Attack simulator routes with asynchronous job execution."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.services.simulation import get_simulation_service

router = APIRouter()


ATTACK_CATALOGUE = [
    {
        "id": "sensor_spoofing",
        "name": "Sensor Spoofing",
        "description": "Falsifies the tank level sensor reading, causing the PLC to make control decisions based on false data. The true physical state diverges from the reported state.",
        "category": "DATA_INTEGRITY",
        "severity": "CRITICAL",
        "target": "127.0.0.1:5020",
        "params": {
            "spoofed_level": {"type": "float", "default": 20.0, "min": 0.0, "max": 100.0, "description": "False level value injected (%)"},
            "duration_sec": {"type": "float", "default": 15.0, "min": 5.0, "max": 60.0, "description": "Attack duration (s)"},
        },
        "expected_effect": "True level rises while PLC sees low reading, risking overflow",
    },
    {
        "id": "unauthorized_write",
        "name": "Unauthorized Register Write",
        "description": "Simulates a rogue client writing directly to critical PLC holding registers without authorization, bypassing the control ladder.",
        "category": "UNAUTHORIZED_ACCESS",
        "severity": "HIGH",
        "target": "127.0.0.1:5020",
        "params": {
            "duration_sec": {"type": "float", "default": 10.0, "min": 5.0, "max": 60.0, "description": "Attack duration (s)"},
        },
        "expected_effect": "Unauthorized state changes in pump/valve commands",
    },
    {
        "id": "replay",
        "name": "Replay Attack",
        "description": "Captures a historical sensor reading snapshot and replays it continuously, decoupling the reported state from real-time physical measurements.",
        "category": "REPLAY",
        "severity": "HIGH",
        "target": "127.0.0.1:5020",
        "params": {
            "duration_sec": {"type": "float", "default": 12.0, "min": 5.0, "max": 60.0, "description": "Attack duration (s)"},
        },
        "expected_effect": "Stale sensor reading masks actual process changes",
    },
    {
        "id": "command_flood",
        "name": "Command Flood",
        "description": "Generates high-frequency Modbus TCP requests against the local virtual PLC, inducing abnormal network traffic and potential contention.",
        "category": "DENIAL_OF_SERVICE",
        "severity": "MEDIUM",
        "target": "127.0.0.1:5020",
        "params": {
            "requests_per_sec": {"type": "int", "default": 150, "min": 50, "max": 500, "description": "Flood rate (requests/s)"},
            "duration_sec": {"type": "float", "default": 8.0, "min": 5.0, "max": 30.0, "description": "Attack duration (s)"},
        },
        "expected_effect": "High request rate anomaly; potential PLC resource contention",
    },
    {
        "id": "setpoint_manipulation",
        "name": "Setpoint Manipulation",
        "description": "Modifies the PLC operational setpoint to a dangerous value (e.g., 98%), forcing the control logic to maintain an unsafe fill level.",
        "category": "CONFIGURATION_TAMPERING",
        "severity": "CRITICAL",
        "target": "127.0.0.1:5020",
        "params": {
            "malicious_setpoint": {"type": "float", "default": 98.0, "min": 85.0, "max": 100.0, "description": "Injected unsafe setpoint (%)"},
            "duration_sec": {"type": "float", "default": 12.0, "min": 5.0, "max": 60.0, "description": "Attack duration (s)"},
        },
        "expected_effect": "PLC commanded to maintain near-overflow fill level",
    },
]


class StartAttackRequest(BaseModel):
    attack_type: str = Field(..., description="Attack identifier from the catalogue")
    params: dict = Field(default_factory=dict, description="Attack-specific parameters")


@router.get("")
def list_attacks():
    """Returns the full attack catalogue."""
    return ATTACK_CATALOGUE


@router.post("/start")
def start_attack(req: StartAttackRequest):
    """Starts an attack asynchronously. Returns a job_id immediately."""
    valid_ids = {a["id"] for a in ATTACK_CATALOGUE}
    if req.attack_type not in valid_ids:
        raise HTTPException(status_code=400, detail=f"Unknown attack type: {req.attack_type}. Valid: {sorted(valid_ids)}")

    svc = get_simulation_service()
    job_id = svc.start_attack_job(req.attack_type, req.params)
    return {"job_id": job_id, "status": "QUEUED", "attack_type": req.attack_type}


@router.get("/jobs")
def list_attack_jobs():
    """Returns all attack jobs."""
    svc = get_simulation_service()
    return svc.list_attack_jobs()


@router.get("/{job_id}")
def get_attack_job(job_id: str):
    """Returns status of a specific attack job."""
    svc = get_simulation_service()
    job = svc.get_attack_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Attack job {job_id} not found")
    return job


@router.post("/{job_id}/stop")
def stop_attack_job(job_id: str):
    """Stops a running attack job."""
    svc = get_simulation_service()
    ok = svc.stop_attack_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Attack job {job_id} not found or not running")
    return {"job_id": job_id, "status": "STOPPED"}
