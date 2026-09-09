import json
import sqlite3
import threading
import time
from pathlib import Path


class PersistentTaskStore:
    """Durable task control/checkpoint state stored in the security database."""

    TERMINAL = {"completed", "failed", "cancelled"}

    def __init__(self, db_path="data/zyra_security.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS task_controls (
                    task_id TEXT PRIMARY KEY,
                    owner_device_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approval_required INTEGER NOT NULL DEFAULT 0,
                    cancelled INTEGER NOT NULL DEFAULT 0,
                    checkpoint TEXT NOT NULL DEFAULT '{}',
                    updated_at INTEGER NOT NULL
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_owner ON task_controls(owner_device_id)"
            )

    def register(self, task_id, owner_device_id, status="queued", checkpoint=None):
        if not task_id or not owner_device_id:
            raise ValueError("task_id and owner_device_id are required")
        approval = status == "awaiting_approval"
        with self._lock, self._connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO task_controls
                (task_id, owner_device_id, status, approval_required, cancelled, checkpoint, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?)""",
                (
                    task_id,
                    owner_device_id,
                    status,
                    int(approval),
                    json.dumps(checkpoint or {}, separators=(",", ":")),
                    int(time.time()),
                ),
            )

    def get(self, task_id):
        with self._connect() as db:
            row = db.execute(
                """SELECT task_id, owner_device_id, status, approval_required,
                          cancelled, checkpoint, updated_at
                   FROM task_controls WHERE task_id=?""",
                (task_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "task_id": row[0],
            "owner_device_id": row[1],
            "status": row[2],
            "approval_required": bool(row[3]),
            "cancelled": bool(row[4]),
            "checkpoint": json.loads(row[5] or "{}"),
            "updated_at": row[6],
        }

    def set_status(self, task_id, status, checkpoint=None):
        task = self.get(task_id)
        if not task:
            raise KeyError(task_id)
        if task["status"] in self.TERMINAL and status != task["status"]:
            raise ValueError("task is already terminal")
        with self._lock, self._connect() as db:
            current_checkpoint = task["checkpoint"] if checkpoint is None else checkpoint
            db.execute(
                """UPDATE task_controls
                   SET status=?, approval_required=?, cancelled=?, checkpoint=?, updated_at=?
                   WHERE task_id=?""",
                (
                    status,
                    int(status == "awaiting_approval"),
                    int(status == "cancelled"),
                    json.dumps(current_checkpoint, separators=(",", ":")),
                    int(time.time()),
                    task_id,
                ),
            )

    def update_checkpoint(self, task_id, checkpoint):
        task = self.get(task_id)
        if not task:
            raise KeyError(task_id)
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE task_controls SET checkpoint=?, updated_at=? WHERE task_id=?",
                (json.dumps(checkpoint, separators=(",", ":")), int(time.time()), task_id),
            )

    def recoverable(self):
        with self._connect() as db:
            rows = db.execute(
                """SELECT task_id, owner_device_id, status, approval_required,
                          cancelled, checkpoint, updated_at
                   FROM task_controls
                   WHERE status NOT IN ('completed','failed','cancelled')
                   ORDER BY updated_at ASC"""
            ).fetchall()
        return [
            {
                "task_id": r[0],
                "owner_device_id": r[1],
                "status": r[2],
                "approval_required": bool(r[3]),
                "cancelled": bool(r[4]),
                "checkpoint": json.loads(r[5] or "{}"),
                "updated_at": r[6],
            }
            for r in rows
        ]
