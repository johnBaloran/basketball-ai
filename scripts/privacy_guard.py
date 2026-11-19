#!/usr/bin/env python3
"""Run the privacy guard without installing the package (used by the pre-commit hook)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from basketball_ai.privacy_guard import main  # noqa: E402

raise SystemExit(main())
