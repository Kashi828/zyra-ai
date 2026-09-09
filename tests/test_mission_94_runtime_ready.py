from desktop.configuration_service import ConfigurationService
from desktop.configuration_status import ConfigurationStatusService
from desktop.first_run_state import FirstRunState
from desktop.onboarding import OnboardingController
from desktop.product_config import ProductConfig
from desktop.runtime_ready import RuntimeReadyService
from desktop.workspace_context import WorkspaceContextService


def make_services(tmp_path):
    state = FirstRunState(str(tmp_path / "setup.json"))
    config = ConfigurationService(ProductConfig(str(tmp_path / "config.json")))
    onboarding = OnboardingController(state)
    status = ConfigurationStatusService(config)
    runtime = RuntimeReadyService(onboarding, status)
    return onboarding, config, runtime


def test_runtime_not_ready_before_setup(tmp_path):
    _, _, runtime = make_services(tmp_path)
    assert runtime.read()["ready"] is False
    assert runtime.read()["screen"] == "onboarding"


def test_runtime_ready_after_setup(tmp_path):
    onboarding, config, runtime = make_services(tmp_path)
    config.update(model_provider="local", model_endpoint="http://127.0.0.1:11434",
                  voice_provider="system", preferred_language="en-IN")
    onboarding.complete()
    state = runtime.read()
    assert state["ready"] is True
    assert state["screen"] == "workspace"


def test_workspace_context_contains_no_endpoint(tmp_path):
    onboarding, config, runtime = make_services(tmp_path)
    config.update(model_provider="local", model_endpoint="http://127.0.0.1:11434",
                  voice_provider="off", preferred_language="kn-IN")
    onboarding.complete()
    context = WorkspaceContextService(runtime).read()
    assert context["runtime_ready"] is True
    assert context["voice_provider"] == "off"
    assert context["preferred_language"] == "kn-IN"
    assert "model_endpoint" not in context
