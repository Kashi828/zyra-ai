from pathlib import Path
import json
import subprocess
import sys

from fastapi.testclient import TestClient
from api.app_factory import create_app


def test_install_checks_are_non_destructive(tmp_path):
    from desktop.install_check import run_install_checks
    result = run_install_checks()
    assert "checks" in result
    assert result["non_destructive"] is True
    assert result["next_step"] in {"ready", "repair_required_dependencies"}


def test_setup_check_route(tmp_path):
    app = create_app(tmp_path / "setup.sqlite3")
    client = TestClient(app)
    response = client.get("/v1/system/setup-check")
    assert response.status_code == 200
    body = response.json()
    assert "ready" in body
    assert "checks" in body


def test_bootstrap_json_mode(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/bootstrap_windows.py", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip()
    data = json.loads(result.stdout)
    assert "ready" in data
    assert "checks" in data


def test_windows_build_pipeline_files_exist():
    assert Path("scripts/prepare_windows.ps1").exists()
    assert Path("scripts/build_windows.ps1").exists()
    package = json.loads(Path("package.json").read_text())
    assert package["scripts"]["build:win"].startswith("electron-builder")


def test_python_selection_helper_is_fixed():
    text = Path("electron/main.js").read_text()
    assert 'if (process.env.ZYRA_PYTHON) return process.env.ZYRA_PYTHON;' in text
    assert 'return process.platform === "win32" ? "python" : "python3";' in text


def test_setup_ui_is_wired():
    html = Path("desktop/index.html").read_text()
    js = Path("desktop/app.js").read_text()
    assert 'id="setup"' in html
    assert '/v1/system/setup-check' in js
    assert 'zyra_setup_check_complete' in js
