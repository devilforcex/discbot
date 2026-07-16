#!/bin/bash
# Dashboard Linux/macOS Start Script
cd "$(dirname "$0")"
source .venv/bin/activate
python -m bot.dashboard.dashboard
