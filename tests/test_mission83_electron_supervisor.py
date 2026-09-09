
from pathlib import Path

def test_electron_backend_restart_is_bounded_and_loopback():
    text=Path("electron/main.js").read_text()
    assert "MAX_BACKEND_RESTARTS = 2" in text
    assert '--host", "127.0.0.1"' in text
    assert "backendRestarts >= MAX_BACKEND_RESTARTS" in text
    assert "setTimeout(() => startBackend(), 500)" in text
