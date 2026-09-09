from __future__ import annotations

from dataclasses import asdict, dataclass

from desktop.configuration_service import ConfigurationService


@dataclass(frozen=True)
class ConfigurationStatus:
    model_provider: str
    voice_provider: str
    preferred_language: str
    telemetry: bool
    endpoint_configured: bool


class ConfigurationStatusService:
    def __init__(self, service: ConfigurationService | None = None) -> None:
        self.service = service or ConfigurationService()

    def read(self) -> dict:
        raw = self.service.read()
        return asdict(
            ConfigurationStatus(
                model_provider=str(raw.get("model_provider", "local")),
                voice_provider=str(raw.get("voice_provider", "system")),
                preferred_language=str(raw.get("preferred_language", "en-IN")),
                telemetry=bool(raw.get("telemetry", False)),
                endpoint_configured=bool(raw.get("model_endpoint")),
            )
        )
