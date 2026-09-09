from core.zyra_runtime import ZyraRuntime
from core.runtime_events import RuntimeEventStream

def test_runtime_task_lifecycle():
    events = RuntimeEventStream()
    runtime = ZyraRuntime(event_stream=events)
    task_id = runtime.submit_goal("open my project")
    runtime.update_task(task_id, "running", "planning")
    runtime.complete_task(task_id, "done")
    state = runtime.snapshot()
    assert state["active_tasks"][task_id]["status"] == "completed"
    assert [e["event"] for e in events.list(task_id)] == ["queued", "status", "status"]

def test_runtime_rejects_empty_goal():
    runtime = ZyraRuntime()
    try:
        runtime.submit_goal("   ")
    except ValueError:
        pass
    else:
        assert False

def test_device_presence():
    runtime = ZyraRuntime()
    runtime.connect_device("android-1")
    assert runtime.snapshot()["connected_devices"] == ["android-1"]
    runtime.disconnect_device("android-1")
    assert runtime.snapshot()["connected_devices"] == []

def test_unknown_task_rejected():
    runtime = ZyraRuntime()
    try:
        runtime.update_task("missing", "running")
    except KeyError:
        pass
    else:
        assert False
