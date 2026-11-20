"""Jersey-crop collector: player crops from a pipeline run, ready for number labelling (step 4).

    bball-crops <gameId>                         # uses outputs/<gameId>/tracks.jsonl and the manifest's clip
    bball-crops <gameId> --every 10 --min-height 120

Reads the tracks that `bball-run` wrote, re-reads the clip once (streaming), and saves the upper body of
each player track every `--every` processed frames, skipping crops too small to read a number. Writes
outputs/<gameId>/crops/<track>__<frame>.jpg and crops.json (track, frame, box) for labelling numbers.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from basketball_ai.contracts import Manifest
from basketball_ai.images import save_jpeg
from basketball_ai.paths import data_dir, data_path
from basketball_ai.tracking import Box
from basketball_ai.video import Frame, iter_frames, probe


@dataclass(frozen=True)
class Crop:
    file: str
    trackId: str
    frame: int
    timestampSeconds: float
    box: Box
    number: int | None = None  # filled in during labelling ("unreadable" stays None)


def jersey_region(box: Box) -> Box:
    """Shoulders to waist, where front and back numbers sit (top 10%..60% of the player box)."""
    h = box.y2 - box.y1
    return Box(box.x1, box.y1 + 0.1 * h, box.x2, box.y1 + 0.6 * h)


def select_crops(rows: list[dict[str, Any]], every: int, min_height: float) -> dict[int, list[tuple[str, Box]]]:
    """frame -> [(track, box)] to crop: each player track every `every` rows it appears in, big enough."""
    seen: dict[str, int] = {}
    picks: dict[int, list[tuple[str, Box]]] = {}
    for row in rows:
        frame = int(row["frame"])
        for t in row["tracks"]:
            if t["label"] != "player":
                continue
            box = Box(**t["box"])
            if box.y2 - box.y1 < min_height:
                continue
            n = seen.get(t["id"], 0)
            seen[t["id"]] = n + 1
            if n % every == 0:
                picks.setdefault(frame, []).append((str(t["id"]), box))
    return picks


def crop(image: Frame, box: Box) -> Frame | None:
    h, w = image.shape[:2]
    x1, y1, x2, y2 = max(0, int(box.x1)), max(0, int(box.y1)), min(w, int(box.x2)), min(h, int(box.y2))
    if x2 - x1 < 2 or y2 - y1 < 2:
        return None
    return image[y1:y2, x1:x2]


def collect(
    tracks_file: Path, video: Path, manifest: Manifest, out_dir: Path, every: int = 10, min_height: float = 120
) -> list[Crop]:
    rows = [json.loads(line) for line in tracks_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    picks = select_crops(rows, every, min_height)
    crops: list[Crop] = []
    info = probe(video)
    for item in iter_frames(video, manifest.video.startSeconds, manifest.video.endSeconds, info=info):
        for track, box in picks.get(item.index, []):
            region = jersey_region(box)
            image = crop(item.image, region)
            if image is None:
                continue
            name = f"{track}__{item.index:06d}.jpg"
            save_jpeg(image, out_dir / name)
            crops.append(Crop(name, track, item.index, item.timestampSeconds, region))
    (out_dir / "crops.json").write_text(
        json.dumps({"gameId": manifest.gameId, "crops": [asdict(c) for c in crops]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return crops


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bball-crops", description="Collect jersey crops from a pipeline run.")
    parser.add_argument("game_id")
    parser.add_argument("--manifest", type=Path, help="default: outputs/<gameId>/manifest.json")
    parser.add_argument("--every", type=int, default=10)
    parser.add_argument("--min-height", type=float, default=120)
    args = parser.parse_args(argv)
    run_dir = data_path("outputs", args.game_id)
    manifest_path: Path = args.manifest or run_dir / "manifest.json"
    manifest = Manifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    video = Path(manifest.video.source)
    crops = collect(
        run_dir / "tracks.jsonl",
        video if video.is_absolute() else data_dir() / video,
        manifest,
        run_dir / "crops",
        args.every,
        args.min_height,
    )
    print(f"{len(crops)} crops from {len({c.trackId for c in crops})} player tracks -> {run_dir / 'crops'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
