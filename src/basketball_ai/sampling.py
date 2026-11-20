"""Frame picker: varied frames from clips, ready to label (step 1 of fine-tuning).

    bball-sample-frames                      # clips/ -> outputs/labelling/<batch>/
    bball-sample-frames --every 1.0 --max-per-clip 40 --prelabel yolo --batch round1

For each clip under BBALL_DATA_DIR/clips/<gym>/, takes about one frame per `--every` seconds and skips
near-duplicates (camera not moving, nothing happening). Writes:

    images/<gym>__<clip>__<ms>.jpg       frames to label
    frames.json                          which clip, gym, game and time each frame came from
    prelabels_yolo.zip                   (with --prelabel) ready-made boxes to correct instead of drawing
                                         (CVAT: Upload annotations > "YOLO 1.1")
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

from basketball_ai.images import save_jpeg
from basketball_ai.labels import CLASSES, game_group, to_yolo
from basketball_ai.paths import data_path
from basketball_ai.tracking import Detector
from basketball_ai.video import Frame, iter_frames, probe

Thumb = npt.NDArray[np.float64]

VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm", ".m4v"})


@dataclass(frozen=True)
class SampledFrame:
    file: str
    gym: str | None
    clip: str
    game: str
    timestampSeconds: float
    width: int
    height: int


def thumbnail(image: Frame, size: tuple[int, int] = (32, 18)) -> Thumb:
    """Tiny greyscale version for cheap "is this frame different?" checks."""
    h, w = image.shape[:2]
    ys = np.linspace(0, h - 1, size[1]).astype(int)
    xs = np.linspace(0, w - 1, size[0]).astype(int)
    return np.asarray(image[np.ix_(ys, xs)].mean(axis=2), dtype=np.float64)


def is_new(thumb: Thumb, kept: list[Thumb], min_change: float) -> bool:
    """True when the frame differs from every kept frame by at least `min_change` (mean grey levels)."""
    return all(float(np.abs(thumb - k).mean()) >= min_change for k in kept)


def sample_clip(
    clip: Path,
    out_images: Path,
    gym: str | None,
    every_seconds: float = 1.0,
    max_frames: int = 40,
    min_change: float = 6.0,
) -> list[tuple[SampledFrame, Frame]]:
    info = probe(clip)
    step = max(1, round(info.fps * every_seconds)) if info.fps else 1
    kept: list[tuple[SampledFrame, Frame]] = []
    thumbs: list[Thumb] = []
    for item in iter_frames(clip, every_n=step, info=info):
        thumb = thumbnail(item.image)
        if not is_new(thumb, thumbs[-30:], min_change):
            continue
        name = f"{gym or 'nogym'}__{clip.stem}__{round(item.timestampSeconds * 1000):08d}.jpg"
        save_jpeg(item.image, out_images / name)
        frame = SampledFrame(
            name, gym, clip.name, game_group(clip.stem), item.timestampSeconds, info.width, info.height
        )
        kept.append((frame, item.image))
        thumbs.append(thumb)
        if len(kept) >= max_frames:
            break
    return kept


def find_clips(root: Path) -> list[tuple[Path, str | None]]:
    clips = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES)
    return [(p, p.relative_to(root).parts[0] if len(p.relative_to(root).parts) > 1 else None) for p in clips]


def prelabel_lines(detector: Detector, image: Frame) -> list[str]:
    h, w = image.shape[:2]
    lines: list[str] = []
    for d in detector.detect(image):
        box = to_yolo(CLASSES.index(d.label), d.box.x1, d.box.y1, d.box.x2, d.box.y2, w, h)
        if box is not None:
            lines.append(box.line())
    return lines


def write_prelabels_zip(path: Path, labels: dict[str, list[str]]) -> None:
    """CVAT "YOLO 1.1" annotation archive (obj.names, obj.data, train.txt, obj_train_data/*.txt)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("obj.names", "\n".join(CLASSES) + "\n")
        z.writestr("obj.data", f"classes = {len(CLASSES)}\nnames = obj.names\ntrain = train.txt\n")
        z.writestr("train.txt", "".join(f"obj_train_data/{name}\n" for name in sorted(labels)))
        for name, lines in labels.items():
            z.writestr(f"obj_train_data/{Path(name).stem}.txt", "".join(f"{x}\n" for x in lines))


def run(
    clips: Iterable[tuple[Path, str | None]],
    out_dir: Path,
    every_seconds: float,
    max_per_clip: int,
    detector: Detector | None = None,
) -> list[SampledFrame]:
    frames: list[SampledFrame] = []
    labels: dict[str, list[str]] = {}
    for clip, gym in clips:
        for frame, image in sample_clip(clip, out_dir / "images", gym, every_seconds, max_per_clip):
            frames.append(frame)
            if detector is not None:
                labels[frame.file] = prelabel_lines(detector, image)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "frames.json").write_text(
        json.dumps({"classes": list(CLASSES), "frames": [asdict(f) for f in frames]}, indent=2) + "\n",
        encoding="utf-8",
    )
    if detector is not None:
        write_prelabels_zip(out_dir / "prelabels_yolo.zip", labels)
    return frames


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bball-sample-frames", description="Pick varied frames to label.")
    parser.add_argument("clips", nargs="?", type=Path, help="default: BBALL_DATA_DIR/clips")
    parser.add_argument("--batch", default="round1", help="name of this labelling batch")
    parser.add_argument("--every", type=float, default=1.0, help="seconds between candidate frames")
    parser.add_argument("--max-per-clip", type=int, default=40)
    parser.add_argument("--prelabel", choices=["yolo"], help="pre-fill boxes with a model")
    parser.add_argument("--weights", default="yolo11s.pt")
    args = parser.parse_args(argv)
    root: Path = args.clips or data_path("clips")
    detector: Detector | None = None
    if args.prelabel == "yolo":
        from basketball_ai.detectors import YoloDetector

        detector = YoloDetector(weights=args.weights)
    out = data_path("outputs", "labelling", args.batch)
    frames = run(find_clips(root), out, args.every, args.max_per_clip, detector)
    gyms = sorted({f.gym or "nogym" for f in frames})
    print(f"{len(frames)} frames from {len({f.clip for f in frames})} clips ({', '.join(gyms)}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
