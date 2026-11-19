#!/usr/bin/env bash
# Every check a task must pass before committing (AGENT_RULES §4).
# Uses whichever Python environment is active (Colab: after `pip install -e . --group dev`).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"
"$PY" scripts/privacy_guard.py
"$PY" -m ruff format --check .
"$PY" -m ruff check .
"$PY" -m mypy
"$PY" -m pytest
