package com.zyra.transport

import org.json.JSONObject

data class RemoteCommandResponse(
    val accepted: Boolean,
    val action: String,
    val status: String,
    val message: String
)

interface RemoteCommandApi {
    fun execute(session: AuthenticatedTransportSession, action: String, payload: JSONObject): RemoteCommandResponse
}
