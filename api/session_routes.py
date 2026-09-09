from fastapi import HTTPException


def register_session_routes(app, session_service):
    @app.post("/v1/session/create")
    def create_session(body: dict):
        device_id = str(body.get("device_id", ""))
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id is required")
        try:
            return {"ok": True, **session_service.create(device_id)}
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    @app.post("/v1/session/refresh")
    def refresh_session(body: dict):
        device_id = str(body.get("device_id", ""))
        token = str(body.get("refresh_token", ""))
        if not device_id or not token:
            raise HTTPException(status_code=400, detail="device_id and refresh_token are required")
        try:
            return {"ok": True, **session_service.refresh(device_id, token)}
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc))

    @app.post("/v1/session/logout")
    def logout(body: dict):
        device_id = str(body.get("device_id", ""))
        session_id = str(body.get("session_id", ""))
        if not device_id or not session_id:
            raise HTTPException(status_code=400, detail="device_id and session_id are required")
        session_service.logout(device_id, session_id)
        return {"ok": True, "logged_out": True}

    @app.post("/v1/session/logout-device")
    def logout_device(body: dict):
        device_id = str(body.get("device_id", ""))
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id is required")
        session_service.logout_device(device_id)
        return {"ok": True, "device_revoked": True}
