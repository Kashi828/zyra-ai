import time

import pytest

from api.session_routes import register_session_routes


class Store:
    def __init__(self):
        now = int(time.time())
        self.devices = {
            "device-1": {"device_id": "device-1", "capabilities": ["windows.browser"], "revoked": False},
            "device-2": {"device_id": "device-2", "capabilities": ["windows.browser"], "revoked": False},
        }
        self.sessions = {
            "active": {"session_id": "active", "device_id": "device-1", "expires_at": now + 3600, "active": True},
            "expired": {"session_id": "expired", "device_id": "device-1", "expires_at": now - 1, "active": True},
            "inactive": {"session_id": "inactive", "device_id": "device-1", "expires_at": now + 3600, "active": False},
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


def route():
    app = FakeApp()
    register_session_routes(app, Sessions())
    return app.routes["/v1/session/status"]


def test_status_rejects_device_session_mismatch():
    with pytest.raises(Exception):
        route()({"device_id": "device-2", "session_id": "active"})


def test_status_rejects_expired_session():
    with pytest.raises(Exception):
        route()({"device_id": "device-1", "session_id": "expired"})


def test_status_rejects_inactive_session():
    with pytest.raises(Exception):
        route()({"device_id": "device-1", "session_id": "inactive"})
