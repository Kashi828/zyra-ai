from dataclasses import dataclass
from threading import Event, Thread, RLock
import time

@dataclass(frozen=True)
class RecoveryJob:
    transfer_id: str
    resume_bytes: int

class TransferRecoveryWorker:
    def __init__(self, recovery_manager, dispatcher, interval_seconds: float = 5.0):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.recovery_manager = recovery_manager
        self.dispatcher = dispatcher
        self.interval_seconds = interval_seconds
        self._stop = Event()
        self._thread: Thread | None = None
        self._lock = RLock()
        self.last_jobs: list[RecoveryJob] = []

    def run_once(self) -> list[RecoveryJob]:
        decisions = self.recovery_manager.scan()
        jobs = [
            RecoveryJob(d.transfer_id, d.resume_bytes)
            for d in decisions
            if d.action in {"resume", "resume_from_disk"}
        ]
        for job in jobs:
            self.dispatcher(job)
        with self._lock:
            self.last_jobs = jobs
        return jobs

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = Thread(target=self._loop, name="zyra-transfer-recovery", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t:
            t.join(timeout=max(1.0, self.interval_seconds + 1.0))

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            finally:
                self._stop.wait(self.interval_seconds)
