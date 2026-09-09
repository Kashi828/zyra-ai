from pathlib import Path
from fastapi.testclient import TestClient

from core.realtime_events import RealtimeEvent, RealtimeEventHub
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment


def provision(db):
    store=PersistentDeviceStore(db)
    device,_=PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device,"sess1",60)
    return store,device


def test_event_serialization():
    e=RealtimeEvent("e1","command.completed","d1",command_id="c1",
                    status="completed",payload={"action":"open_app"})
    text=e.to_json()
    assert '"event_type":"command.completed"' in text
    assert '"command_id":"c1"' in text


def test_hub_subscribe_and_publish():
    hub=RealtimeEventHub()
    seen=[]
    unsub=hub.subscribe("d1",seen.append)
    hub.publish(RealtimeEvent("e1","task.updated","d1",task_id="t1"))
    unsub()
    hub.publish(RealtimeEvent("e2","task.updated","d1",task_id="t2"))
    assert len(seen)==1
    assert seen[0].task_id=="t1"


def test_realtime_socket_requires_valid_session(tmp_path):
    app=__import__("api.app_factory",fromlist=["create_app"]).create_app(tmp_path/"s.sqlite3")
    client=TestClient(app)
    from starlette.websockets import WebSocketDisconnect
    try:
        with client.websocket_connect("/v1/realtime/ws",headers={
            "X-ZYRA-Device-Id":"bad",
            "Authorization":"Bearer bad",
        }) as ws:
            ws.receive_text()
    except WebSocketDisconnect:
        pass


def test_realtime_socket_accepts_persisted_session(tmp_path):
    db=tmp_path/"s.sqlite3"
    _,device=provision(db)
    app=__import__("api.app_factory",fromlist=["create_app"]).create_app(db)
    client=TestClient(app)
    with client.websocket_connect("/v1/realtime/ws",headers={
        "X-ZYRA-Device-Id":device,
        "Authorization":"Bearer sess1",
    }) as ws:
        message=ws.receive_json()
        assert message["event_type"]=="realtime.connected"


def test_android_realtime_event_contract():
    base=Path("android/app/src/main/java/com/zyra/transport")
    text=(base/"RealtimeEvent.kt").read_text(encoding="utf-8")
    ws=(base/"OkHttpZyraWebSocketClient.kt").read_text(encoding="utf-8")
    assert "RealtimeEvent" in text
    assert "fromJson" in text
    assert "eventListener?.onEvent(event)" in ws
    assert "onPresence(true)" in ws
    assert "onPresence(false)" in ws
