from __future__ import annotations

from fastapi import HTTPException

from core.agent_planner import AgentPlanner
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


def register_runtime_routes(app, runtime, auth_gateway=None):
    planner = AgentPlanner()

    def build_plan(goal: str):
        try:
            return planner.plan(goal)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "reason": str(exc),
                    "supported_examples": [
                        "open calculator",
                        "open notepad then open https://example.com",
                        "open folder C:\\Users\\Public then open calculator",
                    ],
                },
            ) from exc

    @app.post("/v1/runtime/plan")
    def preview_plan(body: dict):
        device_id, session_id, device = _authorize(auth_gateway, body)
        goal = str(body.get("goal", "")).strip()
        plan = build_plan(goal)
        decisions = []
        broker = CapabilityBroker(device["capabilities"])
        for step in plan.steps:
            decision = broker.require(step.capability, confirmed=bool(body.get("confirmed", False)))
            decisions.append({
                "step": step.index,
                "action": step.action,
                "capability": step.capability,
                "allowed": decision.allowed,
                "requires_confirmation": decision.requires_confirmation,
                "reason": decision.reason,
            })
        return {
            "goal": plan.goal,
            "device_id": device_id,
            "session_id": session_id,
            "steps": [
                {
                    "index": step.index,
                    "action": step.action,
                    "payload": step.payload,
                    "capability": step.capability,
                }
                for step in plan.steps
            ],
            "authorization": decisions,
        }

    @app.post("/v1/runtime/tasks")
    def create_task(body: dict):
        device_id, session_id, device = _authorize(auth_gateway, body)
        goal = str(body.get("goal", "")).strip()
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")

        action = str(body.get("action", "")).strip()
        payload = dict(body.get("payload") or {})
        confirmed = body.get("confirmed", True)
        if not isinstance(confirmed, bool):
            raise HTTPException(status_code=400, detail="confirmed must be a boolean")

        if action:
            specs = {spec.name: spec for spec in runtime.command_bridge.tools.specs()} if runtime.command_bridge else {}
            spec = specs.get(action)
            if spec is None:
                raise HTTPException(status_code=422, detail="unsupported action")
            capability = spec.capability
            decision = CapabilityBroker(device["capabilities"]).require(capability, confirmed=confirmed)
            if not decision.allowed:
                status = 409 if decision.requires_confirmation else 403
                raise HTTPException(status_code=status, detail={
                    "reason": decision.reason,
                    "capability": capability,
                    "requires_confirmation": decision.requires_confirmation,
                } if decision.requires_confirmation else decision.reason)
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
        else:
            plan = build_plan(goal)
            broker = CapabilityBroker(device["capabilities"])
            for step in plan.steps:
                decision = broker.require(step.capability, confirmed=confirmed)
                if not decision.allowed:
                    status = 409 if decision.requires_confirmation else 403
                    raise HTTPException(status_code=status, detail={
                        "reason": decision.reason,
                        "capability": step.capability,
                        "step": step.index,
                        "requires_confirmation": decision.requires_confirmation,
                    } if decision.requires_confirmation else decision.reason)
            context = dict(body.get("context") or {})
            context.update({
                "device_id": device_id,
                "session_id": session_id,
                "confirmed": confirmed,
                "plan": [
                    {
                        "index": step.index,
                        "action": step.action,
                        "payload": step.payload,
                        "capability": step.capability,
                    }
                    for step in plan.steps
                ],
            })
            task_id = runtime.submit_goal(goal, context)

        task = runtime.snapshot()["active_tasks"][task_id]
        return {
            "task_id": task_id,
            "status": task["status"],
            "detail": task.get("detail", ""),
            "action": task.get("context", {}).get("action"),
            "plan": task.get("plan", []),
            "device_id": device_id,
        }

    @app.get("/v1/runtime/state")
    def runtime_state():
        return runtime.snapshot()
