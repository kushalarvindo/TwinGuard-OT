"""Dataset management routes."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.services.simulation import get_simulation_service

router = APIRouter()


@router.get("")
def list_datasets():
    svc = get_simulation_service()
    return svc.get_datasets()


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    svc = get_simulation_service()
    datasets = svc.get_datasets()
    match = next((d for d in datasets if d["id"] == dataset_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return match


@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: str):
    svc = get_simulation_service()
    datasets = svc.get_datasets()
    match = next((d for d in datasets if d["id"] == dataset_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    file_path = Path(match["path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")
    return FileResponse(
        path=str(file_path),
        filename=match["filename"],
        media_type="text/csv",
    )
