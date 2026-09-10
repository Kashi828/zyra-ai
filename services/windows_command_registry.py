from dataclasses import dataclass
import os
import subprocess


@dataclass(frozen=True)
class ToolSpec:
    name: str
    capability: str
    confirmation_required: bool


class WindowsCommandRegistry:
    """Small allowlisted Windows action registry; no arbitrary shell commands."""

    _KNOWN_APPS = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "settings": "ms-settings:",
        "windows settings": "ms-settings:",
    }

    _CAPABILITY_ALIASES = {
        "windows.apps": {"windows.apps", "pc.apps"},
        "windows.files.read": {"windows.files.read", "pc.files"},
        "windows.browser": {"windows.browser", "pc.web"},
    }

    def __init__(self, runner=None):
        self._runner = runner or self._default_runner
        self._tools = {
            "open_app": ToolSpec("open_app", "windows.apps", False),
            "open_folder": ToolSpec("open_folder", "windows.files.read", False),
            "open_url": ToolSpec("open_url", "windows.browser", False),
        }

    @classmethod
    def _resolve_app(cls, name: str) -> str:
        normalized = name.strip().lower()
        if normalized in cls._KNOWN_APPS:
            return cls._KNOWN_APPS[normalized]
        candidate = os.path.expandvars(os.path.expanduser(name.strip()))
        if candidate.lower().endswith(".exe") and os.path.isfile(candidate):
            return candidate
        raise ValueError("unsupported application; use an allowlisted app or an existing .exe path")

    @classmethod
    def _default_runner(cls, action: str, payload: dict) -> str:
        if action == "open_app":
            target = cls._resolve_app(str(payload.get("name", "")))
            if target == "ms-settings:":
                os.startfile(target)
            else:
                subprocess.Popen([target], shell=False)
            return f"launched:{target}"
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
        allowed = self._CAPABILITY_ALIASES.get(spec.capability, {spec.capability})
        if not allowed.intersection(set(capabilities)):
            raise PermissionError("missing capability")
        return self._runner(action, payload)
