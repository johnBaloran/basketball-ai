"""Dataset builder: labelled frames -> a YOLO training dataset split by whole games (step 2).

    bball-build-dataset outputs/labelling/round1 --labels <export-folder> --name detector-v1

`--labels` is the labelling tool's YOLO export (a folder with one .txt per image; CVAT "YOLO 1.1" exports
put them under obj_train_data/). Frames come from the frame picker's batch folder (images/ + frames.json).

Output, under BBALL_DATA_DIR/datasets/<name>/:

    images/{train,val,test}/   labels/{train,val,test}/
    data.yaml                  for `yolo train`
    test_<gym>.txt + data_test_<gym>.yaml   to measure each gym separately
    report.json                counts per split, class and gym, and every problem found

Splits are by **game** (never frames of one game in two splits) and deterministic, so rebuilding with more
labels keeps games where they were. The test split must stay untouched during development.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from basketball_ai.labels import CLASSES, parse_label_file
from basketball_ai.paths import data_path

SPLITS = ("train", "val", "test")


@dataclass
class BuildReport:
    frames: dict[str, int] = field(default_factory=dict)
    games: dict[str, int] = field(default_factory=dict)
    boxes: dict[str, dict[str, int]] = field(default_factory=dict)
    gyms: dict[str, dict[str, int]] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def assign_split(game: str, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> str:
    """Deterministic split for a game from a hash of its id (stable as games are added)."""
    bucket = int(hashlib.sha256(game.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    if bucket < ratios[0]:
        return "train"
    return "val" if bucket < ratios[0] + ratios[1] else "test"


def split_games(games: list[str], ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, str]:
    """Hash split, but with 3+ games make sure val and test each get at least one game."""
    splits = {g: assign_split(g, ratios) for g in games}
    ordered = sorted(games, key=lambda g: hashlib.sha256(g.encode()).hexdigest())
    for needed in ("test", "val"):
        if len(games) >= 3 and needed not in splits.values():
            donors = [g for g in ordered if splits[g] == "train"]
            if len([g for g in games if splits[g] == "train"]) > 1 and donors:
                splits[donors[0]] = needed
    return splits


def _find_label(labels_dir: Path, stem: str) -> Path | None:
    for candidate in (labels_dir / f"{stem}.txt", labels_dir / "obj_train_data" / f"{stem}.txt"):
        if candidate.exists():
            return candidate
    return None


def build(batch_dirs: list[Path], labels_dir: Path, out: Path) -> BuildReport:
    report = BuildReport()
    frames: list[dict[str, object]] = []
    for batch in batch_dirs:
        meta = json.loads((batch / "frames.json").read_text(encoding="utf-8"))
        if tuple(meta.get("classes", CLASSES)) != CLASSES:
            report.problems.append(f"{batch}: frames were picked for classes {meta.get('classes')}, expected {CLASSES}")
        for f in meta["frames"]:
            frames.append({**f, "_dir": str(batch / "images")})
    splits = split_games(sorted({str(f["game"]) for f in frames}))
    if out.exists():
        shutil.rmtree(out)
    lists: dict[str, list[str]] = defaultdict(list)
    box_counts: dict[str, Counter[str]] = {s: Counter() for s in SPLITS}
    gym_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for f in frames:
        name = str(f["file"])
        stem = Path(name).stem
        label = _find_label(labels_dir, stem)
        if label is None:
            report.problems.append(f"{name}: no label file (an image with no objects still needs an empty file)")
            continue
        boxes, issues = parse_label_file(label.read_text(encoding="utf-8"))
        if issues:
            report.problems.extend(f"{name}: {i}" for i in issues)
            continue
        split = splits[str(f["game"])]
        gym = str(f.get("gym") or "nogym")
        img_out = out / "images" / split / name
        img_out.parent.mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(str(f["_dir"])) / name, img_out)
        (out / "labels" / split / f"{stem}.txt").write_text("".join(f"{b.line()}\n" for b in boxes), encoding="utf-8")
        lists[split].append(str(img_out))
        if split == "test":
            lists[f"test_{gym}"].append(str(img_out))
        box_counts[split].update(CLASSES[b.cls] for b in boxes)
        gym_counts[gym][split] += 1
    report.frames = {s: len(lists[s]) for s in SPLITS}
    report.games = {s: sum(1 for v in splits.values() if v == s) for s in SPLITS}
    report.boxes = {s: {c: box_counts[s][c] for c in CLASSES} for s in SPLITS}
    report.gyms = {g: {s: c[s] for s in SPLITS} for g, c in sorted(gym_counts.items())}
    for s in SPLITS:
        missing = [c for c in CLASSES if box_counts[s][c] == 0 and c != "referee"]
        if report.frames[s] and missing:
            report.warnings.append(f"{s} split has no {', '.join(missing)} boxes")
        if not report.frames[s]:
            report.warnings.append(f"{s} split is empty (need frames from more games)")
    _write_yaml(out / "data.yaml", out, "images/train", "images/val", "images/test")
    for key, paths in lists.items():
        if key.startswith("test_"):
            gym = key.removeprefix("test_")
            (out / f"{key}.txt").write_text("".join(f"{p}\n" for p in paths), encoding="utf-8")
            _write_yaml(out / f"data_test_{gym}.yaml", out, "images/train", "images/val", f"{key}.txt")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report.__dict__, indent=2) + "\n", encoding="utf-8")
    return report


def _write_yaml(path: Path, root: Path, train: str, val: str, test: str) -> None:
    names = "\n".join(f"  {i}: {c}" for i, c in enumerate(CLASSES))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"path: {root}\ntrain: {train}\nval: {val}\ntest: {test}\nnames:\n{names}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bball-build-dataset", description="Build a YOLO dataset split by games.")
    parser.add_argument("batches", nargs="+", type=Path, help="frame-picker batch folders (images/ + frames.json)")
    parser.add_argument("--labels", type=Path, required=True, help="labelling tool's YOLO export folder")
    parser.add_argument("--name", required=True, help="dataset name, e.g. detector-v1")
    args = parser.parse_args(argv)
    out = data_path("datasets", args.name)
    report = build(args.batches, args.labels, out)
    print(json.dumps({"frames": report.frames, "games": report.games, "boxes": report.boxes}, indent=2))
    for w in report.warnings:
        print(f"warning: {w}")
    if report.problems:
        print(f"{len(report.problems)} problems (see {out / 'report.json'}); fix the labels and rebuild")
        return 1
    print(f"dataset ready: {out / 'data.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
