# Data Handling and Secrets

**Status:** Task 0.3, 2026-11-19. Applies to every person and agent working on this project.

This repository is **public** during development (DEC-009). Anything committed can be read and copied by anyone, and making the repo private later doesn't recall copies. The rule follows from that: **git holds code and docs only. League data never goes in git.**

## 1. What is private

| Data | Examples | Where it lives |
|---|---|---|
| Game footage | YouTube downloads, BallerTV files, clips | Google Drive data folder (`raw/`, `clips/`) |
| Derived imagery | extracted frames, crops of players or jerseys, annotated videos | Drive (`frames/`, `outputs/`) |
| People data | rosters, player names, jersey ↔ player mappings, Recess IDs tied to names | Drive, or kept in Recess |
| Labels | annotations, review decisions, correction history | Drive (`labels/`) |
| Model weights trained on league footage | fine-tuned `.pt` / `.onnx` | Drive (`models/`) |
| Secrets | API tokens, Kaggle key, database URLs | Secret stores only (§4) |

**Allowed in git:** source code, tests, docs, notebooks **with outputs cleared**, configuration with placeholders, and small **synthetic** test fixtures (made-up data, never real footage or real names) that are listed in `.private-data-allow`.

## 2. How it's enforced

1. **Pre-commit hook (local, before anything leaves the machine):** `.githooks/pre-commit` runs `scripts/privacy_guard.py --staged`. It needs only git and `python3`. Enable it once per clone with `./scripts/install-hooks.sh`. It blocks:
   - video, images and frames, model weights, pickles and arrays, archives, and tabular files (`.csv`, `.xlsx`, `.parquet`, …);
   - any file over 1 MB;
   - notebooks with saved outputs or attachments, since outputs can embed frames, tables or tokens;
   - text that looks like a secret: GitHub, Google, AWS or Stripe keys, database URLs with passwords, private keys, Kaggle keys.
2. **CI (second safety net):** `scripts/check.sh` runs the same guard on every tracked file in GitHub Actions. By then the commit has already been pushed, so the hook is the real protection.
3. **`.gitignore`:** keeps media, weights and data folders from being added by accident.
4. **Code:** `basketball_ai.paths.data_dir()` reads `BBALL_DATA_DIR` and **refuses a path inside the repo**, so pipeline code can't write clips or frames into git's working tree.

Don't bypass the hook (`git commit --no-verify`). If it blocks something that's genuinely safe, such as a synthetic fixture, add that exact path to `.private-data-allow` in its own reviewed commit.

## 3. Data folder layout (Google Drive)

`BBALL_DATA_DIR` points at the folder, which in Colab is `/content/drive/MyDrive/basketball-ai-data`.

```
basketball-ai-data/
  raw/        source videos as downloaded (never edited)
  clips/      short clips cut from raw/ (per gym: clips/<gym-id>/...)
  frames/     extracted frames and crops
  labels/     annotation exports and review decisions
  datasets/   training datasets built from labels (split by game)
  models/     trained weights and their configs
  outputs/    pipeline results (events JSON, box scores, annotated video)
```

- **Sharing:** the Drive folder stays shared only with the owner (and named collaborators if approved). No "anyone with the link".
- **Naming:** clip and file names use IDs, not player names (e.g. `gym-a/2026-11-14_g123_0612-0655.mp4`).
- **Retention:** keep `raw/` until the owner decides otherwise. Delete unused frame dumps, which can be regenerated from clips.

## 4. Secrets

| Where code runs | Where secrets go |
|---|---|
| Google Colab | Colab Secrets (key icon), read with `google.colab.userdata.get(...)` |
| Kaggle | Kaggle Secrets (Add-ons > Secrets) |
| GitHub Actions | Repository secrets (none needed today) |
| This Mac | `.env` (git-ignored); `.env.example` holds placeholders only |

- **Never in git or notebooks:** never paste a secret into a notebook cell, a commit, an issue or a log line.
- **Least privilege:** use the narrowest token possible, e.g. a fine-grained GitHub token with read-only Contents on one repo, with an expiry date.
- **Logs:** print that a secret is present, never its value.

## 5. External services

- **Free GPU notebooks (Colab, Kaggle):** clips may be processed there (DEC-006). Kaggle notebooks and datasets must be **private**.
- **Labelling:** use a local or self-hosted tool (CVAT or Label Studio). Roboflow's free plan makes projects public, so don't upload league clips there.
- **New services:** any other service that would receive footage or player data needs owner approval first (AGENT_RULES §8).

## 6. If private data or a secret gets pushed

1. **Make the repo private immediately:** `gh repo edit <owner>/basketball-ai --visibility private`.
2. **Revoke or rotate any exposed secret now.** Assume it's compromised the moment it's public.
3. **Remove the data from history.** Deleting the file in a new commit isn't enough; rewrite history and force-push, with owner approval.
4. **Record the incident** in `docs/PROGRESS.md`, including what was exposed and for how long. Remember that public copies (forks, caches) may persist.
