from __future__ import annotations

from dataclasses import asdict, dataclass

from desktop.configuration_status import ConfigurationStatusService
from desktop.runtime_ready import RuntimeReadyService


@dataclass(frozen=True)
class WorkspaceContext:
    product: str
    runtime_ready: bool
    model_provider: str
    voice_provider: str
    preferred_language: str
    telemetry: bool


class WorkspaceContextService:
    def __init__(self, runtime: RuntimeReadyService | None = None) -> None:
        self.runtime = runtime or RuntimeReadyService()
        self.configuration = self.runtime.configuration_status

    def read(self) -> dict:
        status = self.configuration.read()
        ready = self.runtime.read()
        return asdict(WorkspaceContext(
            product="ZYRA AI",
            runtime_ready=bool(ready["ready"]),
            model_provider=str(status["model_provider"]),
            voice_provider=str(status["voice_provider"]),
            preferred_language=str(status["preferred_language"]),
            telemetry=bool(status["telemetry"]),
        ))
