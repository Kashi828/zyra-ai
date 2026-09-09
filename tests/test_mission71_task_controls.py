from fastapi.testclient import TestClient

from api.app_factory import create_app
from core.task_control import TaskControlRegistry
from core.task_realtime_bridge import TaskRealtimeBridge
from core.realtime_events import RealtimeEventHub
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def provision(db):
    store=PersistentDeviceStore(db)
    device,_=PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device,"sess1",60)
    return device


def test_task_control_approval_and_cancel():
    hub=RealtimeEventHub()
    seen=[]
    hub.subscribe("d1",seen.append)
    bridge=TaskRealtimeBridge(hub)
    controls=TaskControlRegistry(bridge)
    controls.register("t1","d1","awaiting_approval")
    task=controls.approve("t1","d1")
    assert task.status=="running"
    controls.cancel("t1","d1")
    assert task.status=="cancelled"
    assert [e.status for e in seen]==["running","cancelled"]


def test_task_control_cross_device_is_blocked():
    controls=TaskControlRegistry()
    controls.register("t1","d1","awaiting_approval")
    try:
        controls.approve("t1","d2")
    except PermissionError:
        pass
    else:
        assert False


def test_task_control_terminal_cancel_is_blocked():
    controls=TaskControlRegistry()
    controls.register("t1","d1","completed")
    try:
        controls.cancel("t1","d1")
    except ValueError:
        pass
    else:
        assert False


def test_approve_route_requires_owned_authenticated_task(tmp_path):
    db=tmp_path/"s.sqlite3"
    d=provision(db)
    app=create_app(db)
    client=TestClient(app)
    client.post("/v1/runtime/tasks/t1/events",json={
        "device_id":d,"session_id":"sess1","status":"awaiting_approval"
    })
    r=client.post("/v1/runtime/tasks/t1/approve",json={
        "device_id":d,"session_id":"sess1"
    })
    assert r.status_code==200
    assert r.json()["status"]=="running"


def test_cancel_route_rejects_unknown_task(tmp_path):
    db=tmp_path/"s.sqlite3"
    d=provision(db)
    client=TestClient(create_app(db))
    r=client.post("/v1/runtime/tasks/nope/cancel",json={
        "device_id":d,"session_id":"sess1"
    })
    assert r.status_code==404


def test_android_task_control_contract_exists():
    from pathlib import Path
    base=Path("android/app/src/main/java/com/zyra/transport")
    assert (base/"TaskControlApi.kt").exists()
    assert (base/"RealtimeTaskTimeline.kt").exists()
