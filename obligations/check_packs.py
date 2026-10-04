#!/usr/bin/env python3
"""Validate every obligation file in obligations/packs/ against
core/schema/obligation.schema.json.  Skips README.md and fixtures/ directories.

A pack may also ship legal-holiday lists as data, one file per year, under
``holidays/<year>.json``. Any rule in that pack whose ``lead`` carries
``exclude_dates`` must list exactly the union of those files' dates, so a year
added to holidays/ but not to the rule (or the reverse) fails here rather than
silently counting a holiday as a working day.

Run from the repo root:  python3 obligations/check_packs.py
Exit status is non-zero if any obligation file fails validation.

Python 3.12, standard library only.  No pip install, ever.
"""

import json
import re
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


def check_pack_holidays(pack_dir: Path) -> list[str]:
    """Problems with ``pack_dir``'s holidays/ files and the rules that use them.

    Returns a list of human-readable problems; empty means consistent. A pack
    with no holidays/ directory and no ``exclude_dates`` has nothing to check."""
    problems = []
    dates = set()
    holidays_dir = pack_dir / "holidays"
    for path in sorted(holidays_dir.glob("*.json")) if holidays_dir.is_dir() else []:
        try:
            data = _load(path)
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: not valid JSON ({exc})")
            continue
        year = data.get("year") if isinstance(data, dict) else None
        if not isinstance(year, int) or path.stem != str(year):
            problems.append(f"{path.name}: 'year' must be an integer matching the file name")
            continue
        if not isinstance(data.get("source"), str) or not data["source"].strip():
            problems.append(f"{path.name}: 'source' must cite where the dates come from")
        for item in data.get("holidays") or []:
            day = item.get("date") if isinstance(item, dict) else None
            if not isinstance(day, str) or not re.fullmatch(rf"{year}-\d{{2}}-\d{{2}}", day):
                problems.append(f"{path.name}: {day!r} is not a {year} date (YYYY-MM-DD)")
                continue
            if not isinstance(item.get("name"), str) or not item["name"].strip():
                problems.append(f"{path.name}: {day} has no 'name'")
            dates.add(day)
        if not data.get("holidays"):
            problems.append(f"{path.name}: 'holidays' is empty")

    for obligation_file in sorted(pack_dir.glob("*.json")):
        lead = _load(obligation_file).get("lead") or {}
        if "exclude_dates" not in lead:
            continue
        listed = set(lead["exclude_dates"])
        missing = sorted(dates - listed)
        extra = sorted(listed - dates)
        if missing:
            problems.append(f"{obligation_file.name}: exclude_dates is missing holidays/ dates {missing}")
        if extra:
            problems.append(f"{obligation_file.name}: exclude_dates has dates no holidays/ file lists {extra}")
    return problems


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
        problems = check_pack_holidays(pack_dir)
        rel_pack = pack_dir.relative_to(REPO_ROOT)
        if problems:
            failures += 1
            print(f"FAIL  {rel_pack}/holidays:")
            for problem in problems:
                print(f"        - {problem}")
        elif (pack_dir / "holidays").is_dir():
            print(f"ok    {rel_pack}/holidays agree with the rules that use them")

    print()
    if failures:
        print(f"{failures} problem(s) across {checked} obligation file(s).")
        return 1
    print(f"all {checked} obligation file(s) validate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
