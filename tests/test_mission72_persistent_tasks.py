from pathlib import Path

from core.task_control import TaskControlRegistry
from security.persistent_task_store import PersistentTaskStore


def test_task_control_survives_registry_reload(tmp_path):
    db = tmp_path / "security.sqlite3"
    store1 = PersistentTaskStore(db)
    r1 = TaskControlRegistry(store=store1)
    r1.register("t1", "d1", "running", checkpoint={"step": 3})
    r1.checkpoint("t1", {"step": 4, "cursor": "abc"})

    store2 = PersistentTaskStore(db)
    r2 = TaskControlRegistry(store=store2)
    r2.bind_store(store2)
    task = r2.get("t1")
    assert task is not None
    assert task.status == "running"
    assert task.owner_device_id == "d1"
    assert task.checkpoint == {"step": 4, "cursor": "abc"}


def test_approval_state_survives_reload(tmp_path):
    db = tmp_path / "security.sqlite3"
    s = PersistentTaskStore(db)
    r = TaskControlRegistry(store=s)
    r.register("t1", "d1", "awaiting_approval")
    r2 = TaskControlRegistry(store=PersistentTaskStore(db))
    r2.bind_store(r2.store)
    t = r2.get("t1")
    assert t.approval_required
    assert t.status == "awaiting_approval"


def test_cancel_state_survives_reload(tmp_path):
    db = tmp_path / "security.sqlite3"
    s = PersistentTaskStore(db)
    r = TaskControlRegistry(store=s)
    r.register("t1", "d1", "running")
    r.cancel("t1", "d1")
    r2 = TaskControlRegistry(store=PersistentTaskStore(db))
    r2.bind_store(r2.store)
    t=r2.get("t1")
    assert t.status == "cancelled"
    assert t.cancelled


def test_recoverable_excludes_terminal_tasks(tmp_path):
    s = PersistentTaskStore(tmp_path/"security.sqlite3")
    s.register("a","d1","running",{"step":1})
    s.register("b","d1","completed",{"step":9})
    ids={x["task_id"] for x in s.recoverable()}
    assert ids == {"a"}


def test_mission72_files_exist():
    assert Path("security/persistent_task_store.py").exists()
    assert Path("core/task_control.py").exists()
