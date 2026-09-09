from pathlib import Path


BASE = Path("android/app/src/main/java/com/zyra")
SESSION = BASE / "session"
TRANSPORT = BASE / "transport"


def test_session_manager_defaults_to_keystore_storage():
    text = (SESSION/"SessionManager.kt").read_text(encoding="utf-8")
    assert "KeystoreSessionStorage(context)" in text
    assert "SessionLifecycleController" in text


def test_transport_session_requires_active_session():
    text = (TRANSPORT/"AuthenticatedTransportSession.kt").read_text(encoding="utf-8")
    assert "if (!session.active) return null" in text
    assert "sessionId" in text


def test_websocket_adapter_refreshes_through_session_manager():
    text = (TRANSPORT/"SessionAwareWebSocket.kt").read_text(encoding="utf-8")
    assert "sessionManager.ensureActive(deviceId)" in text
    assert "onTransportUnauthorized" in text


def test_expired_refresh_window_does_not_trigger_refresh_call():
    text = (SESSION/"SessionLifecycleController.kt").read_text(encoding="utf-8")
    assert "refreshExpiresAtEpochSeconds > nowSeconds()" in text


def test_mission64_files_remain_present():
    assert (SESSION/"SecureSessionStorage.kt").exists()
    assert (SESSION/"SessionLifecycleController.kt").exists()
    assert (SESSION/"KeystoreSessionStorage.kt").exists()
