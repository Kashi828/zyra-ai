from pathlib import Path
from api.app_factory import create_app
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def test_app_factory_exposes_persistent_security(tmp_path):
    app = create_app(tmp_path / "security.sqlite3")
    assert hasattr(app.state, "security_context")
    assert app.state.security_context.store.db_path.exists()


def test_remote_api_rejects_unknown_device_before_runner(tmp_path):
    calls = []
    app = create_app(
        tmp_path / "security.sqlite3",
        runner=lambda action, payload: calls.append((action, payload)) or "ok",
    )
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.post("/v1/remote/commands", json={
        "device_id": "unknown",
        "session_id": "bad-session",
        "action": "open_app",
        "payload": {"name": "Calculator"},
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "unknown device"
    assert calls == []


def test_remote_api_accepts_persisted_authorized_device(tmp_path):
    db = tmp_path / "security.sqlite3"
    store = PersistentDeviceStore(db)
    device, secret = PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device, "sess1", 60)

    calls = []
    app = create_app(
        db,
        runner=lambda action, payload: calls.append((action, payload)) or "launched",
    )
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.post("/v1/remote/commands", json={
        "device_id": device,
        "session_id": "sess1",
        "action": "open_app",
        "payload": {"name": "Calculator"},
    })
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["status"] == "completed"
    assert calls == [("open_app", {"name": "Calculator"})]


def test_capability_is_taken_from_registered_action(tmp_path):
    db = tmp_path / "security.sqlite3"
    store = PersistentDeviceStore(db)
    device, _ = PersistentEnrollment(store).create_device({"pc.files"})
    store.issue_session(device, "sess1", 60)

    calls = []
    app = create_app(db, runner=lambda a,p: calls.append((a,p)) or "ok")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.post("/v1/remote/commands", json={
        "device_id": device,
        "session_id": "sess1",
        "action": "open_app",
        "payload": {"name": "Calculator"},
        # Client-provided capabilities must have no influence.
        "capabilities": ["pc.apps", "pc.web", "admin"],
    })
    assert response.json()["accepted"] is False
    assert calls == []


def test_factory_files_present():
    assert Path("api/app_factory.py").exists()
    assert Path("api/production_security.py").exists()
    assert Path("api/production_command_routes.py").exists()
