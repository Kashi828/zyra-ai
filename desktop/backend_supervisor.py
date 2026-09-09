from __future__ import annotations

from dataclasses import dataclass
import socket
import subprocess
import sys
import time
from typing import Callable


class BackendSupervisorError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    startup_timeout: float = 15.0
    poll_interval: float = 0.25
    max_restarts: int = 2


class BackendSupervisor:
    """Owns a local ZYRA backend process and restarts it within strict bounds."""

    def __init__(
        self,
        config: BackendConfig | None = None,
        *,
        popen_factory: Callable[..., object] | None = None,
        socket_factory: Callable[..., object] | None = None,
    ):
        self.config = config or BackendConfig()
        self._popen_factory = popen_factory or subprocess.Popen
        self._socket_factory = socket_factory or socket.create_connection
        self.process = None
        self.restarts = 0

    @property
    def base_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}"

    def is_healthy(self) -> bool:
        try:
            sock = self._socket_factory(
                (self.config.host, self.config.port),
                timeout=min(1.0, self.config.startup_timeout),
            )
            sock.close()
            return True
        except OSError:
            return False

    def command(self) -> list[str]:
        return [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", self.config.host,
            "--port", str(self.config.port),
        ]

    def start(self) -> None:
        if self.process is not None and getattr(self.process, "poll", lambda: None)() is None:
            return
        self.process = self._popen_factory(
            self.command(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + self.config.startup_timeout
        while time.monotonic() < deadline:
            if self.is_healthy():
                return
            if getattr(self.process, "poll", lambda: None)() is not None:
                raise BackendSupervisorError("ZYRA backend exited during startup")
            time.sleep(self.config.poll_interval)
        self.stop()
        raise BackendSupervisorError("ZYRA backend startup timed out")

    def restart(self) -> None:
        if self.restarts >= self.config.max_restarts:
            raise BackendSupervisorError("ZYRA backend restart limit reached")
        self.stop()
        self.restarts += 1
        self.start()

    def stop(self) -> None:
        process = self.process
        self.process = None
        if process is None:
            return
        try:
            terminate = getattr(process, "terminate", None)
            if callable(terminate):
                terminate()
            wait = getattr(process, "wait", None)
            if callable(wait):
                wait(timeout=5)
        except Exception:
            kill = getattr(process, "kill", None)
            if callable(kill):
                kill()

    def close(self) -> None:
        self.stop()
