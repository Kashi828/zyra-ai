package com.zyra.transfer

class TransferController {
    private val transfers = linkedMapOf<String, TransferState>()

    fun begin(id: String, filename: String, totalBytes: Long): TransferState {
        val state = TransferState(id, filename, totalBytes, 0L, TransferStatus.QUEUED)
        transfers[id] = state
        return state
    }

    fun updateProgress(id: String, transferred: Long): TransferState {
        val current = transfers.getValue(id)
        val bounded = transferred.coerceIn(0L, current.totalBytes)
        return current.copy(
            transferredBytes = bounded,
            status = if (bounded >= current.totalBytes) TransferStatus.RUNNING else TransferStatus.RUNNING
        ).also { transfers[id] = it }
    }

    fun complete(id: String): TransferState =
        transfers.getValue(id).copy(
            transferredBytes = transfers.getValue(id).totalBytes,
            status = TransferStatus.COMPLETED
        ).also { transfers[id] = it }

    fun fail(id: String, message: String): TransferState =
        transfers.getValue(id).copy(status = TransferStatus.FAILED, errorMessage = message)
            .also { transfers[id] = it }

    fun cancel(id: String): TransferState =
        transfers.getValue(id).copy(status = TransferStatus.CANCELLED).also { transfers[id] = it }

    fun get(id: String): TransferState? = transfers[id]
}
