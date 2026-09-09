from dataclasses import dataclass

@dataclass(frozen=True)
class CommandEvent:
    command_id: str
    event: str
    action: str
    status: str
    detail: str = ""

class CommandEventStream:
    def __init__(self):
        self._events: list[CommandEvent] = []

    def publish(self, event: CommandEvent) -> None:
        self._events.append(event)

    def events(self, command_id: str | None = None) -> list[CommandEvent]:
        if command_id is None:
            return list(self._events)
        return [e for e in self._events if e.command_id == command_id]
