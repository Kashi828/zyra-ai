from __future__ import annotations

import os
from pathlib import Path
import webbrowser

from desktop.runtime_bridge import LocalApiClient


def launch_backend(host: str = "127.0.0.1", port: int = 8000):
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is required to launch ZYRA") from exc

    from main import app
    # The desktop shell should never bind the API to a public interface.
    uvicorn.run(app, host=host, port=port)


def open_shell(base_url: str = "http://127.0.0.1:8000"):
    shell = Path(__file__).with_name("index.html")
    webbrowser.open(shell.as_uri())
    return shell


def launch_native_bridge():
    from desktop.native_bridge import NativeBridgeServer
    NativeBridgeServer().serve()


if __name__ == "__main__":
    launch_backend()
