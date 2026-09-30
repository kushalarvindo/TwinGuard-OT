"""Analytics and evaluation routes."""
from typing import Optional
from fastapi import APIRouter, Query
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("/anomaly")
def get_anomaly_analytics(experiment_id: Optional[str] = Query(default=None)):
    svc = get_simulation_service()
    return svc.get_analytics_data(experiment_id=experiment_id)


@router.get("/process")
def get_process_analytics(experiment_id: Optional[str] = Query(default=None)):
    svc = get_simulation_service()
    return svc.get_analytics_data(experiment_id=experiment_id)


@router.get("/evaluation")
def get_evaluation_metrics():
    svc = get_simulation_service()
    return svc.get_evaluations_from_db()
