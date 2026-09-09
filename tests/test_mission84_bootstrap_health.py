from pathlib import Path

from api.app_factory import create_app
from fastapi.testclient import TestClient


def test_dependency_report_is_safe_and_non_installing():
    from api.health import dependency_report
    report=dependency_report(include_optional_voice=True)
    assert "ready" in report
    assert "required" in report
    assert "optional_voice" in report


def test_health_route_registered(tmp_path):
    app=create_app(tmp_path/"s.sqlite3")
    client=TestClient(app)
    r=client.get("/health")
    assert r.status_code==200
    assert r.json()["service"]=="zyra-ai"


def test_diagnostics_route_registered(tmp_path):
    app=create_app(tmp_path/"s.sqlite3")
    client=TestClient(app)
    r=client.get("/v1/system/diagnostics")
    assert r.status_code==200
    body=r.json()
    assert body["ok"] is True
    assert "required" in body
    assert "optional_voice" in body


def test_diagnostics_source_has_no_package_install():
    text=Path("api/health.py").read_text()
    assert "pip install" not in text.lower()
    assert "subprocess" not in text
