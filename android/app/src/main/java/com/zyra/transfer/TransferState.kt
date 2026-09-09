package com.zyra.transfer

enum class TransferStatus { QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED }

data class TransferState(
    val transferId: String,
    val filename: String,
    val totalBytes: Long,
    val transferredBytes: Long,
    val status: TransferStatus,
    val errorMessage: String? = null
) {
    val progress: Float
        get() = if (totalBytes <= 0L) 0f
                else (transferredBytes.toDouble() / totalBytes).coerceIn(0.0, 1.0).toFloat()
}
