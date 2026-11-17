# Dataset, Annotation, Training, and Evaluation Policy

## 1. Dataset inventory

For each source video, record:
- stable video ID
- game ID (if known)
- gym/camera ID
- source file reference (not necessarily a public URL)
- duration, resolution, FPS, codec
- recording date
- audio presence if relevant
- known issues (camera obstruction, missing footage, scoreboard overlay, etc.)
- roster/teams mapping
- permission/data-handling status

Do not assume the three cameras are identical. Compare their video properties and visual characteristics.

## 2. Split policy

Split by complete games, never random frames from the same game across train and test. Keep a fixed, untouched test set. Include footage from all gyms in evaluation where possible. Consider a later-time holdout to test future-game generalization.

An initial split such as 70% train / 15% validation / 15% test is only a starting proposal. The actual split should account for game count, gym diversity, season changes, and rare event coverage.

## 3. Annotation standards

Before labelling, define:
- object classes and bounding-box rules
- visibility/occlusion labels
- jersey-number transcription rules (including partial/ambiguous readings)
- team identity labels
- player identity labels linked to roster IDs
- event start/end timestamps
- shot outcome and shot type definitions
- rebound/assist/steal/block adjudication rules
- confidence/ambiguity labels
- reviewer and adjudication status

Use an explicit `unknown/ambiguous` label. Do not force annotators to guess.

## 4. Human review as data generation

A human correction can become a training label, but is not automatically a model update.

For each correction, preserve:
- original prediction
- corrected answer
- reviewer and timestamp
- evidence clip/frames
- event/identity category
- model and dataset version
- adjudication status

Prioritize examples that are uncertain, incorrect, rare, or representative of a new gym/camera condition. Avoid spending annotation time on thousands of redundant easy frames.

## 5. Training policy

- Start with pretrained models and establish a baseline.
- Fine-tune only when evaluation shows a specific weakness and labelled examples exist.
- Train the relevant component, not necessarily every model.
- Keep training configuration, seed, package versions, weights, and dataset version.
- Compare new model against the baseline on the same held-out data.
- Do not deploy a model solely because training loss improved.
- Do not train on the test set.
- Keep model versions and provide rollback.

## 6. Evaluation report

Every model/event release should report:
- dataset version and split
- gym/game coverage
- model and code version
- precision, recall, F1 where appropriate
- false positives and false negatives
- identity attribution precision and coverage
- review/unresolved rate
- per-gym and per-event breakdown
- qualitative examples of successes and failures
- inference speed and estimated cost
- comparison to previous baseline
- decision: accept, reject, or further investigate

## 7. Human-review quality

Use a second reviewer/adjudication for ambiguous or high-impact labels. Track reviewer disagreement. A noisy label set can make the model worse even when the dataset grows.
