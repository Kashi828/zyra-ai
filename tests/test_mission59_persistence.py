import time
from pathlib import Path

from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def test_device_trust_survives_new_store_instance(tmp_path):
    db = tmp_path / "security.sqlite3"
    s1 = PersistentDeviceStore(db)
    d, secret = PersistentEnrollment(s1).create_device({"pc.apps", "pc.web"})
    assert s1.verify_secret(d, secret)

    s2 = PersistentDeviceStore(db)
    assert s2.verify_secret(d, secret)
    info = s2.get_device(d)
    assert info["capabilities"] == frozenset({"pc.apps", "pc.web"})


def test_secret_is_not_stored_in_plaintext(tmp_path):
    db = tmp_path / "security.sqlite3"
    s = PersistentDeviceStore(db)
    d, secret = PersistentEnrollment(s).create_device({"pc.apps"})
    info = s.get_device(d)
    assert secret.hex() not in info["secret_hash"]
    assert len(info["secret_hash"]) == 64


def test_session_survives_store_reload(tmp_path):
    db = tmp_path / "security.sqlite3"
    s1 = PersistentDeviceStore(db)
    d, _ = PersistentEnrollment(s1).create_device(set())
    expires = s1.issue_session(d, "sess1", 60)
    assert expires > int(time.time())

    s2 = PersistentDeviceStore(db)
    assert s2.validate_session("sess1", d)


def test_revocation_survives_reload_and_invalidates_sessions(tmp_path):
    db = tmp_path / "security.sqlite3"
    s1 = PersistentDeviceStore(db)
    d, _ = PersistentEnrollment(s1).create_device(set())
    s1.issue_session(d, "sess1", 60)
    s1.revoke_device(d)

    s2 = PersistentDeviceStore(db)
    assert not s2.validate_session("sess1", d)


def test_session_expiration(tmp_path):
    db = tmp_path / "security.sqlite3"
    s = PersistentDeviceStore(db)
    d, _ = PersistentEnrollment(s).create_device(set())
    s.issue_session(d, "sess1", 0)
    assert not s.validate_session("sess1", d)


def test_sqlite_file_is_created(tmp_path):
    db = tmp_path / "security.sqlite3"
    PersistentDeviceStore(db)
    assert Path(db).exists()
