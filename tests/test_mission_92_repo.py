from pathlib import Path

from desktop.repository_metadata import get_repository_metadata


def test_repository_metadata():
    data = get_repository_metadata()
    assert data["product"] == "ZYRA AI"
    assert data["repository"] == "Kashi828/zyra-ai"
    assert data["mission"] == "92"


def test_gitignore_protects_local_secrets_and_databases():
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert ".env" in text
    assert "*.db" in text
    assert "*.sqlite3" in text
    assert "node_modules/" in text


def test_env_example_contains_no_real_secret():
    text = Path(".env.example").read_text(encoding="utf-8").lower()
    assert "password" not in text
    assert "api_key=" not in text
