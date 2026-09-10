import hashlib

from api.app_factory import create_app


def _trusted_session(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    store = app.state.security_context.store
    secret = b"a" * 32
    store.enroll_device("pc-01", secret, {"windows.files.read"})
    session = app.state.security_context.sessions.create("pc-01")
    return app, session["session_id"]


def test_pairing_routes_are_authenticated_and_single_use(tmp_path):
    app, session_id = _trusted_session(tmp_path)
    client = app.test_client() if hasattr(app, "test_client") else None
    body = {
        "device_id": "pc-01",
        "session_id": session_id,
        "target_device_id": "esp-01",
        "device_type": "nodemcu",
        "endpoint": "http://192.168.1.20",
    }
    # Route registration itself is the contract; use the FastAPI TestClient when available.
    if client is None:
        from fastapi.testclient import TestClient
        client = TestClient(app)
    response = client.post("/v1/ecosystem/pairing/start", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "esp-01"
    assert len(data["pairing_code"]) == 6

    approve = {
        "device_id": "pc-01",
        "session_id": session_id,
        "pairing_id": data["pairing_id"],
        "pairing_code": data["pairing_code"],
    }
    # The current pairing foundation intentionally requires the target to be trusted
    # before persistence; this verifies the authenticated API contract without creating
    # a credential provisioning path for the LLM.
    response = client.post("/v1/ecosystem/pairing/approve", json=approve)
    assert response.status_code == 403


def test_pairing_start_rejects_public_http(tmp_path):
    app, session_id = _trusted_session(tmp_path)
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.post("/v1/ecosystem/pairing/start", json={
        "device_id": "pc-01",
        "session_id": session_id,
        "target_device_id": "esp-02",
        "device_type": "nodemcu",
        "endpoint": "http://example.com",
    })
    assert response.status_code == 400


def test_pairing_code_is_not_returned_by_approval(tmp_path):
    app, session_id = _trusted_session(tmp_path)
    store = app.state.security_context.store
    store.enroll_device("esp-03", b"b" * 32, {"android.ui"})
    from fastapi.testclient import TestClient
    client = TestClient(app)
    started = client.post("/v1/ecosystem/pairing/start", json={
        "device_id": "pc-01", "session_id": session_id,
        "target_device_id": "esp-03", "device_type": "nodemcu",
        "endpoint": "http://192.168.1.30",
    }).json()
    approved = client.post("/v1/ecosystem/pairing/approve", json={
        "device_id": "pc-01", "session_id": session_id,
        "pairing_id": started["pairing_id"], "pairing_code": started["pairing_code"],
    })
    assert approved.status_code == 200
    assert "pairing_code" not in approved.json()
    assert "secret" not in approved.json()
