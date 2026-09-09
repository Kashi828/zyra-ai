package com.zyra.transport

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

enum class SocketState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    CLOSING,
    FAILED
}

interface SocketStateListener {
    fun onStateChanged(state: SocketState)
    fun onMessage(text: String)
}

class OkHttpZyraWebSocketClient(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .pingInterval(20, TimeUnit.SECONDS)
        .build(),
    private val endpoint: String,
    private val listener: SocketStateListener? = null,
    private val eventListener: RealtimeEventListener? = null
) : ZyraWebSocketClient {

    @Volatile
    private var state: SocketState = SocketState.DISCONNECTED

    @Volatile
    private var socket: WebSocket? = null

    override fun connect(session: AuthenticatedTransportSession) {
        socket?.cancel()
        setState(SocketState.CONNECTING)

        val request = Request.Builder()
            .url(endpoint)
            .header("Authorization", "Bearer ${session.sessionId}")
            .header("X-ZYRA-Device-Id", session.deviceId)
            .build()

        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                socket = webSocket
                setState(SocketState.CONNECTED)
                eventListener?.onPresence(true)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                listener?.onMessage(text)
                try {
                    val event = RealtimeEvent.fromJson(text)
                    eventListener?.onEvent(event)
                } catch (_: Exception) {
                    // Non-event control messages remain available to the raw listener.
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                setState(SocketState.CLOSING)
                webSocket.close(code, reason)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                socket = null
                eventListener?.onPresence(false)
                setState(SocketState.DISCONNECTED)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                socket = null
                eventListener?.onPresence(false)
                setState(SocketState.FAILED)
            }
        })
    }

    override fun disconnect() {
        setState(SocketState.CLOSING)
        socket?.close(1000, "client disconnect")
        socket = null
        setState(SocketState.DISCONNECTED)
    }

    override fun sendText(message: String): Boolean {
        val current = socket ?: return false
        if (state != SocketState.CONNECTED) return false
        return current.send(message)
    }

    fun currentState(): SocketState = state

    private fun setState(next: SocketState) {
        state = next
        listener?.onStateChanged(next)
    }
}
