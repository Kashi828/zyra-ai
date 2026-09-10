from desktop.first_run_state import FirstRunState
from desktop.onboarding import OnboardingController
from desktop.setup_wizard import SetupWizard
from desktop.startup_state import DesktopStartupController


def make_controller(tmp_path):
    state = FirstRunState(str(tmp_path / "setup.json"))
    onboarding = OnboardingController(state)
    return state, onboarding, SetupWizard(state), DesktopStartupController(onboarding)


def test_fresh_install_requires_onboarding(tmp_path):
    _, _, wizard, startup = make_controller(tmp_path)

    assert wizard.status().step.value == "diagnostics"
    decision = startup.decide()
    assert decision.screen == "onboarding"
    assert decision.setup_required is True


def test_passing_diagnostics_does_not_complete_wizard(tmp_path):
    state, _, wizard, startup = make_controller(tmp_path)

    wizard.mark_diagnostics_passed()

    status = wizard.status()
    assert status.diagnostics_passed is True
    assert status.completed is False
    assert status.step.value == "configuration"
    assert startup.decide().screen == "onboarding"
    assert state.load()["completed"] is False


def test_onboarding_completion_transitions_to_workspace(tmp_path):
    _, onboarding, wizard, startup = make_controller(tmp_path)

    wizard.mark_diagnostics_passed()
    onboarding.complete(diagnostics_passed=True)

    status = onboarding.status()
    assert status.completed is True
    assert status.needs_setup is False
    assert startup.decide().screen == "workspace"
    assert startup.decide().setup_required is False


def test_diagnostics_failure_resets_setup_state(tmp_path):
    _, _, wizard, startup = make_controller(tmp_path)

    wizard.mark_diagnostics_passed()
    wizard.reset()

    assert wizard.status().diagnostics_passed is False
    assert wizard.status().completed is False
    assert startup.decide().screen == "onboarding"
