from pathlib import Path


BASE = Path("android/app/src/main/java/com/zyra/session")


def test_keystore_storage_exists():
    p = BASE / "KeystoreSessionStorage.kt"
    assert p.exists()


def test_keystore_uses_android_keystore_and_aes_gcm():
    text = (BASE / "KeystoreSessionStorage.kt").read_text(encoding="utf-8")
    assert 'AndroidKeyStore' in text
    assert 'AES/GCM/NoPadding' in text
    assert 'KeyGenerator.getInstance' in text


def test_keystore_does_not_store_raw_session_fields_in_preferences():
    text = (BASE / "KeystoreSessionStorage.kt").read_text(encoding="utf-8")
    assert 'putString(KEY_CIPHERTEXT' in text
    assert 'putString("refreshToken"' not in text
    assert 'putString("sessionId"' not in text


def test_storage_clears_corrupt_or_incomplete_ciphertext():
    text = (BASE / "KeystoreSessionStorage.kt").read_text(encoding="utf-8")
    assert 'clear()' in text
    assert 'doFinal(ciphertext)' in text


def test_production_storage_is_documented():
    text = Path("docs/MISSION_65.md").read_text(encoding="utf-8")
    assert "KeystoreSessionStorage" in text
    assert "InMemorySecureSessionStorage" in text
