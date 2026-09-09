from config.onboarding import OnboardingStore, OnboardingState
from pathlib import Path

def test_new_onboarding_is_incomplete(tmp_path):
    s = OnboardingStore(str(tmp_path/"state.json")).load()
    assert s.completed is False
    assert s.ai_provider == "local"

def test_complete_persists(tmp_path):
    store = OnboardingStore(str(tmp_path/"state.json"))
    state = store.complete("local")
    assert state.completed
    loaded = store.load()
    assert loaded.completed and loaded.permissions_reviewed
    assert loaded.ai_provider == "local"

def test_corrupt_state_resets_safely(tmp_path):
    p = tmp_path/"state.json"
    p.write_text("{bad", encoding="utf-8")
    state = OnboardingStore(str(p)).load()
    assert state.completed is False

def test_onboarding_ui_exists():
    html = Path("desktop/index.html").read_text()
    js = Path("desktop/app.js").read_text()
    assert 'id="onboarding"' in html
    assert "zyra_onboarding_complete" in js
