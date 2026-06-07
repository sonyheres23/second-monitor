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


def test_install_python_requirements_installs_runtime_deps_without_editable_install(tmp_path: Path, monkeypatch) -> None:
    bootstrap = load_bootstrap()
    commands: list[list[str]] = []
    monkeypatch.setattr(bootstrap, "VENV_DIR", tmp_path)
    monkeypatch.setattr(bootstrap, "run", lambda command, **kwargs: commands.append(command))

    bootstrap.install_python_requirements(tmp_path / "python")

    assert [str(tmp_path / "python"), "-m", "pip", "install", "--upgrade", "pip"] in commands
    assert [str(tmp_path / "python"), "-m", "pip", "install", "mss>=9.0.1", "pillow>=10.0.0"] in commands
    assert all("-e" not in command for command in commands)
    assert (tmp_path / ".second-monitor-installed").read_text(encoding="utf-8") == "installed\n"


def test_maybe_build_apk_downloads_tools_and_copies_output(tmp_path: Path, monkeypatch) -> None:
    bootstrap = load_bootstrap()
    output_apk = tmp_path / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    output_apk.parent.mkdir(parents=True)
    commands: list[list[str]] = []

    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    monkeypatch.setattr(bootstrap, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(bootstrap, "ensure_gradle", lambda: tmp_path / "gradle" / "bin" / "gradle")
    monkeypatch.setattr(bootstrap, "ensure_android_sdk", lambda env: tmp_path / "android-sdk")

    def fake_run(command, **kwargs):
        commands.append(command)
        output_apk.write_bytes(b"apk")

    monkeypatch.setattr(bootstrap, "run", fake_run)

    apk = bootstrap.maybe_build_apk({})

    assert apk == tmp_path / "dist" / bootstrap.APK_NAME
    assert apk.read_bytes() == b"apk"
    assert commands == [[str(tmp_path / "gradle" / "bin" / "gradle"), ":app:assembleDebug"]]
