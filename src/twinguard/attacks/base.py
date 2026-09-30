"""
Base class for controlled ICS attack modules.
Enforces strict simulation isolation to 127.0.0.1 / localhost.
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LocalEnvironmentSecurityError(Exception):
    """Raised when an attack module attempts to target an external or non-localhost address."""
    pass


class BaseAttack(ABC):
    """
    Abstract base class for ICS cybersecurity attack scenarios.
    """

    ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

    def __init__(
        self,
        name: str,
        description: str,
        target_host: str = "127.0.0.1",
        target_port: int = 5020,
        duration_sec: float = 10.0,
    ) -> None:
        # Mandatory Safety Verification
        if target_host not in self.ALLOWED_HOSTS:
            raise LocalEnvironmentSecurityError(
                f"SECURITY VIOLATION: Target host '{target_host}' is not permitted. "
                "TwinGuard-OT attacks are strictly confined to the local virtual environment (127.0.0.1)."
            )

        self.name = name
        self.description = description
        self.target_host = target_host
        self.target_port = target_port
        self.duration_sec = duration_sec

        self.is_running: bool = False
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.events_injected: int = 0
        self.metrics: Dict[str, Any] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Starts attack execution in a background thread."""
        if not self.is_running:
            self._stop_event.clear()
            self.is_running = True
            self.start_time = time.time()
            self.events_injected = 0
            self._thread = threading.Thread(target=self._run_wrapper, name=f"Attack_{self.name}", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stops attack execution."""
        self._stop_event.set()
        self.is_running = False
        self.end_time = time.time()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run_wrapper(self) -> None:
        try:
            self.execute()
        finally:
            self.is_running = False
            self.end_time = time.time()

    @abstractmethod
    def execute(self) -> None:
        """Core attack execution logic. Must be overridden by subclasses."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Returns attack status summary."""
        now = time.time()
        elapsed = (now - self.start_time) if self.start_time else 0.0
        if not self.is_running and self.end_time and self.start_time:
            elapsed = self.end_time - self.start_time

        return {
            "name": self.name,
            "description": self.description,
            "is_running": self.is_running,
            "target": f"{self.target_host}:{self.target_port}",
            "duration_sec": self.duration_sec,
            "elapsed_sec": round(elapsed, 2),
            "events_injected": self.events_injected,
            "metrics": self.metrics,
        }
