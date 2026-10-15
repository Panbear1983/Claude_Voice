#!/bin/bash
# Voice Desk phone receiver — normally started at login by launchd (see install_receiver.sh).
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python receiver.py
