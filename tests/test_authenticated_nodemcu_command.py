import time

import pytest

from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice
from core.nodemcu_command_bridge import NodeMCUCommandBridge
from security.persistent_authorization_gateway import PersistentAuthorizationGateway
from security.persistent_device_store import PersistentDeviceStore
from services.authenticated_nodemcu_command import (
    AuthenticatedNodeMCUCommand,
    AuthenticatedNodeMCUCommandExecutor,
)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, endpoint, action, payload):
        self.calls.append((endpoint, action, dict(payload)))
        return {"ok": True, "action": action}


def make_executor(tmp_path, capabilities=("iot.telemetry", "iot.gpio")):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    secret = b"s" * 32
    store.enroll_device("phone-1", secret, capabilities)
    session_id = store.issue_session_id()
    store.issue_session("phone-1", session_id, 300)
    gateway = PersistentAuthorizationGateway(store)
    transport = FakeTransport()
    adapter = NodeMCUAdapter(
        NodeMCUDevice("nodemcu-1", "http://127.0.0.1:8080", frozenset(capabilities)),
        transport,
    )
    return AuthenticatedNodeMCUCommandExecutor(gateway, NodeMCUCommandBridge(adapter)), transport, session_id


def test_authenticated_status_reaches_nodemcu(tmp_path):
    executor, transport, session_id = make_executor(tmp_path)
    result = executor.execute(AuthenticatedNodeMCUCommand("phone-1", session_id, "status", {}))
    assert result.ok is True
    assert transport.calls == [("http://127.0.0.1:8080", "status", {})]


def test_invalid_session_is_rejected_before_transport(tmp_path):
    executor, transport, _ = make_executor(tmp_path)
    with pytest.raises(PermissionError, match="invalid or expired"):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", "sess-invalid", "status", {}))
    assert transport.calls == []


def test_gpio_requires_enrolled_capability(tmp_path):
    executor, transport, session_id = make_executor(tmp_path, ("iot.telemetry",))
    with pytest.raises(PermissionError, match="capability is not granted"):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", session_id, "gpio.write", {"pin": 5, "value": 1}))
    assert transport.calls == []


def test_expired_session_is_rejected(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    store.enroll_device("phone-1", b"s" * 32, ("iot.telemetry",))
    session_id = store.issue_session_id()
    store.issue_session("phone-1", session_id, -1)
    gateway = PersistentAuthorizationGateway(store)
    transport = FakeTransport()
    bridge = NodeMCUCommandBridge(NodeMCUAdapter(
        NodeMCUDevice("nodemcu-1", "http://127.0.0.1:8080", frozenset({"iot.telemetry"})),
        transport,
    ))
    executor = AuthenticatedNodeMCUCommandExecutor(gateway, bridge)
    with pytest.raises(PermissionError, match="invalid or expired"):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", session_id, "status", {}))
    assert transport.calls == []
