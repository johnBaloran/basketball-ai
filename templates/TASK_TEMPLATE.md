# Task Prompt — [TASK ID]: [TASK TITLE]

Copy this template and fill it in for exactly one task.

## 1. Context
Read:
- `AGENT_RULES.md`
- `docs/PROJECT_PLAN.md`
- `docs/ARCHITECTURE.md` (if relevant)
- `docs/PROGRESS.md`
- `docs/DECISION_LOG.md` (if relevant)

Project context relevant to this task:
[Briefly state only the context needed.]

## 2. Single objective
[One outcome. Do not combine unrelated tasks.]

## 3. Scope
### In scope
- [Specific item]
### Out of scope
- [Explicitly list tempting adjacent work that must not be done.]

## 4. Investigation required before coding
Before implementation, inspect:
- [Files/modules/data/dependencies]
- [Existing tests and conventions]
- [Official documentation or version compatibility, if relevant]

Return an investigation report containing:
1. Current behavior and relevant files.
2. Findings with file paths and line references where possible.
3. Existing reusable code/dependencies.
4. Unknowns and assumptions.
5. Proposed smallest implementation.
6. Risks and test plan.

Do not implement until the investigation and plan are presented. If this task has a material design choice, wait for owner approval.

## 5. Acceptance criteria
The task is complete only when:
- [Observable criterion 1]
- [Observable criterion 2]
- [Observable criterion 3]

## 6. Required tests and evidence
- Tests/checks to run:
- Real footage/sample data to inspect:
- Output artifacts expected:
- Metrics/logs/screenshots expected:
- Cases not tested and must be disclosed:

Do not fabricate results. If a check cannot run, state why and what remains unverified.

## 7. Git requirements
- Inspect `git status` first.
- Preserve pre-existing changes.
- Use task branch: `task/[TASK-ID]-short-name` unless owner specifies otherwise.
- Keep changes scoped.
- Run tests.
- Commit with: `[TASK-ID]: concise description`
- Report branch, commit hash, changed files, and working-tree status.
- Never force-push or discard user changes.

## 8. Documentation/progress
At completion, update `docs/PROGRESS.md` with status, evidence, blockers, and next single task. Update other docs only if an approved decision or architecture changed.

## 9. Required final report
### Investigation
### Implementation
### Files changed
### Commands executed and results
### Tests/evidence
### Limitations and untested cases
### Git checkpoint
### Progress tracker update
### Owner decisions needed

End with exactly one:
- `READY FOR OWNER REVIEW`
- `BLOCKED — OWNER INPUT REQUIRED`
- `NOT COMPLETE — MORE WORK REQUIRED`

Do not start another task.
