from desktop.first_run_state import FirstRunState
from desktop.onboarding import OnboardingController


def test_onboarding_requires_setup_by_default(tmp_path):
    controller = OnboardingController(FirstRunState(str(tmp_path / "setup.json")))
    assert controller.status().needs_setup is True


def test_onboarding_completion_requires_passing_diagnostics(tmp_path):
    controller = OnboardingController(FirstRunState(str(tmp_path / "setup.json")))
    try:
        controller.complete(diagnostics_passed=False)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_onboarding_completion_persists(tmp_path):
    controller = OnboardingController(FirstRunState(str(tmp_path / "setup.json")))
    result = controller.complete()
    assert result["completed"] is True
    assert result["diagnostics_passed"] is True
    assert controller.status().needs_setup is False


def test_repair_returns_to_setup(tmp_path):
    controller = OnboardingController(FirstRunState(str(tmp_path / "setup.json")))
    controller.complete()
    controller.reset_for_repair()
    assert controller.status().needs_setup is True
