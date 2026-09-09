package com.zyra.transport

import com.zyra.session.CreateSessionResponse
import com.zyra.session.RefreshSessionResponse
import com.zyra.session.SessionApi
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Minimal dependency-free HTTP adapter for the session API.
 *
 * A production app may replace this implementation with OkHttp/Retrofit while
 * keeping the SessionApi contract unchanged.
 */
class ZyraHttpTransport(
    private val baseUrl: String,
    private val connectTimeoutMs: Int = 10000,
    private val readTimeoutMs: Int = 10000
) : SessionApi {

    private fun post(path: String, body: JSONObject): JSONObject {
        val connection = (URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection)
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
            throw IllegalStateException("ZYRA HTTP $status: $text")
        }
        return JSONObject(text)
    }

    override fun create(deviceId: String): CreateSessionResponse {
        val json = post("/v1/session/create", JSONObject().put("device_id", deviceId))
        return CreateSessionResponse(
            ok = json.optBoolean("ok", false),
            sessionId = json.getString("session_id"),
            refreshToken = json.getString("refresh_token"),
            expiresAt = json.getLong("expires_at")
        )
    }

    override fun refresh(deviceId: String, refreshToken: String): RefreshSessionResponse {
        val json = post(
            "/v1/session/refresh",
            JSONObject()
                .put("device_id", deviceId)
                .put("refresh_token", refreshToken)
        )
        return RefreshSessionResponse(
            ok = json.optBoolean("ok", false),
            sessionId = json.getString("session_id"),
            refreshToken = json.getString("refresh_token"),
            expiresAt = json.getLong("expires_at")
        )
    }

    override fun logout(deviceId: String, sessionId: String): Boolean {
        return try {
            val json = post(
                "/v1/session/logout",
                JSONObject()
                    .put("device_id", deviceId)
                    .put("session_id", sessionId)
            )
            json.optBoolean("ok", false)
        } catch (_: Exception) {
            false
        }
    }
}
