"""Experiment management routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.services.simulation import get_simulation_service

router = APIRouter()

EXPERIMENT_TYPES = [
    {"id": "normal", "name": "Normal Operation Baseline", "description": "Runs clean baseline — used to train the ML model."},
    {"id": "sensor_spoofing", "name": "Sensor Spoofing", "description": "Full warmup → attack → cooldown experiment with detection."},
    {"id": "unauthorized_write", "name": "Unauthorized Write", "description": "Full warmup → attack → cooldown experiment with detection."},
    {"id": "replay", "name": "Replay Attack", "description": "Full warmup → attack → cooldown experiment with detection."},
    {"id": "command_flood", "name": "Command Flood", "description": "Full warmup → attack → cooldown experiment with detection."},
    {"id": "setpoint_manipulation", "name": "Setpoint Manipulation", "description": "Full warmup → attack → cooldown experiment with detection."},
]


class StartExperimentRequest(BaseModel):
    experiment_type: str = Field(..., description="Experiment type identifier")
    params: dict = Field(default_factory=dict, description="Optional phase durations")


@router.get("/types")
def list_experiment_types():
    return EXPERIMENT_TYPES


@router.get("")
def list_experiments():
    """Returns all experiments from the database."""
    svc = get_simulation_service()
    return svc.get_experiments_from_db()


@router.post("/start")
def start_experiment(req: StartExperimentRequest):
    valid = {e["id"] for e in EXPERIMENT_TYPES}
    if req.experiment_type not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown experiment type: {req.experiment_type}")
    svc = get_simulation_service()
    job_id = svc.start_experiment_job(req.experiment_type, req.params)
    return {"job_id": job_id, "status": "QUEUED", "experiment_type": req.experiment_type}


@router.get("/jobs")
def list_experiment_jobs():
    svc = get_simulation_service()
    return svc.list_experiment_jobs()


@router.get("/jobs/{job_id}")
def get_experiment_job(job_id: str):
    svc = get_simulation_service()
    job = svc.get_experiment_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Experiment job {job_id} not found")
    return job
