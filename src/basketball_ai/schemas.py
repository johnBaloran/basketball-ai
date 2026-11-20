"""Write JSON Schema files for the contracts (for Recess and other consumers): `bball-schemas`."""

from __future__ import annotations

import json
from pathlib import Path

from basketball_ai.contracts import CONTRACTS, SCHEMA_VERSION

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def render(name: str) -> str:
    schema = CONTRACTS[name].model_json_schema()
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://github.com/johnBaloran/basketball-ai/schemas/{name}-{SCHEMA_VERSION}.json",
        **schema,
    }
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def write_all(directory: Path = SCHEMA_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in CONTRACTS:
        path = directory / f"{name}-{SCHEMA_VERSION}.json"
        path.write_text(render(name), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    for p in write_all():
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
