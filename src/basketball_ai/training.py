"""Fine-tune YOLO in Colab with resume, then evaluate on the untouched test split, overall and per gym (step 3).

    bball-train detector-v1                    # train (or resume) on BBALL_DATA_DIR/datasets/detector-v1
    bball-train detector-v1 --epochs 100 --imgsz 1280 --model yolo11s.pt
    bball-train detector-v1 --evaluate-only

Runs are saved under BBALL_DATA_DIR/models/<dataset>/<run>/ (weights/best.pt, last.pt), so a Colab
disconnect loses at most one epoch: run the same command again and it resumes from last.pt.
Needs the `cv` extra (ultralytics) and a GPU runtime.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from basketball_ai.labels import CLASSES
from basketball_ai.paths import data_path


@dataclass(frozen=True)
class TrainPlan:
    dataset: Path
    run_dir: Path
    resume_from: Path | None
    args: dict[str, object]


def plan_training(
    dataset: Path,
    models_root: Path,
    run: str,
    model: str = "yolo11s.pt",
    epochs: int = 100,
    imgsz: int = 1280,
    batch: int = 8,
    patience: int = 25,
) -> TrainPlan:
    """What to run: a fresh run, or resume when this run already has a last.pt."""
    data_yaml = dataset / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"{data_yaml} not found; build the dataset first (bball-build-dataset)")
    run_dir = models_root / dataset.name / run
    last = run_dir / "weights" / "last.pt"
    args: dict[str, object] = {
        "data": str(data_yaml),
        "model": model,
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "patience": patience,
        "project": str(run_dir.parent),
        "name": run,
        "exist_ok": True,
        "save_period": 1,  # checkpoint every epoch (Colab can disconnect)
        "seed": 0,
        "deterministic": True,
    }
    return TrainPlan(dataset, run_dir, last if last.exists() else None, args)


def per_class_table(metrics: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """Precision, recall, mAP50 and mAP50-95 per class from an Ultralytics metrics object's summary."""
    out: dict[str, dict[str, float]] = {}
    names: Mapping[int, str] = metrics.get("names", {})
    for i, cls in enumerate(metrics.get("ap_class_index", [])):
        name = names.get(int(cls), CLASSES[int(cls)] if int(cls) < len(CLASSES) else str(cls))
        out[name] = {
            "precision": round(float(metrics["p"][i]), 4),
            "recall": round(float(metrics["r"][i]), 4),
            "mAP50": round(float(metrics["ap50"][i]), 4),
            "mAP50_95": round(float(metrics["ap"][i]), 4),
        }
    return out


def _metrics_summary(result: Any) -> dict[str, Any]:  # pragma: no cover - needs ultralytics
    box = result.box
    return {
        "names": dict(result.names),
        "ap_class_index": [int(c) for c in result.ap_class_index],
        "p": list(box.p),
        "r": list(box.r),
        "ap50": list(box.ap50),
        "ap": list(box.ap),
    }


def evaluate(weights: Path, dataset: Path, imgsz: int) -> dict[str, Any]:  # pragma: no cover - needs a GPU
    from ultralytics import YOLO

    model = YOLO(str(weights))
    report: dict[str, Any] = {
        "weights": str(weights),
        "evaluatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    yamls = {"all gyms": dataset / "data.yaml"} | {
        p.stem.removeprefix("data_test_"): p for p in sorted(dataset.glob("data_test_*.yaml"))
    }
    for label, yaml in yamls.items():
        result = model.val(data=str(yaml), split="test", imgsz=imgsz, plots=False, verbose=False)
        report[label] = per_class_table(_metrics_summary(result))
    return report


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - needs a GPU
    parser = argparse.ArgumentParser(prog="bball-train", description="Fine-tune YOLO with resume.")
    parser.add_argument("dataset", help="dataset name under BBALL_DATA_DIR/datasets")
    parser.add_argument("--run", default="run1")
    parser.add_argument("--model", default="yolo11s.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--evaluate-only", action="store_true")
    args = parser.parse_args(argv)
    from ultralytics import YOLO

    plan = plan_training(
        data_path("datasets", args.dataset),
        data_path("models"),
        args.run,
        args.model,
        args.epochs,
        args.imgsz,
        args.batch,
    )
    if not args.evaluate_only:
        if plan.resume_from is not None:
            print(f"resuming from {plan.resume_from}")
            YOLO(str(plan.resume_from)).train(resume=True)
        else:
            YOLO(args.model).train(**plan.args)
    best = plan.run_dir / "weights" / "best.pt"
    report = evaluate(best, plan.dataset, args.imgsz)
    out = plan.run_dir / "evaluation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"evaluation -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
