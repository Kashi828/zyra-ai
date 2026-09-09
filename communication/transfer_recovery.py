from dataclasses import dataclass
from pathlib import Path
from communication.transfer_persistence import TransferStore, PersistedTransfer, verified_resume_point

@dataclass(frozen=True)
class RecoveryDecision:
    transfer_id: str
    action: str
    resume_bytes: int
    reason: str

class TransferRecoveryManager:
    def __init__(self, store: TransferStore):
        self.store = store

    def scan(self) -> list[RecoveryDecision]:
        decisions: list[RecoveryDecision] = []
        for t in self.store.recoverable():
            p = Path(t.destination)
            if t.transferred_bytes < 0 or t.transferred_bytes > t.total_bytes:
                self.store.mark(t.transfer_id, "failed")
                decisions.append(RecoveryDecision(t.transfer_id, "fail", 0, "invalid checkpoint"))
                continue
            existing = verified_resume_point(t.destination, t.transferred_bytes)
            if existing == 0 and t.transferred_bytes > 0:
                self.store.mark(t.transfer_id, "queued")
                decisions.append(RecoveryDecision(t.transfer_id, "restart", 0, "checkpoint not present on disk"))
                continue
            if existing < t.transferred_bytes:
                self.store.mark(t.transfer_id, "queued")
                decisions.append(RecoveryDecision(
                    t.transfer_id, "resume_from_disk", existing,
                    "destination shorter than checkpoint"
                ))
                continue
            decisions.append(RecoveryDecision(
                t.transfer_id, "resume", existing, "recoverable checkpoint"
            ))
        return decisions

    def complete_if_verified(self, transfer: PersistedTransfer, verifier) -> bool:
        if transfer.transferred_bytes != transfer.total_bytes:
            return False
        if verifier(transfer.destination, transfer.sha256, transfer.total_bytes):
            self.store.mark(transfer.transfer_id, "completed")
            return True
        self.store.mark(transfer.transfer_id, "failed")
        return False
