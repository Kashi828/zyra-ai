from pathlib import Path


def test_electron_backend_restart_is_bounded_and_packaged_backend_can_use_lan():
    text = Path("electron/main.js").read_text()
    assert "MAX_BACKEND_RESTARTS = 2" in text
    assert 'process.env.ZYRA_BIND_HOST || (app.isPackaged ? "0.0.0.0" : "127.0.0.1")' in text
    assert "backendRestarts >= MAX_BACKEND_RESTARTS" in text
    assert "setTimeout(() => startBackend(), 500)" in text
