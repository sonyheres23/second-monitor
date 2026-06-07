$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
python -m venv .venv-win
. .\.venv-win\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[capture,packaging]"

$pyinstallerArgs = @(
    "--name", "SecondMonitorUSB",
    "--onefile",
    "--windowed",
    "--collect-submodules", "second_monitor"
)

if (Test-Path "dist\SecondMonitorTablet.apk") {
    $pyinstallerArgs += @("--add-data", "dist\SecondMonitorTablet.apk;.")
}

$pyinstallerArgs += @("desktop\second_monitor\gui.py")
python -m PyInstaller @pyinstallerArgs

Write-Host "EXE created: dist\SecondMonitorUSB.exe"
Write-Host "Copy Android platform-tools adb.exe next to the EXE or add adb to PATH."
