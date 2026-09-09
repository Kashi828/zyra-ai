from pathlib import Path

BASE=Path("android/app/src/main/java/com/zyra/transport")


def read(name):
    return (BASE/name).read_text(encoding="utf-8")


def test_okhttp_client_uses_websocket_and_authenticated_headers():
    t=read("OkHttpZyraWebSocketClient.kt")
    assert "OkHttpClient" in t
    assert "newWebSocket" in t
    assert 'Authorization' in t
    assert 'Bearer ${session.sessionId}' in t
    assert "X-ZYRA-Device-Id" in t


def test_okhttp_client_has_heartbeat():
    t=read("OkHttpZyraWebSocketClient.kt")
    assert "pingInterval" in t
    assert "20, TimeUnit.SECONDS" in t


def test_socket_state_machine_exists():
    t=read("OkHttpZyraWebSocketClient.kt")
    for state in ["DISCONNECTED","CONNECTING","CONNECTED","CLOSING","FAILED"]:
        assert state in t
    assert "onFailure" in t
    assert "onClosed" in t


def test_reconnect_policy_is_bounded_exponential():
    t=read("WebSocketReconnectPolicy.kt")
    assert "pow" in t
    assert "maxDelayMs" in t
    assert "maxAttempts" in t
    assert "shouldRetry" in t


def test_session_aware_socket_exposes_retry_policy():
    t=read("SessionAwareWebSocket.kt")
    assert "reconnectAllowed" in t
    assert "reconnectDelayMs" in t
    assert "sessionManager.ensureActive" in t


def test_presence_maps_socket_state():
    t=read("PresenceHeartbeat.kt")
    assert "PresenceSink" in t
    assert "onPresence(true)" in t
    assert "onPresence(false)" in t
