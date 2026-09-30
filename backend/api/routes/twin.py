"""Digital Twin state routes."""
from fastapi import APIRouter
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("/state")
def get_twin_state():
    svc = get_simulation_service()
    return svc.get_twin_state()


@router.get("/plc/status")
def get_plc_status():
    svc = get_simulation_service()
    return svc.get_plc_status()
