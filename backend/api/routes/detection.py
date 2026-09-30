"""Detection and alert routes."""
from fastapi import APIRouter, Query
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("/status")
def get_detection_status():
    svc = get_simulation_service()
    return svc.get_detection_status()


@router.get("/alerts")
def get_alerts(limit: int = Query(default=50, le=200)):
    svc = get_simulation_service()
    return svc.get_recent_alerts(limit=limit)
