import hashlib
import hmac
import sqlite3
import threading
import time
from pathlib import Path


class PersistentDeviceStore:
    """Durable trusted-device, session, and ecosystem membership state."""

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
            CREATE INDEX IF NOT EXISTS idx_sessions_device ON device_sessions(device_id);
            CREATE TABLE IF NOT EXISTS ecosystem_devices (
                device_id TEXT PRIMARY KEY,
                device_type TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                endpoint TEXT NOT NULL DEFAULT '',
                online INTEGER NOT NULL DEFAULT 0,
                last_seen INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(device_id) REFERENCES trusted_devices(device_id)
            );
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(ecosystem_devices)").fetchall()}
            if "endpoint" not in columns:
                db.execute("ALTER TABLE ecosystem_devices ADD COLUMN endpoint TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def hash_secret(secret: bytes) -> str:
        return hashlib.sha256(secret).hexdigest()

    def enroll_device(self, device_id, secret: bytes, capabilities):
        if not device_id or len(secret) < 32:
            raise ValueError("invalid device enrollment")
        caps = ",".join(sorted(set(capabilities)))
        now = int(time.time())
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO trusted_devices "
                "(device_id, secret_hash, capabilities, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (device_id, self.hash_secret(secret), caps, now),
            )

    def get_device(self, device_id):
        with self._connect() as db:
            row = db.execute(
                "SELECT device_id, secret_hash, capabilities, revoked, created_at "
                "FROM trusted_devices WHERE device_id=?", (device_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "device_id": row[0], "secret_hash": row[1],
            "capabilities": frozenset(filter(None, row[2].split(","))),
            "revoked": bool(row[3]), "created_at": row[4],
        }

    def list_trusted_devices(self):
        with self._connect() as db:
            rows = db.execute(
                "SELECT device_id, secret_hash, capabilities, revoked, created_at "
                "FROM trusted_devices ORDER BY device_id"
            ).fetchall()
        return [
            {"device_id": r[0], "secret_hash": r[1],
             "capabilities": frozenset(filter(None, r[2].split(","))),
             "revoked": bool(r[3]), "created_at": r[4]}
            for r in rows
        ]

    def upsert_ecosystem_device(self, device_id, device_type, display_name="", online=True, endpoint=""):
        if not device_id or not device_type:
            raise ValueError("device_id and device_type are required")
        trusted = self.get_device(device_id)
        if not trusted or trusted["revoked"]:
            raise PermissionError("device is not trusted")
        now = int(time.time())
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO ecosystem_devices "
                "(device_id, device_type, display_name, endpoint, online, last_seen, revoked) "
                "VALUES (?, ?, ?, ?, ?, ?, 0) "
                "ON CONFLICT(device_id) DO UPDATE SET "
                "device_type=excluded.device_type, display_name=excluded.display_name, "
                "endpoint=CASE WHEN excluded.endpoint != '' THEN excluded.endpoint ELSE ecosystem_devices.endpoint END, "
                "online=excluded.online, last_seen=excluded.last_seen, revoked=0",
                (device_id, device_type, display_name, endpoint, int(bool(online)), now),
            )

    def get_ecosystem_device(self, device_id):
        with self._connect() as db:
            row = db.execute(
                "SELECT e.device_id, e.device_type, e.display_name, e.endpoint, e.online, "
                "e.last_seen, e.revoked, t.capabilities, t.revoked "
                "FROM ecosystem_devices e JOIN trusted_devices t ON t.device_id=e.device_id "
                "WHERE e.device_id=?", (device_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "device_id": row[0], "device_type": row[1], "display_name": row[2],
            "endpoint": row[3], "online": bool(row[4]), "last_seen": row[5],
            "revoked": bool(row[6] or row[8]),
            "capabilities": frozenset(filter(None, row[7].split(","))),
        }

    def set_ecosystem_online(self, device_id, online):
        now = int(time.time())
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE ecosystem_devices SET online=?, last_seen=? WHERE device_id=?",
                (int(bool(online)), now, device_id),
            )

    def list_ecosystem_devices(self):
        with self._connect() as db:
            rows = db.execute(
                "SELECT e.device_id, e.device_type, e.display_name, e.endpoint, e.online, e.last_seen, "
                "e.revoked, t.capabilities, t.revoked "
                "FROM ecosystem_devices e JOIN trusted_devices t ON t.device_id=e.device_id "
                "ORDER BY e.device_id"
            ).fetchall()
        return [
            {"device_id": r[0], "device_type": r[1], "display_name": r[2], "endpoint": r[3],
             "online": bool(r[4]), "last_seen": r[5], "revoked": bool(r[6] or r[8]),
             "capabilities": frozenset(filter(None, r[7].split(",")))}
            for r in rows
        ]

    def verify_secret(self, device_id, secret: bytes) -> bool:
        item = self.get_device(device_id)
        if not item or item["revoked"]:
            return False
        return hmac.compare_digest(item["secret_hash"], self.hash_secret(secret))

    def revoke_device(self, device_id):
        with self._lock, self._connect() as db:
            db.execute("UPDATE trusted_devices SET revoked=1 WHERE device_id=?", (device_id,))
            db.execute("UPDATE device_sessions SET revoked=1 WHERE device_id=?", (device_id,))
            db.execute("UPDATE ecosystem_devices SET revoked=1, online=0 WHERE device_id=?", (device_id,))

    def issue_session(self, device_id, session_id, ttl_seconds):
        item = self.get_device(device_id)
        if not item or item["revoked"]:
            raise PermissionError("device is not trusted")
        now = int(time.time())
        expires = now + int(ttl_seconds)
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO device_sessions (session_id, device_id, expires_at, revoked, created_at) "
                "VALUES (?, ?, ?, 0, ?)", (session_id, device_id, expires, now)
            )
        return expires

    def get_session(self, session_id):
        with self._connect() as db:
            row = db.execute(
                "SELECT session_id, device_id, expires_at, revoked, created_at "
                "FROM device_sessions WHERE session_id=?", (session_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "session_id": row[0], "device_id": row[1], "expires_at": int(row[2]),
            "revoked": bool(row[3]), "created_at": int(row[4]),
        }

    def get_session_expires_at(self, session_id):
        session = self.get_session(session_id)
        if not session:
            raise PermissionError("session not found")
        return session["expires_at"]

    def list_sessions(self, device_id, include_inactive=False, current_session_id=None):
        query = "SELECT session_id, expires_at, revoked, created_at FROM device_sessions WHERE device_id=?"
        params = [device_id]
        if not include_inactive:
            query += " AND revoked=0 AND expires_at>?"
            params.append(int(time.time()))
        query += " ORDER BY created_at DESC"
        with self._connect() as db:
            rows = db.execute(query, tuple(params)).fetchall()
        now = int(time.time())
        return tuple({
            "session_id": row[0], "expires_at": int(row[1]), "revoked": bool(row[2]),
            "created_at": int(row[3]), "current": row[0] == current_session_id,
            "active": not bool(row[2]) and int(row[1]) > now,
        } for row in rows)

    def validate_session(self, session_id, device_id=None):
        now = int(time.time())
        with self._connect() as db:
            row = db.execute(
                "SELECT session_id, device_id, expires_at, revoked FROM device_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if not row or (device_id is not None and row[1] != device_id) or row[3] or row[2] <= now:
            return False
        device = self.get_device(row[1])
        return bool(device and not device["revoked"])

    def revoke_session(self, session_id):
        with self._lock, self._connect() as db:
            db.execute("UPDATE device_sessions SET revoked=1 WHERE session_id=?", (session_id,))

    def revoke_device_sessions(self, device_id):
        with self._lock, self._connect() as db:
            db.execute("UPDATE device_sessions SET revoked=1 WHERE device_id=? AND revoked=0", (device_id,))

    def purge_expired_sessions(self):
        now = int(time.time())
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM device_sessions WHERE expires_at <= ? OR revoked=1", (now,))

    def issue_session_id(self):
        import secrets
        return "sess_" + secrets.token_urlsafe(18)
