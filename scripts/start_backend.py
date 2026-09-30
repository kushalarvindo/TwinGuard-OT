"""
TwinGuard-OT Backend Startup Script.
Launches the FastAPI server with uvicorn.
"""

import sys
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent


def start_backend(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    print("=" * 60)
    print("  TwinGuard-OT — FastAPI Backend")
    print("=" * 60)
    print(f"  API:       http://{host}:{port}")
    print(f"  Docs:      http://{host}:{port}/docs")
    print(f"  WebSocket: ws://{host}:{port}/ws/telemetry")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info",
    ]
    if reload:
        cmd.append("--reload")

    subprocess.run(cmd, cwd=str(root))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TwinGuard-OT Backend Launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    start_backend(host=args.host, port=args.port, reload=args.reload)
