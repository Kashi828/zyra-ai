from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryDecision:
    task_id: str
    action: str
    reason: str
    checkpoint: dict
    owner_device_id: str


class TaskRecoveryEngine:
    """Reconciles durable task state with the currently known runtime state."""

    SAFE_TO_RESUME = {"queued", "planning", "running"}
    MANUAL_REVIEW = {"awaiting_approval"}

    def reconcile(self, persisted, runtime_state):
        task_id = persisted["task_id"]
        runtime = runtime_state.get(task_id)

        if persisted.get("cancelled") or persisted["status"] == "cancelled":
            return RecoveryDecision(
                task_id, "discard", "task was cancelled before restart",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        if persisted["status"] in {"completed", "failed"}:
            return RecoveryDecision(
                task_id, "discard", "task is terminal",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        if persisted["status"] == "awaiting_approval":
            return RecoveryDecision(
                task_id, "await_approval", "approval state must be re-established",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        if runtime is None:
            return RecoveryDecision(
                task_id, "resume", "no live runtime state; use persisted checkpoint",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        live_status = runtime.get("status")
        if live_status in {"completed", "failed", "cancelled"}:
            return RecoveryDecision(
                task_id, "reconcile_terminal",
                f"runtime reports terminal state: {live_status}",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        live_checkpoint = runtime.get("checkpoint")
        if live_checkpoint is not None and live_checkpoint != persisted.get("checkpoint", {}):
            return RecoveryDecision(
                task_id, "manual_review",
                "persisted and live checkpoints differ",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        if persisted["status"] in self.SAFE_TO_RESUME:
            return RecoveryDecision(
                task_id, "resume", "checkpoint reconciled",
                persisted.get("checkpoint", {}), persisted["owner_device_id"]
            )

        return RecoveryDecision(
            task_id, "manual_review", "unknown recovery condition",
            persisted.get("checkpoint", {}), persisted["owner_device_id"]
        )


class RecoveryReconciler:
    def __init__(self, task_store, runtime_provider=None):
        self.task_store = task_store
        self.runtime_provider = runtime_provider or (lambda: {})

    def scan(self):
        runtime = self.runtime_provider()
        return [
            TaskRecoveryEngine().reconcile(item, runtime)
            for item in self.task_store.recoverable()
        ]
