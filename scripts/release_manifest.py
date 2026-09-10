from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(paths: Iterable[Path]) -> list[dict[str, object]]:
    return [
        {"name": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(paths)
        if path.is_file()
    ]


def write_manifest(directory: str | Path, output: str | Path) -> dict[str, object]:
    root = Path(directory)
    manifest = {"assets": build_manifest(root.iterdir())}
    Path(output).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a deterministic SHA-256 release asset manifest.")
    parser.add_argument("directory")
    parser.add_argument("output")
    args = parser.parse_args()
    write_manifest(args.directory, args.output)
