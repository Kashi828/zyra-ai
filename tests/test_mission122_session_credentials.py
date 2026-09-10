import secrets

from fastapi.testclient import TestClient

from api.app_factory import create_app


def _enroll(store, device_id="dev-test"):
    secret = secrets.token_bytes(32)
    store.enroll_device(device_id, secret, {"windows.files.read"})
    return secret


def test_session_create_requires_device_secret(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)

    denied = client.post("/v1/session/create", json={"device_id": "dev-test"})
    assert denied.status_code == 401

    wrong = client.post(
        "/v1/session/create",
        json={"device_id": "dev-test", "device_secret": secrets.token_hex(32)},
    )
    assert wrong.status_code == 401

    ok = client.post(
        "/v1/session/create",
        json={"device_id": "dev-test", "device_secret": secret.hex()},
    )
    assert ok.status_code == 200
    assert ok.json()["session_id"].startswith("sess_")
    assert "device_secret" not in ok.json()


def test_logout_requires_matching_device_credentials(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    created = client.post(
        "/v1/session/create",
        json={"device_id": "dev-test", "device_secret": secret.hex()},
    ).json()

    denied = client.post(
        "/v1/session/logout",
        json={
            "device_id": "dev-test",
            "session_id": created["session_id"],
            "device_secret": secrets.token_hex(32),
        },
    )
    assert denied.status_code == 401

    ok = client.post(
        "/v1/session/logout",
        json={
            "device_id": "dev-test",
            "session_id": created["session_id"],
            "device_secret": secret.hex(),
        },
    )
    assert ok.status_code == 200
    assert ok.json()["logged_out"] is True
