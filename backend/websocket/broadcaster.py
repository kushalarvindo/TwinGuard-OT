"""
WebSocket manager for real-time telemetry streaming.
"""

import asyncio
import json
import time
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect


class TelemetryBroadcaster:
    """Manages connected WebSocket clients and broadcasts telemetry."""

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        """Sends payload to all connected clients, silently removing dead ones."""
        if not self._clients:
            return
        message = json.dumps(payload)
        dead: Set[WebSocket] = set()
        async with self._lock:
            clients_snapshot = set(self._clients)
        for ws in clients_snapshot:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self._clients -= dead


broadcaster = TelemetryBroadcaster()
