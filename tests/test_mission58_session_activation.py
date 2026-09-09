import time
from security.enrollment_session_bridge import EnrollmentSessionBridge
from security.activation_replay_guard import ActivationReplayGuard


def test_enrollment_secret_can_activate_device_bound_session():
    bridge = EnrollmentSessionBridge(ttl_seconds=600)
    secret = b"x" * 32
    bridge.register_enrollment_secret("d1", secret)
    ts = int(time.time())
    nonce = "n1"
    proof = bridge.build_proof("d1", nonce, ts)

    def issue(device_id, ttl):
        assert device_id == "d1"
        return "sess-123", ts + ttl

    result = bridge.activate("d1", nonce, ts, proof, issue)
    assert result.device_id == "d1"
    assert result.session_id == "sess-123"


def test_invalid_proof_is_rejected():
    bridge = EnrollmentSessionBridge()
    bridge.register_enrollment_secret("d1", b"x" * 32)
    ts = int(time.time())
    try:
        bridge.activate("d1", "n", ts, "bad", lambda d, t: ("s", ts+t))
    except PermissionError:
        pass
    else:
        assert False


def test_unknown_device_is_rejected():
    bridge = EnrollmentSessionBridge()
    ts = int(time.time())
    try:
        bridge.activate("unknown", "n", ts, "bad", lambda d, t: ("s", ts+t))
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
