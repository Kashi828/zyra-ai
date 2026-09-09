from fastapi import HTTPException

from core.task_realtime_bridge import TaskRealtimeBridge
from core.task_control import TaskControlRegistry


def _authorize(auth_guard, body):
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    decision = auth_guard.authorize(
        device_id, session_id, device_id or "anonymous"
    )
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)
    return device_id


def register_task_event_routes(app, event_bridge: TaskRealtimeBridge,
                               controls: TaskControlRegistry, auth_guard):
    @app.post("/v1/runtime/tasks/{task_id}/events")
    def publish_task_event(task_id: str, body: dict):
        device_id = _authorize(auth_guard, body)
        status = str(body.get("status", ""))
        if status == "": 
            raise HTTPException(status_code=400, detail="status is required")
        # A remote device may publish only to a task it owns / has registered.
        existing = controls.get(task_id)
        if existing is None:
            controls.register(task_id, device_id, status=status)
        elif existing.owner_device_id != device_id:
            raise HTTPException(status_code=403, detail="task belongs to another device")
        else:
            controls.set_status(task_id, status)

        event_bridge.publish(
            task_id=task_id,
            status=status,
            detail=str(body.get("detail", "")),
            device_id=device_id,
            phase=body.get("phase"),
            payload=body.get("payload") or {},
        )
        return {"ok": True, "task_id": task_id, "status": status}

    @app.post("/v1/runtime/tasks/{task_id}/approve")
    def approve_task(task_id: str, body: dict):
        device_id = _authorize(auth_guard, body)
        try:
            task = controls.approve(task_id, device_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {"ok": True, "task_id": task.task_id, "status": task.status}

    @app.post("/v1/runtime/tasks/{task_id}/cancel")
    def cancel_task(task_id: str, body: dict):
        device_id = _authorize(auth_guard, body)
        try:
            task = controls.cancel(task_id, device_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {"ok": True, "task_id": task.task_id, "status": task.status}
