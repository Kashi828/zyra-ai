import secrets
import time
from security.persistent_device_store import PersistentDeviceStore
from security.session_rotation_store import SessionRotationStore, RefreshResult


class SessionService:
    """Creates, rotates and revokes short-lived device-bound sessions."""

    def __init__(self, store: PersistentDeviceStore, refresh_store=None, session_ttl=900):
        self.store = store
        self.refresh_store = refresh_store or SessionRotationStore(store.db_path)
        self.session_ttl = int(session_ttl)

    def create(self, device_id: str):
        if not self.store.get_device(device_id) or self.store.get_device(device_id)["revoked"]:
            raise PermissionError("device is not trusted")
        session_id = "sess_" + secrets.token_urlsafe(18)
        self.store.issue_session(device_id, session_id, self.session_ttl)
        token, refresh_expires = self.refresh_store.issue(device_id, session_id)
        return {
            "session_id": session_id,
            "refresh_token": token,
            "expires_at": refresh_expires,
        }

    def refresh(self, device_id: str, refresh_token: str):
        new_session = "sess_" + secrets.token_urlsafe(18)

        def issuer(did, sid):
            return self.store.issue_session(did, sid, self.session_ttl)

        result = self.refresh_store.consume(
            refresh_token, device_id, new_session, issuer
        )
        return {
            "session_id": result.session_id,
            "refresh_token": result.refresh_token,
            "expires_at": result.expires_at,
        }

    def logout(self, device_id: str, session_id: str):
        self.store.revoke_session(session_id)
        self.refresh_store.revoke_for_session(session_id)

    def logout_device(self, device_id: str):
        self.store.revoke_device(device_id)
        self.refresh_store.revoke_for_device(device_id)
