import pytest

from services.windows_command_registry import WindowsCommandRegistry


def test_open_url_rejects_credentials_and_fragments():
    registry = WindowsCommandRegistry(runner=lambda action, payload: "ok")
    with pytest.raises(ValueError):
        registry.execute("open_url", {"url": "https://user:pass@example.com/"}, {"pc.web"})
    with pytest.raises(ValueError):
        registry.execute("open_url", {"url": "https://example.com/#secret"}, {"pc.web"})


def test_open_url_rejects_invalid_scheme():
    registry = WindowsCommandRegistry(runner=lambda action, payload: "ok")
    with pytest.raises(ValueError):
        registry.execute("open_url", {"url": "javascript:alert(1)"}, {"pc.web"})


def test_open_app_rejects_newline_injection():
    registry = WindowsCommandRegistry(runner=lambda action, payload: "ok")
    with pytest.raises(ValueError):
        registry.execute("open_app", {"name": "calc\nmalicious"}, {"pc.apps"})
