# Basketball AI — Project Documentation

This repository contains the permanent project plan and operating rules for building the basketball video analysis and statistics platform with AI coding agents.

## Start here

1. Read `AGENT_RULES.md` before asking an agent to change code.
2. Read `docs/PROJECT_PLAN.md` for scope, architecture, phases, and milestones.
3. Read `docs/ARCHITECTURE.md` before changing system boundaries or data contracts.
4. Read `docs/PROGRESS.md` to find the current phase, task, blockers, and next action.
5. Read `docs/DECISION_LOG.md` before revisiting a settled technical decision.
6. Use `templates/TASK_TEMPLATE.md` for every implementation task.

## Source of truth

- Requirements and scope: `docs/PROJECT_PLAN.md`
- Current architecture: `docs/ARCHITECTURE.md`
- Current progress and next task: `docs/PROGRESS.md`
- Accepted technical decisions: `docs/DECISION_LOG.md`
- Data and evaluation policy: `docs/DATASET_AND_EVALUATION.md`
- Task instructions: `templates/TASK_TEMPLATE.md`
- Agent operating contract: `AGENT_RULES.md`

If code and documentation disagree, do not silently choose one. Report the conflict, identify the affected files, and ask for a decision unless the task explicitly authorizes updating the documentation to match an approved implementation.

## Project status

The project begins in discovery/baseline validation. No model accuracy, performance, or production readiness is assumed until measured on representative BallerTV footage.

## Checks run automatically

Every push runs format, lint, strict type checks and tests in GitHub Actions (`.github/workflows/checks.yml`). See the Actions tab.

## Setup: Google Colab (the only runtime, DEC-008)

Everything runs in free Google Colab: Python 3.12, ffmpeg, ffprobe and a T4 GPU are provided. Nothing is installed on the development Mac; it only edits files and runs git.

One-time setup:
1. Create a fine-grained GitHub token: GitHub > Settings > Developer settings > Fine-grained tokens. Repository access: only `basketball-ai`. Permissions: **Contents: Read-only**.
2. Open `notebooks/00_setup_check.ipynb` in Colab (File > Open notebook > GitHub, or the "Open in Colab" link).
3. Click the key icon (Secrets), add `GITHUB_TOKEN` with the token, and allow notebook access.

Every session: **Runtime > Change runtime type > T4 GPU**, then **Runtime > Run all**. The notebook:
- clones or updates the repo;
- installs the project with `pip install -e . --group dev`;
- runs `bball-doctor` (checks Python, ffmpeg, ffprobe and GPU);
- runs `scripts/check.sh` (format check, lint, strict type check, tests).

| Command (in Colab) | What it does |
|---|---|
| `!bball-doctor` | Runtime check |
| `!bash scripts/check.sh` | All checks; must pass before every commit |
| `!python -m ruff format .` | Format code |
| `!python -m pytest` | Tests only |

Private data stays out of git: clips, datasets and model weights live in Google Drive (`BBALL_DATA_DIR`; see `.env.example`). `.gitignore` blocks video, weights and `.env` files.
