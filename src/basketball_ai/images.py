"""Save frames and crops as JPEG (Pillow)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from basketball_ai.video import Frame


def save_jpeg(image: Frame, path: Path, quality: int = 92) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(path, format="JPEG", quality=quality)
