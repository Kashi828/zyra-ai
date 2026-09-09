from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from desktop.first_run_state import FirstRunState
from desktop.setup_wizard import SetupWizard


@dataclass(frozen=True)
class OnboardingStatus:
    completed: bool
    version: int
    needs_setup: bool
    step: str = "diagnostics"


class OnboardingController:
    def __init__(self, state: FirstRunState | None = None) -> None:
        self.state = state or FirstRunState()
        self.wizard = SetupWizard(self.state)

    def status(self) -> OnboardingStatus:
        raw = self.state.load()
        wizard = self.wizard.status()
        return OnboardingStatus(
            completed=wizard.completed,
            version=int(raw.get("version", 1)),
            needs_setup=not wizard.completed,
            step=wizard.step.value,
        )

    def complete(self, *, diagnostics_passed: bool = True) -> dict[str, Any]:
        if not diagnostics_passed:
            raise ValueError("Diagnostics must pass before onboarding can be completed.")
        self.wizard.mark_diagnostics_passed()
        self.wizard.mark_configuration_ready()
        return self.wizard.complete()

    def reset_for_repair(self) -> dict[str, Any]:
        return self.wizard.reset()
