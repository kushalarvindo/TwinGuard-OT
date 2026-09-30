"""Modbus monitor routes."""
from fastapi import APIRouter, Query
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("/status")
def get_modbus_status():
    svc = get_simulation_service()
    return svc.get_modbus_status()


@router.get("/registers")
def get_modbus_registers():
    svc = get_simulation_service()
    return svc.get_modbus_registers()


@router.get("/events")
def get_modbus_events(limit: int = Query(default=100, le=500)):
    svc = get_simulation_service()
    return svc.get_modbus_events(limit=limit)
