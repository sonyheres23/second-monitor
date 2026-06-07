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
GRADLE_VERSION = "8.14.4"
ANDROID_COMPILE_SDK = "35"
ANDROID_BUILD_TOOLS = "35.0.0"
ANDROID_SDK_DIR = TOOLS_DIR / "android-sdk"
PLATFORM_TOOLS_URLS = {
    "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
    "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
}
COMMANDLINE_TOOLS_URLS = {
    "Windows": "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip",
    "Darwin": "https://dl.google.com/android/repository/commandlinetools-mac-11076708_latest.zip",
    "Linux": "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip",
}
GRADLE_URL = f"https://services.gradle.org/distributions/gradle-{GRADLE_VERSION}-bin.zip"


def log(message: str) -> None:
    print(f"[second-monitor] {message}", flush=True)


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    input_text: str | None = None,
) -> None:
    log("Running: " + " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, env=env, input=input_text, text=input_text is not None, check=True)


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


def env_with_tools(tools: Path, sdk_dir: Path | None = None, gradle_bin: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    path_parts = [str(tools)]
    if gradle_bin is not None:
        path_parts.append(str(gradle_bin))
    path_parts.append(env.get("PATH", ""))
    env["PATH"] = os.pathsep.join(path_parts)
    env["PYTHONPATH"] = str(ROOT / "desktop")
    if sdk_dir is not None:
        env["ANDROID_HOME"] = str(sdk_dir)
        env["ANDROID_SDK_ROOT"] = str(sdk_dir)
    return env


def gradle_executable(gradle_dir: Path | None = None) -> Path | None:
    executable = "gradle.bat" if platform.system() == "Windows" else "gradle"
    if gradle_dir is not None:
        candidate = gradle_dir / "bin" / executable
        if candidate.exists():
            return candidate
    path = shutil.which(executable)
    return Path(path) if path else None


def download_gradle() -> Path:
    gradle_dir = TOOLS_DIR / f"gradle-{GRADLE_VERSION}"
    executable = gradle_executable(gradle_dir)
    if executable is not None:
        log(f"Using downloaded Gradle at {gradle_dir}")
        return executable

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    archive = TOOLS_DIR / f"gradle-{GRADLE_VERSION}-bin.zip"
    log(f"Gradle was not found. Downloading Gradle {GRADLE_VERSION} from {GRADLE_URL}")
    urllib.request.urlretrieve(GRADLE_URL, archive)
    log("Extracting Gradle")
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(TOOLS_DIR)
    archive.unlink(missing_ok=True)
    executable = gradle_executable(gradle_dir)
    if executable is None:
        raise RuntimeError("Downloaded Gradle, but the Gradle executable was not found in the archive.")
    return executable


def ensure_gradle() -> Path:
    gradle = gradle_executable()
    return gradle if gradle is not None else download_gradle()


def sdkmanager_executable(sdk_dir: Path) -> Path:
    executable = "sdkmanager.bat" if platform.system() == "Windows" else "sdkmanager"
    return sdk_dir / "cmdline-tools" / "latest" / "bin" / executable


def download_commandline_tools(sdk_dir: Path = ANDROID_SDK_DIR) -> Path:
    sdkmanager = sdkmanager_executable(sdk_dir)
    if sdkmanager.exists():
        log(f"Using Android command-line tools at {sdkmanager.parent}")
        return sdkmanager

    system = platform.system()
    url = COMMANDLINE_TOOLS_URLS.get(system)
    if url is None:
        raise RuntimeError(f"Automatic Android command-line tools download is not configured for {system}.")

    archive = TOOLS_DIR / "android-commandline-tools.zip"
    extract_dir = TOOLS_DIR / "android-commandline-tools-raw"
    latest_dir = sdk_dir / "cmdline-tools" / "latest"
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    if latest_dir.exists():
        shutil.rmtree(latest_dir)

    log(f"Downloading Android command-line tools from {url}")
    urllib.request.urlretrieve(url, archive)
    log("Extracting Android command-line tools")
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(extract_dir)
    archive.unlink(missing_ok=True)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extract_dir / "cmdline-tools"), str(latest_dir))
    shutil.rmtree(extract_dir, ignore_errors=True)
    if not sdkmanager.exists():
        raise RuntimeError("Downloaded Android command-line tools, but sdkmanager was not found.")
    return sdkmanager


def write_local_properties(sdk_dir: Path) -> None:
    sdk_path = str(sdk_dir.resolve()).replace("\\", "/")
    (ROOT / "android" / "local.properties").write_text(f"sdk.dir={sdk_path}\n", encoding="utf-8")


def ensure_android_sdk(env: dict[str, str]) -> Path:
    configured = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT")
    sdk_dir = Path(configured) if configured else ANDROID_SDK_DIR
    platform_dir = sdk_dir / "platforms" / f"android-{ANDROID_COMPILE_SDK}"
    build_tools_dir = sdk_dir / "build-tools" / ANDROID_BUILD_TOOLS
    if platform_dir.exists() and build_tools_dir.exists():
        write_local_properties(sdk_dir)
        return sdk_dir

    sdkmanager = download_commandline_tools(sdk_dir)
    env["ANDROID_HOME"] = str(sdk_dir)
    env["ANDROID_SDK_ROOT"] = str(sdk_dir)
    licenses = "y\n" * 100
    log("Accepting Android SDK licenses")
    run([str(sdkmanager), "--sdk_root", str(sdk_dir), "--licenses"], env=env, input_text=licenses)
    log("Installing Android SDK packages needed to build the tablet APK")
    run(
        [
            str(sdkmanager),
            "--sdk_root",
            str(sdk_dir),
            "platform-tools",
            f"platforms;android-{ANDROID_COMPILE_SDK}",
            f"build-tools;{ANDROID_BUILD_TOOLS}",
        ],
        env=env,
    )
    write_local_properties(sdk_dir)
    return sdk_dir


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


def maybe_build_apk(env: dict[str, str]) -> Path | None:
    apk = existing_apk()
    if apk is not None:
        copied = copy_apk_to_dist(apk)
        log(f"Tablet APK ready: {copied}")
        return copied

    android_project = ROOT / "android"
    log("No APK found. Preparing Android build tools so the tablet app can be installed automatically.")
    try:
        gradle = ensure_gradle()
        sdk_dir = ensure_android_sdk(env)
        env["ANDROID_HOME"] = str(sdk_dir)
        env["ANDROID_SDK_ROOT"] = str(sdk_dir)
        log("Building the tablet APK with Gradle.")
        run([str(gradle), ":app:assembleDebug"], cwd=android_project, env=env)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        log(f"APK build failed: {exc}. Continuing without APK auto-install.")
        return None

    apk = existing_apk()
    if apk is None:
        log("Gradle finished but APK output was not found. Continuing without APK auto-install.")
        return None
    copied = copy_apk_to_dist(apk)
    log(f"Tablet APK ready: {copied}")
    return copied


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
    env = env_with_tools(tools)
    if not args.skip_apk_build:
        maybe_build_apk(env)

    launcher_command = [str(python), "-m", "second_monitor", *args.launcher_args]
    log("Starting automatic launcher. Connect the tablet and accept the USB debugging prompt.")
    run(launcher_command, env=env)


if __name__ == "__main__":
    main()
