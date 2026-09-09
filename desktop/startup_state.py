from __future__ import annotations

from dataclasses import dataclass

from desktop.onboarding import OnboardingController


@dataclass(frozen=True)
class StartupDecision:
    screen: str
    setup_required: bool


class DesktopStartupController:
    def __init__(self, onboarding: OnboardingController | None = None) -> None:
        self.onboarding = onboarding or OnboardingController()

    def decide(self) -> StartupDecision:
        status = self.onboarding.status()
        return StartupDecision(
            screen="onboarding" if status.needs_setup else "workspace",
            setup_required=status.needs_setup,
        )
