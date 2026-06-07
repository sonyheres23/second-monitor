from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .adb import AdbError, connected_devices, reverse_port, run_adb
from .geometry import Rect
from .server import MonitorServer, MonitorState

LogCallback = Callable[[str], None]


@dataclass(frozen=True)
class AutoStartConfig:
    """Configuration for the one-click desktop launcher."""

    host: str = "127.0.0.1"
    port: int = 5000
    fps: int = 15
    target: Rect = Rect(1920, 0, 1280, 720)
    install_apk: bool = True
    apk_path: Path | None = None
    inject_touch: bool = True
    wait_timeout_seconds: int = 45


def default_apk_candidates() -> list[Path]:
    """Return likely APK locations for source checkouts and frozen EXE bundles."""

    candidates = [
        Path.cwd() / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk",
        Path.cwd() / "SecondMonitorTablet.apk",
        Path(sys.executable).resolve().parent / "SecondMonitorTablet.apk",
    ]
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / "SecondMonitorTablet.apk")
    return candidates


def find_tablet_apk(explicit_path: Path | None = None) -> Path | None:
    """Find the tablet APK that should be installed automatically."""

    candidates = [explicit_path] if explicit_path is not None else default_apk_candidates()
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def wait_for_tablet(timeout_seconds: int, log: LogCallback = print) -> str:
    """Wait until exactly one authorized Android device is visible to adb."""

    deadline = time.monotonic() + timeout_seconds
    last_devices: list[str] = []
    while time.monotonic() < deadline:
        last_devices = connected_devices()
        if len(last_devices) == 1:
            return last_devices[0]
        if len(last_devices) > 1:
            raise AdbError("More than one Android device is connected. Connect only the tablet you want to use.")
        log("Waiting for the tablet. Connect USB and accept the USB debugging prompt if it appears...")
        time.sleep(2)
    raise AdbError(f"No authorized tablet found after {timeout_seconds} seconds. Last adb devices result: {last_devices!r}")


def install_apk_if_available(config: AutoStartConfig, log: LogCallback = print) -> Path | None:
    """Install the bundled APK when it exists, otherwise tell the user what remains manual."""

    if not config.install_apk:
        log("APK auto-install is disabled.")
        return None
    apk = find_tablet_apk(config.apk_path)
    if apk is None:
        log("Tablet APK was not found, so installation is skipped. Build it with scripts/build-android-apk.sh first.")
        return None
    log(f"Installing tablet app: {apk}")
    run_adb(["install", "-r", str(apk)])
    return apk


def launch_tablet_app(log: LogCallback = print) -> bool:
    """Try to open the tablet client after install and USB reverse setup."""

    try:
        run_adb(["shell", "monkey", "-p", "com.example.secondmonitor", "1"])
    except AdbError as exc:
        log(f"Could not auto-open the tablet app: {exc}")
        return False
    log("Tablet app launch requested.")
    return True


def create_auto_server(config: AutoStartConfig) -> MonitorServer:
    """Create the desktop stream server used by the automatic launcher."""

    state = MonitorState(config.target, inject_touch=config.inject_touch)
    return MonitorServer((config.host, config.port), state, max(1, config.fps))


def run_auto(config: AutoStartConfig, log: LogCallback = print) -> None:
    """Run the full automatic setup that an EXE can launch with one click."""

    log("Starting Second Monitor USB automatic setup...")
    device = wait_for_tablet(config.wait_timeout_seconds, log=log)
    log(f"Tablet connected: {device}")
    install_apk_if_available(config, log=log)
    reverse_port(config.port)
    log(f"USB tunnel ready: tablet 127.0.0.1:{config.port} -> laptop {config.host}:{config.port}")
    launch_tablet_app(log=log)
    log("Open the Second Monitor USB app on the tablet manually if it did not open automatically.")
    server = create_auto_server(config)
    log(f"Streaming on http://{config.host}:{config.port}/stream")
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-command USB tablet second monitor launcher.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")))
    parser.add_argument("--fps", type=int, default=int(os.environ.get("FPS", "15")))
    parser.add_argument("--target-x", type=int, default=int(os.environ.get("TARGET_X", "1920")))
    parser.add_argument("--target-y", type=int, default=int(os.environ.get("TARGET_Y", "0")))
    parser.add_argument("--target-width", type=int, default=int(os.environ.get("TARGET_WIDTH", "1280")))
    parser.add_argument("--target-height", type=int, default=int(os.environ.get("TARGET_HEIGHT", "720")))
    parser.add_argument("--apk", type=Path, default=None, help="Path to the tablet APK to install automatically.")
    parser.add_argument("--no-install-apk", action="store_true")
    parser.add_argument("--no-touch-injection", action="store_true")
    parser.add_argument("--wait-timeout", type=int, default=45)
    return parser


def config_from_args(args: argparse.Namespace) -> AutoStartConfig:
    return AutoStartConfig(
        host=args.host,
        port=args.port,
        fps=args.fps,
        target=Rect(args.target_x, args.target_y, args.target_width, args.target_height),
        install_apk=not args.no_install_apk,
        apk_path=args.apk,
        inject_touch=not args.no_touch_injection,
        wait_timeout_seconds=args.wait_timeout,
    )


def main() -> None:
    args = build_parser().parse_args()
    run_auto(config_from_args(args))


if __name__ == "__main__":
    main()
