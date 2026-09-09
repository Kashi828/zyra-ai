import time

from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment
from security.persistent_authorization_gateway import PersistentAuthorizationGateway
from services.remote_windows_bridge import RemoteWindowsBridge
from services.authenticated_command import CommandRequest


def setup(db):
    store = PersistentDeviceStore(db)
    device, secret = PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device, "sess1", 60)
    return store, device, secret


def test_authorizes_valid_persistent_session_and_capability(tmp_path):
    store, device, _ = setup(tmp_path / "security.sqlite3")
    gate = PersistentAuthorizationGateway(store)
    decision = gate.authorize(device, "sess1", "pc.apps")
    assert decision.allowed
    assert decision.reason == "authorized"


def test_rejects_missing_capability(tmp_path):
    store, device, _ = setup(tmp_path / "security.sqlite3")
    gate = PersistentAuthorizationGateway(store)
    decision = gate.authorize(device, "sess1", "pc.files")
    assert not decision.allowed
    assert "capability" in decision.reason


def test_rejects_revoked_device(tmp_path):
    store, device, _ = setup(tmp_path / "security.sqlite3")
    store.revoke_device(device)
    gate = PersistentAuthorizationGateway(store)
    decision = gate.authorize(device, "sess1", "pc.apps")
    assert not decision.allowed
    assert "revoked" in decision.reason


def test_authorization_survives_gateway_reload(tmp_path):
    db = tmp_path / "security.sqlite3"
    store, device, _ = setup(db)
    gate1 = PersistentAuthorizationGateway(store)
    assert gate1.authorize(device, "sess1", "pc.apps").allowed
    store2 = PersistentDeviceStore(db)
    gate2 = PersistentAuthorizationGateway(store2)
    assert gate2.authorize(device, "sess1", "pc.apps").allowed


def test_missing_context_rejected(tmp_path):
    store, device, _ = setup(tmp_path / "security.sqlite3")
    gate = PersistentAuthorizationGateway(store)
    assert not gate.authorize(device, "", "pc.apps").allowed


def test_remote_bridge_uses_persistent_authorization(tmp_path):
    store, device, _ = setup(tmp_path / "security.sqlite3")
    gate = PersistentAuthorizationGateway(store)
    calls = []

    def runner(action, payload):
        calls.append((action, payload))
        return "ok"

    bridge = RemoteWindowsBridge(runner=runner, auth_gateway=gate)
    request = CommandRequest("sess1", device, "open_app", {"name": "Calculator"})
    result = bridge.execute(request)
    assert result.accepted
    assert calls == [("open_app", {"name": "Calculator"})]


def test_remote_bridge_rejects_before_windows_runner_on_capability_denial(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    device, _ = PersistentEnrollment(store).create_device({"pc.files"})
    store.issue_session(device, "sess1", 60)
    gate = PersistentAuthorizationGateway(store)
    calls = []

    def runner(action, payload):
        calls.append((action, payload))
        return "should-not-run"

    bridge = RemoteWindowsBridge(runner=runner, auth_gateway=gate)
    request = CommandRequest("sess1", device, "open_app", {"name": "Calculator"})
    result = bridge.execute(request)
    assert not result.accepted
    assert calls == []
