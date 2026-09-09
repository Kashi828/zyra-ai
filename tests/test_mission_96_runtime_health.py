from desktop.runtime_health import RuntimeHealthService


def test_remote_model_endpoint_is_reported_as_configured(monkeypatch):
    service = RuntimeHealthService("https://example.invalid/model")
    assert service.read(api="online", voice="configured")["model_endpoint"] == "configured"


def test_unreachable_local_model_is_offline(monkeypatch):
    service = RuntimeHealthService("http://127.0.0.1:9")
    assert service.check_model(timeout=0.1) == "offline"


def test_health_degrades_when_api_is_offline():
    service = RuntimeHealthService("https://example.invalid/model")
    assert service.read(api="offline")["runtime"] == "degraded"
