from __future__ import annotations

import shutil
import subprocess


class InputInjector:
    """Inject pointer actions into the Linux desktop using xdotool when available."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._xdotool = shutil.which("xdotool")

    @property
    def available(self) -> bool:
        return self.enabled and self._xdotool is not None

    def move(self, x: int, y: int) -> bool:
        if not self.available:
            return False
        subprocess.run([self._xdotool or "xdotool", "mousemove", str(x), str(y)], check=False)
        return True

    def tap(self, x: int, y: int) -> bool:
        if not self.available:
            return False
        subprocess.run([self._xdotool or "xdotool", "mousemove", str(x), str(y), "click", "1"], check=False)
        return True
