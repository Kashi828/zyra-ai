from dataclasses import dataclass
from communication.transfer_protocol import TransferEvent, TransferEventType

@dataclass
class TransferRuntime:
    transfer_id: str
    total: int
    transferred: int = 0
    cancelled: bool = False
    completed: bool = False

class TransferTransport:
    def __init__(self):
        self._runs: dict[str, TransferRuntime] = {}
        self._events: list[TransferEvent] = []

    def start(self, transfer_id: str, total: int, manifest: dict) -> None:
        self._runs[transfer_id] = TransferRuntime(transfer_id, total)
        self._events.append(TransferEvent(
            transfer_id, TransferEventType.START, 0, manifest
        ))

    def accept_chunk(self, transfer_id: str, sequence: int, size: int) -> TransferEvent:
        run = self._runs[transfer_id]
        if run.cancelled or run.completed:
            raise ValueError("transfer is not active")
        if size < 0 or size > 1024 * 1024:
            raise ValueError("invalid chunk size")
        run.transferred = min(run.total, run.transferred + size)
        ack = TransferEvent(transfer_id, TransferEventType.ACK, sequence, {})
        progress = TransferEvent(
            transfer_id, TransferEventType.PROGRESS, sequence,
            {"transferred": run.transferred, "total": run.total}
        )
        self._events.extend((ack, progress))
        return ack

    def cancel(self, transfer_id: str) -> TransferEvent:
        run = self._runs[transfer_id]
        if run.completed:
            raise ValueError("completed transfer cannot be cancelled")
        run.cancelled = True
        event = TransferEvent(transfer_id, TransferEventType.CANCEL, -1, {})
        self._events.append(event)
        return event

    def complete(self, transfer_id: str) -> TransferEvent:
        run = self._runs[transfer_id]
        if run.cancelled:
            raise ValueError("cancelled transfer cannot complete")
        if run.transferred != run.total:
            raise ValueError("transfer is incomplete")
        run.completed = True
        event = TransferEvent(transfer_id, TransferEventType.COMPLETE, -1, {})
        self._events.append(event)
        return event

    def events(self, transfer_id: str) -> list[TransferEvent]:
        return [e for e in self._events if e.transfer_id == transfer_id]
