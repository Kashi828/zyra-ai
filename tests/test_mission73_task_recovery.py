from pathlib import Path
from fastapi.testclient import TestClient

from core.task_recovery import TaskRecoveryEngine, RecoveryReconciler
from security.persistent_task_store import PersistentTaskStore


def test_cancelled_task_is_discarded():
    d=TaskRecoveryEngine().reconcile({
        "task_id":"t1","owner_device_id":"d1","status":"cancelled",
        "cancelled":True,"checkpoint":{"step":2}
    }, {})
    assert d.action=="discard"


def test_running_task_without_live_runtime_can_resume_from_checkpoint():
    d=TaskRecoveryEngine().reconcile({
        "task_id":"t1","owner_device_id":"d1","status":"running",
        "cancelled":False,"checkpoint":{"step":4}
    }, {})
    assert d.action=="resume"
    assert d.checkpoint=={"step":4}


def test_approval_state_requires_manual_reapproval():
    d=TaskRecoveryEngine().reconcile({
        "task_id":"t1","owner_device_id":"d1","status":"awaiting_approval",
        "cancelled":False,"checkpoint":{"step":5}
    }, {})
    assert d.action=="await_approval"


def test_checkpoint_mismatch_requires_manual_review():
    d=TaskRecoveryEngine().reconcile({
        "task_id":"t1","owner_device_id":"d1","status":"running",
        "cancelled":False,"checkpoint":{"step":4}
    }, {"t1":{"status":"running","checkpoint":{"step":3}}})
    assert d.action=="manual_review"


def test_runtime_terminal_state_is_reconciled():
    d=TaskRecoveryEngine().reconcile({
        "task_id":"t1","owner_device_id":"d1","status":"running",
        "cancelled":False,"checkpoint":{"step":4}
    }, {"t1":{"status":"completed","checkpoint":{"step":4}}})
    assert d.action=="reconcile_terminal"


def test_recovery_scan_reads_persistent_store(tmp_path):
    store=PersistentTaskStore(tmp_path/"s.sqlite3")
    store.register("t1","d1","running",{"step":2})
    results=RecoveryReconciler(store).scan()
    assert len(results)==1
    assert results[0].task_id=="t1"


def test_recovery_routes_registered():
    from api.app_factory import create_app
    app=create_app()
    paths={getattr(r,"path","") for r in app.routes}
    assert "/v1/runtime/recovery" in paths


def test_recovery_ack_only_allows_safe_resume(tmp_path):
    db=tmp_path/"s.sqlite3"
    from security.persistent_device_store import PersistentDeviceStore
    from security.persistent_enrollment import PersistentEnrollment
    security_store=PersistentDeviceStore(db)
    device,_=PersistentEnrollment(security_store).create_device({"pc.apps"})
    security_store.issue_session(device,"sess1",60)
    store=PersistentTaskStore(db)
    store.register("t1",device,"running",{"step":2})
    app=__import__("api.app_factory",fromlist=["create_app"]).create_app(db)
    client=TestClient(app)
    r=client.post("/v1/runtime/recovery/t1/ack",json={
        "device_id":device,"session_id":"sess1","resume":True
    })
    assert r.status_code==200
    assert r.json()["status"] in {"ready","resumed"}
