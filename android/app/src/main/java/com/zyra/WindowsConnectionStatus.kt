package com.zyra

import org.json.JSONObject

enum class WindowsConnectionState {
    OFFLINE,
    REACHABLE,
    AUTHENTICATED,
    READY,
    ERROR
}

data class WindowsConnectionStatus(
    val state: WindowsConnectionState,
    val deviceId: String? = null,
    val sessionId: String? = null,
    val capabilities: Set<String> = emptySet(),
    val sessionActive: Boolean = false,
    val deviceRevoked: Boolean = false,
    val detail: String = ""
) {
    val requiredCapabilitiesPresent: Boolean
        get() = REQUIRED_CAPABILITIES.all(capabilities::contains)

    val ready: Boolean
        get() = state == WindowsConnectionState.READY && sessionActive && !deviceRevoked && requiredCapabilitiesPresent

    companion object {
        val REQUIRED_CAPABILITIES = setOf(
            "windows.apps",
            "windows.files.read",
            "windows.browser"
        )

        fun fromSessionStatus(body: String): WindowsConnectionStatus {
            return try {
                val json = JSONObject(body)
                if (!json.optBoolean("authenticated", false)) {
                    WindowsConnectionStatus(
                        state = WindowsConnectionState.ERROR,
                        detail = "Windows session is not authenticated."
                    )
                } else {
                    val device = json.optJSONObject("device") ?: JSONObject()
                    val session = json.optJSONObject("session") ?: JSONObject()
                    val capabilitiesJson = device.optJSONArray("capabilities")
                    val capabilities = buildSet {
                        if (capabilitiesJson != null) {
                            for (index in 0 until capabilitiesJson.length()) {
                                val value = capabilitiesJson.optString(index).trim()
                                if (value.isNotEmpty()) add(value)
                            }
                        }
                    }
                    val sessionActive = session.optBoolean("active", false)
                    val deviceRevoked = device.optBoolean("revoked", false)
                    val ready = sessionActive && !deviceRevoked && REQUIRED_CAPABILITIES.all(capabilities::contains)
                    WindowsConnectionStatus(
                        state = if (ready) WindowsConnectionState.READY else WindowsConnectionState.AUTHENTICATED,
                        deviceId = device.optString("device_id").ifBlank { null },
                        sessionId = session.optString("session_id").ifBlank { null },
                        capabilities = capabilities,
                        sessionActive = sessionActive,
                        deviceRevoked = deviceRevoked,
                        detail = if (ready) "Windows agent authenticated and ready." else "Windows session authenticated but not ready."
                    )
                }
            } catch (_: Exception) {
                WindowsConnectionStatus(
                    state = WindowsConnectionState.ERROR,
                    detail = "Windows returned an invalid session status response."
                )
            }
        }
    }
}
