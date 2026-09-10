from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "runtime"
BUILD = ROOT / "build" / "pyinstaller"


def build(name: str, entry: str, extra: list[str] | None = None) -> None:
    target = DIST / name
    if target.exists():
        shutil.rmtree(target)
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--name", name, "--distpath", str(DIST), "--workpath", str(BUILD / name),
        "--specpath", str(BUILD),
    ]
    if extra:
        args.extend(extra)
    args.append(entry)
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == "__main__":
    DIST.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    build("zyra-backend", "scripts/windows_backend_entry.py", [
        "--collect-submodules", "uvicorn",
        "--collect-submodules", "fastapi",
    ])
    build("zyra-native-bridge", "desktop/native_bridge.py", [
        "--collect-submodules", "desktop",
    ])
    print("Windows runtime bundle created under runtime/")
