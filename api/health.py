from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
import platform
import sys


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    required: bool
    available: bool
    version: str | None = None
    detail: str = ""


def _version(name: str) -> str | None:
    try:
        module = __import__(name)
        return getattr(module, "__version__", None)
    except Exception:
        return None


def check_python() -> DependencyStatus:
    return DependencyStatus(
        "python",
        True,
        sys.version_info >= (3, 11),
        platform.python_version(),
        f"Python {platform.python_version()}",
    )


def check_module(name: str, required: bool = True) -> DependencyStatus:
    available = importlib.util.find_spec(name) is not None
    return DependencyStatus(
        name, required, available, _version(name) if available else None
    )


def dependency_report(*, include_optional_voice: bool = False) -> dict:
    required = [
        check_python(),
        check_module("fastapi"),
        check_module("uvicorn"),
    ]
    optional = []
    if include_optional_voice:
        optional = [
            check_module("sounddevice", required=False),
            check_module("faster_whisper", required=False),
            check_module("pyttsx3", required=False),
        ]
    all_items = required + optional
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "ready": all(item.available for item in required),
        "required": [vars(item) for item in required],
        "optional_voice": [vars(item) for item in optional],
    }


def bootstrap_environment() -> dict:
    """
    Validate the environment without installing packages or downloading models.
    The installer/build process owns dependency installation.
    """
    return dependency_report(include_optional_voice=True)
