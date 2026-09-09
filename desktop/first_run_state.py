from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any

class FirstRunState:
    """Persistent, non-secret desktop setup state."""
    def __init__(self, path: str | None = None) -> None:
        base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        self.path = Path(path) if path else base / "ZYRA AI" / "setup.json"
    def load(self) -> dict[str, Any]:
        if not self.path.exists(): return {"version": 1, "completed": False}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"version": 1, "completed": False}
        except (OSError, ValueError):
            return {"version": 1, "completed": False}
    def save(self, **updates: Any) -> dict[str, Any]:
        state = self.load(); state.update(updates); self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"); tmp.replace(self.path)
        return state
    def complete(self) -> dict[str, Any]: return self.save(completed=True)
