from pathlib import Path

def test_desktop_runtime_script_exists():
    p = Path("desktop/app.js")
    assert p.exists()
    text = p.read_text()
    assert "/v1/runtime/tasks" in text
    assert "/v1/runtime/state" in text
    assert "/v1/agent/stop" in text

def test_desktop_html_is_wired():
    text = Path("desktop/index.html").read_text()
    assert 'id="runTask"' in text
    assert 'id="goal"' in text
    assert 'id="stopAgent"' in text
    assert 'app.js' in text

def test_stop_route_exists():
    text = Path("api/desktop_api.py").read_text()
    assert "/v1/agent/stop" in text
