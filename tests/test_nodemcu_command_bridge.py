from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice
from core.nodemcu_command_bridge import NodeMCUCommandBridge


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, endpoint, action, payload):
        self.calls.append((endpoint, action, dict(payload)))
        return {"ok": True, "action": action}


def make_bridge():
    transport = FakeTransport()
    adapter = NodeMCUAdapter(
        NodeMCUDevice("nodemcu-1", "http://127.0.0.1:8080", frozenset({"iot.telemetry", "iot.gpio"})),
        transport,
    )
    return NodeMCUCommandBridge(adapter), transport


def test_bridge_routes_status_with_telemetry_capability():
    bridge, transport = make_bridge()
    result = bridge.execute("status", capabilities={"iot.telemetry"})
    assert result.ok is True
    assert transport.calls == [("http://127.0.0.1:8080", "status", {})]


def test_bridge_blocks_gpio_write_without_gpio_capability():
    bridge, transport = make_bridge()
    result = bridge.execute("gpio.write", {"pin": 5, "value": 1}, capabilities={"iot.telemetry"})
    assert result.ok is False
    assert result.message == "missing NodeMCU capability"
    assert transport.calls == []


def test_bridge_rejects_unknown_action_before_transport():
    bridge, transport = make_bridge()
    result = bridge.execute("shell", {"cmd": "whoami"}, capabilities={"iot.gpio"})
    assert result.ok is False
    assert result.message == "unsupported NodeMCU action"
    assert transport.calls == []


def test_bridge_routes_gpio_write_when_capability_is_granted():
    bridge, transport = make_bridge()
    result = bridge.execute("gpio.write", {"pin": 5, "value": 1}, capabilities={"iot.gpio"})
    assert result.ok is True
    assert transport.calls == [("http://127.0.0.1:8080", "gpio.write", {"pin": 5, "value": 1})]
