from security.session_registry import ActiveSession, SessionRegistry
from services.authenticated_command import AuthenticatedCommandExecutor, CommandRequest
from services.command_events import CommandEvent, CommandEventStream

def executor():
    registry = SessionRegistry()
    registry.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    return AuthenticatedCommandExecutor(registry, {"open_app": lambda p: f"opened:{p['name']}"})

def test_authenticated_command_executes():
    ex = executor()
    r = ex.execute(CommandRequest("s1", "d1", "open_app", {"name": "notepad"}), now=1100)
    assert r.accepted and r.status == "completed"

def test_expired_session_rejected():
    ex = executor()
    r = ex.execute(CommandRequest("s1", "d1", "open_app", {"name": "notepad"}), now=2000)
    assert not r.accepted and r.status == "rejected"

def test_unsupported_action_rejected():
    ex = executor()
    r = ex.execute(CommandRequest("s1", "d1", "run_shell", {"cmd": "echo x"}), now=1100)
    assert not r.accepted

def test_command_events_roundtrip():
    stream = CommandEventStream()
    stream.publish(CommandEvent("c1", "started", "open_app", "running"))
    stream.publish(CommandEvent("c1", "completed", "open_app", "completed"))
    assert [x.event for x in stream.events("c1")] == ["started", "completed"]
