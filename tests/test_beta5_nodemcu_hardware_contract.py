from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nodemcu_transport_exposes_required_allowlist_and_secret_header():
    text = (ROOT / "core" / "iot_nodemcu_transport.py").read_text(encoding="utf-8")
    assert 'ALLOWED_ACTIONS = frozenset({"status", "gpio.read", "gpio.write"})' in text
    assert '"X-Zyra-Device-Secret"' in text
    assert '"/v1/{action}"' in text


def test_nodemcu_adapter_requires_enrolled_endpoint_and_known_actions():
    text = (ROOT / "core" / "iot_nodemcu.py").read_text(encoding="utf-8")
    assert "validate_endpoint(device.endpoint)" in text
    assert 'ALLOWED_ACTIONS = frozenset({"status", "gpio.read", "gpio.write"})' in text
    assert "self.transport.request(self.endpoint, action, payload or {})" in text


def test_nodemcu_bridge_enforces_device_capability_before_adapter():
    text = (ROOT / "core" / "nodemcu_command_bridge.py").read_text(encoding="utf-8")
    assert "caller_capabilities = set(capabilities)" in text
    assert "enrolled_capabilities = set(self.adapter.device.capabilities)" in text
    assert '"NodeMCU device lacks capability"' in text


def test_hardware_gate_documents_physical_validation_without_claiming_it():
    text = (ROOT / "MISSION_151.md").read_text(encoding="utf-8")
    assert "physical" in text.lower()
    assert "not" in text.lower()
    assert "GPIO" in text
