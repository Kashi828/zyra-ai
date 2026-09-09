package com.zyra.transport

import org.json.JSONObject

data class RealtimeEvent(
    val eventId: String?,
    val eventType: String,
    val deviceId: String?,
    val taskId: String?,
    val commandId: String?,
    val transferId: String?,
    val status: String?,
    val payload: JSONObject
) {
    companion object {
        fun fromJson(text: String): RealtimeEvent {
            val json = JSONObject(text)
            return RealtimeEvent(
                eventId = json.optString("event_id", null),
                eventType = json.getString("event_type"),
                deviceId = json.optString("device_id", null),
                taskId = json.optString("task_id", null),
                commandId = json.optString("command_id", null),
                transferId = json.optString("transfer_id", null),
                status = json.optString("status", null),
                payload = json.optJSONObject("payload") ?: JSONObject()
            )
        }
    }
}

interface RealtimeEventListener {
    fun onEvent(event: RealtimeEvent)
    fun onPresence(online: Boolean)
}
