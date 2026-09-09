import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class UserSettings:
    theme: str = "dark"
    local_first: bool = True
    remote_access: bool = False
    notifications: bool = True
    sensitive_confirmations: bool = True
    paired_device_ids: list[str] | None = None

    def __post_init__(self):
        if self.paired_device_ids is None:
            self.paired_device_ids = []

    def validate(self):
        if self.theme not in {"dark","light","system"}:
            raise ValueError("invalid theme")
        if self.remote_access and self.local_first:
            raise ValueError("remote access requires local_first=false")
        if not self.sensitive_confirmations:
            raise ValueError("sensitive confirmations cannot be disabled")

class UserSettingsStore:
    def __init__(self, path="zyra_settings.json"):
        self.path=Path(path)

    def load(self):
        if not self.path.exists():
            return UserSettings()
        try:
            s=UserSettings(**json.loads(self.path.read_text(encoding="utf-8")))
            s.validate()
            return s
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return UserSettings()

    def save(self, settings):
        settings.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp=self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
        tmp.replace(self.path)
