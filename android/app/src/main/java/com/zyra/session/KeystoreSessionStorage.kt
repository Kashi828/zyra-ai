package com.zyra.session

import android.content.Context
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Android Keystore-backed storage for the ZYRA session blob.
 *
 * The Keystore key itself is non-exportable. The encrypted payload is kept in
 * SharedPreferences; only ciphertext and nonce are stored there.
 */
class KeystoreSessionStorage(
    private val context: Context
) : SecureSessionStorage {

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = ks.getKey(KEY_ALIAS, null)
        if (existing is SecretKey) return existing

        val generator = KeyGenerator.getInstance(
            "AES",
            ANDROID_KEYSTORE
        )
        generator.init(
            android.security.keystore.KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                android.security.keystore.KeyProperties.PURPOSE_ENCRYPT or
                    android.security.keystore.KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(android.security.keystore.KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(android.security.keystore.KeyProperties.ENCRYPTION_PADDING_NONE)
                .setUserAuthenticationRequired(false)
                .build()
        )
        return generator.generateKey()
    }

    override fun save(state: PersistedSessionState) {
        val plaintext = listOf(
            state.deviceId,
            state.sessionId,
            state.refreshToken,
            state.expiresAtEpochSeconds.toString(),
            state.refreshExpiresAtEpochSeconds.toString()
        ).joinToString("\u001f").toByteArray(StandardCharsets.UTF_8)

        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val ciphertext = cipher.doFinal(plaintext)

        prefs.edit()
            .putString(KEY_CIPHERTEXT, Base64.encodeToString(ciphertext, Base64.NO_WRAP))
            .putString(KEY_IV, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .apply()
    }

    override fun load(): PersistedSessionState? {
        val encoded = prefs.getString(KEY_CIPHERTEXT, null) ?: return null
        val ivEncoded = prefs.getString(KEY_IV, null) ?: run {
            clear()
            return null
        }

        return try {
            val ciphertext = Base64.decode(encoded, Base64.NO_WRAP)
            val iv = Base64.decode(ivEncoded, Base64.NO_WRAP)
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(
                Cipher.DECRYPT_MODE,
                key(),
                GCMParameterSpec(128, iv)
            )
            val fields = String(
                cipher.doFinal(ciphertext),
                StandardCharsets.UTF_8
            ).split("\u001f")

            if (fields.size != 5) {
                clear()
                null
            } else {
                PersistedSessionState(
                    deviceId = fields[0],
                    sessionId = fields[1],
                    refreshToken = fields[2],
                    expiresAtEpochSeconds = fields[3].toLongOrNull() ?: return null,
                    refreshExpiresAtEpochSeconds = fields[4].toLongOrNull() ?: return null
                )
            }
        } catch (_: Exception) {
            clear()
            null
        }
    }

    override fun clear() {
        prefs.edit()
            .remove(KEY_CIPHERTEXT)
            .remove(KEY_IV)
            .apply()
    }

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val PREFS_NAME = "zyra_secure_session"
        private const val KEY_ALIAS = "zyra.session.aes.v1"
        private const val KEY_CIPHERTEXT = "ciphertext"
        private const val KEY_IV = "iv"
    }
}
