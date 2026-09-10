import time

import pytest

from api.session_routes import register_session_routes


class Store:
    def __init__(self):
        self.devices = {
            "device-1": {
                "device_id": "device-1",
                "capabilities": ["windows.browser"],
                "revoked": False,
            }
        }
        self.sessions = {
            "session-1": {
                "session_id": "session-1",
                "device_id": "device-1",
                "expires_at": int(time.time()) + 3600,
                "active": True,
            }
        }

    def validate_session(self, session_id, device_id):
        session = self.sessions.get(session_id)
        return bool(session and session["device_id"] == device_id and session["active"] and session["expires_at"] > int(time.time()))

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def get_session(self, session_id):
        return self.sessions.get(session_id)


class Sessions:
    def __init__(self):
        self.store = Store()


class FakeApp:
    def __init__(self):
        self.routes = {}

    def post(self, path):
        def decorator(fn):
            self.routes[path] = fn
            return fn
        return decorator


def test_session_status_returns_secret_free_authenticated_context():
    app = FakeApp()
    sessions = Sessions()
    register_session_routes(app, sessions)
    result = app.routes["/v1/session/status"]({"device_id": "device-1", "session_id": "session-1"})
    assert result["ok"] is True
    assert result["authenticated"] is True
    assert result["device"]["device_id"] == "device-1"
    assert result["session"]["session_id"] == "session-1"
    assert "device_secret" not in result
    assert "refresh_token" not in result


def test_session_status_rejects_unknown_session():
    app = FakeApp()
    sessions = Sessions()
    register_session_routes(app, sessions)
    with pytest.raises(Exception):
        app.routes["/v1/session/status"]({"device_id": "device-1", "session_id": "missing"})
