from __future__ import annotations

from desktop.runtime_health import RuntimeHealthService


def test_health_shape():
    data = RuntimeHealthService("https://example.com").read(api="online", voice="unconfigured")
    assert data["model_endpoint"] == "configured"
    assert data["runtime"] == "ready"


def test_non_local_endpoint_is_not_probed():
    assert RuntimeHealthService("https://example.com").check_model() == "configured"
