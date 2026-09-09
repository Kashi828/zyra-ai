from __future__ import annotations

from pathlib import Path


def get_repository_metadata(root: str | None = None) -> dict[str, str]:
    base = Path(root) if root else Path(__file__).resolve().parents[1]
    return {
        "product": "ZYRA AI",
        "repository": "Kashi828/zyra-ai",
        "mission": "92",
        "source_root": str(base),
    }
