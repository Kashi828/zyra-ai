from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "android" / "app/src/main/java/com/zyra/WindowsConnectionProbe.kt"


def test_windows_probe_uses_authenticated_session_status_only():
    text = PROBE.read_text(encoding="utf-8")
    assert '"$base/v1/session/status"' in text
    assert '.put("device_id", deviceId)' in text
    assert '.put("session_id", sessionId)' in text
    assert 'device_secret' not in text
    assert 'refresh_token' not in text


def test_windows_probe_has_reachable_authenticated_ready_states():
    text = PROBE.read_text(encoding="utf-8")
    assert 'WindowsConnectionState.REACHABLE' in text
    assert 'WindowsConnectionState.OFFLINE' in text
    assert 'WindowsConnectionStatus.fromSessionStatus(text)' in text


def test_windows_probe_retries_only_transport_failures_with_bounded_backoff():
    text = PROBE.read_text(encoding="utf-8")
    assert 'if (attempt < MAX_ATTEMPTS)' in text
    assert 'postDelayed' in text
    assert '350L' in text
    assert '700L' in text
    assert 'MAX_ATTEMPTS = 3' in text


def test_windows_probe_does_not_retry_authentication_or_http_errors():
    text = PROBE.read_text(encoding="utf-8")
    assert 'response.code == 401 || response.code == 403' in text
    assert 'Windows returned HTTP ${response.code}.' in text
