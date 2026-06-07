# Second Monitor USB Prototype

This repository is a starter app for using an Android tablet as a USB-connected second monitor for a laptop.
It uses Android USB debugging and `adb reverse` so the tablet app can talk to a desktop companion at `127.0.0.1:5000` without Wi-Fi.

## Important reality check

The app can automate USB detection, APK installation, `adb reverse`, streaming, and touch forwarding. A laptop still needs a real virtual display driver or operating-system virtual output before the tablet can be treated by the OS as a true second monitor.

- Linux X11: try `scripts/setup-x11-virtual-monitor.sh` if your graphics stack exposes `VIRTUAL1` or a similar output.
- Linux Wayland: configure a compositor-specific virtual output or use a desktop portal/capture approach.
- Windows: install an indirect/virtual display driver first, then run the EXE launcher from this repo.
- macOS: install a virtual display solution first, then run the desktop launcher.

Without a virtual display, this project can still mirror/stream a screen to the tablet, but Windows/Linux/macOS will not list the tablet itself as a native monitor.

## What is included

- `desktop/second_monitor`: a Python desktop companion that exposes:
  - `/stream` for an MJPEG display stream.
  - `/frame` for a single frame.
  - `/touch` for tablet touch events mapped to the laptop's virtual monitor rectangle.
- `desktop/second_monitor/autostart.py`: one-command automation for tablet detection, APK install, USB tunnel setup, and server startup.
- `desktop/second_monitor/gui.py`: a small GUI intended to be packaged as the Windows EXE.
- `android/`: a minimal Android app that opens the USB-forwarded stream and sends touches back to the laptop.
- `scripts/start-auto.sh`: starts the automatic desktop launcher from source.
- `scripts/build-android-apk.sh`: builds `dist/SecondMonitorTablet.apk`.
- `scripts/build-windows-exe.ps1`: builds `dist/SecondMonitorUSB.exe` on Windows.
- `scripts/setup-x11-virtual-monitor.sh`: optional helper for X11 systems that expose a virtual output such as `VIRTUAL1`.

## Easiest source checkout flow

1. Enable Developer Options on the Android tablet.
2. Enable USB debugging.
3. Connect the tablet to the laptop with USB.
4. Accept the USB debugging trust prompt on the tablet.
5. Confirm the laptop can see the tablet:

   ```bash
   adb devices
   ```

6. Create a Python environment and install optional capture dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e '.[capture]'
   ```

7. Build and copy the tablet APK into `dist/`:

   ```bash
   scripts/build-android-apk.sh
   ```

8. Start the automatic launcher:

   ```bash
   scripts/start-auto.sh
   ```

The automatic launcher waits for one authorized tablet, installs `dist/SecondMonitorTablet.apk` when present, configures `adb reverse`, tries to open the tablet app, and starts the stream server.

## One-click Windows EXE build

Run this from PowerShell on Windows after Android platform-tools and Python are installed:

```powershell
scripts\build-android-apk.sh       # from Git Bash/WSL, or build the APK in Android Studio
scripts\build-windows-exe.ps1
```

The output is:

- `dist/SecondMonitorUSB.exe`: desktop launcher.
- `dist/SecondMonitorTablet.apk`: tablet app, if the APK build succeeded.

For the easiest end-user folder, keep these files together:

```text
SecondMonitorUSB.exe
SecondMonitorTablet.apk
adb.exe
AdbWinApi.dll
AdbWinUsbApi.dll
```

Then the normal use is:

1. Install a virtual display driver on the laptop if you need the OS to recognize a real second monitor.
2. Connect the tablet by USB.
3. Accept the USB debugging prompt.
4. Double-click `SecondMonitorUSB.exe`.
5. Open **Second Monitor USB** on the tablet if it does not open automatically.

## Run on Linux manually

From the repository root:

```bash
source .venv/bin/activate
PYTHONPATH=desktop scripts/start-linux.sh
```

By default, touch is mapped to a 1280×720 virtual monitor located at `x=1920, y=0` on the laptop desktop. Override those values when your virtual display is elsewhere:

```bash
TARGET_X=2560 TARGET_Y=0 TARGET_WIDTH=1920 TARGET_HEIGHT=1080 PYTHONPATH=desktop scripts/start-linux.sh
```

## Build and install the Android app manually

The `android/` folder is a standard Gradle Android project. With Android SDK installed:

```bash
cd android
gradle :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Launch **Second Monitor USB** on the tablet after the desktop companion is running.

## Touch support

The desktop companion maps tablet coordinates to the configured virtual monitor rectangle. On Linux, it uses `xdotool` when installed:

```bash
sudo apt install xdotool
```

Without `xdotool`, `/touch` still accepts events and reports mapped coordinates, but it does not move/click the laptop pointer.

## Persian quick start / راهنمای سریع فارسی

1. روی تبلت Developer Options و USB debugging را روشن کن.
2. تبلت را با کابل USB وصل کن و پیام Allow USB debugging را قبول کن.
3. اگر ویندوز می‌خواهی، `SecondMonitorUSB.exe`، فایل APK و فایل‌های `adb.exe` را در یک پوشه بگذار و EXE را اجرا کن.
4. اگر از سورس اجرا می‌کنی، این دستور را بزن:

   ```bash
   scripts/start-auto.sh
   ```

5. اگر می‌خواهی سیستم‌عامل واقعاً تبلت را به عنوان مانیتور دوم بشناسد، باید قبلش virtual display driver نصب/فعال باشد؛ اپ فقط USB، نصب APK، استریم و تاچ را اتومات می‌کند.

## Development checks

```bash
python -m pytest
python -m compileall desktop
```
