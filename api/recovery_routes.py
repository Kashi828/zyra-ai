from fastapi import HTTPException

from core.task_recovery import RecoveryReconciler
from core.workflow_resume import WorkflowResumeExecutor


def register_recovery_routes(app, reconciler: RecoveryReconciler,
                             resume_executor: WorkflowResumeExecutor,
                             auth_guard):
    @app.get("/v1/runtime/recovery")
    def recovery_scan():
        return {
            "items": [
                {
                    "task_id": d.task_id,
                    "action": d.action,
                    "reason": d.reason,
                    "checkpoint": d.checkpoint,
                    "owner_device_id": d.owner_device_id,
                }
                for d in reconciler.scan()
            ]
        }

    @app.post("/v1/runtime/recovery/{task_id}/ack")
    def acknowledge_recovery(task_id: str, body: dict):
        device_id = str(body.get("device_id", ""))
        session_id = str(body.get("session_id", ""))
        decision_auth = auth_guard.authorize(
            device_id, session_id, device_id or "anonymous"
        )
        if not decision_auth.allowed:
            raise HTTPException(
                status_code=decision_auth.status_code,
                detail=decision_auth.reason,
            )
        task = resume_executor.controls.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="task not recoverable")
        if task.owner_device_id != device_id:
            raise HTTPException(status_code=403, detail="task belongs to another device")

        result = resume_executor.resume(
            task_id, acknowledge=bool(body.get("resume", False))
        )
        return {
            "ok": result.executed or result.status == "ready",
            "task_id": result.task_id,
            "status": result.status,
            "checkpoint": result.checkpoint,
            "reason": result.reason,
        }
