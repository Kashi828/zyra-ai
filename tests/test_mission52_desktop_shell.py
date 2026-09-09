from pathlib import Path

def test_desktop_shell_assets_exist():
    root = Path("desktop")
    assert (root / "index.html").exists()
    assert (root / "styles.css").exists()

def test_desktop_shell_contains_security_controls():
    html = Path("desktop/index.html").read_text()
    assert "Local-first mode" in html
    assert "Remote access" in html
    assert "Sensitive confirmations" in html
    assert "Stop Agent" in html

def test_desktop_shell_contains_core_navigation():
    html = Path("desktop/index.html").read_text()
    for item in ["Assistant", "Tasks", "Devices", "Permissions", "Settings"]:
        assert item in html
