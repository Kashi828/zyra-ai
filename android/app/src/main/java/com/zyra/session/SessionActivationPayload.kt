package com.zyra.session

data class SessionActivationPayload(
    val deviceId: String,
    val nonce: String,
    val timestamp: Long,
    val proof: String
)
