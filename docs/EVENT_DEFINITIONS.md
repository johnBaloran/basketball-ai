# Event and Statistic Definitions

**Status:** Task 0.5 draft, 2026-11-20 (DEC-010). Items marked **PROPOSED** are league-policy choices made so code and labelling can proceed; the owner confirms or changes them before labelling starts (Phase 2). The machine-readable versions are in `src/basketball_ai/contracts.py` and `schemas/`.

## 1. Event types

| Event type | Definition | Credits | `relatedEventId` |
|---|---|---|---|
| `fg2_made` / `fg2_missed` | A field-goal attempt released with the shooter's last ground contact **inside** the 3-point line (a foot on the line counts as inside) | shooter: FGA and 2PA (+FGM, 2PM, 2 pts if made) | — |
| `fg3_made` / `fg3_missed` | A field-goal attempt with the shooter's last ground contact **behind** the 3-point line | shooter: FGA and 3PA (+FGM, 3PM, 3 pts if made) | — |
| `ft_made` / `ft_missed` | A free-throw attempt, identified from game context (players lined up, shooter alone at the line), **not** from location alone | shooter: FTA (+FTM, 1 pt) | — |
| `rebound_offensive` | After a missed shot, the **shooting team** establishes control of the ball | rebounder: OREB, REB | the missed shot (same team) |
| `rebound_defensive` | After a missed shot, the **defending team** establishes control | rebounder: DREB, REB | the missed shot (other team) |
| `assist` | The last pass before a made field goal, by a teammate, when the shooter scores without dribbling to beat a defender (**PROPOSED:** at most 2 dribbles after the pass) | passer: AST | the made field goal (same team, different player) |
| `steal` | A defender's action (deflection or interception) directly causes the offence to lose possession, **not** a defensive rebound and not an out-of-bounds turnover | defender: STL | — |
| `block` | A defender legally touches the ball during a field-goal attempt, changing its path so the shot misses | blocker: BLK | the missed field goal (other team) |

**Out of scope:** fouls and turnovers (PROJECT_PLAN §3). The league app's scorekeeper still records those.

**Edge cases (PROPOSED):**
- **Blocked shot:** a block also creates the missed field-goal event, and the shooter is still charged the attempt.
- **Tip-ins:** an offensive rebound followed by a made shot; the tip is its own `fg2_made` event.
- **Team rebounds:** when the ball goes out of bounds after a miss, there's no player credit. Record it as a rebound with `playerId: null`, which counts for the team only.
- **Goaltending:** count the basket as made for the shooter. No block.
- **And-ones:** the made basket plus a separate `ft_*` event.
- **Free throws:** `ft_made` / `ft_missed` count FTM / FTA only. Points come from `ft_made`.

## 2. Status lifecycle

| Status | Meaning | Counts in stats? |
|---|---|---|
| `proposed` | Created by the model, not yet checked against thresholds | No |
| `pending_review` | Event or identity uncertain; waiting for an admin | No |
| `confirmed` | Passed thresholds automatically, or confirmed by an admin | **Yes** |
| `rejected` | Reviewed and wrong (kept for audit and training data) | No |
| `unresolved` | Reviewed but can't be decided from the video | No |

An event with a confirmed type but an unknown player is still `confirmed` with `playerId: null`. It counts for the **team** ("unattributed") and never for a guessed player (reliability principle, PROJECT_PLAN §3).

## 3. Confidence

- **`eventConfidence`** (0–1): how sure the model is that the event happened as typed.
- **`identityConfidence`** (0–1, or null): how sure it is about the player. It comes from `identity.resolve_tracks`: the share of agreeing jersey readings × their mean reader confidence.
- **Thresholds for automatic `confirmed`:** none yet. They're set after baseline measurement (PROJECT_PLAN §9). Until then everything goes to `pending_review`.

## 4. Identity rules (implemented in `identity.py`)

A temporary track is credited to a roster player only when **all** of these hold. Defaults are PROPOSED and configurable:
1. At least **3** jersey readings with reader confidence of at least **0.5**.
2. The winning number has at least **70%** of the confidence-weighted votes.
3. The team label agrees in at least **70%** of observations, or the number exists on only one team's roster.
4. That team has that number on its game roster.
5. No other track credited to the same player overlaps it in time. If one does, both become `conflict` and go to review.

No face recognition (DEC-001). Players without a jersey number on the roster can't be credited automatically.

## 5. Box score (implemented in `boxscore.py`)

Derived only from `confirmed` events; never edited directly. The keys match the league app's stat map: `pts, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, oreb, dreb, reb, ast, stl, blk`.

**Invariants checked on every computation:**
- makes ≤ attempts;
- FGM = 2PM + 3PM and FGA = 2PA + 3PA;
- PTS = 2·2PM + 3·3PM + FTM;
- REB = OREB + DREB;
- player totals + unattributed = team totals.

**Event-level checks before aggregating:**
- credited players are on the game roster and on the event's team;
- assists, rebounds and blocks reference a confirmed shot of the right kind and team;
- no self-assists.

## 6. Court coordinates

Court coordinates are in **feet**: `x` along the length (0 = left baseline), `y` across (0 = near sideline). The mapping from image to court comes from court keypoints (Phase 1/4, as in the reference repo's tactical view). The 3-point line distance depends on the gym and league (**PROPOSED:** configurable per gym, default 22 ft in the corners and 23.75 ft at the top), so 2PT vs 3PT uses the gym configuration, never a fixed screen region.

## 7. Questions for the owner

1. Assist rule: is "at most 2 dribbles after the pass" right for this league, or should assists require a catch-and-shoot?
2. 3-point line distance per gym (FIBA 6.75 m, NBA 23.75 ft, or a high-school line)?
3. Should team rebounds be tracked, or simply not recorded?
4. Should AI stats eventually replace or supplement the scorekeeper's stats in the league app?
