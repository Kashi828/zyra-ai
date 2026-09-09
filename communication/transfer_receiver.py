import hashlib
from pathlib import Path

MAX_CHUNK = 1024 * 1024

class TransferReceiver:
    def __init__(self, destination: str, expected_size: int, expected_sha256: str):
        self.destination = Path(destination)
        self.expected_size = expected_size
        self.expected_sha256 = expected_sha256.lower()
        self.received = 0
        self._fh = None
        self._started = False
        self._complete = False

    def start(self) -> None:
        if self._started:
            raise ValueError("transfer already started")
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.destination.open("wb")
        self._started = True

    def accept(self, data: bytes) -> int:
        if not self._started or self._fh is None:
            raise ValueError("transfer not started")
        if self._complete:
            raise ValueError("transfer already complete")
        if len(data) > MAX_CHUNK:
            raise ValueError("chunk exceeds maximum size")
        if self.received + len(data) > self.expected_size:
            raise ValueError("transfer exceeds expected size")
        self._fh.write(data)
        self._fh.flush()
        self.received += len(data)
        return self.received

    def finish(self) -> bool:
        if not self._started or self._fh is None:
            raise ValueError("transfer not started")
        if self.received != self.expected_size:
            raise ValueError("transfer incomplete")
        self._fh.close()
        self._fh = None

        digest = hashlib.sha256()
        with self.destination.open("rb") as f:
            while chunk := f.read(1024 * 1024):
                digest.update(chunk)
        self._complete = digest.hexdigest().lower() == self.expected_sha256
        if not self._complete:
            self.destination.unlink(missing_ok=True)
        return self._complete

    def cancel(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        self.destination.unlink(missing_ok=True)
        self._complete = False
