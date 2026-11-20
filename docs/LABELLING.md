# Labelling Guide: Detector (players, ball, hoop, referees)

**Status:** first version, 2026-11-20. These rules are what the model learns, so everyone labels the same way. When a frame doesn't fit a rule, write it down here instead of guessing differently each time.

## The workflow

1. **Pick frames:** `bball-sample-frames --prelabel yolo` (notebook `02_train_detector`). It takes about one varied frame per second from each clip and pre-fills person and ball boxes.
2. **Load them into a local labelling tool:** CVAT or Label Studio (never Roboflow's free plan, which is public).
   - In CVAT: create a task with labels `player, ball, hoop, referee` in that order, upload `images/`, then *Actions > Upload annotations > YOLO 1.1* with `prelabels_yolo.zip`.
3. **Correct, don't redraw:** fix wrong boxes, delete false ones, add what's missing (balls, hoops and referees especially).
4. **Export:** *YOLO 1.1*, unzipped into `basketball-ai-data/labels/<batch>/`.
5. **Build and train:** `bball-build-dataset`, then `bball-train`.

## Box rules

| Class | Box it when | Box covers | Don't box |
|---|---|---|---|
| `player` | Any player on the court, even if partly hidden (box what you'd see if they weren't hidden, when you can tell) | Head to feet, arms included | Bench players, coaches, spectators |
| `referee` | Officials on the court | Head to feet | — |
| `ball` | The game ball whenever any of it is visible, **including blurred or in a hand** | Tight around the ball (include blur streaks only if it's clearly the ball) | Spare balls off court |
| `hoop` | Each rim you can see | The **rim and net**, not the backboard | Backboard alone |

**General:**
- **Tight boxes.** The edges touch the object.
- **Too small or blurry to tell what it is:** don't box it. Never guess.
- **Frames with nothing:** keep the frame and leave it with no boxes. Empty frames teach the model too.
- **Scoreboard overlays and logos:** never box them.

## How much to label

- **First round:** about **300 frames**, spread across all three gyms, about 5–8 hours with pre-labels.
- **Then:** train, look at the evaluation per gym, and label **100–200 more frames where the model failed** (the frame picker on new clips plus correcting the new model's pre-labels). Repeat.
- **The ball is the hardest class:** expect it to need the most rounds.

## Jersey numbers (after the detector works)

`bball-crops <gameId>` saves upper-body crops of each player track. Label each crop with the number you can read, or *unreadable*. Never guess a number: the identity logic only needs a few good readings per track.
