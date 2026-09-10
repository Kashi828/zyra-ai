import secrets

from fastapi.testclient import TestClient

from api.app_factory import create_app


def _enroll(store, device_id="dev-test"):
    secret = secrets.token_bytes(32)
    store.enroll_device(device_id, secret, {"windows.files.read", "windows.apps.launch"})
    return secret


def _create_session(client, secret, device_id="dev-test"):
    response = client.post(
        "/v1/session/create",
        json={"device_id": device_id, "device_secret": secret.hex()},
    )
    assert response.status_code == 200
    return response.json()


def test_session_list_exposes_device_and_current_session(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    first = _create_session(client, secret)["session_id"]
    second = _create_session(client, secret)["session_id"]

    response = client.post("/v1/session/list", json={"device_id": "dev-test", "session_id": first})
    assert response.status_code == 200
    body = response.json()
    assert body["device"]["device_id"] == "dev-test"
    sessions = {item["session_id"]: item for item in body["sessions"]}
    assert sessions[first]["current"] is True
    assert sessions[first]["active"] is True
    assert sessions[second]["current"] is False


def test_session_revoke_invalidates_access_and_refresh_and_blocks_foreign_device(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    first_secret = _enroll(app.state.security_context.store, "dev-one")
    second_secret = _enroll(app.state.security_context.store, "dev-two")
    client = TestClient(app)
    current = _create_session(client, first_secret, "dev-one")["session_id"]
    target_result = _create_session(client, first_secret, "dev-one")
    target = target_result["session_id"]
    foreign = _create_session(client, second_secret, "dev-two")["session_id"]

    revoked = client.post("/v1/session/revoke", json={"device_id": "dev-one", "session_id": current, "target_session_id": target})
    assert revoked.status_code == 200
    assert app.state.security_context.store.validate_session(target, "dev-one") is False
    assert client.post("/v1/session/refresh", json={"device_id": "dev-one", "refresh_token": target_result["refresh_token"]}).status_code == 401

    denied = client.post("/v1/session/revoke", json={"device_id": "dev-one", "session_id": current, "target_session_id": foreign})
    assert denied.status_code == 404
    assert app.state.security_context.store.validate_session(foreign, "dev-two") is True


def test_session_lifecycle_audit_never_contains_credentials(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    created = _create_session(client, secret)
    session_id = created["session_id"]
    client.post("/v1/session/revoke", json={"device_id": "dev-test", "session_id": session_id, "target_session_id": session_id})
    events = app.state.audit_log.recent_for_device("dev-test")
    assert {event.event_type for event in events} >= {"session.created", "session.revoked"}
    assert all(secret.hex() not in event.detail for event in events)
