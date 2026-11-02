#!/usr/bin/env python3
"""Validate every obligation file in obligations/packs/ against
core/schema/obligation.schema.json.  Skips README.md and fixtures/ directories.

A pack may also ship legal-holiday lists as data, one file per year, under
``holidays/<year>.json``. Any rule in that pack whose ``lead`` carries
``exclude_dates`` must list exactly the union of those files' dates, and its
``calendar_years`` must name exactly those files' years, so a year added to
holidays/ but not to the rule (or the reverse) fails here rather than silently
counting a holiday as a working day.

The files must also cover the coming year: always the current year, and from
1 October the next one too. The evaluator already refuses a window in a year
with no list (it shows no-data); this makes the yearly update fail CI in time,
before a year starts with no list at all.

Run from the repo root:  python3 obligations/check_packs.py [--today YYYY-MM-DD]
Exit status is non-zero if any obligation file fails validation.

Python 3.12, standard library only.  No pip install, ever.
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "core" / "schema" / "obligation.schema.json"
PACKS_DIR = Path(__file__).resolve().parent / "packs"

# From this (month, day) on, next year's holidays must be on file as well.
NEXT_YEAR_FROM = (10, 1)

# Re-use the validator that ships with the schemas rather than duplicating it.
sys.path.insert(0, str(REPO_ROOT / "core" / "schema"))
from check_examples import validate  # noqa: E402 — path insert must come first


def _load(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def check_pack_holidays(pack_dir: Path, today: date | None = None) -> list[str]:
    """Problems with ``pack_dir``'s holidays/ files and the rules that use them.

    Returns a list of human-readable problems; empty means consistent. A pack
    with no holidays/ directory and no ``exclude_dates`` has nothing to check.
    ``today`` (default: the real date) decides which years must be covered."""
    problems = []
    dates = set()
    years = set()
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
        years.add(year)
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
        calendar = lead.get("calendar_years")
        if calendar is None:
            problems.append(f"{obligation_file.name}: exclude_dates has no calendar_years, so the "
                            f"evaluator cannot tell a year with no list; set it to {sorted(years)}")
        elif set(calendar) != years:
            problems.append(f"{obligation_file.name}: calendar_years {sorted(calendar)} does not "
                            f"match the holidays/ files {sorted(years)}")

    if years:
        today = today or date.today()
        due = {today.year}
        if (today.month, today.day) >= NEXT_YEAR_FROM:
            due.add(today.year + 1)
        for year in sorted(due - years):
            problems.append(f"holidays/{year}.json is missing: add {year}'s statewide legal "
                            f"holidays, copy the dates into the rule's exclude_dates and the "
                            f"year into its calendar_years (README, \"Legal holidays are data\")")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate the obligation packs.")
    parser.add_argument("--today", type=date.fromisoformat,
                        help="judge holiday coverage as of this date (default: today)")
    args = parser.parse_args(argv)
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
        problems = check_pack_holidays(pack_dir, args.today)
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
