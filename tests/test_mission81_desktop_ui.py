
from pathlib import Path

def test_browser_does_not_persist_refresh_token():
    text=Path("desktop/app.js").read_text()
    assert "zyra_voice_refresh_token" not in text
    assert "zyraDesktopBridge" in text


def test_native_bridge_entrypoint_exists():
    assert Path("desktop/native_bridge.py").exists()
