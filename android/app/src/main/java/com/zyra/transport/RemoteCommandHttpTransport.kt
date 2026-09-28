package com.zyra.transport

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/**
 * HTTP adapter for POST /v1/remote/commands.
 *
 * Every call carries the active device/session pair; the backend re-validates
 * both plus the device's capability grant, so this class never decides what a
 * device may do.
 */
class RemoteCommandHttpTransport(
    private val baseUrl: String,
    private val connectTimeoutMs: Int = 8000,
    private val readTimeoutMs: Int = 15000
) : RemoteCommandApi {

    override fun execute(
        session: AuthenticatedTransportSession,
        action: String,
        payload: JSONObject
    ): RemoteCommandResponse {
        val body = JSONObject()
            .put("device_id", session.deviceId)
            .put("session_id", session.sessionId)
            .put("client_key", session.deviceId)
            .put("command_id", "and_" + UUID.randomUUID().toString().take(12))
            .put("action", action)
            .put("payload", payload)

        val connection = URL(baseUrl.trimEnd('/') + "/v1/remote/commands").openConnection() as HttpURLConnection
        return try {
            connection.requestMethod = "POST"
            connection.connectTimeout = connectTimeoutMs
            connection.readTimeout = readTimeoutMs
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }

            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val detail = runCatching { JSONObject(text).optString("detail") }.getOrDefault("")
                RemoteCommandResponse(false, action, "http_$status", detail.ifBlank { "Request rejected" })
            } else {
                val json = JSONObject(text)
                RemoteCommandResponse(
                    accepted = json.optBoolean("accepted", false),
                    action = json.optString("action", action),
                    status = json.optString("status", ""),
                    message = json.optString("message", "")
                )
            }
        } catch (e: Exception) {
            RemoteCommandResponse(false, action, "network_error", e.message ?: "PC unreachable")
        } finally {
            connection.disconnect()
        }
    }
}
