"""End-to-end checks that mirror what the Windows and Android apps actually do."""
import time

import pytest
from fastapi.testclient import TestClient

from api.app_factory import create_app
from security.enrollment_session_bridge import EnrollmentSessionBridge


def _app(tmp_path, monkeypatch, lan=False, runner=None):
    if lan:
        monkeypatch.setenv("ZYRA_LAN_MODE", "1")
    else:
        monkeypatch.delenv("ZYRA_LAN_MODE", raising=False)
    return create_app(db_path=str(tmp_path / "zyra.sqlite3"), runner=runner)


def _local(app):
    return TestClient(app, client=("127.0.0.1", 50000))


def _phone(app):
    return TestClient(app, client=("192.168.1.50", 50000))


def test_desktop_ui_and_runtime_routes_exist(tmp_path, monkeypatch):
    c = _local(_app(tmp_path, monkeypatch))
    assert c.get("/").status_code == 200
    assert c.get("/app.js").status_code == 200
    assert c.get("/styles.css").status_code == 200
    r = c.post("/v1/runtime/tasks", json={"goal": "open notepad"})
    assert r.status_code == 200 and r.json()["status"] == "queued"
    assert c.get("/v1/runtime/state").status_code == 200
    assert c.post("/v1/agent/stop").json()["ok"] is True


def test_ui_server_never_exposes_python_sources(tmp_path, monkeypatch):
    c = _local(_app(tmp_path, monkeypatch))
    for name in ("launcher.py", "native_bridge.py", "__init__.py", "..%2Fmain.py"):
        assert c.get(f"/{name}").status_code == 404


def test_pairing_offer_is_local_only_and_allowlisted(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    assert _phone(app).post("/v1/desktop/pairing/offer", json={}).status_code == 403
    local = _local(app)
    assert local.post("/v1/desktop/pairing/offer", json={"capabilities": ["pc.root"]}).status_code == 400
    ok = local.post("/v1/desktop/pairing/offer", json={})
    assert ok.status_code == 200
    body = ok.json()
    assert len(body["pairing_code"]) == 6
    assert set(body["capabilities"]) == {"pc.apps", "pc.files", "pc.web"}


def test_android_flow_pair_session_command_logout(tmp_path, monkeypatch):
    executed = []
    app = _app(
        tmp_path, monkeypatch, lan=True,
        runner=lambda action, payload: executed.append((action, payload)) or "ok",
    )
    phone = _phone(app)

    offer = _local(app).post("/v1/desktop/pairing/offer", json={}).json()

    # 1. Phone redeems the offer (Android maps windows.* -> pc.* names).
    enrolled = phone.post("/v1/devices/pairing/enroll", json={
        "offer_id": offer["offer_id"],
        "pairing_code": offer["pairing_code"],
        "capabilities": ["pc.apps", "pc.files", "pc.web"],
    })
    assert enrolled.status_code == 200, enrolled.text
    device_id = enrolled.json()["device_id"]
    secret = enrolled.json()["device_secret"]
    assert len(secret) == 64

    # Offers are single-use.
    again = phone.post("/v1/devices/pairing/enroll", json={
        "offer_id": offer["offer_id"], "pairing_code": offer["pairing_code"],
    })
    assert again.status_code in (400, 403)

    # 2. Session creation needs the secret; the expiry fields are distinct.
    assert phone.post("/v1/session/create", json={"device_id": device_id}).status_code == 401
    created = phone.post("/v1/session/create", json={"device_id": device_id, "device_secret": secret})
    assert created.status_code == 200
    body = created.json()
    assert body["session_expires_at"] < body["expires_at"]
    session_id = body["session_id"]

    # 3. Authenticated session listing (the Devices quick action).
    listing = phone.post("/v1/session/list", json={"device_id": device_id, "session_id": session_id})
    assert listing.status_code == 200 and listing.json()["summary"]["active"] >= 1

    # 3b. The phone can run an allowed command; the PC runs the validated payload.
    cmd = phone.post("/v1/remote/commands", json={
        "device_id": device_id, "session_id": session_id, "client_key": device_id,
        "action": "open_url", "payload": {"url": "https://example.com/docs"},
    })
    assert cmd.status_code == 200, cmd.text
    assert cmd.json()["accepted"] is True
    assert executed == [("open_url", {"url": "https://example.com/docs"})]

    # A command the phone was never granted, or an unsafe payload, never reaches the runner.
    bad = phone.post("/v1/remote/commands", json={
        "device_id": device_id, "session_id": session_id, "client_key": device_id,
        "action": "open_url", "payload": {"url": "javascript:alert(1)"},
    })
    assert bad.status_code == 200 and bad.json()["accepted"] is False
    assert len(executed) == 1

    # 4. Refresh rotates the session.
    refreshed = phone.post("/v1/session/refresh", json={"device_id": device_id, "refresh_token": body["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["session_id"] != session_id

    # 5. Logout requires the secret (what ZyraHttpTransport now sends).
    sid = refreshed.json()["session_id"]
    assert phone.post("/v1/session/logout", json={"device_id": device_id, "session_id": sid}).status_code == 401
    out = phone.post("/v1/session/logout", json={"device_id": device_id, "session_id": sid, "device_secret": secret})
    assert out.status_code == 200 and out.json()["logged_out"] is True


def test_lan_guard_blocks_desktop_routes_for_phones_only(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, lan=True)
    phone, local = _phone(app), _local(app)
    assert phone.get("/health").status_code == 200
    for method, path in [("post", "/v1/runtime/tasks"), ("get", "/v1/runtime/state"),
                         ("post", "/v1/agent/stop"), ("get", "/"), ("get", "/v1/system/setup-check")]:
        assert getattr(phone, method)(path).status_code == 403, path
    assert local.get("/v1/runtime/state").status_code == 200


def test_lan_guard_is_off_by_default(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, lan=False)
    assert _phone(app).get("/v1/runtime/state").status_code == 200
