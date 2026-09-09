# ZYRA AI — Mission 65
## Android Keystore Session Storage

The Android companion now has a production storage implementation for session
credentials.

### Protection model
- A non-exportable AES key is generated/kept by Android Keystore.
- Session and refresh-token fields are serialized into one encrypted blob.
- AES-GCM provides confidentiality and integrity.
- SharedPreferences stores only ciphertext and IV.
- Decryption failures clear the local credential blob rather than returning
  potentially corrupt credentials.

### Integration
Use `KeystoreSessionStorage(context)` wherever `SessionLifecycleController`
is constructed in the Android application.

`InMemorySecureSessionStorage` remains available only for tests/development.
