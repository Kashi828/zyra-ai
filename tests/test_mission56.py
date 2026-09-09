from pathlib import Path
from config.user_settings import UserSettings, UserSettingsStore
from config.pairing_wizard import PairingWizard, PairingStep

def test_settings_roundtrip(tmp_path):
    s=UserSettingsStore(str(tmp_path/"s.json"))
    s.save(UserSettings(notifications=False))
    assert s.load().notifications is False

def test_settings_safety():
    try: UserSettings(remote_access=True, local_first=True).validate()
    except ValueError: pass
    else: assert False

def test_pairing_flow():
    w=PairingWizard()
    w.load_offer("o1","ZYRA PC","fp")
    w.confirm("d1")
    assert w.step==PairingStep.COMPLETE

def test_ui_hooks():
    assert 'id="pairDevice"' in Path("desktop/index.html").read_text()
    assert "/v1/devices/pairing/offer" in Path("desktop/app.js").read_text()
