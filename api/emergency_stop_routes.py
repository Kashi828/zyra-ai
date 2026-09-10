from fastapi import HTTPException


def register_emergency_stop_routes(app, security_context):
    auth_guard = security_context.api_auth
    stop = security_context.emergency_stop
    audit_log = getattr(app.state, "audit_log", None)

    def authenticate(body):
        device_id = str(body.get("device_id", ""))
        session_id = str(body.get("session_id", ""))
        key = str(body.get("client_key") or device_id or "anonymous")
        decision = auth_guard.authorize(device_id, session_id, key)
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        return device_id, session_id

    @app.get("/v1/security/emergency-stop")
    def emergency_stop_status():
        state = stop.snapshot()
        return {"stopped": state.stopped, "changed_at": state.changed_at, "reason": state.reason}

    @app.post("/v1/security/emergency-stop/engage")
    def emergency_stop_engage(body: dict):
        device_id, session_id = authenticate(body)
        reason = str(body.get("reason") or "manual emergency stop")[:256]
        state = stop.engage(reason)
        if audit_log:
            audit_log.record("emergency_stop.engaged", device_id, session_id, {"reason": reason})
        return {"ok": True, "device_id": device_id, "stopped": state.stopped, "changed_at": state.changed_at}

    @app.post("/v1/security/emergency-stop/release")
    def emergency_stop_release(body: dict):
        device_id, session_id = authenticate(body)
        state = stop.release()
        if audit_log:
            audit_log.record("emergency_stop.released", device_id, session_id)
        return {"ok": True, "device_id": device_id, "stopped": state.stopped, "changed_at": state.changed_at}
