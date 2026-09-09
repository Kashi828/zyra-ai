from pathlib import Path

import pytest

from desktop.runtime_bridge import DesktopRuntimeError, DesktopSessionStore, WindowsDesktopVoiceRuntime


def test_session_store_round_trip(tmp_path):
    store = DesktopSessionStore(tmp_path / "state.json")
    value = {"device_id":"d1","session_id":"s1","refresh_token":"r1","expires_at":9999999999}
    store.save(value)
    assert store.load() == value


def test_session_store_clear(tmp_path):
    store=DesktopSessionStore(tmp_path/"state.json")
    store.save({"x":1})
    store.clear()
    assert store.load() is None


def test_runtime_reuses_valid_session_without_api_call(tmp_path):
    class Client:
        def post(self,*a,**kw):
            raise AssertionError("API must not be called")
    store=DesktopSessionStore(tmp_path/"state.json")
    state={"device_id":"d1","session_id":"s1","refresh_token":"r1","expires_at":9999999999}
    store.save(state)
    assert WindowsDesktopVoiceRuntime(Client(),store).ensure_session()==state


def test_runtime_refreshes_near_expiry(tmp_path):
    calls=[]
    class Client:
        def post(self,path,body=None,headers=None):
            calls.append((path,body))
            return {"session_id":"s2","refresh_token":"r2","expires_at":9999999999}
    store=DesktopSessionStore(tmp_path/"state.json")
    store.save({"device_id":"d1","session_id":"s1","refresh_token":"r1","expires_at":0})
    runtime=WindowsDesktopVoiceRuntime(Client(),store)
    state=runtime.ensure_session()
    assert state["session_id"]=="s2"
    assert calls[0][0]=="/v1/session/refresh"


def test_runtime_bootstraps_when_no_state(tmp_path):
    class Client:
        def post(self,path,body=None,headers=None):
            assert path=="/v1/voice/desktop/bootstrap"
            return {"device_id":"d1","session_id":"s1","refresh_token":"r1","expires_at":9999999999}
    store=DesktopSessionStore(tmp_path/"state.json")
    state=WindowsDesktopVoiceRuntime(Client(),store).ensure_session()
    assert state["device_id"]=="d1"
    assert store.load()["refresh_token"]=="r1"


def test_runtime_logout_clears_state(tmp_path):
    calls=[]
    class Client:
        def post(self,path,body=None,headers=None):
            calls.append((path,body))
            return {"ok":True}
    store=DesktopSessionStore(tmp_path/"state.json")
    store.save({"device_id":"d1","session_id":"s1","refresh_token":"r1","expires_at":9999999999})
    WindowsDesktopVoiceRuntime(Client(),store).logout()
    assert store.load() is None
    assert calls[0][0]=="/v1/session/logout"
