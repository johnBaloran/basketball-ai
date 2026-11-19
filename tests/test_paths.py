from pathlib import Path

import pytest

from basketball_ai.paths import DataDirError, data_dir, data_path


def test_unset_data_dir_explains_what_to_do(tmp_path: Path) -> None:
    with pytest.raises(DataDirError, match="BBALL_DATA_DIR is not set"):
        data_dir({}, repo_root=tmp_path)


def test_data_dir_inside_repo_is_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    for inside in (repo, repo / "data"):
        with pytest.raises(DataDirError, match="inside the git repo"):
            data_dir({"BBALL_DATA_DIR": str(inside)}, repo_root=repo)


def test_data_dir_outside_repo_is_used(tmp_path: Path) -> None:
    repo, data = tmp_path / "repo", tmp_path / "drive" / "basketball-ai-data"
    repo.mkdir()
    assert data_dir({"BBALL_DATA_DIR": str(data)}, repo_root=repo) == data.resolve()
    clip = data_path("clips", "gym-a", "c1.mp4", env={"BBALL_DATA_DIR": str(data)}, repo_root=repo)
    assert clip == data.resolve() / "clips" / "gym-a" / "c1.mp4"


def test_unknown_data_folder_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown data folder"):
        data_path("videos", env={"BBALL_DATA_DIR": str(tmp_path / "d")}, repo_root=tmp_path / "r")
