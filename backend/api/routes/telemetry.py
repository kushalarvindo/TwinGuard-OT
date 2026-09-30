"""Live telemetry query routes."""
from typing import Optional
from fastapi import APIRouter, Query
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("")
def get_telemetry(limit: int = Query(default=300, le=600)):
    svc = get_simulation_service()
    return svc.get_recent_telemetry(limit=limit)


@router.get("/latest")
def get_latest_telemetry():
    svc = get_simulation_service()
    tele = svc.get_recent_telemetry(limit=1)
    return tele[-1] if tele else {}
