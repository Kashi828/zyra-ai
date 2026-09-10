from __future__ import annotations

import re

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
    return device_id, session_id, device


def _plan_goal(goal: str) -> tuple[str, dict, str]:
    text = goal.strip()
    lowered = text.lower()

    urls = re.findall(r"https?://[^\s]+", text)
    if urls:
        return "open_url", {"url": urls[0].rstrip(".,)"]}, "windows.browser"

    folder_match = re.match(r"^(?:open|show)\s+(?:folder|directory)\s+(.+)$", text, re.IGNORECASE)
    if folder_match:
        return "open_folder", {"path": folder_match.group(1).strip().strip('"')}, "windows.files.read"

    app_match = re.match(r"^(?:open|launch|start)\s+(.+)$", text, re.IGNORECASE)
    if app_match:
        target = app_match.group(1).strip().strip('"')
        return "open_app", {"name": target}, "windows.apps"

    if lowered in {"open settings", "open windows settings"}:
        return "open_app", {"name": "settings"}, "windows.apps"

    raise HTTPException(
        status_code=422,
        detail={
            "reason": "goal is not mapped to a safe built-in action",
            "supported_examples": [
                "open calculator",
                "open notepad",
                "open folder C:\\Users\\Public",
                "open https://example.com",
            ],
        },
    )


def register_runtime_routes(app, runtime, auth_gateway=None):
    @app.post("/v1/runtime/tasks")
    def create_task(body: dict):
        device_id, session_id, device = _authorize(auth_gateway, body)
        goal = str(body.get("goal", "")).strip()
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")

        action = str(body.get("action", "")).strip()
        payload = dict(body.get("payload") or {})
        if not action:
            action, planned_payload, capability = _plan_goal(goal)
            if not payload:
                payload = planned_payload
        else:
            specs = {spec.name: spec for spec in runtime.command_bridge.tools.specs()} if runtime.command_bridge else {}
            spec = specs.get(action)
            if spec is None:
                raise HTTPException(status_code=422, detail="unsupported action")
            capability = spec.capability

        confirmed = body.get("confirmed", False)
        if not isinstance(confirmed, bool):
            raise HTTPException(status_code=400, detail="confirmed must be a boolean")

        broker = CapabilityBroker(device["capabilities"])
        decision = broker.require(capability, confirmed=confirmed)
        if not decision.allowed:
            status = 409 if decision.requires_confirmation else 403
            detail = {
                "reason": decision.reason,
                "capability": capability,
                "requires_confirmation": decision.requires_confirmation,
            } if decision.requires_confirmation else decision.reason
            raise HTTPException(status_code=status, detail=detail)

        context = dict(body.get("context") or {})
        context.update({
            "device_id": device_id,
            "session_id": session_id,
            "capability": capability,
            "action": action,
            "payload": payload,
            "confirmed": confirmed,
        })
        task_id = runtime.submit_goal(goal, context)
        task = runtime.snapshot()["active_tasks"][task_id]
        return {
            "task_id": task_id,
            "status": task["status"],
            "detail": task.get("detail", ""),
            "action": action,
            "device_id": device_id,
            "capability": capability,
        }

    @app.get("/v1/runtime/state")
    def runtime_state():
        return runtime.snapshot()
