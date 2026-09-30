"""System health and status routes."""
from fastapi import APIRouter
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("/status")
def get_system_status():
    svc = get_simulation_service()
    return svc.get_system_status()
