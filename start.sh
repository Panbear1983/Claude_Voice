#!/bin/bash
# Claude Voice — double-click (or run) to open the listening window.
# First run: macOS asks whether Terminal may use the microphone. Click Allow.
cd "$(dirname "$0")" || exit 1
[ -x .venv/bin/python ] || { echo "missing .venv — run: uv venv .venv --python 3.11 && uv pip install --python .venv/bin/python -r requirements.txt"; exit 1; }
exec .venv/bin/python app.py
