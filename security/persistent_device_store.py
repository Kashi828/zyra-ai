import hashlib
import hmac
import sqlite3
import threading
import time
from pathlib import Path


class PersistentDeviceStore:
    """Durable trusted-device and session state."""

    def __init__(self, db_path="data/zyra_security.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS trusted_devices (
                device_id TEXT PRIMARY KEY,
                secret_hash TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS device_sessions (
                session_id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(device_id) REFERENCES trusted_devices(device_id)
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_device
              ON device_sessions(device_id);
            """)

    @staticmethod
    def hash_secret(secret: bytes) -> str:
        return hashlib.sha256(secret).hexdigest()

    def enroll_device(self, device_id, secret: bytes, capabilities):
        if not device_id or len(secret) < 32:
            raise ValueError("invalid device enrollment")
        caps = ",".join(sorted(set(capabilities)))
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO trusted_devices "
                "(device_id, secret_hash, capabilities, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (device_id, self.hash_secret(secret), caps, int(time.time())),
            )

    def get_device(self, device_id):
        with self._connect() as db:
            row = db.execute(
                "SELECT device_id, secret_hash, capabilities, revoked, created_at "
                "FROM trusted_devices WHERE device_id=?",
                (device_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "device_id": row[0],
            "secret_hash": row[1],
            "capabilities": frozenset(filter(None, row[2].split(","))),
            "revoked": bool(row[3]),
            "created_at": row[4],
        }

    def verify_secret(self, device_id, secret: bytes) -> bool:
        item = self.get_device(device_id)
        if not item or item["revoked"]:
            return False
        return hmac.compare_digest(item["secret_hash"], self.hash_secret(secret))

    def revoke_device(self, device_id):
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE trusted_devices SET revoked=1 WHERE device_id=?",
                (device_id,),
            )
            db.execute(
                "UPDATE device_sessions SET revoked=1 WHERE device_id=?",
                (device_id,),
            )

    def issue_session(self, device_id, session_id, ttl_seconds):
        item = self.get_device(device_id)
        if not item or item["revoked"]:
            raise PermissionError("device is not trusted")
        now = int(time.time())
        expires = now + int(ttl_seconds)
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO device_sessions "
                "(session_id, device_id, expires_at, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (session_id, device_id, expires, now),
            )
        return expires

    def validate_session(self, session_id, device_id=None):
        now = int(time.time())
        with self._connect() as db:
            row = db.execute(
                "SELECT session_id, device_id, expires_at, revoked "
                "FROM device_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if not row:
            return False
        if device_id is not None and row[1] != device_id:
            return False
        if row[3] or row[2] <= now:
            return False
        device = self.get_device(row[1])
        if not device or device["revoked"]:
            return False
        return True

    def revoke_session(self, session_id):
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE device_sessions SET revoked=1 WHERE session_id=?",
                (session_id,),
            )

    def revoke_device_sessions(self, device_id):
        """Revoke every active session for a device without changing trust state."""
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE device_sessions SET revoked=1 WHERE device_id=? AND revoked=0",
                (device_id,),
            )

    def purge_expired_sessions(self):
        now = int(time.time())
        with self._lock, self._connect() as db:
            db.execute(
                "DELETE FROM device_sessions WHERE expires_at <= ? OR revoked=1",
                (now,),
            )
