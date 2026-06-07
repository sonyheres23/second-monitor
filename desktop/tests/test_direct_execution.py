from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "desktop" / "second_monitor"


def test_autostart_script_can_show_help_when_run_directly() -> None:
    result = subprocess.run(
        [sys.executable, "autostart.py", "--help"],
        cwd=PACKAGE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "One-command USB tablet second monitor launcher" in result.stdout


def test_gui_script_can_be_import_checked_when_run_directly() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import runpy; runpy.run_path('gui.py', run_name='not_main')"],
        cwd=PACKAGE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
