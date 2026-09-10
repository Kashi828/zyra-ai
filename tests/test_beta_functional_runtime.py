import secrets

from fastapi.testclient import TestClient

from api.app_factory import create_app


def test_beta_runtime_task_executes_allowlisted_action(tmp_path):
    calls = []

    def runner(action, payload):
        calls.append((action, payload))
        return "ok"

    app = create_app(db_path=str(tmp_path / "security.sqlite3"), runner=runner)
    security = app.state.security_context
    device_id = "test-device"
    secret = secrets.token_bytes(32)
    security.store.enroll_device(device_id, secret, {"windows.apps", "windows.browser", "windows.files.read"})
    session = security.sessions.create(device_id)

    client = TestClient(app)
    response = client.post(
        "/v1/runtime/tasks",
        json={
            "device_id": device_id,
            "session_id": session["session_id"],
            "goal": "open calculator",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["action"] == "open_app"
    assert calls == [("open_app", {"name": "calculator"})]


def test_beta_routes_are_registered(tmp_path):
    app = create_app(db_path=str(tmp_path / "security.sqlite3"), runner=lambda *_: "ok")
    paths = {route.path for route in app.routes}
    assert "/v1/local/bootstrap" in paths
    assert "/v1/runtime/tasks" in paths
    assert "/v1/agent/stop" in paths
    assert "/v1/setup/startup" in paths
