from __future__ import annotations

from dataclasses import asdict, dataclass

from desktop.configuration_status import ConfigurationStatusService
from desktop.onboarding import OnboardingController
from desktop.startup_state import DesktopStartupController


@dataclass(frozen=True)
class RuntimeReadyState:
    ready: bool
    screen: str
    setup_required: bool
    configuration_ready: bool


class RuntimeReadyService:
    def __init__(self, onboarding: OnboardingController | None = None,
                 configuration_status: ConfigurationStatusService | None = None) -> None:
        self.onboarding = onboarding or OnboardingController()
        self.configuration_status = configuration_status or ConfigurationStatusService()

    def read(self) -> dict:
        startup = DesktopStartupController(self.onboarding).decide()
        configuration = self.configuration_status.read()
        ready = (not startup.setup_required and bool(configuration.get("endpoint_configured", False)))
        return asdict(RuntimeReadyState(
            ready=ready,
            screen="workspace" if ready else startup.screen,
            setup_required=not ready,
            configuration_ready=bool(configuration.get("endpoint_configured", False)),
        ))
