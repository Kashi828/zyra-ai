import pytest

from security.persistent_device_store import PersistentDeviceStore


def test_session_rotation_revokes_old_and_keeps_new(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    store.enroll_device("pc-1", b"x" * 32, {"pc.apps"})
    old = "sess_old"
    store.issue_session("pc-1", old, 900)

    new, device_id, expires_at = store.rotate_session(old, 900)

    assert device_id == "pc-1"
    assert expires_at > 0
    assert new != old
    assert store.validate_session(old, "pc-1") is False
    assert store.validate_session(new, "pc-1") is True


def test_rotation_rejects_replay_of_rotated_session(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    store.enroll_device("pc-1", b"x" * 32, {"pc.apps"})
    old = "sess_old"
    store.issue_session("pc-1", old, 900)
    store.rotate_session(old, 900)

    with pytest.raises(PermissionError, match="invalid or expired"):
        store.rotate_session(old, 900)
