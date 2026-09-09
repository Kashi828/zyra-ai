from security.session_registry import ActiveSession, SessionRegistry
from services.authenticated_command import CommandRequest
from services.remote_windows_bridge import RemoteWindowsBridge

def setup_bridge():
    registry = SessionRegistry()
    registry.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    calls = []
    def runner(action, payload):
        calls.append((action, payload))
        return "ok"
    bridge = RemoteWindowsBridge(registry, {"d1": {"pc.apps", "pc.files", "pc.web"}}, runner=runner)
    return bridge, calls

def test_remote_bridge_executes_allowlisted_app_action():
    bridge, calls = setup_bridge()
    result = bridge.execute(CommandRequest("s1", "d1", "open_app", {"name": "notepad"}), now=1100, command_id="c1")
    assert result.accepted and result.status == "completed"
    assert calls == [("open_app", {"name": "notepad"})]
    assert [e.event for e in bridge.events.events("c1")] == ["started", "completed"]

def test_missing_capability_blocks_action():
    registry = SessionRegistry()
    registry.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    bridge = RemoteWindowsBridge(registry, {"d1": set()}, runner=lambda *_: "bad")
    result = bridge.execute(CommandRequest("s1", "d1", "open_app", {"name": "notepad"}), now=1100)
    assert not result.accepted and result.status == "failed"

def test_unsupported_remote_action_rejected():
    bridge, calls = setup_bridge()
    result = bridge.execute(CommandRequest("s1", "d1", "run_shell", {"cmd": "whoami"}), now=1100)
    assert not result.accepted
    assert calls == []

def test_invalid_session_does_not_touch_windows_runner():
    bridge, calls = setup_bridge()
    result = bridge.execute(CommandRequest("wrong", "d1", "open_app", {"name": "notepad"}), now=1100)
    assert not result.accepted
    assert calls == []
