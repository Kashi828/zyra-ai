
import json
from pathlib import Path


def test_electron_shell_manifest():
    pkg=json.loads(Path("package.json").read_text())
    assert pkg["main"]=="electron/main.js"
    assert "electron" in pkg["devDependencies"]
    assert "electron-builder" in pkg["devDependencies"]
    assert pkg["build"]["win"]["target"][0]["target"]=="nsis"


def test_electron_security_isolation():
    text=Path("electron/main.js").read_text()
    assert "contextIsolation: true" in text
    assert "nodeIntegration: false" in text
    assert "sandbox: true" in text
    assert 'permission === "media"' in text


def test_preload_exposes_narrow_bridge():
    text=Path("electron/preload.js").read_text()
    assert "contextBridge.exposeInMainWorld" in text
    assert "ensureVoiceSession" in text
    assert "getVoiceAuthHeaders" in text
    assert "logoutVoiceSession" in text
    assert "require(\"electron\")" in text


def test_renderer_prefers_native_bridge_and_no_refresh_token():
    text=Path("desktop/app.js").read_text()
    assert "window.zyraDesktopBridge" in text
    assert "zyra_voice_refresh_token" not in text
