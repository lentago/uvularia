#!/usr/bin/env python3
"""Validate every obligation file in obligations/packs/ against
core/schema/obligation.schema.json.  Skips README.md and fixtures/ directories.

Run from the repo root:  python3 obligations/check_packs.py
Exit status is non-zero if any obligation file fails validation.

Python 3.12, standard library only.  No pip install, ever.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "core" / "schema" / "obligation.schema.json"
PACKS_DIR = Path(__file__).resolve().parent / "packs"

# Re-use the validator that ships with the schemas rather than duplicating it.
sys.path.insert(0, str(REPO_ROOT / "core" / "schema"))
from check_examples import validate  # noqa: E402 — path insert must come first


def _load(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"schema not found: {SCHEMA_PATH}", file=sys.stderr)
        return 1

    schema = _load(SCHEMA_PATH)
    failures = 0
    checked = 0

    for pack_dir in sorted(PACKS_DIR.iterdir()):
        if not pack_dir.is_dir():
            continue
        for obligation_file in sorted(pack_dir.glob("*.json")):
            if obligation_file.parent.name == "fixtures":
                continue
            checked += 1
            instance = _load(obligation_file)
            errors = validate(schema, instance, schema)
            rel = obligation_file.relative_to(REPO_ROOT)
            if errors:
                failures += 1
                print(f"FAIL  {rel}:")
                for err in errors:
                    print(f"        - {err}")
            else:
                print(f"ok    {rel} validates")

    print()
    if failures:
        print(f"{failures} problem(s) across {checked} obligation file(s).")
        return 1
    print(f"all {checked} obligation file(s) validate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
