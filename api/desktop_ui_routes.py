from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

DESKTOP_DIR = Path(__file__).resolve().parent.parent / "desktop"
# Only front-end assets are ever served; the Python modules beside them are not.
SERVED_SUFFIXES = {".html", ".js", ".css"}


def register_desktop_ui_routes(app):
    @app.get("/", include_in_schema=False)
    def ui_index():
        return FileResponse(DESKTOP_DIR / "index.html")

    @app.get("/{name}", include_in_schema=False)
    def ui_asset(name: str):
        path = (DESKTOP_DIR / name).resolve()
        if (
            path.parent != DESKTOP_DIR.resolve()
            or path.suffix not in SERVED_SUFFIXES
            or not path.is_file()
        ):
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(path)
