from dataclasses import dataclass, field
from threading import RLock
import uuid
from core.realtime_events import RealtimeEvent


@dataclass
class RuntimeState:
    active_tasks: dict = field(default_factory=dict)
    connected_devices: set[str] = field(default_factory=set)


class ZyraRuntime:
    """Coordinates safe task execution while keeping authorization at the command boundary."""

    def __init__(self, orchestrator=None, workflow_engine=None, command_bridge=None, transfer_worker=None, event_stream=None):
        self.orchestrator = orchestrator
        self.workflow_engine = workflow_engine
        self.command_bridge = command_bridge
        self.transfer_worker = transfer_worker
        self.event_stream = event_stream
        self.realtime_hub = None
        self.state = RuntimeState()
        self._lock = RLock()

    def _publish(self, task_id: str, status: str, detail: str = "") -> None:
        if self.event_stream:
            self.event_stream.publish({"task_id": task_id, "event": "status", "status": status, "detail": detail})
        hub = getattr(self, "realtime_hub", None)
        if hub:
            hub.publish(RealtimeEvent(event_id=task_id, event_type="task.updated", device_id=None, task_id=task_id, status=status, payload={"detail": detail}))

    def submit_goal(self, goal: str, context: dict | None = None) -> str:
        if not goal or not goal.strip():
            raise ValueError("goal is required")
        context = dict(context or {})
        task_id = uuid.uuid4().hex
        clean_goal = goal.strip()
        plan = list(context.get("plan") or [])
        with self._lock:
            task = {"goal": clean_goal, "status": "queued", "context": context}
            if plan:
                task["plan"] = plan
                task["current_step"] = 0
                task["step_status"] = ["queued"] * len(plan)
            self.state.active_tasks[task_id] = task
        if self.event_stream:
            self.event_stream.publish({"task_id": task_id, "event": "queued", "status": "queued", "detail": ""})
        hub = getattr(self, "realtime_hub", None)
        if hub:
            hub.publish(RealtimeEvent(event_id=task_id, event_type="task.queued", device_id=context.get("device_id"), task_id=task_id, status="queued", payload={"goal": clean_goal, "steps": len(plan)}))

        if self.command_bridge is None:
            return task_id
        if plan:
            self._execute_plan(task_id, plan, context)
            return task_id

        action = context.get("action")
        if not action:
            return task_id
        self._execute_single(task_id, action, dict(context.get("payload") or {}), context)
        return task_id

    def _execute_plan(self, task_id: str, plan: list[dict], context: dict) -> None:
        from services.authenticated_command import CommandRequest
        self.update_task(task_id, "running", f"Planning complete · {len(plan)} step(s)")
        for index, step in enumerate(plan):
            task = self.state.active_tasks.get(task_id)
            if task is None or task.get("status") == "cancelled":
                return
            action = str(step.get("action", ""))
            payload = dict(step.get("payload") or {})
            if not action:
                self.fail_task(task_id, f"plan step {index + 1} is invalid")
                return
            with self._lock:
                task["current_step"] = index
                task["step_status"][index] = "running"
            self._publish(task_id, "running", f"Step {index + 1}/{len(plan)} · {action}")
            try:
                request = CommandRequest(
                    session_id=str(context.get("session_id", "")),
                    device_id=str(context.get("device_id", "")),
                    action=action,
                    payload=payload,
                )
                result = self.command_bridge.execute(request, command_id=f"{task_id}:{index}")
            except Exception:
                result = None
            if result is None or not result.accepted:
                with self._lock:
                    task["step_status"][index] = "failed"
                self.fail_task(task_id, result.message if result else "action execution failed")
                return
            with self._lock:
                task["step_status"][index] = "completed"
                task["last_result"] = result.message
            self._publish(task_id, "running", f"Step {index + 1}/{len(plan)} completed · {result.message}")
        self.complete_task(task_id, "agent plan completed")

    def _execute_single(self, task_id: str, action: str, payload: dict, context: dict) -> None:
        self.update_task(task_id, "running", f"Executing {action}")
        try:
            from services.authenticated_command import CommandRequest
            request = CommandRequest(
                session_id=str(context.get("session_id", "")),
                device_id=str(context.get("device_id", "")),
                action=str(action),
                payload=payload,
            )
            result = self.command_bridge.execute(request, command_id=task_id)
            if result.accepted:
                self.complete_task(task_id, result.message)
            else:
                self.fail_task(task_id, result.message)
        except Exception:
            self.fail_task(task_id, "action execution failed")

    def update_task(self, task_id: str, status: str, detail: str = "") -> None:
        with self._lock:
            if task_id not in self.state.active_tasks:
                raise KeyError(task_id)
            self.state.active_tasks[task_id]["status"] = status
            self.state.active_tasks[task_id]["detail"] = detail
        self._publish(task_id, status, detail)

    def complete_task(self, task_id: str, result: str) -> None:
        self.update_task(task_id, "completed", result)

    def fail_task(self, task_id: str, reason: str) -> None:
        self.update_task(task_id, "failed", reason)

    def connect_device(self, device_id: str) -> None:
        if not device_id:
            raise ValueError("device_id is required")
        with self._lock:
            self.state.connected_devices.add(device_id)

    def disconnect_device(self, device_id: str) -> None:
        with self._lock:
            self.state.connected_devices.discard(device_id)

    def submit_voice_audio(self, voice_gateway, session_id: str, device_id: str, audio: bytes, *, content_type: str = "audio/wav", context: dict | None = None):
        transcript = voice_gateway.transcribe(audio, content_type=content_type)
        return voice_gateway.handle_transcript(session_id, device_id, transcript, context=context)

    def snapshot(self) -> dict:
        with self._lock:
            return {"active_tasks": dict(self.state.active_tasks), "connected_devices": sorted(self.state.connected_devices)}
