import json
from urllib.parse import urlparse

import pytest

from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice
from core.iot_nodemcu_transport import NodeMCUResult
from core.nodemcu_command_bridge import NodeMCUCommandBridge
from security.persistent_authorization_gateway import PersistentAuthorizationGateway
from services.authenticated_nodemcu_command import (
    AuthenticatedNodeMCUCommand,
    AuthenticatedNodeMCUCommandExecutor,
)


SECRET = "test-node-secret-" + "x" * 32


class SimulatedNodeMCUTransport:
    def __init__(self, secret):
        self.secret = secret
        self.calls = []
        self.gpio = {5: 0}

    def request(self, action, payload=None):
        self.calls.append((action, dict(payload or {})))
        if self.secret != SECRET:
            return NodeMCUResult(False, action, 401, {}, "device authentication failed")
        if action == "status":
            return NodeMCUResult(True, action, 200, {"device": "sim-node", "online": True})
        if action == "gpio.read":
            pin = int((payload or {}).get("pin", 5))
            return NodeMCUResult(True, action, 200, {"pin": pin, "value": self.gpio.get(pin, 0)})
        if action == "gpio.write":
            pin = int(payload["pin"])
            self.gpio[pin] = int(bool(payload["value"]))
            return NodeMCUResult(True, action, 200, {"pin": pin, "value": self.gpio[pin]})
        return NodeMCUResult(False, action, 403, {}, "action is not allowed")


class FakeStore:
    def __init__(self):
        self.device = {"device_id": "phone-1", "capabilities": ["iot.telemetry", "iot.gpio"], "revoked": False}
        self.session = {"session_id": "session-1", "device_id": "phone-1", "expires_at": 4_000_000_000}

    def get_device(self, device_id):
        return self.device if device_id == self.device["device_id"] else None

    def get_session(self, session_id):
        return self.session if session_id == self.session["session_id"] else None


class AllowingGateway(PersistentAuthorizationGateway):
    def __init__(self, store):
        self.store = store

    def authorize(self, device_id, session_id, capability):
        if device_id != self.store.device["device_id"] or session_id != self.store.session["session_id"]:
            return type("Decision", (), {"allowed": False, "reason": "invalid session"})()
        if capability not in self.store.device["capabilities"]:
            return type("Decision", (), {"allowed": False, "reason": "capability denied"})()
        return type("Decision", (), {"allowed": True, "reason": "authorized"})()


def build_executor():
    transport = SimulatedNodeMCUTransport(SECRET)
    device = NodeMCUDevice("node-1", "http://127.0.0.1:8080", ["iot.telemetry", "iot.gpio"])
    adapter = NodeMCUAdapter(device, transport=transport)
    bridge = NodeMCUCommandBridge(adapter)
    store = FakeStore()
    executor = AuthenticatedNodeMCUCommandExecutor(AllowingGateway(store), bridge)
    return executor, transport


def test_authenticated_status_reaches_simulated_nodemcu():
    executor, transport = build_executor()
    result = executor.execute(AuthenticatedNodeMCUCommand("phone-1", "session-1", "status", {}))
    assert result.success
    assert transport.calls == [("status", {})]


def test_authenticated_gpio_write_and_read_round_trip():
    executor, transport = build_executor()
    write = executor.execute(AuthenticatedNodeMCUCommand("phone-1", "session-1", "gpio.write", {"pin": 5, "value": True}))
    read = executor.execute(AuthenticatedNodeMCUCommand("phone-1", "session-1", "gpio.read", {"pin": 5}))
    assert write.success and read.success
    assert read.payload["value"] == 1
    assert [call[0] for call in transport.calls] == ["gpio.write", "gpio.read"]


def test_invalid_session_stops_before_nodemcu_transport():
    executor, transport = build_executor()
    with pytest.raises(PermissionError):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", "bad-session", "status", {}))
    assert transport.calls == []


def test_unsupported_action_stops_before_nodemcu_transport():
    executor, transport = build_executor()
    with pytest.raises(PermissionError):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", "session-1", "shell.exec", {"command": "whoami"}))
    assert transport.calls == []
