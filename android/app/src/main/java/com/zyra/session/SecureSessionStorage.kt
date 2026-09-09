package com.zyra.session

/**
 * Storage contract for device-bound session credentials.
 * Production implementation: use KeystoreSessionStorage, backed by Android Keystore.
 */
interface SecureSessionStorage {
    fun save(state: PersistedSessionState)
    fun load(): PersistedSessionState?
    fun clear()
}

data class PersistedSessionState(
    val deviceId: String,
    val sessionId: String,
    val refreshToken: String,
    val expiresAtEpochSeconds: Long,
    val refreshExpiresAtEpochSeconds: Long
)
