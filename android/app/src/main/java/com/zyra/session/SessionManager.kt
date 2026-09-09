package com.zyra.session

import android.content.Context

/**
 * Application-facing session coordinator.
 * The default constructor uses the Android Keystore-backed storage.
 */
class SessionManager(
    context: Context,
    private val api: SessionApi,
    private val nowSeconds: () -> Long = { System.currentTimeMillis() / 1000L }
) {
    private val storage: SecureSessionStorage = KeystoreSessionStorage(context)
    private val lifecycle = SessionLifecycleController(api, storage, nowSeconds)

    fun restore(): DeviceSession? = lifecycle.restore()

    fun ensureActive(deviceId: String): DeviceSession =
        lifecycle.ensureActive(deviceId)

    fun logout(): Boolean = lifecycle.logout()

    fun clearLocalSession() = storage.clear()
}
