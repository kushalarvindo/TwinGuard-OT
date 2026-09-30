"""
TwinGuard-OT FastAPI Backend — Main Application.

Starts the simulation service, registers all routes, and drives the
real-time WebSocket telemetry broadcast loop.
"""

import sys
import asyncio
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Ensure project source is importable
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))

from backend.services.simulation import get_simulation_service
from backend.websocket.broadcaster import broadcaster
from backend.api.routes import system, twin, telemetry, modbus, attacks, detection, experiments, analytics, datasets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the simulation service on startup; stop it on shutdown."""
    svc = get_simulation_service()
    svc.start()

    # Launch real-time telemetry broadcast task (10 Hz → 100 ms per tick)
    task = asyncio.create_task(_telemetry_broadcast_loop(svc))
    yield
    task.cancel()
    svc.stop()


async def _telemetry_broadcast_loop(svc) -> None:
    """Pushes the latest telemetry frame to all WebSocket subscribers at ~5 Hz."""
    while True:
        try:
            tele = svc.get_recent_telemetry(limit=1)
            if tele:
                frame = tele[-1]
                # Attach live detection
                det = svc.get_detection_status()
                frame["detection"] = det
                # Attach active attack if any
                active = svc._get_active_attack_name()
                frame["active_attack"] = active
                await broadcaster.broadcast({"type": "telemetry", "data": frame})
        except Exception:
            pass
        await asyncio.sleep(0.2)   # 5 Hz


app = FastAPI(
    title="TwinGuard-OT API",
    description="Industrial Cybersecurity Digital Twin — FastAPI Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(system.router,      prefix="/api/system",      tags=["System"])
app.include_router(twin.router,        prefix="/api/twin",        tags=["Digital Twin"])
app.include_router(telemetry.router,   prefix="/api/telemetry",   tags=["Telemetry"])
app.include_router(modbus.router,      prefix="/api/modbus",      tags=["Modbus"])
app.include_router(attacks.router,     prefix="/api/attacks",     tags=["Attacks"])
app.include_router(detection.router,   prefix="/api/detection",   tags=["Detection"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["Experiments"])
app.include_router(analytics.router,   prefix="/api/analytics",   tags=["Analytics"])
app.include_router(datasets.router,    prefix="/api/datasets",    tags=["Datasets"])


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """Real-time telemetry stream — connect and receive JSON frames at ~5 Hz."""
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection alive; actual data is pushed by the broadcast loop
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "application": "TwinGuard-OT API",
        "version": "2.0.0",
        "docs": "/docs",
        "websocket": "ws://localhost:8000/ws/telemetry",
    }
