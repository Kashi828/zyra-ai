from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


_STATUS_TEXT = {
    "queued": "I queued your task.",
    "planning": "I am planning that now.",
    "running": "I am working on it.",
    "awaiting_approval": "I need your approval before I continue.",
    "completed": "Your task is complete.",
    "failed": "Your task could not be completed.",
    "cancelled": "Your task was cancelled.",
}


@dataclass(frozen=True)
class VoiceStatusMessage:
    status: str
    text: str
    task_id: str | None = None


class VoiceStatusAnnouncer:
    """Provider-neutral task-status speech policy with duplicate suppression."""

    def __init__(
        self,
        speak: Callable[[str], None],
        *,
        enabled: bool = True,
        announce_statuses: set[str] | None = None,
    ):
        self.speak = speak
        self.enabled = enabled
        self.announce_statuses = announce_statuses or {
            "queued", "planning", "running",
            "awaiting_approval", "completed", "failed", "cancelled",
        }
        self._last: dict[str, str] = {}

    def message(self, task_id: str | None, status: str) -> VoiceStatusMessage | None:
        status = str(status or "").strip()
        if not self.enabled or status not in self.announce_statuses:
            return None
        if task_id and self._last.get(task_id) == status:
            return None
        if task_id:
            self._last[task_id] = status
        return VoiceStatusMessage(
            status=status,
            task_id=task_id,
            text=_STATUS_TEXT.get(status, f"Task status: {status}."),
        )

    def announce(self, task_id: str | None, status: str) -> VoiceStatusMessage | None:
        msg = self.message(task_id, status)
        if msg is not None:
            self.speak(msg.text)
        return msg
