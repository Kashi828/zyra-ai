import sqlite3
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PersistedTransfer:
    transfer_id: str
    source_device: str
    target_device: str
    filename: str
    destination: str
    total_bytes: int
    transferred_bytes: int
    next_sequence: int
    sha256: str
    status: str

class TransferStore:
    def __init__(self, db_path: str = "zyra_transfers.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS transfers ("
                "transfer_id TEXT PRIMARY KEY,"
                "source_device TEXT NOT NULL,"
                "target_device TEXT NOT NULL,"
                "filename TEXT NOT NULL,"
                "destination TEXT NOT NULL,"
                "total_bytes INTEGER NOT NULL,"
                "transferred_bytes INTEGER NOT NULL,"
                "next_sequence INTEGER NOT NULL,"
                "sha256 TEXT NOT NULL,"
                "status TEXT NOT NULL)"
            )

    def save(self, t: PersistedTransfer) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "INSERT INTO transfers "
                "(transfer_id, source_device, target_device, filename, destination, "
                "total_bytes, transferred_bytes, next_sequence, sha256, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(transfer_id) DO UPDATE SET "
                "transferred_bytes=excluded.transferred_bytes,"
                "next_sequence=excluded.next_sequence,"
                "status=excluded.status",
                (t.transfer_id, t.source_device, t.target_device, t.filename,
                 t.destination, t.total_bytes, t.transferred_bytes, t.next_sequence,
                 t.sha256, t.status),
            )

    def get(self, transfer_id: str):
        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "SELECT transfer_id, source_device, target_device, filename, destination, "
                "total_bytes, transferred_bytes, next_sequence, sha256, status "
                "FROM transfers WHERE transfer_id=?",
                (transfer_id,),
            ).fetchone()
        return PersistedTransfer(*row) if row else None

    def recoverable(self):
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT transfer_id, source_device, target_device, filename, destination, "
                "total_bytes, transferred_bytes, next_sequence, sha256, status "
                "FROM transfers WHERE status IN ('queued','running','paused') "
                "ORDER BY transfer_id"
            ).fetchall()
        return [PersistedTransfer(*row) for row in rows]

    def mark(self, transfer_id: str, status: str) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute("UPDATE transfers SET status=? WHERE transfer_id=?", (status, transfer_id))

def verified_resume_point(path: str, transferred_bytes: int) -> int:
    p = Path(path)
    if transferred_bytes <= 0 or not p.is_file():
        return 0
    return min(p.stat().st_size, transferred_bytes)
