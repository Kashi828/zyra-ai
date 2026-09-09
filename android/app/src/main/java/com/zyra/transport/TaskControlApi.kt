package com.zyra.transport

import org.json.JSONObject

interface TaskControlApi {
    fun approve(taskId: String, session: AuthenticatedTransportSession): Boolean
    fun cancel(taskId: String, session: AuthenticatedTransportSession): Boolean
}

data class TaskProgress(
    val taskId: String,
    val status: String,
    val phase: String?,
    val detail: String?
)

fun taskControlBody(taskId: String, session: AuthenticatedTransportSession): JSONObject =
    JSONObject()
        .put("task_id", taskId)
        .put("device_id", session.deviceId)
        .put("session_id", session.sessionId)
