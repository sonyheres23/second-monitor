#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH="${PYTHONPATH:-desktop}" python3 -m second_monitor "$@"
