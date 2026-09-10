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

    response = client.post(
        "/v1/session/list",
        json={"device_id": "dev-test", "session_id": first},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["device"]["device_id"] == "dev-test"
    assert body["device"]["capabilities"] == ["windows.apps.launch", "windows.files.read"]
    sessions = {item["session_id"]: item for item in body["sessions"]}
    assert sessions[first]["current"] is True
    assert sessions[first]["active"] is True
    assert sessions[second]["current"] is False


def test_session_revoke_allows_only_same_device_target(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    first_secret = _enroll(app.state.security_context.store, "dev-one")
    second_secret = _enroll(app.state.security_context.store, "dev-two")
    client = TestClient(app)
    first_result = _create_session(client, first_secret, "dev-one")
    first = first_result["session_id"]
    second_result = _create_session(client, first_secret, "dev-one")
    second = second_result["session_id"]
    foreign = _create_session(client, second_secret, "dev-two")["session_id"]

    revoked = client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-one",
            "session_id": first,
            "target_session_id": second,
        },
    )
    assert revoked.status_code == 200
    assert revoked.json() == {
        "ok": True,
        "revoked": True,
        "session_id": second,
        "current_session": False,
    }
    assert app.state.security_context.store.validate_session(second, "dev-one") is False
    assert app.state.security_context.store.validate_session(first, "dev-one") is True

    # Per-session revocation must also invalidate that session's refresh path.
    refresh_attempt = client.post(
        "/v1/session/refresh",
        json={"device_id": "dev-one", "refresh_token": second_result["refresh_token"]},
    )
    assert refresh_attempt.status_code == 401

    denied = client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-one",
            "session_id": first,
            "target_session_id": foreign,
        },
    )
    assert denied.status_code == 404
    assert app.state.security_context.store.validate_session(foreign, "dev-two") is True


def test_session_revoke_rejects_missing_and_inactive_targets(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    current = _create_session(client, secret)["session_id"]
    target = _create_session(client, secret)["session_id"]

    missing = client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-test",
            "session_id": current,
            "target_session_id": "sess_missing",
        },
    )
    assert missing.status_code == 404

    ok = client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-test",
            "session_id": current,
            "target_session_id": target,
        },
    )
    assert ok.status_code == 200

    inactive = client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-test",
            "session_id": current,
            "target_session_id": target,
        },
    )
    assert inactive.status_code == 409


def test_session_lifecycle_actions_are_audited_without_credentials(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"))
    secret = _enroll(app.state.security_context.store)
    client = TestClient(app)
    created = _create_session(client, secret)
    session_id = created["session_id"]

    client.post(
        "/v1/session/revoke",
        json={
            "device_id": "dev-test",
            "session_id": session_id,
            "target_session_id": session_id,
        },
    )

    events = app.state.audit_log.recent_for_device("dev-test")
    event_types = [event.event_type for event in events]
    assert "session.created" in event_types
    assert "session.revoked" in event_types
    assert all(secret.hex() not in event.detail for event in events)
