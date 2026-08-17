#!/usr/bin/env sh
set -eu
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m realistic_dance_avatar.cli download-model
printf '%s\n' "Setup complete. Run scripts/run_macos_linux.sh"
