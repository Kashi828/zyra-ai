from pathlib import Path

def test_all_navigation_sections_exist():
    text = Path("desktop/index.html").read_text()
    for section in ["assistant", "tasks", "devices", "permissions", "settings"]:
        assert f'data-section="{section}"' in text
        assert f'id="page-{section}"' in text

def test_runtime_integration_hooks_remain():
    text = Path("desktop/app.js").read_text()
    assert "/v1/runtime/tasks" in text
    assert "/v1/runtime/state" in text
    assert "/v1/agent/stop" in text

def test_security_state_is_visible():
    text = Path("desktop/index.html").read_text()
    assert "Local-first mode" in text
    assert "Remote access" in text
    assert "Sensitive confirmations" in text
