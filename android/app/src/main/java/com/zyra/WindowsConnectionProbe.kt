package com.zyra

import android.os.Handler
import android.os.Looper
import okhttp3.Call
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaType
import org.json.JSONObject
import java.io.IOException

class WindowsConnectionProbe(
    private val http: OkHttpClient,
    private val onStatus: (WindowsConnectionStatus) -> Unit
) {
    private val jsonType = "application/json; charset=utf-8".toMediaType()
    private val handler = Handler(Looper.getMainLooper())

    fun check(baseUrl: String, deviceId: String?, sessionId: String?) {
        val base = baseUrl.trim().trimEnd('/')
        if (deviceId.isNullOrBlank() || sessionId.isNullOrBlank()) {
            onStatus(WindowsConnectionStatus(
                state = WindowsConnectionState.REACHABLE,
                detail = "Windows is reachable, but no authenticated session is available."
            ))
            return
        }

        val body = JSONObject()
            .put("device_id", deviceId)
            .put("session_id", sessionId)

        checkAttempt(base, body.toString(), attempt = 1)
    }

    private fun checkAttempt(base: String, body: String, attempt: Int) {
        val request = try {
            Request.Builder()
                .url("$base/v1/session/status")
                .post(body.toRequestBody(jsonType))
                .build()
        } catch (_: Exception) {
            onStatus(WindowsConnectionStatus(
                state = WindowsConnectionState.ERROR,
                detail = "Windows connection URL is invalid."
            ))
            return
        }

        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) {
                if (attempt < MAX_ATTEMPTS) {
                    handler.postDelayed({ checkAttempt(base, body, attempt + 1) }, backoffMillis(attempt))
                    return
                }
                onStatus(WindowsConnectionStatus(
                    state = WindowsConnectionState.OFFLINE,
                    detail = "Windows agent is unavailable: ${e.message ?: "connection failed"}"
                ))
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val text = response.body?.string().orEmpty()
                    if (response.isSuccessful) {
                        onStatus(WindowsConnectionStatus.fromSessionStatus(text))
                    } else if (response.code == 401 || response.code == 403) {
                        onStatus(WindowsConnectionStatus(
                            state = WindowsConnectionState.REACHABLE,
                            detail = "Windows is reachable, but the session is not authenticated."
                        ))
                    } else {
                        onStatus(WindowsConnectionStatus(
                            state = WindowsConnectionState.ERROR,
                            detail = "Windows returned HTTP ${response.code}."
                        ))
                    }
                }
            }
        })
    }

    private fun backoffMillis(attempt: Int): Long = when (attempt) {
        1 -> 350L
        2 -> 700L
        else -> 1000L
    }

    companion object {
        private const val MAX_ATTEMPTS = 3
    }
}
