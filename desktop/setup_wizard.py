from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from desktop.first_run_state import FirstRunState


class SetupStep(str, Enum):
    DIAGNOSTICS = "diagnostics"
    CONFIGURATION = "configuration"
    COMPLETE = "complete"


@dataclass(frozen=True)
class WizardStatus:
    step: SetupStep
    completed: bool
    diagnostics_passed: bool
    configuration_ready: bool = False


class SetupWizard:
    def __init__(self, state: FirstRunState | None = None) -> None:
        self.state = state or FirstRunState()

    def status(self) -> WizardStatus:
        raw = self.state.load()
        completed = bool(raw.get("completed", False))
        diagnostics = bool(raw.get("diagnostics_passed", False))
        if completed:
            step = SetupStep.COMPLETE
        elif diagnostics:
            step = SetupStep.CONFIGURATION
        else:
            step = SetupStep.DIAGNOSTICS
        return WizardStatus(step, completed, diagnostics, bool(raw.get("configuration_ready", diagnostics)))

    def mark_diagnostics_passed(self) -> dict[str, Any]:
        return self.state.save(diagnostics_passed=True, completed=False)

    def mark_configuration_ready(self) -> dict[str, Any]:
        if not self.state.load().get("diagnostics_passed", False):
            raise ValueError("Diagnostics must pass before configuration.")
        return self.state.save(configuration_ready=True, completed=False)

    def complete(self) -> dict[str, Any]:
        if not self.state.load().get("diagnostics_passed", False):
            raise ValueError("Diagnostics must pass before completing setup.")
        return self.state.save(diagnostics_passed=True, completed=True)

    def reset(self) -> dict[str, Any]:
        return self.state.save(diagnostics_passed=False, completed=False)
