import time

from security.persistent_device_store import PersistentDeviceStore


def test_revoke_device_sessions_preserves_device_trust(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    secret = b"x" * 32
    store.enroll_device("device-1", secret, {"pc.apps"})
    store.issue_session("device-1", "session-1", 900)
    store.issue_session("device-1", "session-2", 900)

    store.revoke_device_sessions("device-1")

    assert not store.validate_session("session-1", "device-1")
    assert not store.validate_session("session-2", "device-1")
    assert store.verify_secret("device-1", secret)
    assert store.get_device("device-1")["revoked"] is False
