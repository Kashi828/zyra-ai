from fastapi import HTTPException


def register_agent_routes(app, security_context, runtime):
    auth_guard = security_context.api_auth
    stop = security_context.emergency_stop
    audit_log = getattr(app.state, "audit_log", None)

    def authenticate(body):
        device_id = str(body.get("device_id", ""))
        session_id = str(body.get("session_id", ""))
        decision = auth_guard.authorize(device_id, session_id, session_id)
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        return device_id, session_id

    @app.post("/v1/agent/stop")
    def stop_agent(body: dict):
        device_id, session_id = authenticate(body)
        state = stop.engage("agent stop requested")
        for task_id, task in list(runtime.snapshot()["active_tasks"].items()):
            if task.get("status") in {"queued", "running"}:
                runtime.fail_task(task_id, "cancelled by agent stop")
        if audit_log:
            audit_log.record("agent.stop", device_id, session_id)
        return {"ok": True, "stopped": state.stopped}

    @app.post("/v1/agent/resume")
    def resume_agent(body: dict):
        device_id, session_id = authenticate(body)
        state = stop.release()
        if audit_log:
            audit_log.record("agent.resume", device_id, session_id)
        return {"ok": True, "stopped": state.stopped}
