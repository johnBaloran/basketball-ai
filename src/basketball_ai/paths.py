"""Where private data lives. Clips, frames, labels and weights are never stored inside the repo.

`BBALL_DATA_DIR` points at the data folder (in Colab: a Google Drive folder, see docs/DATA_HANDLING.md).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "BBALL_DATA_DIR"
REPO_ROOT = Path(__file__).resolve().parents[2]

# Standard layout inside the data folder (docs/DATA_HANDLING.md §3)
SUBDIRS = ("raw", "clips", "frames", "labels", "models", "outputs")


class DataDirError(RuntimeError):
    pass


def data_dir(env: dict[str, str] | None = None, repo_root: Path = REPO_ROOT) -> Path:
    """The private data folder. Raises if it's unset or would put data inside the git repo."""
    value = (os.environ if env is None else env).get(ENV_VAR, "").strip()
    if not value:
        raise DataDirError(
            f"{ENV_VAR} is not set. Point it at the private data folder, e.g. "
            "/content/drive/MyDrive/basketball-ai-data in Colab."
        )
    path = Path(value).expanduser().resolve()
    root = repo_root.resolve()
    if path == root or root in path.parents:
        raise DataDirError(
            f"{ENV_VAR}={path} is inside the git repo ({root}); private data must live outside it."
        )
    return path


def data_path(kind: str, *parts: str, env: dict[str, str] | None = None, repo_root: Path = REPO_ROOT) -> Path:
    """A path inside one of the standard subfolders, e.g. data_path("clips", "gym-a", "clip-001.mp4")."""
    if kind not in SUBDIRS:
        raise ValueError(f"unknown data folder {kind!r}; expected one of {', '.join(SUBDIRS)}")
    return data_dir(env, repo_root).joinpath(kind, *parts)
