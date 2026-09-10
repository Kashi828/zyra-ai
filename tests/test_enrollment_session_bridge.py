import time

import pytest

from security.enrollment_session_bridge import EnrollmentSessionBridge


class FakeStore:
    def __init__(self, device_id="dev_1", secret=b"s" * 32):
        self.device_id = device_id
        self.secret = secret
        self.revoked = False
        self.sessions = {}

    def get_device(self, device_id):
        if device_id != self.device_id:
            return None
        return {"device_id": device_id, "revoked": self.revoked}

    def verify_proof(self, device_id, nonce, timestamp, proof):
        if device_id != self.device_id or self.revoked:
            return False
        return proof == EnrollmentSessionBridge.proof(self.secret, nonce, timestamp)

    def issue_session(self, device_id, session_id, ttl_seconds):
        expires = int(time.time()) + ttl_seconds
        self.sessions[session_id] = (device_id, expires)
        return expires


def test_activation_rejects_replayed_nonce():
    store = FakeStore()
    bridge = EnrollmentSessionBridge(store)
    now = int(time.time())
    nonce = "nonce-1"
    proof = bridge.build_proof(store.secret, nonce, now)
    verify = store.verify_proof

    first = bridge.activate(store.device_id, nonce, now, proof, verify)
    assert first.device_id == store.device_id

    with pytest.raises(PermissionError, match="already used"):
        bridge.activate(store.device_id, nonce, now, proof, verify)


def test_activation_rejects_stale_proof():
    store = FakeStore()
    bridge = EnrollmentSessionBridge(store)
    timestamp = int(time.time()) - 91
    nonce = "nonce-stale"
    proof = bridge.build_proof(store.secret, nonce, timestamp)

    with pytest.raises(PermissionError, match="stale"):
        bridge.activate(store.device_id, nonce, timestamp, proof, store.verify_proof)


def test_activation_rejects_revoked_device():
    store = FakeStore()
    store.revoked = True
    bridge = EnrollmentSessionBridge(store)
    now = int(time.time())
    proof = bridge.build_proof(store.secret, "nonce-revoked", now)

    with pytest.raises(PermissionError, match="not enrolled"):
        bridge.activate(store.device_id, "nonce-revoked", now, proof, store.verify_proof)
