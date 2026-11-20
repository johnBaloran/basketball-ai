"""Clip pipeline: stream frames -> detect -> track -> possession. Writes results next to each other:

    outputs/<gameId>/tracks.jsonl       one line per processed frame (tracks with boxes)
    outputs/<gameId>/possession.json    possession segments and changes
    outputs/<gameId>/annotated.mp4      boxes drawn on the clip (optional)

    bball-run manifest.json [--every-n 2] [--detector yolo] [--no-video]

Everything is written under BBALL_DATA_DIR (outside git). Detection quality isn't claimed: this is the
Phase 1 baseline harness that later models plug into.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO

import numpy as np

from basketball_ai.contracts import Manifest
from basketball_ai.paths import data_dir, data_path
from basketball_ai.tracking import (
    Detector,
    IouTracker,
    TrackedBox,
    holder_in_frame,
    possession_changes,
    possession_segments,
)
from basketball_ai.video import Frame, VideoInfo, iter_frames, probe

COLORS: dict[str, tuple[int, int, int]] = {"player": (0, 200, 255), "ball": (255, 140, 0), "hoop": (255, 0, 200)}


@dataclass(frozen=True)
class RunResult:
    outDir: str
    framesProcessed: int
    tracks: int
    possessionSegments: int
    video: VideoInfo


def draw_boxes(frame: Frame, boxes: list[TrackedBox], thickness: int = 3) -> Frame:
    """Rectangle outlines in place-safe copy (no OpenCV dependency)."""
    img = frame.copy()
    h, w = img.shape[:2]
    for b in boxes:
        color = np.array(COLORS.get(b.label, (255, 255, 255)), dtype=np.uint8)
        x1, y1 = max(0, int(b.box.x1)), max(0, int(b.box.y1))
        x2, y2 = min(w - 1, int(b.box.x2)), min(h - 1, int(b.box.y2))
        if x2 <= x1 or y2 <= y1:
            continue
        t = thickness
        img[y1 : y1 + t, x1:x2] = color
        img[max(y2 - t, y1) : y2, x1:x2] = color
        img[y1:y2, x1 : x1 + t] = color
        img[y1:y2, max(x2 - t, x1) : x2] = color
    return img


class _VideoWriter:
    def __init__(self, path: Path, width: int, height: int, fps: float) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg not found on PATH")
        cmd = [
            ffmpeg, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", f"{fps:.3f}", "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(path),
        ]  # fmt: skip
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        assert self._proc.stdin is not None  # stdin=PIPE above
        self._stdin: IO[bytes] = self._proc.stdin

    def write(self, frame: Frame) -> None:
        self._stdin.write(frame.tobytes())

    def close(self) -> None:
        self._stdin.close()
        if self._proc.wait() != 0:
            raise RuntimeError("ffmpeg failed writing the annotated video")


def run_clip(
    manifest: Manifest,
    detector: Detector,
    out_dir: Path,
    video_path: Path,
    every_n: int = 1,
    write_video: bool = True,
    min_possession_frames: int = 5,
    on_progress: Callable[[int], None] | None = None,
) -> RunResult:
    info = probe(video_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    tracker = IouTracker()
    holders: list[str | None] = []
    frame_numbers: list[int] = []
    track_ids: set[str] = set()
    writer = None
    if write_video:
        writer = _VideoWriter(out_dir / "annotated.mp4", info.width, info.height, info.fps / every_n)
    n = 0
    try:
        with (out_dir / "tracks.jsonl").open("w", encoding="utf-8") as tracks_file:
            for item in iter_frames(
                video_path, manifest.video.startSeconds, manifest.video.endSeconds, every_n, info
            ):
                boxes = tracker.update(detector.detect(item.image))
                track_ids.update(b.trackId for b in boxes)
                balls = [b for b in boxes if b.label == "ball"]
                ball = max(balls, key=lambda b: b.confidence) if balls else None
                holders.append(holder_in_frame(boxes, ball))
                frame_numbers.append(item.index)
                row = {
                    "frame": item.index,
                    "t": item.timestampSeconds,
                    "tracks": [
                        {"id": b.trackId, "label": b.label, "box": asdict(b.box), "conf": round(b.confidence, 3)}
                        for b in boxes
                    ],
                }
                tracks_file.write(json.dumps(row) + "\n")
                if writer is not None:
                    writer.write(draw_boxes(item.image, boxes))
                n += 1
                if on_progress is not None and n % 100 == 0:
                    on_progress(n)
    finally:
        if writer is not None:
            writer.close()
    segments = possession_segments(holders, min_possession_frames)
    possession = {
        "gameId": manifest.gameId,
        "note": "frames are source frame numbers within the clip range; holder = temporary track id",
        "segments": [
            {"trackId": s.trackId, "startFrame": frame_numbers[s.startFrame], "endFrame": frame_numbers[s.endFrame]}
            for s in segments
        ],
        "changes": [
            {"from": a.trackId, "to": b.trackId, "atFrame": frame_numbers[b.startFrame]}
            for a, b in possession_changes(segments)
        ],
    }
    (out_dir / "possession.json").write_text(json.dumps(possession, indent=2) + "\n", encoding="utf-8")
    return RunResult(str(out_dir), n, len(track_ids), len(segments), info)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bball-run", description="Run the clip pipeline on a manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--every-n", type=int, default=1, help="process every n-th frame")
    parser.add_argument("--detector", choices=["yolo"], default="yolo")
    parser.add_argument("--weights", default="yolo11n.pt")
    parser.add_argument("--no-video", action="store_true", help="skip the annotated video")
    args = parser.parse_args(argv)
    manifest = Manifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    video = Path(manifest.video.source)
    video_path = video if video.is_absolute() else data_dir() / video
    from basketball_ai.detectors import YoloDetector

    result = run_clip(
        manifest,
        YoloDetector(weights=args.weights),
        data_path("outputs", manifest.gameId),
        video_path,
        every_n=args.every_n,
        write_video=not args.no_video,
        on_progress=lambda n: print(f"  {n} frames", flush=True),
    )
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
