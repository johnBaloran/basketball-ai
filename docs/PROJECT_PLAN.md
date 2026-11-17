# Project Plan — Basketball Video Analysis & Statistics

**Status:** Draft baseline plan  
**Product owner:** League operator  
**Primary implementation approach:** AI-assisted development with human review and measured model improvement  
**Last updated:** 2026-11-13

## 1. Product vision

Build a system that processes full-game BallerTV MP4 recordings and produces trustworthy basketball game events and player/team statistics. Results flow into the league's existing Next.js application, where administrators can review uncertain events and players can see validated statistics.

The goal is not merely to draw boxes around players. The product must connect video observations to rostered player identities, infer basketball events, preserve uncertainty, and produce auditable statistics.

## 2. Known operating context

- At least 3 gyms, each with its own BallerTV camera.
- At least 50 games per gym; approximately 150+ historical full-game recordings.
- 1080p MP4 footage.
- Cameras auto-follow the ball and pan/reframe during play.
- Camera models/configurations have not yet been confirmed identical.
- The league already stores games, teams, rosters, player IDs, and jersey numbers in its Next.js application.
- Jersey numbers appear on both front and back of uniforms.
- Jersey numbers are expected to remain consistent during a season.
- No facial recognition is to be used.
- New gyms may be added later; architecture must support per-gym configuration/calibration rather than hardcoding one gym.

These are project inputs, not proof that the footage is sufficient for every event or identity.

## 3. Product outcomes

### Required outcomes
1. Ingest a game video and create a trackable processing job.
2. Detect and track players and the basketball.
3. Assign team membership.
4. Read jersey numbers over multiple frames and associate observations with the game roster.
5. Maintain permanent player identity independently of temporary tracking IDs.
6. Detect and classify requested basketball events.
7. Attribute events to players only when evidence is sufficient.
8. Mark uncertain events/identities for admin review.
9. Store validated events as the source of truth.
10. Aggregate box scores, shot charts, scoring timelines, leaderboards, player histories, and standings.
11. Send processing results securely to the existing Next.js application.
12. Preserve corrections and evaluation data so the system can improve safely.

### Statistics in scope
- 2-point field goals made/attempted
- 3-point field goals made/attempted
- Free throws made/attempted
- Offensive rebounds
- Defensive rebounds
- Assists
- Steals
- Blocks
- Team score and team-level totals where appropriate
- Shot location and shot outcome
- Scoring timeline

Fouls and turnovers are not currently in scope.

### Reliability principle
A correct team score with an unresolved shooter is preferable to a confidently wrong player attribution. Unknown, pending-review, and unresolved are valid system outcomes.

## 4. Explicit non-goals for the initial MVP

- Facial recognition or face embeddings.
- Fully autonomous officiating.
- Foul and turnover tracking.
- Live, real-time in-game analytics unless separately approved.
- Guaranteed zero-human-review operation.
- Training a large model from scratch.
- Replacing the existing Next.js league application.
- Supporting arbitrary camera types before the BallerTV workflow is validated.

## 5. Proposed system architecture

### System boundaries
- **Existing Next.js application:** games, teams, rosters, player IDs, admin UI, player profiles, league records, database, authentication.
- **Python CV service:** video decoding, detection, tracking, identity evidence, event inference, event confidence, review package generation.
- **Worker/job layer:** long-running video processing, retries, status transitions.
- **GPU compute:** model inference/training on an approved provider or local hardware.
- **Object storage:** source videos, clips, annotated videos, and approved dataset artifacts.
- **Integration API/webhook:** authenticated job submission and result callbacks.

### High-level pipeline
1. Receive game processing request and roster/game metadata.
2. Validate video, game, roster, and configuration.
3. Create durable job; do not hold an HTTP request open for a full game.
4. Decode video and record metadata (resolution, FPS, duration, timestamps).
5. Detect players, ball, and relevant court/hoop elements.
6. Track objects across frames, accounting for camera motion and occlusion.
7. Classify teams.
8. Read jersey numbers from front/back observations across multiple frames.
9. Resolve temporary tracks to permanent roster player IDs using evidence.
10. Infer possession and basketball events.
11. Determine event and identity confidence separately.
12. Deduplicate and validate event candidates.
13. Create review queue for uncertain items.
14. Persist accepted events.
15. Aggregate statistics and update the Next.js application.
16. Store outputs, model version, processing logs, and evaluation evidence.

### Identity model
Temporary tracker IDs are not permanent player identities. A player may have several tracker IDs during one game due to occlusion, camera movement, or leaving/returning to view.

Maintain a permanent player identity registry that can link multiple temporary tracks to one roster `playerId`. Evidence may include:
- Team classification.
- Jersey-number observations and OCR confidence.
- Game roster uniqueness.
- Track continuity and time/location.
- Non-face appearance/re-identification evidence.
- Contradiction checks and timestamped history.

Never map a player solely from one weak OCR result. If evidence conflicts or is insufficient, keep identity unresolved and request review.

### Event model
Events should be stored separately from derived box scores. Each event should carry:
- game ID
- event type
- timestamp or time interval
- team ID
- player ID when known
- court coordinates when available
- event confidence
- identity confidence
- status: proposed / pending_review / confirmed / rejected / unresolved
- evidence references (clip, frames, tracks, model version)
- correction/audit history

Use idempotent event identifiers and deduplication so retries do not double-count.

## 6. Event inference principles

- **Shot attempt:** identify release and trajectory toward the basket; determine 2PT/3PT using court geometry and shooter foot position, not a simple screen-space rectangle.
- **Shot outcome:** combine ball path, hoop/rim interaction, net motion, and post-shot trajectory. Keep uncertain outcomes pending.
- **Free throw:** infer from game context and sequence, not location alone.
- **Rebound:** after a missed shot, identify the player who establishes controlled possession; classify offensive/defensive by team relative to shooter.
- **Assist:** use pass/receiver history and scoring context; rules must be configurable and reviewed against league policy.
- **Steal:** distinguish defensive possession gained through an actual steal/interception from a defensive rebound or other possession change.
- **Block:** detect a defensive player-ball interaction during a shot that changes the shot trajectory; distinguish rim and incidental deflections.

Event definitions and edge cases must be written and agreed before training labels are created.

## 7. Delivery phases and gates

Each phase is broken into small tasks. Only one implementation task is active at a time. A phase is not complete merely because code exists; its exit criteria must be demonstrated.

### Phase 0 — Project foundation and discovery
**Purpose:** establish a reproducible repository, data policy, requirements, and agent workflow.

Tasks:
- 0.1 Inspect current repository/environment and document actual starting state.
- 0.2 Establish project structure, Python environment, formatting/linting/test commands.
- 0.3 Establish safe video/data handling and secret management.
- 0.4 Inventory sample videos across all three gyms and record metadata.
- 0.5 Define event/stat terminology and unresolved/review states.

Exit gate:
- A new developer/agent can set up the project from documented instructions.
- Sample video inventory exists.
- Requirements and event definitions are versioned.
- No private footage or secrets are accidentally committed.

### Phase 1 — Video ingestion and baseline detection
**Purpose:** prove that actual BallerTV footage can be decoded and analysed.

Tasks:
- 1.1 Build video metadata and frame extraction utility.
- 1.2 Inspect reference repository and document reusable components/limitations.
- 1.3 Implement baseline player detection on representative clips.
- 1.4 Implement baseline basketball detection and evaluate small/fast ball visibility.
- 1.5 Add player/ball tracking and camera-motion handling.
- 1.6 Produce annotated MP4 and frame-level JSON/CSV.
- 1.7 Evaluate separately by gym and identify failure modes.

Exit gate:
- Full-game or representative long-duration processing works reproducibly.
- Annotated output is visually inspected.
- Detection/tracking metrics are measured on labelled samples.
- Limitations and next bottleneck are documented.

### Phase 2 — Dataset and model improvement foundation
**Purpose:** make improvement repeatable rather than ad hoc.

Tasks:
- 2.1 Define annotation schema and labelling instructions.
- 2.2 Establish game-level train/validation/test split.
- 2.3 Build dataset manifest/versioning and quality checks.
- 2.4 Create baseline evaluation scripts.
- 2.5 Add training/fine-tuning scripts for the selected model component.
- 2.6 Compare candidate models on the same held-out footage.

Exit gate:
- Dataset version and split are reproducible.
- Baseline metrics are recorded.
- Training can be repeated from documented configuration.
- No test-set leakage.

### Phase 3 — Team and player identity
**Purpose:** connect visual tracks to rostered players.

Tasks:
- 3.1 Team classification baseline.
- 3.2 Jersey crop extraction and OCR baseline.
- 3.3 Multi-frame jersey-number voting and contradiction handling.
- 3.4 Roster-constrained player resolution.
- 3.5 Permanent identity registry linking multiple temporary track IDs.
- 3.6 Non-face appearance re-identification as supporting evidence.
- 3.7 Admin identity-review workflow and correction capture.
- 3.8 Evaluate identity precision, coverage, and review rate by gym.

Exit gate:
- Automatically credited identities meet an agreed precision threshold.
- Uncertain identities remain pending/unresolved.
- Track ID changes do not create duplicate player identities.
- Human corrections are auditable.

### Phase 4 — Basketball event recognition
**Purpose:** infer requested statistics from video.

Recommended order:
1. Possession and ball control.
2. Shot release and attempt detection.
3. Shot outcome (make/miss).
4. 2PT/3PT classification and shot coordinates.
5. Free-throw sequence recognition.
6. Rebounds.
7. Assists.
8. Steals.
9. Blocks.

Each event type is developed and evaluated independently before combining into the complete game pipeline.

Exit gate:
- Event definitions are documented.
- Each event has precision/recall and attribution metrics.
- Ambiguous events are routed to review.
- Duplicate and impossible stat combinations are caught.

### Phase 5 — Human review and statistics engine
**Purpose:** make outputs trustworthy and correctable.

Tasks:
- 5.1 Event review queue and clip/evidence display.
- 5.2 Admin correction actions with audit history.
- 5.3 Event confirmation/rejection and unresolved workflows.
- 5.4 Box-score aggregation and validation.
- 5.5 Shot charts and scoring timeline.
- 5.6 Player history, leaderboards, and standings.
- 5.7 Recalculation after corrections.

Exit gate:
- Admin can resolve uncertain events.
- Statistics are derived from validated events.
- Corrections recalculate affected outputs without double counting.
- Statistical invariants are tested.

### Phase 6 — Production integration
**Purpose:** connect the Python processing service to the existing Next.js platform safely.

Tasks:
- 6.1 Agree API contracts and authentication.
- 6.2 Implement job submission and durable job lifecycle.
- 6.3 Implement authenticated, idempotent callbacks.
- 6.4 Store source and generated artifacts.
- 6.5 Integrate admin review UI.
- 6.6 Integrate player profiles, leaderboards, standings, and game pages.
- 6.7 Add retries, observability, alerts, and failure recovery.
- 6.8 Load/cost test a full game and multiple concurrent jobs.

Exit gate:
- End-to-end processing works in staging.
- Failure/retry paths are tested.
- Security and cost controls are documented.
- No duplicate stats after retries.

### Phase 7 — Pilot and controlled rollout
**Purpose:** validate in real league operations.

Tasks:
- 7.1 Run shadow processing on historical games.
- 7.2 Run pilot across all three gyms.
- 7.3 Compare AI output with manually verified box scores.
- 7.4 Measure admin review time and correction frequency.
- 7.5 Fix highest-impact errors and repeat held-out evaluation.
- 7.6 Define release thresholds and rollback plan.
- 7.7 Gradually enable official stats only after owner approval.

Exit gate:
- Agreed per-stat acceptance criteria are met.
- Review workload is operationally manageable.
- No known critical integrity/security issue.
- Product owner explicitly approves official use.

## 8. Proposed evaluation metrics

These are measurement requirements, not claims about current performance or guaranteed targets.

For detection:
- Precision and recall for players and ball.
- Miss rate during occlusion, motion blur, and camera pans.
- Tracking continuity and ID switches.

For identity:
- Player identity precision among automatically credited events.
- Identity coverage (fraction of relevant observations/events resolved).
- Wrong-player attribution rate.
- Percentage requiring review.
- Metrics by gym, jersey number, camera condition, and game.

For events:
- Precision, recall, and F1 per event type.
- Correct player attribution rate.
- Correct team attribution rate.
- Timestamp/location error where applicable.
- False events per game and missed events per game.

For operations:
- Processing time per game.
- GPU/compute cost per game.
- Review minutes per game.
- Failed job/retry rate.
- Percentage of games completing without intervention.

Never report only overall accuracy. Class imbalance can make it misleading.

## 9. Proposed acceptance targets

Targets must be agreed after baseline measurements. Initial discussion targets may include:
- High precision for automatically credited player identities.
- Separate precision/recall thresholds for each event type.
- A maximum acceptable unresolved/review percentage.
- Maximum admin review minutes per game.
- No silent player attribution when identity confidence is below threshold.

Do not lock numeric targets until the baseline reveals what is achievable and what the league requires.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Ball is tiny/blurred or hidden | Dedicated ball evaluation, high-resolution crops, temporal tracking, review |
| Camera pans and reframes | Camera-motion-aware tracking and gym-specific calibration |
| Players overlap or leave frame | Multiple track IDs linked through identity registry; uncertainty states |
| Jersey OCR fails | Front/back multi-frame voting, roster constraints, human review |
| Uniforms are visually similar | Team + jersey + temporal evidence; non-face ReID only as support |
| Event semantics are ambiguous | Written league event definitions and adjudicated examples |
| Model overfits known games | Game-level held-out test set and later-game evaluation |
| Human corrections are noisy | Label QA, adjudication, dataset versions |
| Processing costs rise | Benchmark per-game costs before scale; approval for paid resources |
| Callback retries duplicate stats | Idempotency keys and event deduplication |

## 11. Change control

Any proposed scope or architecture change must include:
- Why the change is needed.
- Alternatives considered.
- Cost, schedule, performance, and maintenance impact.
- Migration/backward-compatibility impact.
- Tests/evidence required.
- Owner approval.

Record accepted decisions in `docs/DECISION_LOG.md`.
