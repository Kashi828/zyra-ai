from dataclasses import dataclass
from enum import Enum

MAX_CHUNK = 1024 * 1024

class TransferEventType(str, Enum):
    START = "transfer.start"
    CHUNK = "transfer.chunk"
    ACK = "transfer.ack"
    PROGRESS = "transfer.progress"
    CANCEL = "transfer.cancel"
    COMPLETE = "transfer.complete"
    FAIL = "transfer.fail"

@dataclass(frozen=True)
class TransferEvent:
    transfer_id: str
    event_type: TransferEventType
    sequence: int
    payload: dict

def make_start(transfer_id: str, manifest: dict) -> TransferEvent:
    return TransferEvent(transfer_id, TransferEventType.START, 0, manifest)

def make_chunk(transfer_id: str, sequence: int, data_b64: str) -> TransferEvent:
    if not data_b64:
        raise ValueError("chunk data required")
    return TransferEvent(
        transfer_id, TransferEventType.CHUNK, sequence,
        {"data_b64": data_b64}
    )

def make_ack(transfer_id: str, sequence: int) -> TransferEvent:
    return TransferEvent(transfer_id, TransferEventType.ACK, sequence, {})

def make_progress(transfer_id: str, sequence: int, transferred: int, total: int) -> TransferEvent:
    if transferred < 0 or total < 0 or transferred > total:
        raise ValueError("invalid transfer progress")
    return TransferEvent(
        transfer_id, TransferEventType.PROGRESS, sequence,
        {"transferred": transferred, "total": total}
    )
