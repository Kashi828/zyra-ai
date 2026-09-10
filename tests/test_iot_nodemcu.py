import pytest

from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice, validate_endpoint


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, endpoint, action, payload):
        self.calls.append((endpoint, action, dict(payload)))
        return {"ok": True}


def test_endpoint_requires_http_scheme():
    with pytest.raises(ValueError):
        validate_endpoint("serial:///dev/ttyUSB0")


def test_adapter_allows_only_known_actions():
    transport = FakeTransport()
    adapter = NodeMCUAdapter(
        NodeMCUDevice("nodemcu-1", "http://192.168.1.50", frozenset({"iot.telemetry", "iot.gpio"})),
        transport,
    )
    adapter.execute("status")
    assert transport.calls[0][1] == "status"
    with pytest.raises(PermissionError):
        adapter.execute("shell")


def test_adapter_uses_enrolled_endpoint():
    transport = FakeTransport()
    adapter = NodeMCUAdapter(
        NodeMCUDevice("nodemcu-1", "http://192.168.1.50", frozenset({"iot.telemetry"})),
        transport,
    )
    adapter.execute("status", {"request_id": "r1"})
    assert transport.calls == [("http://192.168.1.50", "status", {"request_id": "r1"})]
