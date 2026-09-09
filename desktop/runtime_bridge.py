from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import time
import urllib.error
import urllib.request


class DesktopRuntimeError(RuntimeError):
    pass


def default_state_path() -> Path:
    root = os.getenv("LOCALAPPDATA") or os.getenv("XDG_STATE_HOME")
    base = Path(root) if root else Path.home() / ".local" / "state"
    return base / "zyra" / "desktop_session.json"


class DesktopSessionStore:
    """
    Small native-host session store. The store only persists the device/session
    identifiers and refresh token needed by the desktop host. On Windows the
    parent directory is placed under LOCALAPPDATA when available.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_state_path()

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DesktopRuntimeError("desktop session state is unreadable") from exc
        if not isinstance(value, dict):
            raise DesktopRuntimeError("desktop session state is invalid")
        return value

    def save(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(self.path)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class LocalApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, body: dict | None = None, *, headers: dict | None = None) -> dict:
        data = json.dumps(body or {}).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DesktopRuntimeError(f"local API {exc.code}: {detail}") from exc
        except OSError as exc:
            raise DesktopRuntimeError(f"local API unavailable: {exc}") from exc
        try:
            result = json.loads(payload)
        except ValueError as exc:
            raise DesktopRuntimeError("local API returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise DesktopRuntimeError("local API returned an invalid response")
        return result


class WindowsDesktopVoiceRuntime:
    """
    Native-host lifecycle for desktop voice credentials.

    This keeps refresh tokens out of the browser UI. The actual token storage
    is in the native host state file, and all network calls target loopback.
    """

    def __init__(self, client: LocalApiClient | None = None, store: DesktopSessionStore | None = None):
        self.client = client or LocalApiClient()
        self.store = store or DesktopSessionStore()

    def ensure_session(self) -> dict:
        state = self.store.load()
        if state and state.get("device_id") and state.get("session_id"):
            # Keep near-expiry sessions fresh before reuse.
            if float(state.get("expires_at", 0)) > time.time() + 60:
                return state
            try:
                refreshed = self.client.post("/v1/session/refresh", {
                    "device_id": state["device_id"],
                    "refresh_token": state["refresh_token"],
                })
                refreshed_state = {
                    **state,
                    "session_id": refreshed["session_id"],
                    "refresh_token": refreshed["refresh_token"],
                    "expires_at": refreshed.get("expires_at", time.time() + 900),
                }
                self.store.save(refreshed_state)
                return refreshed_state
            except DesktopRuntimeError:
                self.store.clear()

        created = self.client.post("/v1/voice/desktop/bootstrap")
        state = {
            "device_id": created["device_id"],
            "session_id": created["session_id"],
            "refresh_token": created["refresh_token"],
            "expires_at": created.get("expires_at", time.time() + 900),
            "created_by": "zyra-desktop-host",
            "state_nonce": secrets.token_hex(8),
        }
        self.store.save(state)
        return state

    def logout(self) -> None:
        state = self.store.load()
        if state and state.get("device_id") and state.get("session_id"):
            try:
                self.client.post("/v1/session/logout", {
                    "device_id": state["device_id"],
                    "session_id": state["session_id"],
                })
            finally:
                self.store.clear()
        else:
            self.store.clear()

    def auth_headers(self) -> dict:
        state = self.ensure_session()
        return {
            "X-ZYRA-Device-Id": state["device_id"],
            "Authorization": f"Bearer {state['session_id']}",
        }
