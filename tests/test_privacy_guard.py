import json
import subprocess
from pathlib import Path

import pytest

from basketball_ai.privacy_guard import check_file, scan

FAKE_GH_TOKEN = "ghp_" + "a" * 36


@pytest.mark.parametrize(
    "path", ["game.mp4", "clips/c1.MOV", "frame_0001.jpg", "best.pt", "roster.csv", "x.tar.gz"]
)
def test_media_weights_and_data_files_are_blocked(path: str) -> None:
    assert check_file(path, b"x")


def test_code_and_docs_are_fine() -> None:
    assert check_file("src/basketball_ai/doctor.py", b"print('hi')\n") == []
    assert check_file("docs/PLAN.md", b"# plan\n") == []


def test_large_files_are_blocked() -> None:
    (problem,) = check_file("notes.txt", b"x" * 1_000_001)
    assert "bytes" in problem.reason


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        (f'token = "{FAKE_GH_TOKEN}"', "GitHub token"),
        # Built in pieces so this test file doesn't trip the guard itself
        ("uri = 'mongodb+srv://user:" + "pa55@cluster0.example.net/db'", "Database URL"),
        ("-----BEGIN RSA " + "PRIVATE KEY-----", "Private key"),
        ("sk_live_" + "0" * 24, "Stripe key"),
    ],
)
def test_secrets_are_blocked(text: str, kind: str) -> None:
    problems = check_file("config.py", text.encode())
    assert any(kind in p.reason for p in problems)


def test_notebook_outputs_are_blocked() -> None:
    clean = {"cells": [{"cell_type": "code", "source": "1", "outputs": []}]}
    dirty = {
        "cells": [{"cell_type": "code", "source": "1", "outputs": [{"output_type": "stream", "text": "x"}]}]
    }
    assert check_file("n.ipynb", json.dumps(clean).encode()) == []
    assert "saved outputs" in check_file("n.ipynb", json.dumps(dirty).encode())[0].reason


def test_allow_list_permits_a_named_fixture() -> None:
    assert check_file("tests/fixtures/tiny.png", b"x", frozenset({"tests/fixtures/tiny.png"})) == []


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_scan_checks_staged_files(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "ok.py").write_text("x = 1\n")
    (tmp_path / "clip.mp4").write_bytes(b"\x00")
    _git(tmp_path, "add", "ok.py", "clip.mp4")
    assert [p.path for p in scan(tmp_path, staged=True)] == ["clip.mp4"]
