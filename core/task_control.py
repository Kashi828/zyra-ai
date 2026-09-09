from dataclasses import dataclass
from threading import RLock

from security.persistent_task_store import PersistentTaskStore


@dataclass
class TaskControl:
    task_id: str
    owner_device_id: str
    status: str = "queued"
    approval_required: bool = False
    cancelled: bool = False
    checkpoint: dict | None = None


class TaskControlRegistry:
    """Persistent task-control registry; memory is only a compatibility cache."""

    def __init__(self, event_bridge=None, store: PersistentTaskStore | None = None):
        self._tasks: dict[str, TaskControl] = {}
        self._lock = RLock()
        self._event_bridge = event_bridge
        self.store = store

    def bind_store(self, store: PersistentTaskStore):
        self.store = store
        for item in store.recoverable():
            self._tasks[item["task_id"]] = TaskControl(
                item["task_id"],
                item["owner_device_id"],
                item["status"],
                item["approval_required"],
                item["cancelled"],
                item["checkpoint"],
            )

    def register(self, task_id: str, device_id: str, status: str = "queued", checkpoint=None):
        if not task_id or not device_id:
            raise ValueError("task_id and device_id are required")
        task = TaskControl(
            task_id, device_id, status=status,
            approval_required=(status == "awaiting_approval"),
            checkpoint=checkpoint or {},
        )
        with self._lock:
            self._tasks[task_id] = task
        if self.store:
            self.store.register(task_id, device_id, status, task.checkpoint)

    def get(self, task_id: str):
        with self._lock:
            cached = self._tasks.get(task_id)
        if cached:
            return cached
        if self.store:
            item = self.store.get(task_id)
            if item:
                task = TaskControl(
                    item["task_id"], item["owner_device_id"], item["status"],
                    item["approval_required"], item["cancelled"], item["checkpoint"]
                )
                with self._lock:
                    self._tasks[task_id] = task
                return task
        return None

    def set_status(self, task_id: str, status: str, checkpoint=None):
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        with self._lock:
            if task.status in {"completed", "failed", "cancelled"} and status != task.status:
                raise ValueError("task is already terminal")
            task.status = status
            task.approval_required = status == "awaiting_approval"
            if checkpoint is not None:
                task.checkpoint = checkpoint
        if self.store:
            self.store.set_status(task_id, status, task.checkpoint)

    def checkpoint(self, task_id: str, checkpoint: dict):
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        with self._lock:
            task.checkpoint = dict(checkpoint)
        if self.store:
            self.store.update_checkpoint(task_id, task.checkpoint)

    def approve(self, task_id: str, device_id: str):
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        if task.owner_device_id != device_id:
            raise PermissionError("task belongs to another device")
        if not task.approval_required:
            raise ValueError("task is not awaiting approval")
        with self._lock:
            task.approval_required = False
            task.status = "running"
        if self.store:
            self.store.set_status(task_id, "running", task.checkpoint)
        if self._event_bridge:
            self._event_bridge.publish(
                task_id, "running", detail="approval granted",
                device_id=device_id, phase="approval"
            )
        return task

    def cancel(self, task_id: str, device_id: str):
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        if task.owner_device_id != device_id:
            raise PermissionError("task belongs to another device")
        if task.status in {"completed", "failed", "cancelled"}:
            raise ValueError("task is already terminal")
        with self._lock:
            task.cancelled = True
            task.status = "cancelled"
            task.approval_required = False
        if self.store:
            self.store.set_status(task_id, "cancelled", task.checkpoint)
        if self._event_bridge:
            self._event_bridge.publish(
                task_id, "cancelled", detail="remote cancellation requested",
                device_id=device_id, phase="control"
            )
        return task
