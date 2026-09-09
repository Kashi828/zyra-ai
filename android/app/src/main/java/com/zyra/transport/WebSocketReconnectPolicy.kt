package com.zyra.transport

import kotlin.math.min
import kotlin.math.pow

class WebSocketReconnectPolicy(
    private val baseDelayMs: Long = 1000L,
    private val maxDelayMs: Long = 30_000L,
    private val maxAttempts: Int = 10
) {
    fun delayMs(attempt: Int): Long {
        if (attempt < 0) return baseDelayMs
        val exponential = baseDelayMs * 2.0.pow(attempt.toDouble()).toLong()
        return min(maxDelayMs, exponential)
    }

    fun shouldRetry(attempt: Int): Boolean =
        attempt < maxAttempts
}
