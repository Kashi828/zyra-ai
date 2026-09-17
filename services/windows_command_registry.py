from dataclasses import dataclass
import os
import subprocess
import sys
from urllib.parse import urlparse


@dataclass(frozen=True)
class ToolSpec:
    name: str
    capability: str
    confirmation_required: bool


class WindowsCommandRegistry:
    """Small allowlisted Windows action registry; never exposes arbitrary shell."""

    def __init__(self, runner=None):
        self._runner = runner or self._default_runner
        self._tools = {
            "open_app": ToolSpec("open_app", "pc.apps", False),
            "open_folder": ToolSpec("open_folder", "pc.files", False),
            "open_url": ToolSpec("open_url", "pc.web", False),
        }

    @staticmethod
    def _validate(action: str, payload: dict) -> dict:
        """Validate and normalize a payload. Runs regardless of which runner
        is installed, so a custom/test runner can never bypass these checks."""
        if action == "open_app":
            name = str(payload.get("name", "")).strip()
            if not name or len(name) > 260 or any(c in name for c in "\r\n"):
                raise ValueError("invalid application name")
            return {"name": name}

        if action == "open_folder":
            path = os.path.abspath(str(payload.get("path", "")))
            return {"path": path}

        if action == "open_url":
            url = str(payload.get("url", "")).strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                raise ValueError("URL must be a valid http(s) URL")
            if parsed.username or parsed.password or parsed.fragment:
                raise ValueError("URL credentials/fragments are not allowed")
            return {"url": url}

        raise ValueError("unsupported action")

    @staticmethod
    def _default_runner(action: str, payload: dict) -> str:
        if action == "open_app":
            name = payload["name"]
            subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
            return f"launched:{name}"

        if action == "open_folder":
            path = payload["path"]
            if not os.path.isdir(path):
                raise FileNotFoundError("folder not found")
            os.startfile(path)
            return f"opened_folder:{path}"

        if action == "open_url":
            url = payload["url"]
            import webbrowser
            webbrowser.open(url)
            return f"opened_url:{url}"

        raise ValueError("unsupported action")

    def specs(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def execute(self, action: str, payload: dict, capabilities: set[str]) -> str:
        spec = self._tools.get(action)
        if spec is None:
            raise ValueError("unsupported action")
        if spec.capability not in capabilities:
            raise PermissionError("missing capability")
        safe_payload = self._validate(action, payload)
        return self._runner(action, safe_payload)
