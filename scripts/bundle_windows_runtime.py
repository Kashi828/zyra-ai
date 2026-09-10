from pathlib import Path

# Build two self-contained PyInstaller executables for the Windows beta.
# The Electron shell launches these binaries when running from a packaged app.

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "runtime"
BUILD = ROOT / "build" / "pyinstaller"

# Keep backend and native bridge separate so each process has a minimal responsibility.
# --onedir is used because it is substantially more reliable for FastAPI/uvicorn and
# native Python dependencies than a single-file executable, while still being bundled
# inside the Electron installer.

BACKEND = [
    "python", "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
    "--name", "zyra-backend", "--distpath", str(DIST), "--workpath", str(BUILD / "backend"),
    "--specpath", str(BUILD), "--collect-submodules", "uvicorn", "--collect-submodules", "fastapi",
    "main.py",
]

BRIDGE = [
    "python", "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
    "--name", "zyra-native-bridge", "--distpath", str(DIST), "--workpath", str(BUILD / "bridge"),
    "--specpath", str(BUILD), "--collect-submodules", "desktop", "desktop/native_bridge.py",
]

if __name__ == "__main__":
    import subprocess
    import sys

    DIST.mkdir(parents=True, exist_ok=True)
    for command in (BACKEND, BRIDGE):
        print("+", " ".join(command))
        subprocess.run(command, cwd=ROOT, check=True)
    print("Windows runtime bundle created under runtime/")
