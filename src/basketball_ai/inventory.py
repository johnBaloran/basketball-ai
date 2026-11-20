"""Footage inventory (task 0.4 tooling; fields from docs/DATASET_AND_EVALUATION.md §1).

    bball-inventory raw/            # scans BBALL_DATA_DIR/raw by default when run with no argument
    bball-inventory raw/ --out outputs/inventory.json

The gym is taken from the first folder under the scanned root (raw/<gym-id>/...). Video ids are stable
content fingerprints (size + first/last MB), so renaming a file doesn't change its id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from basketball_ai.paths import data_path
from basketball_ai.video import VideoError, probe

VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"})
_DATE = re.compile(r"(20\d\d)[-_]?(\d\d)[-_]?(\d\d)")
_CHUNK = 1 << 20


@dataclass
class InventoryRecord:
    videoId: str
    source: str  # path relative to the scanned root
    gymId: str | None
    recordingDate: str | None  # from the file name (YYYY-MM-DD) when present
    durationSeconds: float | None
    width: int | None
    height: int | None
    fps: float | None
    codec: str | None
    bitRate: int | None
    hasAudio: bool | None
    sizeBytes: int
    gameId: str | None = None  # filled in by hand or from Recess later
    permissionStatus: str = "unknown"  # owner confirms per DATA_HANDLING.md
    knownIssues: list[str] = field(default_factory=list)


def fingerprint(path: Path) -> str:
    """Stable id from size + first and last MB (fast on multi-GB files)."""
    size = path.stat().st_size
    h = hashlib.sha256(str(size).encode())
    with path.open("rb") as f:
        h.update(f.read(_CHUNK))
        if size > 2 * _CHUNK:
            f.seek(-_CHUNK, 2)
            h.update(f.read(_CHUNK))
    return "vid_" + h.hexdigest()[:16]


def record_for(path: Path, root: Path) -> InventoryRecord:
    rel = path.relative_to(root)
    gym = rel.parts[0] if len(rel.parts) > 1 else None
    m = _DATE.search(path.name)
    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
    vid, source, size = fingerprint(path), rel.as_posix(), path.stat().st_size
    try:
        info = probe(path)
    except VideoError as err:
        return InventoryRecord(
            videoId=vid,
            source=source,
            gymId=gym,
            recordingDate=date,
            durationSeconds=None,
            width=None,
            height=None,
            fps=None,
            codec=None,
            bitRate=None,
            hasAudio=None,
            sizeBytes=size,
            knownIssues=[f"unreadable: {err}"],
        )
    issues: list[str] = []
    if info.height < 1080:
        issues.append(f"below 1080p ({info.width}x{info.height})")
    if info.fps and info.fps < 25:
        issues.append(f"low frame rate ({info.fps} fps)")
    return InventoryRecord(
        videoId=vid,
        source=source,
        gymId=gym,
        recordingDate=date,
        durationSeconds=info.durationSeconds,
        width=info.width,
        height=info.height,
        fps=info.fps,
        codec=info.codec,
        bitRate=info.bitRate,
        hasAudio=info.hasAudio,
        sizeBytes=size,
        knownIssues=issues,
    )


def scan(root: Path) -> list[InventoryRecord]:
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES)
    return [record_for(p, root) for p in files]


def summarize(records: list[InventoryRecord]) -> dict[str, dict[str, float | int]]:
    """Per-gym counts and hours, for a quick look at coverage."""
    out: dict[str, dict[str, float | int]] = {}
    for r in records:
        gym = r.gymId or "(no gym folder)"
        s = out.setdefault(gym, {"videos": 0, "hours": 0.0})
        s["videos"] = int(s["videos"]) + 1
        s["hours"] = round(float(s["hours"]) + (r.durationSeconds or 0) / 3600, 2)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bball-inventory", description="Inventory game footage (task 0.4).")
    parser.add_argument("root", nargs="?", type=Path, help="folder to scan (default: BBALL_DATA_DIR/raw)")
    parser.add_argument("--out", type=Path, help="where to write the JSON (default: BBALL_DATA_DIR/outputs/)")
    args = parser.parse_args(argv)
    root: Path = args.root or data_path("raw")
    out: Path = args.out or data_path("outputs", "inventory.json")
    records = scan(root)
    summary = summarize(records)
    doc = {
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "root": str(root),
        "summary": summary,
        "videos": [asdict(r) for r in records],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"{len(records)} videos -> {out}")
    for gym, s in summary.items():
        print(f"  {gym}: {s['videos']} videos, {s['hours']} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
