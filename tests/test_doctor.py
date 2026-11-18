import shutil
import subprocess
from typing import Any

import pytest

import basketball_ai
from basketball_ai import doctor


def test_package_has_version() -> None:
    assert basketball_ai.__version__


def test_python_version_is_supported() -> None:
    checks = {c.name: c for c in doctor.run_checks()}
    assert checks["python"].ok


def test_missing_ffmpeg_fails_the_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    checks = {c.name: c for c in doctor.run_checks()}
    assert not checks["ffmpeg"].ok
    assert checks["ffmpeg"].detail == "not found on PATH"
    assert doctor.main() == 1


def test_no_gpu_is_reported_but_never_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    real_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "nvidia-smi" else real_which(name))
    gpu = {c.name: c for c in doctor.run_checks()}["gpu"]
    assert not gpu.ok
    assert not gpu.required
    assert "CPU only" in gpu.detail


def test_gpu_name_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        out = "Tesla T4, 15360 MiB\n" if args[0].endswith("nvidia-smi") else f"{args[0]} version 6.1\n"
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    checks = {c.name: c for c in doctor.run_checks()}
    assert checks["gpu"].ok
    assert checks["gpu"].detail == "Tesla T4, 15360 MiB"


def test_runtime_detects_colab(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLAB_RELEASE_TAG", "release-colab-2026")
    assert doctor.runtime_name() == "Google Colab"
