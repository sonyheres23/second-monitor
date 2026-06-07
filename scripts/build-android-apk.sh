#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../android"
gradle :app:assembleDebug
mkdir -p ../dist
cp app/build/outputs/apk/debug/app-debug.apk ../dist/SecondMonitorTablet.apk
echo "APK created: dist/SecondMonitorTablet.apk"
