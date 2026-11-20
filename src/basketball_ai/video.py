"""Video metadata, streaming frame reading and clip cutting with ffmpeg/ffprobe.

Frames are **streamed** one at a time from an ffmpeg pipe, never loaded all at once (DEC-005), so the same
code handles a 30-second clip or a full game in constant memory.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import numpy.typing as npt

Frame = npt.NDArray[np.uint8]  # height x width x 3, RGB


class VideoError(RuntimeError):
    pass


@dataclass(frozen=True)
class VideoInfo:
    path: str
    width: int
    height: int
    fps: float
    durationSeconds: float
    codec: str
    frameCount: int | None
    bitRate: int | None
    hasAudio: bool


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise VideoError(f"{name} not found on PATH (run bball-doctor)")
    return path


def probe(path: str | Path) -> VideoInfo:
    """Resolution, frame rate, duration, codec and bitrate of a video file."""
    out = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        raise VideoError(f"ffprobe failed for {path}: {out.stderr.strip()}")
    data = json.loads(out.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise VideoError(f"{path} has no video stream")
    fmt = data.get("format", {})
    fps = float(Fraction(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"))
    duration = float(video.get("duration") or fmt.get("duration") or 0)
    frames = video.get("nb_frames")
    bitrate = video.get("bit_rate") or fmt.get("bit_rate")
    return VideoInfo(
        path=str(path),
        width=int(video["width"]),
        height=int(video["height"]),
        fps=round(fps, 3),
        durationSeconds=round(duration, 3),
        codec=str(video.get("codec_name", "unknown")),
        frameCount=int(frames) if frames and str(frames).isdigit() else None,
        bitRate=int(bitrate) if bitrate and str(bitrate).isdigit() else None,
        hasAudio=any(s.get("codec_type") == "audio" for s in streams),
    )


@dataclass(frozen=True)
class FrameItem:
    index: int  # frame number within the requested range (0-based, before sampling)
    timestampSeconds: float  # position in the source video
    image: Frame


def iter_frames(
    path: str | Path,
    start_seconds: float = 0.0,
    end_seconds: float | None = None,
    every_n: int = 1,
    info: VideoInfo | None = None,
) -> Iterator[FrameItem]:
    """Yield RGB frames from start to end, keeping every `every_n`-th frame. Constant memory."""
    if every_n < 1:
        raise ValueError("every_n must be >= 1")
    meta = info or probe(path)
    w, h = meta.width, meta.height
    cmd = [_tool("ffmpeg"), "-v", "error", "-ss", f"{start_seconds:.3f}", "-i", str(path)]
    if end_seconds is not None:
        cmd += ["-t", f"{max(end_seconds - start_seconds, 0):.3f}"]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-sn", "pipe:1"]
    frame_bytes = w * h * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None  # stdout=PIPE above
    try:
        i = 0
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            if i % every_n == 0:
                image = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
                ts = start_seconds + (i / meta.fps if meta.fps else 0.0)
                yield FrameItem(i, round(ts, 4), image)
            i += 1
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


def cut_clip(
    src: str | Path,
    dst: str | Path,
    start_seconds: float,
    end_seconds: float,
    keep_audio: bool = False,
    crf: int = 18,
) -> VideoInfo:
    """Cut [start, end) from `src` into `dst` (H.264, frame-accurate). Audio is dropped unless asked for."""
    if end_seconds <= start_seconds:
        raise ValueError("end_seconds must be after start_seconds")
    out = Path(dst)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _tool("ffmpeg"),
        "-v",
        "error",
        "-y",
        "-ss",
        f"{start_seconds:.3f}",
        "-i",
        str(src),
        "-t",
        f"{end_seconds - start_seconds:.3f}",
        "-c:v",
        "libx264",
        "-crf",
        str(crf),
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
    ]
    cmd += ["-c:a", "aac"] if keep_audio else ["-an"]
    cmd.append(str(out))
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise VideoError(f"ffmpeg failed cutting {src}: {res.stderr.strip()}")
    return probe(out)
