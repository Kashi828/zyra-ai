import time

from security.enrollment_session_bridge import EnrollmentSessionBridge
from security.activation_replay_guard import ActivationReplayGuard
from security.persistent_device_store import PersistentDeviceStore


def _store(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    store.enroll_device("d1", b"x" * 32, {"pc.apps"})
    return store


def test_enrollment_secret_can_activate_device_bound_session(tmp_path):
    store = _store(tmp_path)
    bridge = EnrollmentSessionBridge(store, ttl_seconds=600)
    secret = b"x" * 32
    ts = int(time.time())
    nonce = "n1"
    proof = EnrollmentSessionBridge.proof(secret, nonce, ts)

    def verify(device_id, nonce_, timestamp, proof_):
        assert device_id == "d1"
        return proof_ == EnrollmentSessionBridge.proof(secret, nonce_, timestamp)

    result = bridge.activate("d1", nonce, ts, proof, verify)
    assert result.device_id == "d1"
    assert result.session_id.startswith("sess_")


def test_invalid_proof_is_rejected(tmp_path):
    store = _store(tmp_path)
    bridge = EnrollmentSessionBridge(store)
    ts = int(time.time())
    try:
        bridge.activate("d1", "n", ts, "bad", lambda *a: False)
    except PermissionError:
        pass
    else:
        assert False


def test_unknown_device_is_rejected(tmp_path):
    store = _store(tmp_path)
    bridge = EnrollmentSessionBridge(store)
    ts = int(time.time())
    try:
        bridge.activate("unknown", "n", ts, "bad", lambda *a: True)
    except PermissionError:
        pass
    else:
        assert False


def test_replay_guard_rejects_same_nonce():
    guard = ActivationReplayGuard()
    ts = int(time.time())
    assert guard.accept("d1", "n1", ts)
    assert not guard.accept("d1", "n1", ts)


def test_replay_guard_rejects_stale_timestamp():
    guard = ActivationReplayGuard(ttl_seconds=10)
    assert not guard.accept("d1", "n1", int(time.time()) - 100)


def test_protocol_files_exist():
    from pathlib import Path
    assert Path("api/session_activation_routes.py").exists()
    assert Path("android/app/src/main/java/com/zyra/session/DeviceSession.kt").exists()
    assert Path("android/app/src/main/java/com/zyra/session/SessionActivationPayload.kt").exists()
