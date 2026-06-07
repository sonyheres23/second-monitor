from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk

from .autostart import AutoStartConfig, run_auto


class LauncherApp(tk.Tk):
    """Small GUI intended to be packaged as the Windows EXE."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Second Monitor USB")
        self.geometry("720x460")
        self._messages: queue.Queue[str] = queue.Queue()
        self._worker: threading.Thread | None = None

        self.status = tk.StringVar(value="Connect your tablet with USB debugging enabled, then press Start.")
        ttk.Label(self, text="Second Monitor USB", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, textvariable=self.status, wraplength=680).pack(anchor="w", padx=16, pady=(0, 12))
        self.start_button = ttk.Button(self, text="Start automatic setup", command=self.start)
        self.start_button.pack(anchor="w", padx=16, pady=(0, 12))
        self.log_box = tk.Text(self, height=18, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.after(200, self._drain_messages)

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self.start_button.configure(state="disabled")
        self._worker = threading.Thread(target=self._run, name="second-monitor-autostart", daemon=True)
        self._worker.start()

    def _run(self) -> None:
        try:
            run_auto(AutoStartConfig(), log=self._messages.put)
        except Exception as exc:  # noqa: BLE001 - GUI must show actionable startup failures.
            self._messages.put(f"ERROR: {exc}")
            self._messages.put("Fix the issue above, then restart this app.")

    def _drain_messages(self) -> None:
        while True:
            try:
                message = self._messages.get_nowait()
            except queue.Empty:
                break
            self.status.set(message)
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
        self.after(200, self._drain_messages)


def main() -> None:
    LauncherApp().mainloop()


if __name__ == "__main__":
    main()
