from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android" / "app/src/main/java/com/zyra/MainActivity.kt"


def test_android_connection_check_keeps_health_probe_local_and_authenticated_path_available():
    text = ANDROID.read_text(encoding="utf-8")
    assert '"$base/health"' in text
    assert '"$base/v1/session/refresh"' in text
    assert '"$base/v1/session/create"' in text
    assert '"$base/v1/runtime/tasks"' in text


def test_android_connection_diagnostics_never_send_device_secret_to_status_endpoint():
    text = ANDROID.read_text(encoding="utf-8")
    status_index = text.find("/v1/session/status")
    if status_index == -1:
        return
    window = text[max(0, status_index - 900): status_index + 900]
    assert 'device_secret' not in window
    assert 'refresh_token' not in window


def test_android_connection_state_has_distinct_failure_messages():
    text = ANDROID.read_text(encoding="utf-8")
    assert 'pcState.text = "OFFLINE"' in text
    assert 'pcState.text = "ERROR"' in text
    assert 'pcState.text = "PAIRED"' in text
