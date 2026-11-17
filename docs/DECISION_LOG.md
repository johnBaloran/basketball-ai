# Technical Decision Log

Record decisions that materially affect architecture, data, model selection, cost, or scope. Newest entries at the bottom.

## Decision template

### DEC-XXX — Short title
- **Date:**
- **Status:** Proposed / Accepted / Superseded
- **Context/problem:**
- **Options considered:**
- **Decision:**
- **Reasoning/trade-offs:**
- **Consequences/migration:**
- **Evidence/links:**
- **Approver:**

## Initial constraints (not all are final technical decisions)

### DEC-001 — No facial recognition
- **Date:** 2026-11-13
- **Status:** Accepted project constraint
- **Context/problem:** Need identify rostered players from video.
- **Decision:** Do not use facial recognition or face embeddings.
- **Reasoning/trade-offs:** Use team, jersey number, roster, tracking continuity, and non-face visual evidence; uncertain cases go to review.
- **Consequences/migration:** Identity design and model selection must comply.

### DEC-002 — Keep permanent player identity separate from tracker IDs
- **Date:** 2026-11-13
- **Status:** Accepted design principle
- **Context/problem:** Visual tracker IDs can change after occlusion, camera movement, or a player leaving/returning.
- **Decision:** Maintain a permanent roster `playerId` registry that can link multiple temporary track IDs with evidence.
- **Reasoning/trade-offs:** Avoid identity fragmentation and incorrect player histories.
- **Consequences/migration:** Identity mapping must be auditable and confidence-aware.

### DEC-003 — Separate repository
- **Date:** 2026-11-17
- **Status:** Accepted
- **Context/problem:** The documentation package arrived inside the Recess (Next.js/pnpm/Turbo) monorepo. The CV project is Python, GPU-oriented, and handles large private files.
- **Options considered:** (a) folder inside the Recess monorepo; (b) standalone repository.
- **Decision:** Standalone repository `basketball-ai`.
- **Reasoning/trade-offs:** Keeps Python/ML tooling, large-file rules and agent rules separate from the Node monorepo; the two connect through versioned files/API later (DEC-007).
- **Consequences/migration:** The original untracked `recess/basketball-ai-project-docs/` folder can be removed once the owner confirms.
- **Evidence/links:** `docs/STARTING_STATE.md` §1
- **Approver:** Owner (2026-11-17)

### DEC-004 — Footage source is YouTube, not original BallerTV MP4s
- **Date:** 2026-11-17
- **Status:** Proposed
- **Context/problem:** The plan assumes original BallerTV 1080p MP4 files; the owner reports the games are on YouTube.
- **Options considered:** (a) download from the league's YouTube channel; (b) obtain originals from BallerTV.
- **Decision:** Pending. Use YouTube downloads for discovery if the quality check in task 0.4 is acceptable.
- **Reasoning/trade-offs:** YouTube re-encodes (lower bitrate, possibly lower resolution), which may hurt ball and jersey-number visibility.
- **Consequences/migration:** Task 0.4 must measure resolution, bitrate and FPS per gym and record download permission.
- **Evidence/links:** `docs/STARTING_STATE.md` §3, §5.1
- **Approver:** Pending owner

### DEC-005 — Clip-based MVP
- **Date:** 2026-11-17
- **Status:** Accepted
- **Context/problem:** No CUDA GPU, 16 GB RAM, 27 GB free disk; full-game processing is impractical for development.
- **Options considered:** (a) full games from the start; (b) short clips (about 10–60 s) for Phases 1–4, then full games by processing consecutive clips.
- **Decision:** (b).
- **Reasoning/trade-offs:** Clips fit the hardware and free GPU sessions, and are faster to label and evaluate. Whole-game identity continuity and full box-score totals are deferred to chunked processing (Phase 6).
- **Consequences/migration:** Phase 1 exit gate changed to representative clips per gym with streamed frames. All code must stream frames rather than load a video into memory, so long footage works later without redesign.
- **Evidence/links:** `docs/STARTING_STATE.md` §2, §6
- **Approver:** Owner (2026-11-17)

### DEC-006 — Free compute and local labelling
- **Date:** 2026-11-17
- **Status:** Accepted
- **Context/problem:** No local GPU; owner wants free resources.
- **Options considered:** paid cloud GPU; Colab Pro; Google Colab free tier; Kaggle notebooks; local CPU/MPS only.
- **Decision:** Google Colab free tier (T4) for training and heavy inference, Kaggle notebooks (~30 GPU h/week) as backup, the M2 Mac for development and small `mps` inference. Labelling with a free local tool (CVAT or Label Studio), **not** Roboflow's free plan, whose projects are public.
- **Reasoning/trade-offs:** $0 cost. Free sessions disconnect and GPU access isn't guaranteed, so training must checkpoint to Google Drive and jobs must be small and resumable.
- **Consequences/migration:** The owner approves uploading clips needed for training or evaluation to Google Drive/Colab (private league footage; it's already hosted on YouTube). Any paid upgrade needs separate approval.
- **Evidence/links:** `docs/STARTING_STATE.md` §2
- **Approver:** Owner (2026-11-17)

### DEC-007 — Standalone first, with a Recess-shaped contract
- **Date:** 2026-11-17
- **Status:** Accepted
- **Context/problem:** Results must eventually flow into Recess, but integration now would slow down the uncertain CV work.
- **Options considered:** (a) integrate with Recess models and database now; (b) standalone with file-based input and output that mirror Recess.
- **Decision:** (b). No Recess imports, database access or API calls until Phase 6. Input is a versioned manifest JSON (game, teams, roster with jersey numbers, gym, court, clip range). Output is versioned events JSON plus box-score JSON using Recess-compatible stat keys (`fg2m, fg2a, fg3m, fg3a, ftm, fta, oreb, dreb, reb, ast, stl, blk, pts`).
- **Reasoning/trade-offs:** Fast standalone iteration; integration later becomes "Recess exports a manifest and imports events". Recess models may be extended (attempts, OREB/DREB, a `GameEvent` collection).
- **Consequences/migration:** JSON Schemas for the manifest and events are defined in a later approved task. Stable `eventId`s make later imports idempotent.
- **Evidence/links:** `docs/STARTING_STATE.md` §4, §7
- **Approver:** Owner (2026-11-17)
