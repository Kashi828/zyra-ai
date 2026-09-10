from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_electron_file_renderer_routes_root_api_paths_to_loopback():
    html = (ROOT / "desktop" / "index.html").read_text(encoding="utf-8")
    assert 'const API_ORIGIN = "http://127.0.0.1:8000";' in html
    assert "window.fetch = (input, init) =>" in html
    assert 'nativeFetch(`${API_ORIGIN}${input}`, init)' in html


def test_backend_allows_the_file_origin_used_by_electron():
    source = (ROOT / "api" / "app_factory.py").read_text(encoding="utf-8")
    assert "from fastapi.middleware.cors import CORSMiddleware" in source
    assert 'allow_origins=["null"]' in source
    assert 'allow_origin_regex=r"^https?://(?:127\\.0\\.0\\.1|localhost)(?::\\d+)?$"' in source
