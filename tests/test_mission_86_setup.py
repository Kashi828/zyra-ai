from desktop.first_run_state import FirstRunState
from desktop.release_channel import get_release_info

def test_first_run_state_defaults_to_incomplete(tmp_path):
    state=FirstRunState(str(tmp_path/"setup.json")); assert state.load()["completed"] is False

def test_first_run_state_persists_completion(tmp_path):
    state=FirstRunState(str(tmp_path/"setup.json")); assert state.complete()["completed"] is True; assert FirstRunState(str(tmp_path/"setup.json")).load()["completed"] is True

def test_release_channel_defaults_to_beta(monkeypatch):
    monkeypatch.delenv("ZYRA_RELEASE_CHANNEL", raising=False); assert get_release_info()["channel"]=="beta"

def test_release_info_targets_windows_x64():
    assert get_release_info()["installer_target"]=="win32-x64-nsis"
