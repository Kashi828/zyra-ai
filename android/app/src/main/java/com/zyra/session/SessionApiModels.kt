package com.zyra.session

/**
 * `expiresAt` is the refresh-token expiry; `sessionExpiresAt` is the (much
 * shorter) access-session expiry returned by the backend as session_expires_at.
 */
data class CreateSessionResponse(
    val ok: Boolean,
    val sessionId: String,
    val refreshToken: String,
    val expiresAt: Long,
    val sessionExpiresAt: Long = expiresAt
)

data class RefreshSessionResponse(
    val ok: Boolean,
    val sessionId: String,
    val refreshToken: String,
    val expiresAt: Long,
    val sessionExpiresAt: Long = expiresAt
)
