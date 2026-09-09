from core.realtime_events import RealtimeEvent, RealtimeEventHub


class TaskRealtimeBridge:
    """Publishes normalized agent lifecycle events into the realtime hub."""

    def __init__(self, hub: RealtimeEventHub):
        self.hub = hub

    def publish(self, task_id, status, detail="", device_id=None, phase=None, payload=None):
        event_type = {
            "queued": "task.queued",
            "planning": "task.planning",
            "running": "task.running",
            "awaiting_approval": "task.approval_required",
            "completed": "task.completed",
            "failed": "task.failed",
            "cancelled": "task.cancelled",
        }.get(status, "task.updated")
        data = dict(payload or {})
        if detail:
            data["detail"] = detail
        if phase:
            data["phase"] = phase
        self.hub.publish(RealtimeEvent(
            event_id=task_id,
            event_type=event_type,
            device_id=device_id,
            task_id=task_id,
            status=status,
            payload=data,
        ))
