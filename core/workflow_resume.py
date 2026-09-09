from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeResult:
    task_id: str
    status: str
    checkpoint: dict
    executed: bool
    reason: str


class WorkflowResumeExecutor:
    """Executes only explicitly approved recovery decisions."""

    def __init__(self, controls, recovery_engine, workflow_runner=None, event_bridge=None):
        self.controls = controls
        self.recovery_engine = recovery_engine
        self.workflow_runner = workflow_runner
        self.event_bridge = event_bridge

    def resume(self, task_id: str, acknowledge: bool = False) -> ResumeResult:
        task = self.controls.get(task_id)
        if task is None:
            raise KeyError(task_id)

        persisted = {
            "task_id": task.task_id,
            "owner_device_id": task.owner_device_id,
            "status": task.status,
            "approval_required": task.approval_required,
            "cancelled": task.cancelled,
            "checkpoint": task.checkpoint or {},
        }
        decision = self.recovery_engine.reconcile(persisted, {})
        if decision.action != "resume":
            return ResumeResult(
                task_id, "blocked", decision.checkpoint, False, decision.reason
            )
        if not acknowledge:
            return ResumeResult(
                task_id, "awaiting_ack", decision.checkpoint, False,
                "explicit recovery acknowledgement required"
            )
        if task.cancelled or task.status == "cancelled":
            return ResumeResult(
                task_id, "blocked", task.checkpoint or {}, False, "task was cancelled"
            )

        self.controls.set_status(task_id, "running", task.checkpoint)
        if self.event_bridge:
            self.event_bridge.publish(
                task_id, "running",
                detail="workflow recovery approved",
                device_id=task.owner_device_id,
                phase="recovery",
                payload={"checkpoint": task.checkpoint or {}},
            )

        if self.workflow_runner is None:
            return ResumeResult(
                task_id, "ready", task.checkpoint or {}, False,
                "checkpoint validated; workflow runner is not configured"
            )

        try:
            self.workflow_runner(task_id, task.checkpoint or {})
        except Exception as exc:
            self.controls.set_status(task_id, "failed", task.checkpoint)
            if self.event_bridge:
                self.event_bridge.publish(
                    task_id, "failed",
                    detail="workflow resume failed",
                    device_id=task.owner_device_id,
                    phase="recovery",
                    payload={"error": str(exc)},
                )
            return ResumeResult(
                task_id, "failed", task.checkpoint or {}, False, "workflow runner failed"
            )

        return ResumeResult(
            task_id, "resumed", task.checkpoint or {}, True,
            "workflow runner accepted checkpoint"
        )
