"""Detector adapters. YOLO needs the optional `cv` extra (`pip install -e ".[cv]"`, done in Colab).

The pretrained COCO model finds `person` and `sports ball`; it knows nothing about our gyms, so its
accuracy on league footage is unmeasured until Phase 1 evaluation. Treat it as a baseline only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from basketball_ai.tracking import Box, Detection, Label
from basketball_ai.video import Frame

# COCO class names -> our labels (pretrained baseline)
COCO_LABELS: dict[str, Label] = {"person": "player", "sports ball": "ball"}


@dataclass
class YoloDetector:
    """Ultralytics YOLO. `weights` is a model name (downloaded on first use) or a path in BBALL_DATA_DIR."""

    weights: str = "yolo11n.pt"
    confidence: float = 0.25
    class_map: dict[str, Label] | None = None
    device: str | None = None  # "cuda:0" in Colab, None = auto

    def __post_init__(self) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as err:  # pragma: no cover - depends on optional extra
            raise RuntimeError('YOLO needs the cv extra: pip install -e ".[cv]"') from err
        self._model: Any = YOLO(self.weights)
        self._names: dict[int, str] = dict(self._model.names)
        self._map = self.class_map or COCO_LABELS

    def detect(self, frame: Frame) -> list[Detection]:  # pragma: no cover - needs model weights
        result = self._model.predict(frame, conf=self.confidence, device=self.device, verbose=False)[0]
        out: list[Detection] = []
        for xyxy, cls, conf in zip(
            result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist(), strict=True
        ):
            label = self._map.get(self._names.get(int(cls), ""))
            if label is not None:
                out.append(Detection(label, Box(*map(float, xyxy)), float(conf)))
        return out
