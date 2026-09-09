from dataclasses import dataclass
from enum import Enum

class TransferStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TransferSession:
    transfer_id: str
    source_device: str
    target_device: str
    filename: str
    total_bytes: int
    transferred_bytes: int = 0
    status: TransferStatus = TransferStatus.QUEUED
    error: str | None = None

    def update(self, transferred: int) -> None:
        self.transferred_bytes = max(0, min(transferred, self.total_bytes))
        if self.status == TransferStatus.QUEUED:
            self.status = TransferStatus.RUNNING
