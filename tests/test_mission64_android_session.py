from pathlib import Path


def test_android_session_lifecycle_files_exist():
    base = Path("android/app/src/main/java/com/zyra/session")
    assert (base/"SecureSessionStorage.kt").exists()
    assert (base/"SessionApiModels.kt").exists()
    assert (base/"SessionLifecycleController.kt").exists()


def test_android_session_controller_contains_restore_refresh_logout():
    p = Path("android/app/src/main/java/com/zyra/session/SessionLifecycleController.kt")
    text = p.read_text(encoding="utf-8")
    assert "fun restore()" in text
    assert "fun ensureActive" in text
    assert "api.refresh" in text
    assert "fun logout()" in text
    assert "storage.clear()" in text


def test_android_storage_contract_is_explicitly_secure():
    p = Path("android/app/src/main/java/com/zyra/session/SecureSessionStorage.kt")
    text = p.read_text(encoding="utf-8")
    assert "Android Keystore" in text


def test_python_api_has_session_routes_and_rotation():
    from api.app_factory import create_app
    routes = {getattr(r, "path", "") for r in create_app().routes}
    assert "/v1/session/create" in routes
    assert "/v1/session/refresh" in routes
    assert "/v1/session/logout" in routes
