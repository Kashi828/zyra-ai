from fastapi.testclient import TestClient

from core.task_control import TaskControlRegistry
from core.task_recovery import TaskRecoveryEngine
from core.task_realtime_bridge import TaskRealtimeBridge
from core.realtime_events import RealtimeEventHub
from core.workflow_resume import WorkflowResumeExecutor
from security.persistent_task_store import PersistentTaskStore
from security.persistent_device_store import PersistentDeviceStore
from security.persistent_enrollment import PersistentEnrollment
from api.app_factory import create_app


def test_resume_requires_explicit_ack(tmp_path):
    store=PersistentTaskStore(tmp_path/"tasks.sqlite3")
    hub=RealtimeEventHub()
    bridge=TaskRealtimeBridge(hub)
    controls=TaskControlRegistry(bridge, store)
    controls.register("t1","d1","running",{"step":3})
    executor=WorkflowResumeExecutor(controls, TaskRecoveryEngine(), event_bridge=bridge)
    result=executor.resume("t1", acknowledge=False)
    assert result.status=="awaiting_ack"
    assert not result.executed


def test_resume_without_runner_is_ready_not_executed(tmp_path):
    store=PersistentTaskStore(tmp_path/"tasks.sqlite3")
    controls=TaskControlRegistry(store=store)
    controls.register("t1","d1","running",{"step":4})
    executor=WorkflowResumeExecutor(controls, TaskRecoveryEngine())
    result=executor.resume("t1", acknowledge=True)
    assert result.status=="ready"
    assert not result.executed


def test_runner_receives_checkpoint(tmp_path):
    store=PersistentTaskStore(tmp_path/"tasks.sqlite3")
    controls=TaskControlRegistry(store=store)
    controls.register("t1","d1","running",{"step":7,"cursor":"x"})
    seen=[]
    executor=WorkflowResumeExecutor(
        controls, TaskRecoveryEngine(),
        workflow_runner=lambda tid, cp: seen.append((tid, cp))
    )
    result=executor.resume("t1", acknowledge=True)
    assert result.status=="resumed"
    assert result.executed
    assert seen==[("t1",{"step":7,"cursor":"x"})]


def test_runner_failure_marks_task_failed(tmp_path):
    store=PersistentTaskStore(tmp_path/"tasks.sqlite3")
    controls=TaskControlRegistry(store=store)
    controls.register("t1","d1","running",{"step":2})
    executor=WorkflowResumeExecutor(
        controls, TaskRecoveryEngine(),
        workflow_runner=lambda tid, cp: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    result=executor.resume("t1", acknowledge=True)
    assert result.status=="failed"
    assert controls.get("t1").status=="failed"


def test_approval_task_cannot_resume_without_reapproval(tmp_path):
    store=PersistentTaskStore(tmp_path/"tasks.sqlite3")
    controls=TaskControlRegistry(store=store)
    controls.register("t1","d1","awaiting_approval",{"step":5})
    executor=WorkflowResumeExecutor(controls, TaskRecoveryEngine())
    result=executor.resume("t1", acknowledge=True)
    assert result.status=="blocked"
    assert result.reason=="approval state must be re-established"


def test_recovery_ack_route_requires_owner_session(tmp_path):
    db=tmp_path/"all.sqlite3"
    store=PersistentDeviceStore(db)
    device,_=PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device,"sess1",60)
    store_tasks=PersistentTaskStore(db)
    store_tasks.register("t1",device,"running",{"step":1})

    app=create_app(db)
    client=TestClient(app)
    r=client.post("/v1/runtime/recovery/t1/ack",json={
        "device_id":device,"session_id":"sess1","resume":True
    })
    assert r.status_code==200
    assert r.json()["status"] in {"ready","resumed"}
