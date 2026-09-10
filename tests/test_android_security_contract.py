from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android" / "app/src/main/java/com/zyra/MainActivity.kt"


def test_android_windows_endpoint_is_private_lan_only():
    text = ANDROID.read_text(encoding="utf-8")
    assert 'uri.scheme == "http" || uri.scheme == "https"' in text
    assert 'host == "localhost"' in text
    assert 'host == "127.0.0.1"' in text
    assert 'host.endsWith(".local")' in text
    assert 'Regex("^10\\\\..*")' in text
    assert 'Regex("^192\\\\.168\\\\..*")' in text
    assert 'Regex("^172\\\\.(1[6-9]|2[0-9]|3[0-1])\\\\..*")' in text


def test_android_windows_requests_keep_authenticated_session_fields():
    text = ANDROID.read_text(encoding="utf-8")
    assert '.put("device_id", deviceId)' in text
    assert '.put("session_id", sessionId)' in text
    assert '.put("auth_key", sessionId)' in text
    assert '.put("client_key", sessionId)' in text


def test_android_pairing_keeps_capabilities_allowlisted():
    text = ANDROID.read_text(encoding="utf-8")
    assert 'put("windows.apps")' in text
    assert 'put("windows.files.read")' in text
    assert 'put("windows.browser")' in text
    assert 'v1/devices/pairing/enroll' in text
