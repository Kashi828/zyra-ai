package com.zyra.transport

interface PresenceSink {
    fun onPresence(online: Boolean)
}

class PresenceHeartbeat(
    private val sink: PresenceSink
) : SocketStateListener {
    override fun onStateChanged(state: SocketState) {
        when (state) {
            SocketState.CONNECTED -> sink.onPresence(true)
            SocketState.DISCONNECTED, SocketState.FAILED -> sink.onPresence(false)
            SocketState.CONNECTING, SocketState.CLOSING -> Unit
        }
    }

    override fun onMessage(text: String) {
        // Server heartbeat/agent events are surfaced to the owning UI layer.
    }
}
