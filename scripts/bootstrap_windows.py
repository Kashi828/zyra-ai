from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow direct execution as `python scripts/bootstrap_windows.py` from the repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.install_check import run_install_checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the ZYRA AI Windows runtime without installing anything.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result = run_install_checks()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("ZYRA AI environment")
        for item in result["checks"]:
            state = "OK" if item["ok"] else ("OPTIONAL" if not item["required"] else "MISSING")
            print(f"[{state}] {item['label']}: {item['detail']}")
        print("READY" if result["ready"] else "REPAIR REQUIRED")
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
