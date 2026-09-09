from fastapi.testclient import TestClient

from api.app_factory import create_app
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment
from security.session_rotation_store import SessionRotationStore
from security.session_service import SessionService


def provision(db):
    store = PersistentDeviceStore(db)
    device, secret = PersistentEnrollment(store).create_device({"pc.apps"})
    return store, device


def test_create_session_returns_refresh_token(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    result = SessionService(store).create(device)
    assert result["session_id"].startswith("sess_")
    assert result["refresh_token"]
    assert result["expires_at"] > 0
    assert store.validate_session(result["session_id"], device)


def test_refresh_rotates_token_and_session(tmp_path):
    db = tmp_path/"s.sqlite3"
    store, device = provision(db)
    service = SessionService(store)
    first = service.create(device)
    second = service.refresh(device, first["refresh_token"])
    assert second["session_id"] != first["session_id"]
    assert second["refresh_token"] != first["refresh_token"]
    assert store.validate_session(second["session_id"], device)


def test_refresh_token_is_single_use(tmp_path):
    db = tmp_path/"s.sqlite3"
    store, device = provision(db)
    service = SessionService(store)
    first = service.create(device)
    service.refresh(device, first["refresh_token"])
    try:
        service.refresh(device, first["refresh_token"])
    except PermissionError:
        pass
    else:
        assert False


def test_refresh_token_is_device_bound(tmp_path):
    db = tmp_path/"s.sqlite3"
    store = PersistentDeviceStore(db)
    d1, _ = PersistentEnrollment(store).create_device({"pc.apps"})
    d2, _ = PersistentEnrollment(store).create_device({"pc.apps"})
    service = SessionService(store)
    first = service.create(d1)
    try:
        service.refresh(d2, first["refresh_token"])
    except PermissionError:
        pass
    else:
        assert False


def test_logout_revokes_session_and_refresh_token(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    service = SessionService(store)
    first = service.create(device)
    service.logout(device, first["session_id"])
    assert not store.validate_session(first["session_id"], device)
    try:
        service.refresh(device, first["refresh_token"])
    except PermissionError:
        pass
    else:
        assert False


def test_device_logout_revokes_device(tmp_path):
    store, device = provision(tmp_path/"s.sqlite3")
    service = SessionService(store)
    first = service.create(device)
    service.logout_device(device)
    assert not store.validate_session(first["session_id"], device)
    assert store.get_device(device)["revoked"]


def test_session_routes_work(tmp_path):
    db=tmp_path/"s.sqlite3"
    _, device = provision(db)
    client=TestClient(create_app(db))
    created=client.post("/v1/session/create", json={"device_id":device})
    assert created.status_code == 200
    body=created.json()
    refreshed=client.post("/v1/session/refresh", json={
        "device_id":device,
        "refresh_token":body["refresh_token"],
    })
    assert refreshed.status_code == 200
    assert refreshed.json()["session_id"] != body["session_id"]


def test_reused_refresh_route_returns_401(tmp_path):
    db=tmp_path/"s.sqlite3"
    _, device = provision(db)
    client=TestClient(create_app(db))
    body=client.post("/v1/session/create",json={"device_id":device}).json()
    assert client.post("/v1/session/refresh",json={
        "device_id":device,"refresh_token":body["refresh_token"]
    }).status_code == 200
    assert client.post("/v1/session/refresh",json={
        "device_id":device,"refresh_token":body["refresh_token"]
    }).status_code == 401
