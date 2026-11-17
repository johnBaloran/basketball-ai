# Architecture — Current Intended Boundaries

**Status:** Proposed architecture; implementation must be verified against the repository.

## Components and responsibilities

### Existing Next.js application
Owns league domain data: games, teams, rosters, player IDs, jersey numbers, admin permissions, player profiles, leaderboards, standings, and official league records.

### Python computer-vision service
Owns video analysis: decoding, frame sampling, object detection, tracking, team/jersey evidence, identity resolution proposals, event proposals, confidence, and evidence packaging.

### Worker/job system
Owns long-running processing, retries, cancellation, job state, and resource scheduling. A full game must not depend on a single long-lived web request.

### Storage
Keep source MP4s and derived clips/annotated outputs in approved object storage. Keep metadata and event records in the appropriate application database. Do not commit private video or large weights to Git.

## Processing lifecycle

Suggested states:
`queued -> validating -> processing -> review_required -> completed`

Failure/cancellation states:
`failed`, `cancelled`

State transitions must be explicit and auditable. A job can complete with some events unresolved if the product owner approves that workflow; unresolved events must not be silently counted as confirmed individual statistics.

## API contract principles

- Version request and response schemas.
- Authenticate job submission and callbacks.
- Use idempotency keys.
- Include game ID, job ID, model version, and schema version.
- Separate job status from event records.
- Include event and identity confidence separately.
- Include evidence references and timestamps.
- Validate roster/player IDs against the game roster.
- Make retries safe.

## Canonical event proposal shape

Illustrative only; adapt to the existing database and approved schema.

```json
{
  "eventId": "stable-id",
  "gameId": "game-id",
  "eventType": "three_point_made",
  "timestampSeconds": 532.4,
  "teamId": "team-id",
  "playerId": null,
  "courtCoordinates": {"x": 18.2, "y": 7.4},
  "eventConfidence": 0.94,
  "identityConfidence": 0.41,
  "status": "pending_review",
  "evidence": {
    "clipRef": "approved-storage-reference",
    "trackIds": ["track-17"],
    "modelVersion": "model-version"
  }
}
```

Do not treat this example as an approved production contract until reviewed against the existing application.

## Permanent identity vs temporary tracking

- `trackId`: temporary visual track, scoped to a processing run/game.
- `playerId`: permanent league identity from the existing roster.
- One player may map to multiple `trackId` values.
- Store evidence for each mapping and time range.
- Jersey number is unique only within the relevant team/game context, not globally.
- Never use face recognition.
- Conflicting or weak evidence results in unresolved identity.

## Statistics source of truth

Persist validated events as the source of truth. Derive box scores and aggregates from those events. Avoid independently mutating multiple totals in ways that can drift.

Suggested invariants:
- 3PM <= 3PA
- FGM <= FGA
- Points = 2 × (FGM − 3PM) + 3 × 3PM + FTM
- REB = OREB + DREB, subject to explicitly defined team-rebound policy
- Every credited player belongs to the game's roster
- One shot event cannot be counted as both made and missed
- Retries cannot create duplicate events

Final team score/standings may use the official validated game result; do not infer standings solely from player attribution totals.
