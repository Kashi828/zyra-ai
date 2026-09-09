package com.zyra.session

data class CreateSessionResponse(
    val ok: Boolean,
    val sessionId: String,
    val refreshToken: String,
    val expiresAt: Long
)

data class RefreshSessionResponse(
    val ok: Boolean,
    val sessionId: String,
    val refreshToken: String,
    val expiresAt: Long
)
