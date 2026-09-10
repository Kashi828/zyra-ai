import hashlib
import hmac
import secrets
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
    def _hash_secret(secret: bytes) -> str:
        return hashlib.sha256(secret).hexdigest()

    def enroll_device(self, device_id: str, secret: bytes, capabilities):
        if not device_id or not isinstance(secret, (bytes, bytearray)) or len(secret) < 32:
            raise ValueError("invalid device enrollment")
        now = int(time.time())
        caps = "\n".join(sorted(set(str(c) for c in capabilities)))
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO trusted_devices "
                "(device_id, secret_hash, capabilities, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (device_id, self._hash_secret(bytes(secret)), caps, now),
            )

    def get_device(self, device_id: str):
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
            "capabilities": frozenset(filter(None, row[2].split("\n"))),
            "revoked": bool(row[3]),
            "created_at": row[4],
        }

    def verify_secret(self, device_id: str, secret: bytes) -> bool:
        device = self.get_device(device_id)
        if not device or device["revoked"]:
            return False
        if not isinstance(secret, (bytes, bytearray)):
            return False
        return hmac.compare_digest(self._hash_secret(bytes(secret)), device["secret_hash"])

    def issue_session(self, device_id: str, session_id: str, ttl_seconds: int = 900):
        if not device_id or not session_id:
            raise ValueError("invalid session")
        now = int(time.time())
        expires_at = now + int(ttl_seconds)
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO device_sessions "
                "(session_id, device_id, expires_at, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (session_id, device_id, expires_at, now),
            )
        return expires_at

    def get_session(self, session_id: str):
        with self._connect() as db:
            row = db.execute(
                "SELECT session_id, device_id, expires_at, revoked, created_at "
                "FROM device_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "session_id": row[0],
            "device_id": row[1],
            "expires_at": int(row[2]),
            "revoked": bool(row[3]),
            "created_at": int(row[4]),
        }

    def get_session_expires_at(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            raise PermissionError("session not found")
        return session["expires_at"]

    def list_sessions(self, device_id: str, include_inactive: bool = False):
        query = "SELECT session_id, expires_at, revoked, created_at FROM device_sessions WHERE device_id=?"
        params = [device_id]
        if not include_inactive:
            query += " AND revoked=0 AND expires_at>?"
            params.append(int(time.time()))
        query += " ORDER BY created_at DESC"
        with self._connect() as db:
            rows = db.execute(query, tuple(params)).fetchall()
        return tuple({
            "session_id": row[0],
            "expires_at": int(row[1]),
            "revoked": bool(row[2]),
            "created_at": int(row[3]),
        } for row in rows)

    def validate_session(self, session_id: str, device_id: str) -> bool:
        now = int(time.time())
        with self._connect() as db:
            row = db.execute(
                "SELECT expires_at, revoked FROM device_sessions "
                "WHERE session_id=? AND device_id=?",
                (session_id, device_id),
            ).fetchone()
        return bool(row and not row[1] and row[0] > now)

    def revoke_session(self, session_id: str):
        with self._lock, self._connect() as db:
            db.execute("UPDATE device_sessions SET revoked=1 WHERE session_id=?", (session_id,))

    def revoke_device_sessions(self, device_id: str):
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE device_sessions SET revoked=1 WHERE device_id=? AND revoked=0",
                (device_id,),
            )

    def revoke_device(self, device_id: str):
        with self._lock, self._connect() as db:
            db.execute("UPDATE trusted_devices SET revoked=1 WHERE device_id=?", (device_id,))
            db.execute("UPDATE device_sessions SET revoked=1 WHERE device_id=?", (device_id,))

    def issue_session_id(self):
        return "sess_" + secrets.token_urlsafe(18)
