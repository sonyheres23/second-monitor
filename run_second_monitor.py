#!/usr/bin/env python3
"""One-file bootstrapper for the Second Monitor USB prototype.

Run this file from the repository root with system Python. It creates a local
virtual environment, installs Python requirements, downloads Android
platform-tools when adb is missing, optionally builds/copies the tablet APK when
Gradle is available, and then starts the automatic desktop launcher.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".second-monitor-venv"
TOOLS_DIR = ROOT / ".second-monitor-tools"
DIST_DIR = ROOT / "dist"
APK_NAME = "SecondMonitorTablet.apk"
PLATFORM_TOOLS_URLS = {
    "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
    "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
}


def log(message: str) -> None:
    print(f"[second-monitor] {message}", flush=True)


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> None:
    log("Running: " + " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, env=env, check=True)


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def create_venv() -> Path:
    python = venv_python()
    if not python.exists():
        log(f"Creating local Python environment at {VENV_DIR}")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return python


def install_python_requirements(python: Path) -> None:
    marker = VENV_DIR / ".second-monitor-installed"
    if marker.exists():
        log("Python requirements already installed. Use --reinstall to force reinstall.")
        return
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "mss>=9.0.1", "pillow>=10.0.0"])
    marker.write_text("installed\n", encoding="utf-8")


def platform_tools_dir() -> Path:
    return TOOLS_DIR / "platform-tools"


def adb_executable(tools: Path | None = None) -> Path | None:
    executable = "adb.exe" if platform.system() == "Windows" else "adb"
    if tools is not None:
        candidate = tools / executable
        if candidate.exists():
            return candidate
    path = shutil.which(executable)
    return Path(path) if path else None


def download_platform_tools() -> Path:
    tools = platform_tools_dir()
    if adb_executable(tools) is not None:
        log(f"Using downloaded platform-tools at {tools}")
        return tools

    system = platform.system()
    url = PLATFORM_TOOLS_URLS.get(system)
    if url is None:
        raise RuntimeError(f"Automatic platform-tools download is not configured for {system}.")

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    archive = TOOLS_DIR / "platform-tools.zip"
    log(f"Downloading Android platform-tools from {url}")
    urllib.request.urlretrieve(url, archive)
    log("Extracting Android platform-tools")
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(TOOLS_DIR)
    archive.unlink(missing_ok=True)
    if adb_executable(tools) is None:
        raise RuntimeError("Downloaded platform-tools, but adb was not found in the archive.")
    return tools


def env_with_tools(tools: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(tools) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(ROOT / "desktop")
    return env


def apk_candidates() -> list[Path]:
    return [
        DIST_DIR / APK_NAME,
        ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk",
        ROOT / APK_NAME,
    ]


def existing_apk() -> Path | None:
    for candidate in apk_candidates():
        if candidate.is_file():
            return candidate
    return None


def copy_apk_to_dist(apk: Path) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    destination = DIST_DIR / APK_NAME
    if apk.resolve() != destination.resolve():
        shutil.copy2(apk, destination)
    return destination


def maybe_build_apk() -> Path | None:
    apk = existing_apk()
    if apk is not None:
        return copy_apk_to_dist(apk)

    gradle = shutil.which("gradle")
    if gradle is None:
        log("Gradle was not found, so APK auto-build is skipped. Put SecondMonitorTablet.apk in dist/ to auto-install it.")
        return None

    android_project = ROOT / "android"
    log("No APK found. Trying to build the tablet APK with Gradle.")
    try:
        run([gradle, ":app:assembleDebug"], cwd=android_project)
    except subprocess.CalledProcessError as exc:
        log(f"APK build failed: {exc}. Continuing without APK auto-install.")
        return None

    apk = existing_apk()
    if apk is None:
        log("Gradle finished but APK output was not found. Continuing without APK auto-install.")
        return None
    return copy_apk_to_dist(apk)


def reset_install_marker() -> None:
    marker = VENV_DIR / ".second-monitor-installed"
    marker.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download requirements and start Second Monitor USB with one file.")
    parser.add_argument("--reinstall", action="store_true", help="Reinstall Python requirements in the local virtual environment.")
    parser.add_argument("--skip-apk-build", action="store_true", help="Do not try to build the Android APK if it is missing.")
    args, launcher_args = parser.parse_known_args()
    args.launcher_args = launcher_args
    return args


def main() -> None:
    args = parse_args()
    if args.reinstall:
        reset_install_marker()

    python = create_venv()
    install_python_requirements(python)
    tools = download_platform_tools() if adb_executable() is None else adb_executable().parent
    if not args.skip_apk_build:
        maybe_build_apk()

    env = env_with_tools(tools)
    launcher_command = [str(python), "-m", "second_monitor", *args.launcher_args]
    log("Starting automatic launcher. Connect the tablet and accept the USB debugging prompt.")
    run(launcher_command, env=env)


if __name__ == "__main__":
    main()
