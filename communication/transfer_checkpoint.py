from dataclasses import dataclass
from enum import Enum

class TransferStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TransferCheckpoint:
    transfer_id: str
    total_bytes: int
    transferred_bytes: int = 0
    next_sequence: int = 0
    status: TransferStatus = TransferStatus.QUEUED

    def checkpoint(self, transferred: int, next_sequence: int) -> None:
        if transferred < 0 or transferred > self.total_bytes:
            raise ValueError("invalid transferred byte count")
        if next_sequence < 0:
            raise ValueError("invalid sequence")
        self.transferred_bytes = transferred
        self.next_sequence = next_sequence
        self.status = TransferStatus.RUNNING

    def pause(self) -> None:
        if self.status not in {TransferStatus.RUNNING, TransferStatus.QUEUED}:
            raise ValueError("transfer cannot be paused")
        self.status = TransferStatus.PAUSED

    def resume(self) -> None:
        if self.status != TransferStatus.PAUSED:
            raise ValueError("transfer is not paused")
        self.status = TransferStatus.RUNNING

    def cancel(self) -> None:
        if self.status == TransferStatus.COMPLETED:
            raise ValueError("completed transfer cannot be cancelled")
        self.status = TransferStatus.CANCELLED
