from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_desktop_auth_recovery_keeps_existing_device_usable():
    text = (ROOT / "electron" / "main.js").read_text(encoding="utf-8")
    assert '"/v1/session/refresh"' in text
    assert '"/v1/local/bootstrap"' in text
    assert "saveAuthState(state)" in text
    assert "safeStorage.encryptString" in text


def test_desktop_pairing_shows_offer_id_and_code():
    text = (ROOT / "desktop" / "index.html").read_text(encoding="utf-8")
    assert "data.offer_id" in text
    assert "data.pairing_code" in text
    assert "/v1/devices/pairing/offer" in text


def test_desktop_task_submission_sends_authenticated_context():
    text = (ROOT / "desktop" / "index.html").read_text(encoding="utf-8")
    assert "/v1/runtime/tasks" in text
    assert "body.device_id = body.device_id || auth.device_id" in text
    assert "body.session_id = body.session_id || auth.session_id" in text
    assert "getAuthContext" in text


def test_android_run_and_pairing_paths_are_present():
    text = (ROOT / "android" / "app/src/main/java/com/zyra/MainActivity.kt").read_text(encoding="utf-8")
    assert 'setOnClickListener { executeTask() }' in text
    assert 'runtime/tasks' in text
    assert 'v1/session/refresh' in text
    assert 'v1/session/create' in text
    assert 'v1/devices/pairing/enroll' in text
    assert '"device_secret"' in text
    assert '"offer_id"' in text
    assert '"pairing_code"' in text


def test_android_pc_task_carries_authenticated_compatibility_fields():
    text = (ROOT / "android" / "MainActivity.kt").read_text(encoding="utf-8") if (ROOT / "android" / "MainActivity.kt").exists() else (ROOT / "android" / "app/src/main/java/com/zyra/MainActivity.kt").read_text(encoding="utf-8")
    assert '.put("auth_key", sessionId)' in text
    assert '.put("client_key", sessionId)' in text
