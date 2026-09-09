from __future__ import annotations

import json
import sys
from desktop.runtime_bridge import WindowsDesktopVoiceRuntime


class NativeBridgeServer:
    """Tiny stdio JSON-RPC bridge for a packaged Windows desktop shell."""

    def __init__(self, runtime: WindowsDesktopVoiceRuntime | None = None):
        self.runtime = runtime or WindowsDesktopVoiceRuntime()

    def dispatch(self, message: dict) -> dict:
        method = str(message.get("method", "")).strip()
        if method == "ping":
            return {"ok": True, "service": "zyra-desktop-bridge"}
        if method == "voice.session.ensure":
            state = self.runtime.ensure_session()
            return {
                "ok": True,
                "device_id": state["device_id"],
                "session_id": state["session_id"],
                "expires_at": state.get("expires_at"),
            }
        if method == "voice.auth.headers":
            return {"ok": True, "headers": self.runtime.auth_headers()}
        if method == "voice.logout":
            self.runtime.logout()
            return {"ok": True}
        return {"ok": False, "error": "unknown method"}

    def serve(self, stdin=None, stdout=None) -> None:
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            try:
                message = json.loads(line)
                result = self.dispatch(message)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
            stdout.flush()


if __name__ == "__main__":
    NativeBridgeServer().serve()
