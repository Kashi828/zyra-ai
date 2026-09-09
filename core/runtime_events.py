class RuntimeEventStream:
    def __init__(self):
        self._events = []

    def publish(self, event):
        self._events.append(dict(event))

    def list(self, task_id=None):
        if task_id is None:
            return list(self._events)
        return [e for e in self._events if e.get("task_id") == task_id]
