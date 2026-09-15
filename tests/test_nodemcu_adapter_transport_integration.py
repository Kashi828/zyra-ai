from core.iot_nodemcu import NodeMCUAdapter, NodeMCUDevice


class RecordingTransport:
    def __init__(self):
        self.calls = []

    def request(self, action, payload=None):
        self.calls.append((action, dict(payload or {})))
        return {"ok": True, "action": action}


def test_adapter_forwards_allowlisted_command_to_concrete_transport_contract():
    transport = RecordingTransport()
    adapter = NodeMCUAdapter(
        NodeMCUDevice(
            "nodemcu-1",
            "https://nodemcu.example",
            frozenset({"iot.telemetry", "iot.gpio"}),
        ),
        transport,
    )

    result = adapter.execute("gpio.write", {"pin": 5, "value": 1})

    assert result == {"ok": True, "action": "gpio.write"}
    assert transport.calls == [("gpio.write", {"pin": 5, "value": 1})]
