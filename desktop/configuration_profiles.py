from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from desktop.configuration_service import ConfigurationService


@dataclass(frozen=True)
class ConfigurationProfile:
    name: str
    model_provider: str
    model_endpoint: str
    voice_provider: str
    preferred_language: str
    telemetry: bool = False


LOCAL_PROFILE = ConfigurationProfile(
    name="local",
    model_provider="local",
    model_endpoint="http://127.0.0.1:11434",
    voice_provider="system",
    preferred_language="en-IN",
    telemetry=False,
)

PRIVACY_PROFILE = ConfigurationProfile(
    name="privacy",
    model_provider="local",
    model_endpoint="http://127.0.0.1:11434",
    voice_provider="off",
    preferred_language="en-IN",
    telemetry=False,
)


class ConfigurationProfileService:
    PROFILES = {LOCAL_PROFILE.name: LOCAL_PROFILE, PRIVACY_PROFILE.name: PRIVACY_PROFILE}

    def __init__(self, service: ConfigurationService | None = None) -> None:
        self.service = service or ConfigurationService()

    def list_profiles(self) -> list[dict[str, Any]]:
        return [
            {"name": p.name, "model_provider": p.model_provider, "model_endpoint": p.model_endpoint,
             "voice_provider": p.voice_provider, "preferred_language": p.preferred_language,
             "telemetry": p.telemetry}
            for p in self.PROFILES.values()
        ]

    def apply(self, name: str) -> dict[str, Any]:
        profile = self.PROFILES.get(name)
        if profile is None:
            raise ValueError("Unknown configuration profile")
        return self.service.update(
            model_provider=profile.model_provider, model_endpoint=profile.model_endpoint,
            voice_provider=profile.voice_provider, preferred_language=profile.preferred_language,
            telemetry=profile.telemetry,
        )
