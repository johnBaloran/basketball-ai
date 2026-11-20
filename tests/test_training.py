from pathlib import Path

import pytest

from basketball_ai.training import per_class_table, plan_training


def test_plan_starts_fresh_then_resumes(tmp_path: Path) -> None:
    dataset = tmp_path / "datasets" / "v1"
    dataset.mkdir(parents=True)
    (dataset / "data.yaml").write_text("path: x\n")
    models = tmp_path / "models"
    plan = plan_training(dataset, models, "run1")
    assert plan.resume_from is None and plan.args["imgsz"] == 1280 and plan.args["save_period"] == 1
    last = models / "v1" / "run1" / "weights" / "last.pt"
    last.parent.mkdir(parents=True)
    last.write_bytes(b"checkpoint")
    assert plan_training(dataset, models, "run1").resume_from == last


def test_plan_needs_a_built_dataset(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="bball-build-dataset"):
        plan_training(tmp_path / "nope", tmp_path / "models", "run1")


def test_per_class_table() -> None:
    table = per_class_table(
        {"names": {0: "player", 1: "ball"}, "ap_class_index": [0, 1], "p": [0.9, 0.5], "r": [0.8, 0.4], "ap50": [0.85, 0.3], "ap": [0.6, 0.1]}
    )
    assert table["ball"] == {"precision": 0.5, "recall": 0.4, "mAP50": 0.3, "mAP50_95": 0.1}
