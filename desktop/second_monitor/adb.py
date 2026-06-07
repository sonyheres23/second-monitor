from __future__ import annotations

import shutil
import subprocess


class AdbError(RuntimeError):
    """Raised when adb is missing or fails."""


def adb_path() -> str:
    path = shutil.which("adb")
    if path is None:
        raise AdbError("adb was not found. Install Android platform-tools and enable USB debugging.")
    return path


def run_adb(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [adb_path(), *args]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "adb command failed"
        raise AdbError(message)
    return result


def reverse_port(port: int) -> None:
    run_adb(["reverse", f"tcp:{port}", f"tcp:{port}"])


def connected_devices() -> list[str]:
    result = run_adb(["devices"])
    devices: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices
