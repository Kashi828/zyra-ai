from pathlib import Path

ANDROID_ROOT = Path(__file__).resolve().parents[1] / "android" / "app/src/main/java/com/zyra"
STATUS = ANDROID_ROOT / "WindowsConnectionStatus.kt"
CHECKER = ANDROID_ROOT / "WindowsConnectionChecker.kt"


def test_windows_connection_status_requires_all_safe_capabilities():
    text = STATUS.read_text(encoding="utf-8")
    assert '"windows.apps"' in text
    assert '"windows.files.read"' in text
    assert '"windows.browser"' in text
    assert "state == WindowsConnectionState.READY" in text
    assert "sessionActive" in text
    assert "!deviceRevoked" in text


def test_windows_connection_status_does_not_expose_device_secret():
    text = STATUS.read_text(encoding="utf-8")
    assert "device_secret" not in text
    assert "refresh_token" not in text


def test_windows_connection_checker_builds_secret_free_status_request():
    text = CHECKER.read_text(encoding="utf-8")
    assert '.put("device_id", deviceId)' in text
    assert '.put("session_id", sessionId)' in text
    assert "device_secret" not in text
    assert "refresh_token" not in text


def test_windows_connection_checker_distinguishes_reachability_from_readiness():
    text = CHECKER.read_text(encoding="utf-8")
    assert "WindowsConnectionState.REACHABLE" in text
    assert "fromSessionStatus" in text
