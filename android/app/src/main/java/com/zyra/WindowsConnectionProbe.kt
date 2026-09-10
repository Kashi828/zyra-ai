package com.zyra

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

        val request = try {
            Request.Builder()
                .url("$base/v1/session/status")
                .post(body.toString().toRequestBody(jsonType))
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
                    } else if (response.code == 401) {
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
}
