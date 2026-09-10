from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_route_requires_session_and_capability():
    text = (ROOT / "api" / "runtime_routes.py").read_text(encoding="utf-8")
    assert '"/v1/runtime/tasks"' in text
    assert "auth_gateway.authorize" in text
    assert '"device_id and session_id are required"' in text
    assert '"capability is required"' in text
    assert "CapabilityBroker(device[\"capabilities\"])" in text


def test_runtime_route_cannot_bypass_confirmation():
    text = (ROOT / "api" / "runtime_routes.py").read_text(encoding="utf-8")
    assert 'confirmed=bool(body.get("confirmed", False))' in text
    assert '"requires_confirmation": True' in text
    assert 'status_code=409' in text
