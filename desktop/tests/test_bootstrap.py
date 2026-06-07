from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_PATH = ROOT / "run_second_monitor.py"


def load_bootstrap():
    spec = importlib.util.spec_from_file_location("run_second_monitor", BOOTSTRAP_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_existing_apk_finds_dist_file(tmp_path: Path, monkeypatch) -> None:
    bootstrap = load_bootstrap()
    apk = tmp_path / "dist" / bootstrap.APK_NAME
    apk.parent.mkdir()
    apk.write_bytes(b"apk")
    monkeypatch.setattr(bootstrap, "DIST_DIR", apk.parent)
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)

    assert bootstrap.existing_apk() == apk


def test_env_with_tools_prepends_adb_and_sets_pythonpath(tmp_path: Path, monkeypatch) -> None:
    bootstrap = load_bootstrap()
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    monkeypatch.setenv("PATH", "old-path")

    env = bootstrap.env_with_tools(tmp_path / "platform-tools")

    assert env["PATH"].startswith(str(tmp_path / "platform-tools"))
    assert env["PYTHONPATH"] == str(tmp_path / "desktop")
