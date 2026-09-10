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

    def __init__(
        self,
        orchestrator=None,
        workflow_engine=None,
        command_bridge=None,
        transfer_worker=None,
        event_stream=None,
    ):
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
            self.event_stream.publish({
                "task_id": task_id,
                "event": "status",
                "status": status,
                "detail": detail,
            })
        hub = getattr(self, "realtime_hub", None)
        if hub:
            hub.publish(RealtimeEvent(
                event_id=task_id,
                event_type="task.updated",
                device_id=None,
                task_id=task_id,
                status=status,
                payload={"detail": detail},
            ))

    def submit_goal(self, goal: str, context: dict | None = None) -> str:
        if not goal or not goal.strip():
            raise ValueError("goal is required")
        context = dict(context or {})
        task_id = uuid.uuid4().hex
        with self._lock:
            self.state.active_tasks[task_id] = {
                "goal": goal.strip(),
                "status": "queued",
                "context": context,
            }

        hub = getattr(self, "realtime_hub", None)
        if hub:
            hub.publish(RealtimeEvent(
                event_id=task_id,
                event_type="task.queued",
                device_id=context.get("device_id"),
                task_id=task_id,
                status="queued",
                payload={"goal": goal.strip()},
            ))

        action = context.get("action")
        if not action or self.command_bridge is None:
            return task_id

        self.update_task(task_id, "running", f"Executing {action}")
        try:
            from services.authenticated_command import CommandRequest
            request = CommandRequest(
                session_id=str(context.get("session_id", "")),
                device_id=str(context.get("device_id", "")),
                action=str(action),
                payload=dict(context.get("payload") or {}),
            )
            result = self.command_bridge.execute(request, command_id=task_id)
            if result.accepted:
                self.complete_task(task_id, result.message)
            else:
                self.fail_task(task_id, result.message)
        except Exception:
            self.fail_task(task_id, "action execution failed")
        return task_id

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

    def submit_voice_audio(
        self,
        voice_gateway,
        session_id: str,
        device_id: str,
        audio: bytes,
        *,
        content_type: str = "audio/wav",
        context: dict | None = None,
    ):
        transcript = voice_gateway.transcribe(audio, content_type=content_type)
        return voice_gateway.handle_transcript(
            session_id,
            device_id,
            transcript,
            context=context,
        )

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "active_tasks": dict(self.state.active_tasks),
                "connected_devices": sorted(self.state.connected_devices),
            }
