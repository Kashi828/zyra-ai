from fastapi import HTTPException

from security.capability_broker import CapabilityBroker


def _authorize(auth_gateway, body):
    if auth_gateway is None:
        raise HTTPException(status_code=503, detail="runtime authentication is unavailable")
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    if not device_id or not session_id:
        raise HTTPException(status_code=401, detail="device_id and session_id are required")
    decision = auth_gateway.authorize(device_id, session_id, session_id)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)
    device = auth_gateway.store.get_device(device_id)
    if not device:
        raise HTTPException(status_code=401, detail="unknown device")
    return device_id, device


def register_runtime_routes(app, runtime, auth_gateway=None):
    @app.post("/v1/runtime/tasks")
    def create_task(body: dict):
        device_id, device = _authorize(auth_gateway, body)
        goal = str(body.get("goal", ""))
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")

        capability = str(body.get("capability", ""))
        if not capability:
            raise HTTPException(status_code=400, detail="capability is required")

        broker = CapabilityBroker(device["capabilities"])
        decision = broker.require(
            capability,
            confirmed=bool(body.get("confirmed", False)),
        )
        if not decision.allowed:
            if decision.requires_confirmation:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "reason": decision.reason,
                        "capability": capability,
                        "requires_confirmation": True,
                    },
                )
            raise HTTPException(status_code=403, detail=decision.reason)

        context = dict(body.get("context") or {})
        context["device_id"] = device_id
        context["capability"] = capability
        task_id = runtime.submit_goal(goal, context)
        return {
            "task_id": task_id,
            "status": "queued",
            "device_id": device_id,
            "capability": capability,
        }

    @app.get("/v1/runtime/state")
    def runtime_state():
        return runtime.snapshot()
