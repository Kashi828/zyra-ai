from __future__ import annotations
from fastapi import APIRouter
from desktop.first_run_state import FirstRunState
from desktop.onboarding import OnboardingController
from desktop.startup_state import DesktopStartupController
from desktop.setup_wizard import SetupWizard
from desktop.configuration_service import ConfigurationService
from desktop.configuration_status import ConfigurationStatusService

def build_setup_router(state: FirstRunState | None = None) -> APIRouter:
    state = state or FirstRunState()
    onboarding = OnboardingController(state)
    startup = DesktopStartupController(onboarding)
    wizard = SetupWizard(state)
    configuration = ConfigurationService()
    configuration_status = ConfigurationStatusService(configuration)
    router = APIRouter(prefix="/v1/setup", tags=["setup"])

    @router.get("/startup")
    def startup_state():
        return startup.decide().__dict__

    @router.get("/configuration/status")
    def configuration_status_read():
        return configuration_status.read()

    @router.get("/configuration")
    def configuration_read():
        return configuration.read()

    @router.post("/configuration")
    def configuration_update(
        model_provider: str = "local",
        model_endpoint: str = "http://127.0.0.1:11434",
        voice_provider: str = "system",
        preferred_language: str = "en-IN",
        telemetry: bool = False,
    ):
        return configuration.update(
            model_provider=model_provider,
            model_endpoint=model_endpoint,
            voice_provider=voice_provider,
            preferred_language=preferred_language,
            telemetry=telemetry,
        )

    @router.get("/wizard")
    def wizard_status():
        return wizard.status().__dict__

    @router.post("/wizard/diagnostics")
    def wizard_diagnostics(passed: bool = True):
        if not passed:
            wizard.reset()
            return wizard.status().__dict__
        wizard.mark_diagnostics_passed()
        return wizard.status().__dict__

    @router.post("/wizard/complete")
    def wizard_complete():
        return wizard.complete()

    @router.post("/wizard/reset")
    def wizard_reset():
        return wizard.reset()

    @router.get("/onboarding")
    def onboarding_status():
        return onboarding.status().__dict__

    @router.post("/onboarding/complete")
    def onboarding_complete(diagnostics_passed: bool = True):
        return onboarding.complete(diagnostics_passed=diagnostics_passed)

    @router.post("/onboarding/repair")
    def onboarding_repair():
        return onboarding.reset_for_repair()

    @router.get("/state")
    def setup_state(): return state.load()
    @router.post("/complete")
    def setup_complete(): return state.complete()
    return router
