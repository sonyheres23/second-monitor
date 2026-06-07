#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"
TARGET_X="${TARGET_X:-1920}"
TARGET_Y="${TARGET_Y:-0}"
TARGET_WIDTH="${TARGET_WIDTH:-1280}"
TARGET_HEIGHT="${TARGET_HEIGHT:-720}"
FPS="${FPS:-15}"

python3 -m second_monitor.server \
  --port "$PORT" \
  --fps "$FPS" \
  --target-x "$TARGET_X" \
  --target-y "$TARGET_Y" \
  --target-width "$TARGET_WIDTH" \
  --target-height "$TARGET_HEIGHT"
