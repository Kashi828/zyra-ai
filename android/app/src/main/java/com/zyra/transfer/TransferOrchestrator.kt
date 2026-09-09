package com.zyra.transfer

sealed interface TransferUiEvent {
    data class Progress(val transferred: Long, val total: Long) : TransferUiEvent
    data class Completed(val transferId: String) : TransferUiEvent
    data class Failed(val transferId: String, val message: String) : TransferUiEvent
    data class Cancelled(val transferId: String) : TransferUiEvent
}

class TransferOrchestrator(
    private val emit: (TransferUiEvent) -> Unit
) {
    private val active = mutableSetOf<String>()

    fun start(transferId: String) {
        active.add(transferId)
    }

    fun progress(transferId: String, transferred: Long, total: Long) {
        if (transferId in active) emit(TransferUiEvent.Progress(transferred, total))
    }

    fun complete(transferId: String) {
        if (active.remove(transferId)) emit(TransferUiEvent.Completed(transferId))
    }

    fun fail(transferId: String, message: String) {
        if (active.remove(transferId)) emit(TransferUiEvent.Failed(transferId, message))
    }

    fun cancel(transferId: String) {
        if (active.remove(transferId)) emit(TransferUiEvent.Cancelled(transferId))
    }
}
