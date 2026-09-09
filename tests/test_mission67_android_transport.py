from pathlib import Path


BASE = Path("android/app/src/main/java/com/zyra")
T = BASE / "transport"


def read(name):
    return (T / name).read_text(encoding="utf-8")


def test_http_transport_implements_session_api():
    text=read("ZyraHttpTransport.kt")
    assert "SessionApi" in text
    assert '"/v1/session/create"' in text
    assert '"/v1/session/refresh"' in text
    assert '"/v1/session/logout"' in text
    assert "HttpURLConnection" in text


def test_http_transport_does_not_put_refresh_token_in_url():
    text=read("ZyraHttpTransport.kt")
    assert "?refresh_token" not in text
    assert 'put("refresh_token", refreshToken)' in text


def test_websocket_controller_refreshes_before_reconnect():
    text=read("ZyraWebSocketClient.kt")
    assert "onTransportUnauthorized(deviceId)" in text
    assert "socket.disconnect()" in text
    assert "socket.connect(session)" in text


def test_refresh_token_never_enters_websocket_contract():
    text=read("ZyraWebSocketClient.kt")
    assert "refreshToken" not in text


def test_remote_command_contract_exists():
    text=read("RemoteCommandTransport.kt")
    assert "RemoteCommandApi" in text
    assert "AuthenticatedTransportSession" in text


def test_session_manager_and_keystore_still_exist():
    assert (BASE/"session/SessionManager.kt").exists()
    assert (BASE/"session/KeystoreSessionStorage.kt").exists()
