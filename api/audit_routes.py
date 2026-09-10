from fastapi import HTTPException


def _authenticate(auth_guard, body: dict):
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    key = str(body.get("client_key") or device_id or "anonymous")
    decision = auth_guard.authorize(device_id, session_id, key)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)
    return device_id, session_id


def register_audit_routes(app, security_context, audit_log):
    auth_guard = security_context.api_auth

    @app.post("/v1/security/audit")
    def record_audit(body: dict):
        device_id, session_id = _authenticate(auth_guard, body)
        event = audit_log.record(
            body.get("event_type", "client.event"),
            device_id,
            session_id,
            body.get("detail", ""),
        )
        return {"ok": True, "event_id": event.event_id, "created_at": event.created_at}

    @app.post("/v1/security/audit/query")
    def query_audit(body: dict):
        device_id, _ = _authenticate(auth_guard, body)
        events = audit_log.recent_for_device(device_id, body.get("limit", 100))
        return {
            "ok": True,
            "device_id": device_id,
            "events": [event.__dict__ for event in events],
        }
