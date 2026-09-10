from fastapi import HTTPException


def _authorize(auth_guard, body):
    if auth_guard is None:
        raise HTTPException(status_code=503, detail="ecosystem authentication is unavailable")
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    if not device_id or not session_id:
        raise HTTPException(status_code=401, detail="device_id and session_id are required")
    decision = auth_guard.authorize(device_id, session_id, session_id)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)
    return device_id


def register_ecosystem_routes(app, coordinator, auth_guard, registry=None):
    @app.get("/v1/ecosystem/devices")
    def ecosystem_devices():
        if registry is not None:
            return {"devices": [
                {
                    "device_id": d.device_id,
                    "device_type": d.device_type,
                    "display_name": d.display_name,
                    "capabilities": sorted(d.capabilities),
                    "online": d.online,
                    "last_seen": d.last_seen,
                    "revoked": d.revoked,
                }
                for d in registry.devices()
            ]}
        return coordinator.snapshot()

    @app.post("/v1/ecosystem/enroll")
    def ecosystem_enroll(body: dict):
        source_device_id = _authorize(auth_guard, body)
        target_device_id = str(body.get("target_device_id", ""))
        device_type = str(body.get("device_type", ""))
        display_name = str(body.get("display_name", ""))
        if not target_device_id or not device_type:
            raise HTTPException(status_code=400, detail="target_device_id and device_type are required")
        if registry is None:
            raise HTTPException(status_code=503, detail="ecosystem registry is unavailable")
        trusted = registry.store.get_device(target_device_id)
        if not trusted or trusted["revoked"]:
            raise HTTPException(status_code=403, detail="target device is not trusted")
        # Only an already-authenticated trusted device can add another already-trusted device.
        registry.register(target_device_id, device_type, display_name, online=False)
        return {
            "ok": True,
            "authorized_by": source_device_id,
            "device_id": target_device_id,
            "device_type": device_type,
            "status": "enrolled",
        }

    @app.post("/v1/ecosystem/heartbeat")
    def ecosystem_heartbeat(body: dict):
        device_id = _authorize(auth_guard, body)
        if registry is None:
            raise HTTPException(status_code=503, detail="ecosystem registry is unavailable")
        registry.register(
            device_id,
            str(body.get("device_type", "unknown")),
            str(body.get("display_name", "")),
            online=True,
        )
        return {"ok": True, "device_id": device_id, "status": "online"}

    @app.post("/v1/ecosystem/route")
    def route_ecosystem_task(body: dict):
        source_device_id = _authorize(auth_guard, body)
        target_device_id = str(body.get("target_device_id", ""))
        capability = str(body.get("capability", ""))
        if not target_device_id or not capability:
            raise HTTPException(status_code=400, detail="target_device_id and capability are required")

        decision = coordinator.route(source_device_id, target_device_id, capability)
        if not decision.allowed:
            status = 409 if "confirmation" in decision.reason else 403
            raise HTTPException(
                status_code=status,
                detail={
                    "reason": decision.reason,
                    "source_device_id": source_device_id,
                    "target_device_id": target_device_id,
                    "capability": capability,
                },
            )
        return {
            "ok": True,
            "source_device_id": source_device_id,
            "target_device_id": target_device_id,
            "capability": capability,
            "status": "route_authorized",
        }
