import secrets

from fastapi.testclient import TestClient

from api.app_factory import create_app


def _enroll(store, device_id="dev-test"):
    secret = secrets.token_bytes(32)
    store.enroll_device(device_id, secret, {"windows.files.read", "windows.apps.launch"})
    return secret


def _create_session(client, secret, device_id="dev-test"):
    response = client.post("/v1/session/create", json={"device_id": device_id, "device_secret": secret.hex()})
    assert response.status_code == 200
    return response.json()


def _list(client, device_id, session_id, include_inactive=None):
    payload = {"device_id": device_id, "session_id": session_id}
    if include_inactive is not None:
        payload["include_inactive"] = include_inactive
    return client.post("/v1/session/list", json=payload)


def test_session_inventory_defaults_to_active_only(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    current = _create_session(client, secret)["session_id"]
    target = _create_session(client, secret)["session_id"]
    assert client.post("/v1/session/revoke", json={"device_id": "dev-test", "session_id": current, "target_session_id": target}).status_code == 200

    response = _list(client, "dev-test", current)
    assert response.status_code == 200
    assert response.json()["summary"] == {"total": 1, "active": 1, "inactive": 0}
    assert [item["session_id"] for item in response.json()["sessions"]] == [current]


def test_session_inventory_includes_inactive_history_on_request(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    current = _create_session(client, secret)["session_id"]
    target = _create_session(client, secret)["session_id"]
    assert client.post("/v1/session/revoke", json={"device_id": "dev-test", "session_id": current, "target_session_id": target}).status_code == 200

    body = _list(client, "dev-test", current, True).json()
    assert body["summary"] == {"total": 2, "active": 1, "inactive": 1}
    sessions = {item["session_id"]: item for item in body["sessions"]}
    assert sessions[target]["active"] is False
    assert sessions[target]["revoked"] is True
    assert "refresh_token" not in sessions[target]
    assert "device_secret" not in sessions[target]


def test_session_inventory_rejects_non_boolean_history_flag(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    current = _create_session(client, secret)["session_id"]
    response = _list(client, "dev-test", current, "true")
    assert response.status_code == 400
    assert response.json()["detail"] == "include_inactive must be a boolean"


def test_session_inventory_never_crosses_device_boundary(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    first_secret = _enroll(app.state.security_context.store, "dev-one")
    second_secret = _enroll(app.state.security_context.store, "dev-two")
    client = TestClient(app)
    first = _create_session(client, first_secret, "dev-one")["session_id"]
    foreign = _create_session(client, second_secret, "dev-two")["session_id"]
    response = _list(client, "dev-one", first, True)
    assert response.status_code == 200
    assert foreign not in {item["session_id"] for item in response.json()["sessions"]}
