from pathlib import Path

import re

from fastapi.testclient import TestClient

from api.app_factory import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_route_requires_session_and_capability():
    text = (ROOT / "api" / "runtime_routes.py").read_text(encoding="utf-8")
    assert '"/v1/runtime/tasks"' in text
    assert "auth_gateway.authorize" in text
    assert '"device_id and session_id are required"' in text
    assert "CapabilityBroker" in text
    assert 'if not capability:' in text or 'capability = spec.capability' in text


def test_runtime_route_cannot_bypass_confirmation():
    text = (ROOT / "api" / "runtime_routes.py").read_text(encoding="utf-8")
    assert 'confirmed = body.get("confirmed", True)' in text
    assert '"requires_confirmation": decision.requires_confirmation' in text
    assert "status = 409 if decision.requires_confirmation else 403" in text
