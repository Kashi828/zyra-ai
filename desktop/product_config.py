from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any

DEFAULTS = {
    "version": 1,
    "model_provider": "local",
    "model_endpoint": "http://127.0.0.1:11434",
    "voice_provider": "system",
    "preferred_language": "en-IN",
    "telemetry": False,
}

class ProductConfig:
    def __init__(self, path: str | None = None) -> None:
        base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CONFIG_HOME") or (Path.home()/".config"))
        self.path = Path(path) if path else base/"ZYRA AI"/"config.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULTS)
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return dict(DEFAULTS)
            out = dict(DEFAULTS)
            for k in DEFAULTS:
                if k in raw: out[k] = raw[k]
            return out
        except (OSError, ValueError):
            return dict(DEFAULTS)

    def update(self, **values: Any) -> dict[str, Any]:
        current = self.load()
        for k in DEFAULTS:
            if k in values: current[k] = values[k]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
        return current
