from fastapi.testclient import TestClient

from core.realtime_events import RealtimeEventHub
from core.task_realtime_bridge import TaskRealtimeBridge
from api.app_factory import create_app
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def test_task_bridge_maps_lifecycle_statuses():
    hub = RealtimeEventHub()
    seen=[]
    hub.subscribe("d1", seen.append)
    bridge = TaskRealtimeBridge(hub)
    for status in ["queued","planning","running","awaiting_approval","completed","failed","cancelled"]:
        bridge.publish("t1", status, device_id="d1")
    assert [e.event_type for e in seen] == [
        "task.queued","task.planning","task.running",
        "task.approval_required","task.completed","task.failed","task.cancelled"
    ]


def test_task_bridge_includes_phase_and_detail():
    hub=RealtimeEventHub()
    seen=[]
    hub.subscribe("d1", seen.append)
    TaskRealtimeBridge(hub).publish(
        "t1","running",detail="executing step",device_id="d1",
        phase="execute",payload={"step":2}
    )
    assert seen[0].payload["detail"] == "executing step"
    assert seen[0].payload["phase"] == "execute"
    assert seen[0].payload["step"] == 2


def test_runtime_has_realtime_hub_slot():
    from core.zyra_runtime import ZyraRuntime
    rt=ZyraRuntime()
    assert hasattr(rt, "realtime_hub")
    assert rt.realtime_hub is None


def test_task_event_route_is_registered():
    app=create_app()
    paths={getattr(r,"path","") for r in app.routes}
    assert "/v1/runtime/tasks/{task_id}/events" in paths


def _provision_app(tmp_path):
    db=tmp_path/"secure.sqlite3"
    store=PersistentDeviceStore(db)
    device,_=PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device,"sess1",60)
    return create_app(db), device


def test_task_event_route_publishes(tmp_path):
    app, device = _provision_app(tmp_path)
    seen=[]
    app.state.realtime_events.subscribe(device, seen.append)
    client=TestClient(app)
    r=client.post("/v1/runtime/tasks/t9/events",json={
        "status":"awaiting_approval","device_id":device,"session_id":"sess1",
        "phase":"approval","detail":"confirm sensitive action"
    })
    assert r.status_code==200
    assert seen[0].event_type=="task.approval_required"


def test_task_route_requires_authenticated_session():
    app=create_app()
    client=TestClient(app)
    r=client.post("/v1/runtime/tasks/t9/events",json={"status":"completed"})
    assert r.status_code==401


