# Starting State: Task 0.1 Investigation Report

**Task:** 0.1, inspect the existing repository and environment and document the actual starting state
**Date:** 2026-11-17
**Branch:** `task/0.1-starting-state`
**Method:** read-only inspection. Nothing was installed, downloaded or changed outside this repository.

---

## 1. Repository

| Item | Finding | Evidence |
|---|---|---|
| Project repo | New standalone repo at `~/Desktop/riseup-projects/basketball-ai` (DEC-003) | `git init`, baseline commit `24d6dfa` with the documentation package as received |
| Remote | None. Nothing is pushed anywhere. | `git remote -v` is empty |
| Code | None yet. The repo holds only documentation and `.gitignore`. | `git ls-files` |
| Original docs | Still present, untracked, at `recess/basketball-ai-project-docs/`. Left in place pending owner decision. | `git status` in recess shows `?? basketball-ai-project-docs/` |

`.gitignore` blocks video (`*.mp4`, `*.mov`, …), model weights (`*.pt`, `*.onnx`, …), pickles, dataset/clip folders and `.env*` files, per AGENT_RULES §4 and §8.

## 2. Development machine

| Item | Finding | Evidence |
|---|---|---|
| OS | macOS 13.5 (22G74) | `sw_vers` |
| CPU/GPU | Apple M2, integrated GPU with Metal 3. **No NVIDIA GPU and no CUDA.** PyTorch can use the Apple `mps` backend for small inference. | `sysctl machdep.cpu.brand_string`, `system_profiler SPDisplaysDataType` |
| RAM | 16 GB | `sysctl hw.memsize` |
| Free disk | 27 GB free of 228 GB (87% used) | `df -h ~` |
| Python | System Python 3.9.6 only | `python3 --version` |
| Video tools | ffmpeg / ffprobe **not installed** | `which ffmpeg ffprobe` |
| Env managers | uv, conda **not installed**; pip3 is the system one | `which uv conda pip3` |
| Docker | **Not installed** | `which docker` |
| Homebrew | Installed (`/opt/homebrew/bin/brew`) | `which brew` |

**Implications**
- Training and heavy inference can't run on this machine at useful speed. Per DEC-006 they move to free Google Colab or Kaggle GPUs.
- 27 GB of free disk can't hold the historical footage. One full 1080p game is likely several GB, and there are 150+ games. Work from short clips (DEC-005) and keep the source videos off this disk.
- Task 0.2 needs a modern Python (3.11+) environment and ffmpeg. Both are missing.

## 3. Footage

| Item | Finding |
|---|---|
| Location | On **YouTube** (owner answer, 2026-11-17). No local MP4s have been inventoried. |
| Format | Unverified. The docs assume BallerTV 1080p MP4, but YouTube re-encodes uploads, so the available bitrate and resolution must be measured (task 0.4). |
| Gyms | The docs state 3 gyms with one BallerTV camera each. This hasn't been verified from footage. |
| Permissions | Downloading from the league's own YouTube channel needs owner confirmation of the channel and videos, plus a data-handling note (task 0.4). |

## 4. Recess application (integration target, read only)

Recess is a pnpm/Turbo monorepo (Next.js 15 + MongoDB/Mongoose), last commit `c764a6a`. **This project doesn't import from or connect to Recess until Phase 6 (DEC-007).** The fields below define the shape our input and output files should mirror.

| Concept | Recess field | Evidence |
|---|---|---|
| Game teams | `Game.homeTeamId`, `Game.awayTeamId` | `packages/db/models/Game.ts:21` |
| Gym | `Game.locationId` → `Location` (name, address, `courts[]`) | `Game.ts:23`, `packages/db/models/Location.ts` |
| Court | `Game.court` (string) | `Game.ts:44` |
| Video link | `Game.youtubeUrl`, set when admin uploads to YouTube | `Game.ts:45`, `apps/admin/lib/actions/games.ts:511` |
| Period scores | `Game.periods[] {home, away}` | `Game.ts:32` |
| Roster | `TeamEntry.roster[].userId` (required), `jerseyNumber` (**optional**) | `packages/db/models/TeamEntry.ts:18-20` |
| Walk-ins | Game attendance entries with `displayName`, `jerseyNumber` | `Game.ts` attendance sub-schema |
| Player stats | `PlayerStatLine.stats` (map of key → number) + `pointsString` (one digit per made basket: 1 = FT, 2, 3) | `packages/db/models/PlayerStatLine.ts:13-14` |
| Temp players | `isTempPlayer`, `tempPlayerName`, `tempPlayerJerseyNumber` | `PlayerStatLine.ts:16-18` |
| Stat categories | `League.sportConfig.statCategories[] {key, label, perPlayer, isCore, sortDirection}` | `packages/types/index.ts:227` |

Basketball categories configured today (test DB): `pts, reb, ast, stl, blk, to, foul`.

The live `recessleagues` DB currently holds **0 games**, 1 location and 1 division (read-only count, 2026-11-16).

## 5. Conflicts between the docs and reality (for owner decision, not resolved here)

1. **Footage source:** the docs assume original BallerTV 1080p MP4s, but the footage available is on YouTube (re-encoded). Quality is unverified until task 0.4. Recorded as DEC-004 (Proposed).
2. **Stats Recess can't store yet:** shot attempts (2PA/3PA/FTA), OREB/DREB, shot location and per-event records. Recess keeps per-player totals and made-shot digits only, while the docs require events as the source of truth. The owner has said Recess models can be extended later (DEC-007).
3. **Jersey numbers are optional in Recess:** Phase 3 identity depends on them, so missing numbers mean unresolved identities.
4. **Fouls and turnovers:** out of scope here but tracked in Recess by scorekeepers. It's still to be decided whether AI stats replace or supplement scorekeeper stats.
5. **Historical games:** the docs cite 150+ games across 3 gyms, but Recess has 1 location and no games. How historical videos map to teams and rosters is unknown.
6. **Full-game processing:** the docs' Phase 1 exit gate required full-game processing. The owner moved development to clips (DEC-005), and `PROJECT_PLAN.md` was updated accordingly.

## 6. Reference repository (preliminary; full inspection is task 1.2)

[abdullahtarek/basketball_analysis](https://github.com/abdullahtarek/basketball_analysis), read from its README and source on 2026-11-17. It hasn't been cloned or run.

| Aspect | Finding |
|---|---|
| License | MIT |
| Stack | Python 3.8+; pinned `torch==2.2.0`, `ultralytics==8.3.67`, `supervision==0.25.1`, `transformers==4.46.3`, `opencv_python==4.9.0.80`, `numpy==1.24.4`, `roboflow==1.1.51` |
| Usage | `python main.py input.mp4 --output_video output_videos/output_result.avi` (plus a Dockerfile) |
| Detection | YOLO models for players (v11), ball (v5) and court keypoints (v8). Weights are downloaded from Google Drive, with unknown training data. |
| Tracking | ByteTrack via `supervision`; batch 20, conf 0.5 |
| Teams | Zero-shot `patrickjohncyh/fashion-clip`, prompts hardcoded as "white shirt" / "dark blue shirt"; cache reset every 50 frames |
| Events | Ball possession, passes, interceptions; speed/distance; bird's-eye "tactical view" from court keypoints |
| Output | Annotated video only. No structured events and no confidence values. |

**Reusable:** the module layout, ByteTrack tracking, court keypoint → court coordinate mapping (the basis for 2PT/3PT from foot position), the possession logic as a starting point, and the training notebooks.

**Gaps against our scope:** jersey reading and roster identity; shot attempt, make/miss, 2PT/3PT, free throws, rebounds, assists, steals (interception is only close) and blocks; any structured output.

**Problems for our use:**
- `utils/video_utils.read_video` loads **every frame into memory**. That's fine for short clips but impossible for long footage on 16 GB, where a 1-hour 1080p game is roughly 100k frames, around 600 GB as raw frames. Frames must be streamed.
- Tracks are held per frame in memory, and intermediate results are cached as pickles.
- Team prompts must come from per-game configuration instead of being hardcoded.
- Its pretrained weights' accuracy on our gym footage is unknown until measured (Phase 1).

## 7. Integration-ready contract (proposal, implemented in a later approved task)

Standalone now, easy to connect later (DEC-007):

**Input: clip/game manifest (JSON, versioned)**
```json
{
  "schemaVersion": "0.1",
  "gameId": "external-game-id",
  "homeTeam": { "id": "team-id", "name": "Home", "colorHint": "white" },
  "awayTeam": { "id": "team-id", "name": "Away", "colorHint": "dark blue" },
  "roster": [ { "teamId": "team-id", "playerId": "user-id", "jerseyNumber": 23, "displayName": "Name" } ],
  "gymId": "location-id",
  "court": "Court 1",
  "video": { "source": "clip-file-or-reference", "startSeconds": 0, "endSeconds": 45 }
}
```
The names mirror `Game.homeTeamId`, `TeamEntry.roster[].userId` / `jerseyNumber`, `Game.locationId` and `Game.court`. Recess can later export exactly this.

**Outputs**
- **Events JSON:** the event shape in `ARCHITECTURE.md`, plus `schemaVersion`. Each event has a stable `eventId`, and `playerId` is `null` when identity is uncertain.
- **Box score JSON:** derived from events only. Per-player and per-team keys use names suitable for the Recess stat map: `fg2m, fg2a, fg3m, fg3a, ftm, fta, oreb, dreb, reb, ast, stl, blk, pts`.

**Later Recess-side work (backlog):**
- add the new keys to basketball `sportConfig.statCategories`;
- optionally add a `GameEvent` collection;
- an admin review screen;
- an idempotent import from confirmed events into `PlayerStatLine`.

## 8. Unknowns

- Which YouTube channel or videos, how many per gym, and their actual resolution and bitrate.
- Whether the gym cameras are configured the same way.
- Whether jersey numbers are readable at YouTube quality.
- Where clips and datasets will be stored (external drive, Google Drive), and how much space is available.
- League rules for assists, steals and blocks (needed before labelling, Phase 2).
- Whether Recess should be populated with the historical games and gyms.

## 9. Owner decisions recorded during this task

- **DEC-003:** separate repository. Accepted.
- **DEC-004:** footage source is YouTube. Proposed; pending the quality check in 0.4.
- **DEC-005:** clip-based MVP. Accepted.
- **DEC-006:** free compute (Colab/Kaggle) and local labelling. Accepted.
- **DEC-007:** standalone first with a Recess-shaped contract. Accepted.
