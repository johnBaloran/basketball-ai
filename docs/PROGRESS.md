# Project Progress Tracker

**Tracker owner:** AI agent updates; project owner approves acceptance.  
**Rule:** There is exactly one active implementation task.

## Current status

- **Overall phase:** Phase 0 — Project foundation and discovery
- **Current task:** 0.1 — Inspect the existing repository/environment and document the actual starting state
- **Task status:** READY FOR OWNER REVIEW
- **Active branch:** `task/0.1-starting-state` (baseline docs import on `main`: `24d6dfa`)
- **Last accepted commit:** None yet (0.1 awaiting owner acceptance)
- **Current blocker:** None for 0.1. Owner inputs needed before 0.4 (see below).
- **Next task:** 0.2 (project structure, Python environment, formatting/linting/test commands). Do not start until 0.1 is accepted.

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
| Project documentation initialized | Imported | `24d6dfa` | Documentation package committed as received |
| 0.1 Starting state | READY FOR OWNER REVIEW | branch `task/0.1-starting-state` | `docs/STARTING_STATE.md` |

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
