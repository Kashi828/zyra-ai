from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "android" / "app/src/main/java/com/zyra/WindowsConnectionProbe.kt"
STATUS = ROOT / "android" / "app/src/main/java/com/zyra/WindowsConnectionStatus.kt"


def test_connection_probe_uses_authenticated_session_status():
    text = PROBE.read_text(encoding="utf-8")
    assert '"$base/v1/session/status"' in text
    assert '.put("device_id", deviceId)' in text
    assert '.put("session_id", sessionId)' in text
    assert 'device_secret' not in text
    assert 'refresh_token' not in text


def test_connection_probe_distinguishes_auth_failure_from_transport_failure():
    text = PROBE.read_text(encoding="utf-8")
    assert 'WindowsConnectionState.OFFLINE' in text
    assert 'WindowsConnectionState.REACHABLE' in text
    assert 'response.code == 401' in text


def test_ready_state_requires_all_windows_capabilities():
    text = STATUS.read_text(encoding="utf-8")
    assert '"windows.apps"' in text
    assert '"windows.files.read"' in text
    assert '"windows.browser"' in text
    assert 'sessionActive && !deviceRevoked' in text
