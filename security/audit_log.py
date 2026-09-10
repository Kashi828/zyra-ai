from dataclasses import dataclass
import json
import sqlite3
import threading
import time
from pathlib import Path


@dataclass(frozen=True)
class AuditEvent:
    event_id: int
    event_type: str
    device_id: str
    session_id: str
    detail: str
    created_at: int


class AuditLog:
    """Durable, append-only security event history."""

    def __init__(self, db_path="data/zyra_security.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS security_audit_log (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                device_id TEXT NOT NULL DEFAULT '',
                session_id TEXT NOT NULL DEFAULT '',
                detail TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL
            )""")

    def record(self, event_type, device_id="", session_id="", detail="") -> AuditEvent:
        payload = detail if isinstance(detail, str) else json.dumps(detail, separators=(",", ":"), sort_keys=True)
        with self._lock, sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                "INSERT INTO security_audit_log(event_type,device_id,session_id,detail,created_at) VALUES(?,?,?,?,?)",
                (str(event_type)[:128], str(device_id)[:256], str(session_id)[:256], payload[:4096], int(time.time())),
            )
            return AuditEvent(cur.lastrowid, str(event_type)[:128], str(device_id)[:256], str(session_id)[:256], payload[:4096], int(time.time()))

    def recent(self, limit=100) -> tuple[AuditEvent, ...]:
        limit = max(1, min(int(limit), 500))
        with self._lock, sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT event_id,event_type,device_id,session_id,detail,created_at FROM security_audit_log ORDER BY event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple(AuditEvent(*row) for row in rows)
