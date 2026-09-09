from desktop.first_run_state import FirstRunState
from desktop.setup_wizard import SetupStep, SetupWizard


def test_wizard_starts_at_diagnostics(tmp_path):
    w = SetupWizard(FirstRunState(str(tmp_path / "setup.json")))
    s = w.status()
    assert s.step is SetupStep.DIAGNOSTICS
    assert s.completed is False
    assert s.diagnostics_passed is False


def test_wizard_moves_to_configuration_after_diagnostics(tmp_path):
    w = SetupWizard(FirstRunState(str(tmp_path / "setup.json")))
    w.mark_diagnostics_passed()
    assert w.status().step is SetupStep.CONFIGURATION


def test_wizard_cannot_complete_before_diagnostics(tmp_path):
    w = SetupWizard(FirstRunState(str(tmp_path / "setup.json")))
    try:
        w.complete()
        assert False
    except ValueError:
        pass


def test_wizard_completes_after_diagnostics(tmp_path):
    w = SetupWizard(FirstRunState(str(tmp_path / "setup.json")))
    w.mark_diagnostics_passed()
    result = w.complete()
    assert result["completed"] is True
    assert w.status().step is SetupStep.COMPLETE


def test_wizard_reset_returns_to_diagnostics(tmp_path):
    w = SetupWizard(FirstRunState(str(tmp_path / "setup.json")))
    w.mark_diagnostics_passed()
    w.complete()
    w.reset()
    assert w.status().step is SetupStep.DIAGNOSTICS
