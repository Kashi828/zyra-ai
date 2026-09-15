from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "desktop" / "index.html").read_text(encoding="utf-8")
WORKSPACE = (ROOT / "desktop" / "agent_workspace.js").read_text(encoding="utf-8")
STARTUP = (ROOT / "desktop" / "startup_controller.js").read_text(encoding="utf-8")


def test_builder_and_console_entry_points_exist():
    assert 'id="openBuilder"' in INDEX
    assert 'id="openConsole"' in INDEX
    assert 'data-section="builder"' in INDEX
    assert 'data-section="console"' in INDEX
    assert 'id="page-builder"' in INDEX
    assert 'id="page-console"' in INDEX


def test_workspace_calls_agent_runtime_contracts():
    assert '/v1/runtime/plan' in WORKSPACE
    assert '/v1/runtime/tasks' in WORKSPACE
    assert '/v1/runtime/state' in WORKSPACE
    assert '/v1/agent/stop' in WORKSPACE
    assert '/v1/agent/resume' in WORKSPACE


def test_startup_loader_keeps_workspace_module_connected():
    assert 'agent_workspace.js' in STARTUP
