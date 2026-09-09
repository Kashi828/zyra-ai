import time

from fastapi.testclient import TestClient

from api.app_factory import create_app
from security.api_rate_limiter import SlidingWindowRateLimiter
from security.api_auth_guard import ApiAuthGuard
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def provision(db, caps={"pc.apps"}, ttl=60):
    store = PersistentDeviceStore(db)
    device, secret = PersistentEnrollment(store).create_device(caps)
    store.issue_session(device, "sess1", ttl)
    return store, device


def test_limiter_uses_sliding_window():
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("k", now=100)
    assert limiter.allow("k", now=101)
    assert not limiter.allow("k", now=102)
    assert limiter.allow("k", now=111)


def test_auth_guard_allows_valid_session(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    guard = ApiAuthGuard(store)
    d = guard.authorize(device, "sess1", device)
    assert d.allowed


def test_auth_guard_rejects_invalid_session(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    guard = ApiAuthGuard(store)
    d = guard.authorize(device, "bad", device)
    assert not d.allowed
    assert d.status_code == 401


def test_auth_guard_rejects_revoked_device(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    store.revoke_device(device)
    guard = ApiAuthGuard(store)
    d = guard.authorize(device, "sess1", device)
    assert not d.allowed
    assert d.status_code == 403


def test_remote_route_requires_authentication(tmp_path):
    app = create_app(tmp_path/"s.sqlite3", runner=lambda a,p: "ok")
    client = TestClient(app)
    r = client.post("/v1/remote/commands", json={
        "device_id":"unknown",
        "session_id":"bad",
        "action":"open_app",
        "payload":{"name":"Calculator"},
    })
    assert r.status_code == 401


def test_remote_route_accepts_valid_authenticated_session(tmp_path):
    db=tmp_path/"s.sqlite3"
    _, device = provision(db)
    app = create_app(db, runner=lambda a,p: "ok")
    client=TestClient(app)
    r=client.post("/v1/remote/commands", json={
        "device_id":device,
        "session_id":"sess1",
        "action":"open_app",
        "payload":{"name":"Calculator"},
    })
    assert r.status_code == 200
    assert r.json()["accepted"] is True


def test_remote_route_rate_limits_same_client(tmp_path):
    db=tmp_path/"s.sqlite3"
    _, device = provision(db)
    app=create_app(db, runner=lambda a,p: "ok")
    app.state.security_context.api_auth.limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    client=TestClient(app)
    body={
        "device_id":device,
        "session_id":"sess1",
        "action":"open_app",
        "payload":{"name":"Calculator"},
    }
    assert client.post("/v1/remote/commands",json=body).status_code == 200
    assert client.post("/v1/remote/commands",json=body).status_code == 429
