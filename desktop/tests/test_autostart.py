from pathlib import Path

from second_monitor.autostart import AutoStartConfig, find_tablet_apk, install_apk_if_available


def test_find_tablet_apk_uses_explicit_path(tmp_path: Path) -> None:
    apk = tmp_path / "tablet.apk"
    apk.write_bytes(b"apk")

    assert find_tablet_apk(apk) == apk


def test_find_tablet_apk_returns_none_when_missing(tmp_path: Path) -> None:
    assert find_tablet_apk(tmp_path / "missing.apk") is None


def test_install_apk_skips_when_no_apk(monkeypatch) -> None:
    monkeypatch.setattr("second_monitor.autostart.find_tablet_apk", lambda explicit_path=None: None)
    messages: list[str] = []

    installed = install_apk_if_available(AutoStartConfig(), log=messages.append)

    assert installed is None
    assert "Tablet APK was not found" in messages[-1]
