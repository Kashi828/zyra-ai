import pytest

from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice
from core.nodemcu_command_bridge import NodeMCUCommandBridge
from services.authenticated_nodemcu_command import (
    AuthenticatedNodeMCUCommand,
    AuthenticatedNodeMCUCommandExecutor,
)


SECRET = "test-node-secret-" + "x" * 32


class SimulatedNodeMCUTransport:
    """Deterministic in-process NodeMCU transport matching the adapter contract."""

    def __init__(self, secret):
        self.secret = secret
        self.calls = []
        self.gpio = {5: 0}

    def request(self, endpoint, action, payload):
        self.calls.append((endpoint, action, dict(payload)))
        if self.secret != SECRET:
            return {"ok": False, "status": 401, "error": "device authentication failed"}
        if action == "status":
            return {"ok": True, "device": "sim-node", "online": True}
        if action == "gpio.read":
            pin = int(payload.get("pin", 5))
            return {"ok": True, "pin": pin, "value": self.gpio.get(pin, 0)}
        if action == "gpio.write":
            pin = int(payload["pin"])
            self.gpio[pin] = int(bool(payload["value"]))
            return {"ok": True, "pin": pin, "value": self.gpio[pin]}
        return {"ok": False, "status": 403, "error": "action is not allowed"}


class FakeStore:
    def __init__(self):
        self.device = {
            "device_id": "phone-1",
            "capabilities": ["iot.telemetry", "iot.gpio"],
            "revoked": False,
        }
        self.session = {
            "session_id": "session-1",
            "device_id": "phone-1",
            "expires_at": 4_000_000_000,
        }

    def get_device(self, device_id):
        return self.device if device_id == self.device["device_id"] else None


class AllowingGateway:
    def __init__(self, store):
        self.store = store

    def authorize(self, device_id, session_id, capability):
        allowed = (
            device_id == self.store.device["device_id"]
            and session_id == self.store.session["session_id"]
            and capability in self.store.device["capabilities"]
        )
        return type(
            "Decision",
            (),
            {"allowed": allowed, "reason": "authorized" if allowed else "invalid session or capability"},
        )()


def build_executor():
    transport = SimulatedNodeMCUTransport(SECRET)
    device = NodeMCUDevice(
        "node-1",
        "http://127.0.0.1:8080",
        frozenset(["iot.telemetry", "iot.gpio"]),
    )
    adapter = NodeMCUAdapter(device, transport=transport)
    bridge = NodeMCUCommandBridge(adapter)
    store = FakeStore()
    executor = AuthenticatedNodeMCUCommandExecutor(AllowingGateway(store), bridge)
    return executor, transport


def test_authenticated_status_reaches_simulated_nodemcu():
    executor, transport = build_executor()
    result = executor.execute(AuthenticatedNodeMCUCommand("phone-1", "session-1", "status", {}))
    assert result.ok is True
    assert transport.calls == [("http://127.0.0.1:8080", "status", {})]


def test_authenticated_gpio_write_and_read_round_trip():
    executor, transport = build_executor()
    write = executor.execute(
        AuthenticatedNodeMCUCommand("phone-1", "session-1", "gpio.write", {"pin": 5, "value": True})
    )
    read = executor.execute(
        AuthenticatedNodeMCUCommand("phone-1", "session-1", "gpio.read", {"pin": 5})
    )
    assert write.ok is True and read.ok is True
    assert read.payload["value"] == 1
    assert [call[1] for call in transport.calls] == ["gpio.write", "gpio.read"]


def test_invalid_session_stops_before_nodemcu_transport():
    executor, transport = build_executor()
    with pytest.raises(PermissionError):
        executor.execute(AuthenticatedNodeMCUCommand("phone-1", "bad-session", "status", {}))
    assert transport.calls == []


def test_unsupported_action_stops_before_nodemcu_transport():
    executor, transport = build_executor()
    with pytest.raises(PermissionError):
        executor.execute(
            AuthenticatedNodeMCUCommand("phone-1", "session-1", "shell.exec", {"command": "whoami"})
        )
    assert transport.calls == []
