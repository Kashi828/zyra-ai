package com.zyra.enrollment

import android.content.Context
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Long-lived pairing credentials for one PC. Distinct from the short-lived session blob. */
data class DeviceCredentials(
    val pcBaseUrl: String,
    val deviceId: String,
    val deviceSecret: String,
    val capabilities: Set<String>
)

/**
 * Android Keystore-backed storage for pairing credentials. The AES key is
 * non-exportable; only ciphertext + IV land in SharedPreferences.
 */
class DeviceCredentialStorage(private val context: Context) {
    private val prefs by lazy { context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE) }

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (ks.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        val generator = KeyGenerator.getInstance("AES", ANDROID_KEYSTORE)
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

    fun save(credentials: DeviceCredentials) {
        val plaintext = listOf(
            credentials.pcBaseUrl,
            credentials.deviceId,
            credentials.deviceSecret,
            credentials.capabilities.sorted().joinToString(",")
        ).joinToString("\u001f").toByteArray(StandardCharsets.UTF_8)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val ciphertext = cipher.doFinal(plaintext)
        prefs.edit()
            .putString(KEY_CIPHERTEXT, Base64.encodeToString(ciphertext, Base64.NO_WRAP))
            .putString(KEY_IV, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .apply()
    }

    fun load(): DeviceCredentials? {
        val encoded = prefs.getString(KEY_CIPHERTEXT, null) ?: return null
        val iv = prefs.getString(KEY_IV, null) ?: run { clear(); return null }
        return try {
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(
                Cipher.DECRYPT_MODE,
                key(),
                GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP))
            )
            val fields = String(
                cipher.doFinal(Base64.decode(encoded, Base64.NO_WRAP)),
                StandardCharsets.UTF_8
            ).split("\u001f")
            if (fields.size != 4) {
                clear(); null
            } else {
                DeviceCredentials(
                    pcBaseUrl = fields[0],
                    deviceId = fields[1],
                    deviceSecret = fields[2],
                    capabilities = fields[3].split(",").filter { it.isNotBlank() }.toSet()
                )
            }
        } catch (_: Exception) {
            clear(); null
        }
    }

    fun clear() {
        prefs.edit().remove(KEY_CIPHERTEXT).remove(KEY_IV).apply()
    }

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val PREFS_NAME = "zyra_device_credentials"
        private const val KEY_ALIAS = "zyra.device.credentials.aes.v1"
        private const val KEY_CIPHERTEXT = "ciphertext"
        private const val KEY_IV = "iv"
    }
}
