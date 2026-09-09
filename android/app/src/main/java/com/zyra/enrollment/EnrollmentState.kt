package com.zyra.enrollment

data class EnrollmentState(
    val deviceId: String,
    val expiresAtEpochSeconds: Long,
    val capabilities: Set<String>,
    val enrolled: Boolean
)
