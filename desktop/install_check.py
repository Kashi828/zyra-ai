from __future__ import annotations

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import platform
import shutil
import sys

from api.health import dependency_report


@dataclass(frozen=True)
class Check:
    key: str
    label: str
    ok: bool
    required: bool
    detail: str


def _python_detail() -> Check:
    ok = sys.version_info >= (3, 11)
    return Check("python", "Python runtime", ok, True, platform.python_version())


def _dependency_checks(report: dict) -> list[Check]:
    items: list[Check] = []
    for item in report.get("required", []):
        detail = item.get("version") or item.get("detail") or ("available" if item.get("available") else "missing")
        items.append(Check(item["name"], item["name"], bool(item.get("available")), True, detail))
    for item in report.get("optional_voice", []):
        detail = item.get("version") or item.get("detail") or ("available" if item.get("available") else "not installed")
        items.append(Check(item["name"], item["name"], bool(item.get("available")), False, detail))
    return items


def _ollama_check() -> Check:
    exe = shutil.which("ollama")
    return Check("ollama", "Ollama", bool(exe), False, exe or "not installed")


def _data_dir_check() -> Check:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ZYRA AI"
    else:
        root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "zyra-ai"
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return Check("data_dir", "Local data directory", True, True, str(root))
    except OSError as exc:
        return Check("data_dir", "Local data directory", False, True, str(exc))


def run_install_checks() -> dict:
    report = dependency_report(include_optional_voice=True)
    checks = [_python_detail(), *_dependency_checks(report), _ollama_check(), _data_dir_check()]
    required_ok = all(c.ok for c in checks if c.required)
    return {
        "ready": required_ok,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "checks": [asdict(c) for c in checks],
        "next_step": "ready" if required_ok else "repair_required_dependencies",
        "non_destructive": True,
    }
