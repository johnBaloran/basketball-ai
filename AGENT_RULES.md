# AI Agent Operating Rules

These rules apply to every AI coding agent working in this repository. They are mandatory unless the project owner explicitly changes them.

## 1. One implementation task at a time

- Work on only the single task identified as `CURRENT TASK` in `docs/PROGRESS.md`.
- Do not begin the next task, phase, feature, refactor, or cleanup until the current task is accepted by the project owner.
- You may inspect related code and dependencies to understand the task, but do not bundle unrelated changes.
- If the task reveals necessary follow-up work, record it in the backlog/progress tracker. Do not implement it without approval.
- Do not interpret a broad goal as permission to implement every implied feature.

## 2. Investigate before implementing

Before editing code:
1. Read the relevant project documentation and current progress.
2. Inspect the repository structure and the specific files involved.
3. Trace relevant call paths, data contracts, dependencies, and tests.
4. Check the installed package/library versions and official documentation when version-sensitive behavior matters.
5. Search for existing implementations before creating duplicates.
6. Identify assumptions, risks, and unknowns.
7. Present a short investigation report and implementation plan.
8. Wait for approval if the task requires a design choice, changes an interface/schema, adds a significant dependency, incurs cost, or has material uncertainty.

Do not start coding merely because the user described an outcome.

## 3. Evidence, not claims

Never say a task is complete because code was written or because the agent believes it should work.

A completion report must distinguish:
- **Implemented:** what changed.
- **Executed:** commands actually run.
- **Passed:** tests/checks with observed results.
- **Not tested:** checks not run and why.
- **Evidence:** logs, test output, generated artifacts, screenshots, metrics, or reproducible commands.
- **Limitations:** known failures, untested cases, and remaining risks.

Never fabricate test results, benchmark numbers, model metrics, video inspection, or deployment status. If a command was not run, say so. If a video was not visually inspected, say so.

For computer-vision work, include representative frame/clip evidence and quantitative evaluation where relevant. A successful script exit is not proof of detection accuracy.

## 4. Git discipline and checkpoints

- Inspect `git status` before changing anything.
- Do not overwrite or discard user changes.
- Create/use a task-specific branch unless the owner specifies another workflow.
- Keep changes small and scoped to the current task.
- Run relevant tests before committing.
- Commit only after checks pass or after explicitly documenting why a known failing check is accepted.
- Use a clear commit message: `phase-N task-N: concise outcome`.
- Never force-push, rewrite shared history, reset hard, or delete branches without explicit permission.
- Do not commit secrets, credentials, private video, personal data, large model weights, or generated datasets unless the owner explicitly approves and the repository policy permits it.
- At task completion, report branch, commit hash, changed files, test evidence, and working-tree status.
- If work is interrupted, leave a clean checkpoint or clearly document uncommitted changes.

## 5. Documentation and progress tracker

At the end of every task, update:
- `docs/PROGRESS.md` — status, completed work, evidence, blockers, next single task.
- Relevant architecture or dataset docs if approved design changed.
- `docs/DECISION_LOG.md` for decisions that affect future work.

Do not mark a task complete until its acceptance criteria and evidence are recorded. The agent maintains the tracker; the project owner approves status transitions to accepted.

## 6. Scope and change control

- No opportunistic refactoring.
- No new framework, model family, database, cloud provider, or major dependency without explaining alternatives and obtaining approval.
- Do not change public API schemas, database schemas, event definitions, or model input/output contracts without documenting migration/compatibility impact.
- Preserve backward compatibility unless the task explicitly permits breaking changes.
- Do not use facial recognition. Player identity must use roster, team, jersey number, tracking continuity, and non-face visual evidence.
- Unknown identity or uncertain event must remain unknown/pending review; do not guess to make statistics look complete.

## 7. Model and dataset integrity

- Do not train from scratch unless explicitly approved.
- Establish a reproducible baseline before fine-tuning.
- Split data by whole games (and, where useful, by gym/time period), not random frames from the same game.
- Keep a held-out test set untouched during model development.
- Save dataset versions, annotation definitions, model versions, training configurations, and evaluation reports.
- Human corrections are candidate labels; review quality and adjudicate ambiguous labels before training.
- Do not automatically train on every correction.
- Report precision, recall, false positives, false negatives, identity coverage, review rate, and performance by gym/statistic where applicable.

## 8. Security, privacy, and cost

- Never place API keys, passwords, tokens, or webhook secrets in source control or logs.
- Use environment variables/secrets management and `.env.example` with placeholders only.
- Do not upload private game footage to an external service without owner approval and a data-handling review.
- Before using paid APIs, GPU instances, storage, or annotation services, estimate cost and obtain approval.
- Treat video, roster data, and player information as private league data.

## 9. Required response format for every task

Use the task template in `templates/TASK_TEMPLATE.md`. Keep responses concise but specific. End each task report with one of:
- `READY FOR OWNER REVIEW`
- `BLOCKED — OWNER INPUT REQUIRED`
- `NOT COMPLETE — MORE WORK REQUIRED`

Do not proceed to another implementation task until the owner accepts the current task.
