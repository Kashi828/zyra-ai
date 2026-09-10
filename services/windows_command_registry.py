from dataclasses import dataclass
import os
import subprocess


@dataclass(frozen=True)
class ToolSpec:
    name: str
    capability: str
    confirmation_required: bool


class WindowsCommandRegistry:
    def __init__(self, runner=None):
        self._runner = runner or self._default_runner
        self._tools = {
            "open_app": ToolSpec("open_app", "windows.apps", False),
            "open_folder": ToolSpec("open_folder", "windows.files.read", False),
            "open_url": ToolSpec("open_url", "windows.browser", False),
        }

    @staticmethod
    def _default_runner(action: str, payload: dict) -> str:
        if action == "open_app":
            name = str(payload.get("name", "")).strip()
            if not name:
                raise ValueError("application name required")
            subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
            return f"launched:{name}"
        if action == "open_folder":
            path = os.path.abspath(str(payload.get("path", "")))
            if not os.path.isdir(path):
                raise FileNotFoundError("folder not found")
            os.startfile(path)
            return f"opened_folder:{path}"
        if action == "open_url":
            import webbrowser
            url = str(payload.get("url", "")).strip()
            if not (url.startswith("https://") or url.startswith("http://")):
                raise ValueError("URL must be http(s)")
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
        return self._runner(action, payload)
