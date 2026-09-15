from types import SimpleNamespace

from core.zyra_runtime import ZyraRuntime


class FakeBridge:
    def __init__(self):
        self.calls = []

    def execute(self, request, command_id=None):
        self.calls.append((request.action, request.payload, command_id))
        return SimpleNamespace(accepted=True, message=f"done:{request.action}")


def test_runtime_executes_multi_step_plan_in_order():
    bridge = FakeBridge()
    runtime = ZyraRuntime(command_bridge=bridge)
    task_id = runtime.submit_goal(
        "open calculator then open https://example.com",
        {
            "device_id": "pc-1",
            "session_id": "session-1",
            "plan": [
                {"index": 0, "action": "open_app", "payload": {"name": "calculator"}, "capability": "windows.apps"},
                {"index": 1, "action": "open_url", "payload": {"url": "https://example.com"}, "capability": "windows.browser"},
            ],
        },
    )
    task = runtime.snapshot()["active_tasks"][task_id]
    assert task["status"] == "completed"
    assert task["step_status"] == ["completed", "completed"]
    assert [call[0] for call in bridge.calls] == ["open_app", "open_url"]
    assert task["current_step"] == 1


def test_runtime_fails_at_first_rejected_step():
    class RejectingBridge(FakeBridge):
        def execute(self, request, command_id=None):
            self.calls.append((request.action, request.payload, command_id))
            return SimpleNamespace(accepted=False, message="rejected")

    bridge = RejectingBridge()
    runtime = ZyraRuntime(command_bridge=bridge)
    task_id = runtime.submit_goal(
        "open calculator then open notepad",
        {
            "device_id": "pc-1",
            "session_id": "session-1",
            "plan": [
                {"index": 0, "action": "open_app", "payload": {"name": "calculator"}, "capability": "windows.apps"},
                {"index": 1, "action": "open_app", "payload": {"name": "notepad"}, "capability": "windows.apps"},
            ],
        },
    )
    task = runtime.snapshot()["active_tasks"][task_id]
    assert task["status"] == "failed"
    assert task["step_status"] == ["failed", "queued"]
    assert len(bridge.calls) == 1
