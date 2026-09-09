package com.zyra.session

data class ZyraSession(
    val sessionId: String,
    val deviceId: String,
    val issuedAtEpochSeconds: Long,
    val expiresAtEpochSeconds: Long,
    val authenticated: Boolean
) {
    fun isExpired(nowEpochSeconds: Long): Boolean =
        nowEpochSeconds >= expiresAtEpochSeconds
}

sealed interface SessionStatus {
    data object SignedOut : SessionStatus
    data object Authenticating : SessionStatus
    data class Active(val session: ZyraSession) : SessionStatus
    data class Expired(val session: ZyraSession) : SessionStatus
    data class Error(val message: String) : SessionStatus
}
