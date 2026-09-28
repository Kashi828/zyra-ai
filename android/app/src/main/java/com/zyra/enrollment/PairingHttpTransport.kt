package com.zyra.enrollment

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class EnrollmentResult(
    val deviceId: String,
    /** 64-char hex secret, returned exactly once by the PC. Store in Keystore only. */
    val deviceSecret: String,
    val expiresAt: Long,
    val capabilities: Set<String>
)

/**
 * Exchanges a one-time pairing offer + 6-digit code for device credentials.
 *
 * The app requests capabilities using its own user-facing names
 * (windows.apps, ...) and this class maps them to the PC agent's grant names.
 */
class PairingHttpTransport(
    private val baseUrl: String,
    private val connectTimeoutMs: Int = 8000,
    private val readTimeoutMs: Int = 10000,
    private val enrollPath: String = "/v1/devices/pairing/enroll"
) {
    fun enroll(offerId: String, pairingCode: String, requested: Collection<String>): EnrollmentResult {
        val caps = JSONArray()
        requested.mapNotNull { CAPABILITY_MAP[it] }.distinct().forEach { caps.put(it) }
        val body = JSONObject()
            .put("offer_id", offerId)
            .put("pairing_code", pairingCode)
            .put("capabilities", caps)

        val connection = URL(baseUrl.trimEnd('/') + enrollPath).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = connectTimeoutMs
            connection.readTimeout = readTimeoutMs
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }

            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val detail = runCatching { JSONObject(text).optString("detail") }.getOrDefault("")
                throw IllegalStateException(detail.ifBlank { "Pairing failed ($status)" })
            }
            val json = JSONObject(text)
            val granted = json.optJSONArray("capabilities") ?: JSONArray()
            return EnrollmentResult(
                deviceId = json.getString("device_id"),
                deviceSecret = json.getString("device_secret"),
                expiresAt = json.optLong("expires_at"),
                capabilities = (0 until granted.length()).map { granted.getString(it) }.toSet()
            )
        } finally {
            connection.disconnect()
        }
    }

    companion object {
        val CAPABILITY_MAP = mapOf(
            "windows.apps" to "pc.apps",
            "windows.files.read" to "pc.files",
            "windows.browser" to "pc.web"
        )
    }
}
