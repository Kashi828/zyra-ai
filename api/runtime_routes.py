from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import HTTPException


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
        url = urls[0].rstrip(".,)"]
        return "open_url", {"url": url}, "windows.browser"

    match = re.match(r"^(?:open|launch|start)\s+(.+)$", text, re.IGNORECASE)
    if match:
        target = match.group(1).strip().strip('"')
        if lowered.startswith(("open folder", "open directory", "open file location")):
            remainder = re.sub(r"^(?:open folder|open directory|open file location)\s*", "", text, flags=re.IGNORECASE).strip()
            return "open_folder", {"path": remainder or "."}, "windows.files.read"
        if target.lower() in {"settings", "windows settings"}:
            return "open_app", {"name": "ms-settings:"}, "windows.apps"
        return "open_app", {"name": target}, "windows.apps"

    if lowered.startswith("open "):
        target = text[5:].strip()
        return "open_app", {"name": target}, "windows.apps"

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

        if capability not in device["capabilities"]:
            raise HTTPException(status_code=403, detail="capability is not granted to device")

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
