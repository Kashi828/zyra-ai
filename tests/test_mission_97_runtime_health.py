from desktop.runtime_health import RuntimeHealthService


def test_remote_endpoint_is_reported_as_configured(monkeypatch):
    service = RuntimeHealthService("https://example.invalid/model")
    assert service.check_model() == "configured"


def test_local_unavailable_endpoint_is_offline():
    service = RuntimeHealthService("http://127.0.0.1:1")
    assert service.check_model(timeout=0.05) == "offline"


def test_api_online_and_configured_model_is_ready():
    service = RuntimeHealthService("https://example.invalid/model")
    state = service.read(api="online", voice="unconfigured")
    assert state["runtime"] == "ready"
    assert state["model_endpoint"] == "configured"
