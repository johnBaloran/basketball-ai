"""Environment check: reports what this runtime (Colab, Kaggle or a local machine) has for video work.

Run with `bball-doctor`. Exits non-zero when a required tool is missing. The GPU line is informational:
a missing GPU never fails the check, because code and tests run on CPU.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass

REQUIRED_TOOLS = ("ffmpeg", "ffprobe")
MIN_PYTHON = (3, 12)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = True


def runtime_name() -> str:
    if os.environ.get("COLAB_RELEASE_TAG"):
        return "Google Colab"
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return "Kaggle"
    return "local"


def tool_version(name: str) -> str | None:
    """First line of `<tool> -version`, or None when the tool isn't on PATH."""
    path = shutil.which(name)
    if path is None:
        return None
    out = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=10, check=False)
    first = out.stdout.splitlines()[0] if out.stdout else ""
    return first or path


def gpu_info() -> str | None:
    """NVIDIA GPU name and memory, or None when there's no NVIDIA GPU."""
    path = shutil.which("nvidia-smi")
    if path is None:
        return None
    out = subprocess.run(
        [path, "--query-gpu=name,memory.total", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    line = out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout.strip() else ""
    return line or None


def run_checks() -> list[Check]:
    checks = [
        Check(
            "python",
            sys.version_info[:2] >= MIN_PYTHON,
            f"{platform.python_version()} (need >= {'.'.join(map(str, MIN_PYTHON))})",
        ),
        Check(
            "runtime", True, f"{runtime_name()} ({platform.system()} {platform.machine()})", required=False
        ),
    ]
    for tool in REQUIRED_TOOLS:
        version = tool_version(tool)
        checks.append(Check(tool, version is not None, version or "not found on PATH"))
    gpu = gpu_info()
    checks.append(
        Check(
            "gpu", gpu is not None, gpu or "none (CPU only; in Colab pick Runtime > T4 GPU)", required=False
        )
    )
    return checks


def main() -> int:
    checks = run_checks()
    for c in checks:
        status = "ok" if c.ok else ("MISSING" if c.required else "info")
        print(f"[{status}] {c.name}: {c.detail}")
    return 0 if all(c.ok for c in checks if c.required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
