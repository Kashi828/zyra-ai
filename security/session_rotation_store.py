import hashlib
import hmac
import secrets
import sqlite3
import time
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class RefreshResult:
    session_id: str
    refresh_token: str
    expires_at: int


class SessionRotationStore:
    """Durable session + single-use refresh-token rotation store."""

    def __init__(self, db_path="data/zyra_security.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_hash TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                revoked INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_refresh_device
              ON refresh_tokens(device_id);
            CREATE INDEX IF NOT EXISTS idx_refresh_session
              ON refresh_tokens(session_id);
            """)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def issue(self, device_id: str, session_id: str, ttl_seconds: int = 7 * 24 * 3600):
        token = secrets.token_urlsafe(48)
        now = int(time.time())
        expires = now + int(ttl_seconds)
        with self._connect() as db:
            db.execute(
                "INSERT INTO refresh_tokens "
                "(token_hash, device_id, session_id, expires_at, used, revoked, created_at) "
                "VALUES (?, ?, ?, ?, 0, 0, ?)",
                (self.hash_token(token), device_id, session_id, expires, now),
            )
        return token, expires

    def consume(self, token: str, expected_device_id: str, new_session_id: str,
                session_issuer):
        token_hash = self.hash_token(token)
        now = int(time.time())
        with self._connect() as db:
            row = db.execute(
                "SELECT token_hash, device_id, session_id, expires_at, used, revoked "
                "FROM refresh_tokens WHERE token_hash=?",
                (token_hash,),
            ).fetchone()

            if not row:
                raise PermissionError("invalid refresh token")

            if row[1] != expected_device_id:
                raise PermissionError("refresh token device mismatch")

            if row[4] or row[5] or row[3] <= now:
                raise PermissionError("refresh token is expired, used, or revoked")

            # Rotate before issuing the replacement. Reuse cannot silently create
            # multiple live sessions from the same refresh token.
            db.execute(
                "UPDATE refresh_tokens SET used=1 WHERE token_hash=?",
                (token_hash,),
            )

        expires_at = session_issuer(expected_device_id, new_session_id)
        replacement, replacement_expires = self.issue(
            expected_device_id, new_session_id
        )
        return RefreshResult(new_session_id, replacement, replacement_expires)

    def revoke_for_device(self, device_id: str):
        with self._connect() as db:
            db.execute(
                "UPDATE refresh_tokens SET revoked=1 WHERE device_id=?",
                (device_id,),
            )

    def revoke_for_session(self, session_id: str):
        with self._connect() as db:
            db.execute(
                "UPDATE refresh_tokens SET revoked=1 WHERE session_id=?",
                (session_id,),
            )

    def purge(self):
        now = int(time.time())
        with self._connect() as db:
            db.execute(
                "DELETE FROM refresh_tokens WHERE expires_at <= ? OR used=1 OR revoked=1",
                (now,),
            )
