package com.zyra.transfer

sealed interface TransferNotification {
    data class Progress(val transferId: String, val percent: Int) : TransferNotification
    data class Completed(val transferId: String, val filename: String) : TransferNotification
    data class Failed(val transferId: String, val reason: String) : TransferNotification
    data class Cancelled(val transferId: String) : TransferNotification
}

fun mapTransferEvent(
    transferId: String,
    filename: String,
    transferred: Long,
    total: Long,
    status: String,
    reason: String? = null
): TransferNotification? = when (status.lowercase()) {
    "running" -> {
        val percent = if (total <= 0L) 0 else ((transferred * 100L) / total).coerceIn(0L, 100L).toInt()
        TransferNotification.Progress(transferId, percent)
    }
    "completed" -> TransferNotification.Completed(transferId, filename)
    "failed" -> TransferNotification.Failed(transferId, reason ?: "Transfer failed")
    "cancelled" -> TransferNotification.Cancelled(transferId)
    else -> null
}
