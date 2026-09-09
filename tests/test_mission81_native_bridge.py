import io
import json
from desktop.native_bridge import NativeBridgeServer


def test_native_bridge_ping():
    result = NativeBridgeServer().dispatch({"method":"ping"})
    assert result == {"ok":True,"service":"zyra-desktop-bridge"}


def test_native_bridge_ensure_hides_refresh_token():
    class Runtime:
        def ensure_session(self):
            return {
                "device_id":"d1","session_id":"s1",
                "refresh_token":"secret","expires_at":123
            }
    result=NativeBridgeServer(Runtime()).dispatch({"method":"voice.session.ensure"})
    assert result["device_id"]=="d1"
    assert result["session_id"]=="s1"
    assert "refresh_token" not in result


def test_native_bridge_returns_auth_headers():
    class Runtime:
        def auth_headers(self):
            return {"Authorization":"Bearer s1","X-ZYRA-Device-Id":"d1"}
    result=NativeBridgeServer(Runtime()).dispatch({"method":"voice.auth.headers"})
    assert result["headers"]["Authorization"] == "Bearer s1"


def test_native_bridge_unknown_method():
    result=NativeBridgeServer().dispatch({"method":"nope"})
    assert result["ok"] is False
