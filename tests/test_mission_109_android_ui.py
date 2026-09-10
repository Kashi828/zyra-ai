from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_android_manifest_uses_zyra_no_actionbar_theme():
    manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    assert 'android:theme="@style/Theme.Zyra"' in manifest


def test_android_home_is_not_placeholder():
    source = (ROOT / "android/app/src/main/java/com/zyra/MainActivity.kt").read_text(encoding="utf-8")
    assert 'text = "✦  ZYRA"' in source
    assert 'text = "Control your PC\\nfrom anywhere."' in source
    assert 'text = "Run with ZYRA"' in source
    assert 'text = "PC STATUS"' in source
    assert 'text = "QUICK ACTIONS"' in source
