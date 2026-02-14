"""Build script — compiles the launcher into a Windows .exe and assembles dist/.

Usage:
    python scripts/build.py

Requirements:
    pip install pyinstaller
"""

import os
import shutil
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
LAUNCHER_DIR = os.path.join(PROJECT_ROOT, "launcher")
ENTRY_POINT = os.path.join(LAUNCHER_DIR, "main.py")


def clean():
    """Remove previous build artifacts."""
    for d in ("build", "dist"):
        path = os.path.join(PROJECT_ROOT, d)
        if os.path.exists(path):
            shutil.rmtree(path)
    spec = os.path.join(PROJECT_ROOT, "main.spec")
    if os.path.exists(spec):
        os.remove(spec)


def build_exe():
    """Run PyInstaller to create the launcher .exe."""
    icon_path = os.path.join(LAUNCHER_DIR, "resources", "icon.ico")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "LocalLLM",
        "--add-data", f"{os.path.join(LAUNCHER_DIR, 'resources')}{os.pathsep}resources",
    ]
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])
    cmd.append(ENTRY_POINT)

    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=PROJECT_ROOT)


def copy_config_files():
    """Copy docker-compose.yml and .env into dist/."""
    for filename in ("docker-compose.yml", ".env"):
        src = os.path.join(PROJECT_ROOT, filename)
        dst = os.path.join(DIST_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {filename} → dist/")


def main():
    print("=== LocalLLM Build ===")
    clean()
    build_exe()
    copy_config_files()
    print(f"\nBuild complete. Artifacts in: {DIST_DIR}")


if __name__ == "__main__":
    main()
