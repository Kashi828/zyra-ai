package com.zyra.session

data class DeviceSession(
    val deviceId: String,
    val sessionId: String?,
    val expiresAtEpochSeconds: Long,
    val active: Boolean
)
