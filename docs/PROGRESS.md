# Project Progress Tracker

**Tracker owner:** AI agent updates; project owner approves acceptance.  
**Rule:** There is exactly one active implementation task.

## Current status

- **Overall phase:** Phase 0 — Project foundation and discovery
- **Current task:** offline build (DEC-010): everything that needs no owner input, built in parallel
- **Task status:** READY FOR OWNER REVIEW (0.3, 0.5 and the offline build); 0.4 waits on owner inputs
- **Active branch:** `build/offline-foundations` (merged to `main` so Colab notebooks get it)
- **Last accepted commit:** `877f2e4` (0.2)
- **Current blocker:** footage. Every remaining step needs clips in Drive (0.4) or league decisions (`docs/EVENT_DEFINITIONS.md` §7).
- **Next:** owner provides clips → run `bball-inventory` (0.4) → run `notebooks/01_baseline_detection.ipynb` on clips from each gym (1.3–1.7 evaluation).

### Offline build report (DEC-010)
Built and tested with **synthetic data only**. Nothing here claims accuracy on real footage.

| Area | Plan task | Module | What it does |
|---|---|---|---|
| Contracts | DEC-007 | `contracts.py`, `schemas/*.json`, `bball-schemas` | Manifest, events and box score models (Recess field names, strict validation); JSON Schemas kept in sync by a test |
| Event definitions | 0.5 | `docs/EVENT_DEFINITIONS.md` | Event types, status lifecycle, confidence, identity and box score rules; PROPOSED league choices plus owner questions |
| Box score | 5.4 | `boxscore.py` | Confirmed events only; unattributed events count for the team; roster/team/relation checks; statistical invariants |
| Identity | 3.3–3.5 | `identity.py` | Multi-frame jersey voting, roster constraint, shared-number handling, overlap conflicts, player→tracks registry |
| Video | 1.1 | `video.py` | ffprobe metadata, streaming frames (constant memory), frame-accurate clip cutting (audio dropped by default) |
| Inventory | 0.4 tooling | `inventory.py`, `bball-inventory` | Scans footage, stable video ids, gym from folder, date from file name, quality flags, per-gym summary |
| Tracking | 1.5, 4.1 | `tracking.py` | Detector interface, IoU tracker baseline, ball holder, possession segments and changes |
| Teams | 3.1 | `teams.py` | Torso colour, 2-means team split named from colour hints, referee rejection, per-track vote |
| Court | 4.4 | `court.py` | Homography image→court feet, 2PT/3PT from shooter location with per-gym line config |
| Possession events | 4.6–4.8 | `possession_events.py` | Pass, steal and rebound candidates from possession changes (always pending review) |
| Evaluation | 2.4 | `evaluation.py` | Per-type precision/recall/F1 with time tolerance, team accuracy, player-attribution precision |
| Pipeline | 1.6 | `pipeline.py`, `bball-run`, `detectors.py` | Frames → detector → tracker → possession; writes tracks.jsonl, possession.json, annotated.mp4; YOLO adapter (`cv` extra) |
| Colab | 1.3 | `notebooks/01_baseline_detection.ipynb` | Runs the pipeline with pretrained YOLO on a Drive clip and shows the result |

- **Evidence:** GitHub Actions run 44692434658 (CPython 3.12.16, real ffmpeg on synthetic test video): privacy guard ok; `ruff format --check` "50 files already formatted"; `ruff check` "All checks passed!"; `mypy` strict "Success: no issues found in 32 source files"; `pytest` "87 passed".
- **Not tested:** anything on real footage; the YOLO adapter and both Colab notebooks (they need a GPU session and clips); shot detection (needs a hoop/ball model trained on our footage).
- **Not built (needs owner input or footage):** shot attempt/make detection, jersey OCR model, court keypoint model, fine-tuning, the review UI and league-app integration.

### Task 0.3 report
- **Implemented:**
  - `src/basketball_ai/privacy_guard.py`: standard library only and Python 3.9-compatible. It blocks media, frames, weights, data/tabular files, files over 1 MB, notebooks with outputs, and secret patterns, with an explicit `.private-data-allow` list for exceptions.
  - `scripts/privacy_guard.py` wrapper, `.githooks/pre-commit`, `scripts/install-hooks.sh`.
  - The guard was added to `scripts/check.sh`, so CI runs it on all tracked files.
  - `src/basketball_ai/paths.py`: `BBALL_DATA_DIR`, which refuses paths inside the repo, plus the standard subfolders.
  - Tests in `tests/test_privacy_guard.py` and `tests/test_paths.py`.
  - `docs/DATA_HANDLING.md` (what's private, enforcement, Drive layout, secrets, external services, incident steps); extra `.gitignore` patterns.
- **Executed locally (no installs):**
  - `/usr/bin/python3` (3.9) and `python3` (3.15) `scripts/privacy_guard.py`: "privacy guard: ok", exit 0.
  - Hook enabled (`core.hooksPath=.githooks`). A test commit with a fake `leak.mp4` and a fake GitHub token was **blocked**; output listed both files. Nothing was committed, and the files were removed.
- **The guard caught its own test file:** the first commit attempt was blocked because the fake samples in `tests/test_privacy_guard.py` matched the database-URL and private-key patterns. The test strings are now built in pieces.
- **CI (GitHub Actions run 44631288593, CPython 3.12.16):** privacy guard "ok" on all tracked files; `ruff format --check` "22 files already formatted"; `ruff check` "All checks passed!"; `mypy` strict "Success: no issues found in 7 source files"; `pytest` "25 passed in 0.27s".
- **Earlier CI failures, fixed:** run 44630900663 (3 files needed formatting), run 44631139658 (unused `noqa`). Actions were also updated to checkout@v5 and setup-python@v6 (Node 20 deprecation warning).
- **Not tested:** the hook on a fresh clone of another machine (it needs only git and python3); the Drive folder itself (created in task 0.4).

### Task 0.2 report
- **Implemented:** `pyproject.toml` (Python >= 3.12; dev group ruff, mypy, pytest; strict mypy; `bball-doctor` entry point); `src/basketball_ai/` package with `doctor.py` (runtime, Python, ffmpeg, ffprobe, GPU); `tests/test_doctor.py` (6 tests: version, Python, missing ffmpeg fails, no GPU never fails, GPU name reported, Colab detected); `scripts/check.sh` (format check, lint, mypy, pytest); `notebooks/00_setup_check.ipynb` (clone with a token from Colab Secrets, install, doctor, checks); `.env.example`; README setup for Colab; DEC-008.
- **Executed (local, no installs):** `python3 -m py_compile` on doctor and tests (ok). `PYTHONPATH=src python3 -m basketball_ai.doctor` ran: python 3.15.2 ok, ffmpeg/ffprobe MISSING (expected on this Mac), gpu info "none", exit 1 (correct, since required tools are missing).
- **Executed in GitHub Actions** (run 44612564972 on `task/0.2-python-env`, ubuntu-latest, CPython 3.12.16): `bball-doctor` reported python 3.12.16 ok, ffmpeg 8.0.1 ok, ffprobe 8.0.1 ok, gpu info "none"; `ruff format --check` passed; `ruff check` "All checks passed!"; `mypy` (strict) "Success: no issues found in 3 source files"; `pytest` "6 passed in 0.10s".
- **Earlier failure, fixed:** run 44612396472 failed `ruff format --check` (2 files: `doctor.py` and the notebook). Fixed in the next commit.
- **Not executed:** the Colab notebook hasn't been run (it needs a person to click Run all). It's only needed for GPU/video work from Phase 1 on; code checks now run automatically in CI.
- **Repo:** created private, author email rewritten to the GitHub noreply address (force-pushed with owner approval), then made public (DEC-009).
- **Environment attempts (evidence for DEC-008):** `brew install uv ffmpeg` began compiling LLVM from source (no prebuilt packages for macOS 13.5) and was stopped. It left `python@3.15` and build dependencies installed plus an empty `llvm` keg (see `STARTING_STATE.md` note). The `curl … | sh` uv installer was blocked by the agent's permission policy.

### Task 0.1 report
- **Investigated:** this machine (OS, CPU/GPU, RAM, disk, Python, ffmpeg, env managers, Docker); the Recess app models that the project will later connect to (read only); footage location; the reference repository (preliminary, from its README and source).
- **Changed:** created standalone repo (DEC-003), `.gitignore` for video/weights/datasets/secrets, `docs/STARTING_STATE.md` (full report), `docs/DECISION_LOG.md` (DEC-003 to DEC-007), `docs/PROJECT_PLAN.md` (Phase 1 exit gate and a free-GPU risk row per DEC-005/006), this file.
- **Commands and results:** listed with evidence in `docs/STARTING_STATE.md` §1–§4 (`sw_vers`, `sysctl`, `system_profiler`, `df -h`, `python3 --version`, `which ffmpeg ffprobe uv conda docker brew`, `grep -n` on Recess model files).
- **Key findings:** Apple M2 / 16 GB / no CUDA / 27 GB free disk; only system Python 3.9.6; no ffmpeg, uv or Docker. Footage is on YouTube (quality unverified). Recess stores per-player totals plus made-shot digits, not attempts, OREB/DREB or events; jersey numbers are optional. The reference repo loads every frame into memory and has no jersey, shot or rebound logic.
- **Tests/evidence:** documentation-only task; no code, so no tests. `git ls-files` shows only markdown and `.gitignore`.
- **Limitations:** the reference repo wasn't cloned or run (task 1.2); no footage was viewed or measured (task 0.4); Recess was read, not modified.

### Owner inputs needed (before task 0.4)
- Which YouTube channel and videos, and confirmation that downloading them is permitted.
- Where clips and datasets will live (external drive or Google Drive) and how much space.
- Whether the 3 gyms and historical games should be entered in Recess (affects the video-to-roster mapping).
- Whether to delete the original untracked `recess/basketball-ai-project-docs/` folder now that this repo holds the docs.
- Reference repository link: **received** (`abdullahtarek/basketball_analysis`), to be inspected in task 1.2.

## Phase status

| Phase | Name | Status |
|---|---|---|
| 0 | Foundation and discovery | In progress (0.1 ready for review) |
| 1 | Video ingestion and baseline detection | Not started |
| 2 | Dataset and model improvement foundation | Not started |
| 3 | Team and player identity | Not started |
| 4 | Basketball event recognition | Not started |
| 5 | Human review and statistics engine | Not started |
| 6 | Production integration | Not started |
| 7 | Pilot and controlled rollout | Not started |

## Backlog

Only add tasks here; do not implement them until they become the single current task.

- Inventory representative MP4 footage from each gym.
- Confirm video permissions, storage, and compute budget.
- Define event/statistics rules with league owner.
- Establish dataset annotation and evaluation conventions.
- Define JSON Schemas for the clip/game manifest, events and box score (DEC-007).
- Make every frame reader stream frames, never load a whole video into memory (DEC-005; the reference repo's `read_video` loads all frames).
- Later, on the Recess side: add `fg2m, fg2a, fg3m, fg3a, ftm, fta, oreb, dreb` to basketball stat categories; optional `GameEvent` collection; admin review screen; idempotent event import (Phase 5/6).

## Task history

| Task | Status | Commit | Evidence |
|---|---|---|---|
| Project documentation initialized | Imported | `8e7f595` | Documentation package committed as received |
| 0.1 Starting state | Accepted (owner, 2026-11-17) | `42609ef` | `docs/STARTING_STATE.md` |
| 0.2 Environment and checks | Accepted (owner, 2026-11-19) | merged to `main` | GitHub Actions run 44612564972 (all checks pass) |
| 0.3 Data handling and secrets | READY FOR OWNER REVIEW | branch `task/0.3-data-handling` | GitHub Actions run 44631288593 (all checks pass) |
| Offline build (DEC-010) | READY FOR OWNER REVIEW | `build/offline-foundations` | GitHub Actions run 44692434658 (87 tests pass) |

## Required update at every task end

1. Current task and status.
2. What was investigated.
3. What changed (files).
4. Commands run and exact results.
5. Tests and evidence.
6. Commit hash and branch.
7. Remaining risks/limitations.
8. Blockers/owner decisions.
9. Next single task (do not start it).

The agent must not mark a task accepted. Use `READY FOR OWNER REVIEW` until the owner accepts.
