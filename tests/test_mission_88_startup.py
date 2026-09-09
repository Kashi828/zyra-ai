from desktop.first_run_state import FirstRunState
from desktop.onboarding import OnboardingController
from desktop.startup_state import DesktopStartupController


def make_controller(tmp_path):
    state = FirstRunState(str(tmp_path / "setup.json"))
    return DesktopStartupController(OnboardingController(state))


def test_startup_routes_to_onboarding_before_setup(tmp_path):
    decision = make_controller(tmp_path).decide()
    assert decision.screen == "onboarding"
    assert decision.setup_required is True


def test_startup_routes_to_workspace_after_setup(tmp_path):
    controller = make_controller(tmp_path)
    controller.onboarding.complete()
    decision = controller.decide()
    assert decision.screen == "workspace"
    assert decision.setup_required is False


def test_startup_decision_is_stable_across_new_controller(tmp_path):
    state_path = tmp_path / "setup.json"
    c1 = DesktopStartupController(OnboardingController(FirstRunState(str(state_path))))
    c1.onboarding.complete()
    c2 = DesktopStartupController(OnboardingController(FirstRunState(str(state_path))))
    assert c2.decide().screen == "workspace"
