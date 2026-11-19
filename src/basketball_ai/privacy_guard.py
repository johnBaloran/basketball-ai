"""Blocks private league data and secrets from entering git (the repo is public during development, DEC-009).

Standard library only and Python 3.9-compatible, so the pre-commit hook runs with the Mac's system
`python3` without installing anything. Used by `.githooks/pre-commit` (staged files) and by
`scripts/check.sh` / CI (all tracked files).

A path can be allowed explicitly by listing it in `.private-data-allow` (one path per line), for example a
small synthetic test fixture. Never allow real footage, frames, rosters or player data.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_BYTES = 1_000_000  # anything larger than 1 MB is almost certainly media, weights or data

# Video, images/frames, model weights, serialized arrays, archives, tabular data (rosters, labels)
BLOCKED_SUFFIXES = frozenset(
    {
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".ts", ".mts",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic",
        ".pt", ".pth", ".onnx", ".engine", ".ckpt", ".safetensors", ".h5", ".tflite", ".weights",
        ".pkl", ".pickle", ".npy", ".npz", ".joblib",
        ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
        ".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".feather", ".sqlite", ".db",
    }
)  # fmt: skip

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "GitHub token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}"),
    ),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Stripe key", re.compile(r"\b[sr]k_(?:live|test)_[0-9A-Za-z]{16,}")),
    (
        "Database URL with password",
        re.compile(r"\b(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql)://[^\s:/@]+:[^\s@]+@"),
    ),
    ("Private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("Kaggle key", re.compile(r'"key"\s*:\s*"[0-9a-f]{32}"')),
)

ALLOW_FILE = ".private-data-allow"


@dataclass(frozen=True)
class Problem:
    path: str
    reason: str


def check_file(path: str, data: bytes, allowed: frozenset[str] = frozenset()) -> list[Problem]:
    """Every reason this file must not be committed (empty list = fine)."""
    if path in allowed:
        return []
    problems: list[Problem] = []
    suffixes = [s.lower() for s in PurePosixPath(path).suffixes]
    blocked = [s for s in suffixes if s in BLOCKED_SUFFIXES]
    if blocked:
        problems.append(Problem(path, f"file type {blocked[-1]} may hold video, frames, weights or data"))
    if len(data) > MAX_BYTES:
        problems.append(Problem(path, f"file is {len(data):,} bytes (limit {MAX_BYTES:,})"))
    text = data.decode("utf-8", errors="ignore")
    if path.endswith(".ipynb"):
        problems.extend(_check_notebook(path, text))
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            problems.append(Problem(path, f"looks like it contains a secret ({name})"))
    return problems


def _check_notebook(path: str, text: str) -> list[Problem]:
    """Notebook outputs can embed frames, roster tables and tokens: they must be cleared before committing."""
    try:
        nb = json.loads(text)
    except json.JSONDecodeError:
        return [Problem(path, "notebook is not valid JSON")]
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("outputs"):
            return [Problem(path, f"notebook cell {i} has saved outputs (clear outputs before committing)")]
        if cell.get("attachments"):
            return [Problem(path, f"notebook cell {i} has attachments (images)")]
    return []


def _git(args: list[str], cwd: Path) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout


def _allowed(repo: Path) -> frozenset[str]:
    allow = repo / ALLOW_FILE
    if not allow.exists():
        return frozenset()
    lines = (line.strip() for line in allow.read_text(encoding="utf-8").splitlines())
    return frozenset(line for line in lines if line and not line.startswith("#"))


def scan(repo: Path, staged: bool) -> list[Problem]:
    """Check staged files (pre-commit) or every tracked file (CI)."""
    allowed = _allowed(repo)
    if staged:
        names = _git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], repo).split(b"\0")
    else:
        names = _git(["ls-files", "-z"], repo).split(b"\0")
    problems: list[Problem] = []
    for raw in names:
        if not raw:
            continue
        path = raw.decode("utf-8")
        data = _git(["show", f":{path}"], repo) if staged else (repo / path).read_bytes()
        problems.extend(check_file(path, data, allowed))
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    repo = Path(_git(["rev-parse", "--show-toplevel"], Path.cwd()).decode().strip())
    problems = scan(repo, staged="--staged" in args)
    if not problems:
        print("privacy guard: ok")
        return 0
    print("privacy guard: BLOCKED. This repo is public; these must not be committed:", file=sys.stderr)
    for p in problems:
        print(f"  {p.path}: {p.reason}", file=sys.stderr)
    print("See docs/DATA_HANDLING.md. Private data belongs in Google Drive, not git.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
