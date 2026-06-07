#!/usr/bin/env bash
set -euo pipefail

# Starter helper for X11 systems. Many Wayland compositors and Windows/macOS
# need a different virtual display driver.
MODE_NAME="${MODE_NAME:-1280x720_60.00}"
WIDTH="${WIDTH:-1280}"
HEIGHT="${HEIGHT:-720}"
OUTPUT="${OUTPUT:-VIRTUAL1}"
RIGHT_OF="${RIGHT_OF:-$(xrandr --query | awk '/ connected primary/{print $1; exit} / connected/{print $1; exit}')}"

if ! command -v xrandr >/dev/null 2>&1; then
  echo "xrandr is required for this helper" >&2
  exit 1
fi

if ! xrandr --query | grep -q "^${OUTPUT}"; then
  echo "Output ${OUTPUT} was not found. Check xrandr --query for your virtual output name." >&2
  exit 1
fi

if ! xrandr | grep -q "${MODE_NAME}"; then
  read -r _ _ modeline < <(cvt "$WIDTH" "$HEIGHT" 60 | awk '/Modeline/{print $1, $2, substr($0, index($0,$3))}')
  xrandr --newmode "$MODE_NAME" $modeline
  xrandr --addmode "$OUTPUT" "$MODE_NAME"
fi

xrandr --output "$OUTPUT" --mode "$MODE_NAME" --right-of "$RIGHT_OF"
echo "Enabled ${OUTPUT} as ${WIDTH}x${HEIGHT} to the right of ${RIGHT_OF}."
