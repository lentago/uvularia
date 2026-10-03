#!/usr/bin/env python3
"""Run every obligations pack's own fixtures through core/evaluate.py.

`obligations/packs/<pack>/fixtures/*.{pass,fail}.json` (added with the Massachusetts
pack, issue #14) are each pack's claim about how its own rule behaves: a minimal
record set, an `as_of` instant, and the `expected_state` the evaluator should
produce. Nothing ran that claim against the evaluator until now — a pack and
`evaluate.py` could drift and nothing would notice. This test loads every fixture
under every pack and asserts `expected_state`, so they can't silently disagree.

Fixture records are deliberately smaller than a real record (see
`obligations/packs/ma/README.md#fixtures`): they carry only the fields the rule
kind needs, using `published_at` or `approved` as a test-convenience stand-in for
"when this record went public" — in production that only ever comes from a
publish receipt (see `core/evaluate.md`). They also omit `subjects`, since the
fixture's one record is always the one the rule is meant to match. The adapter
below turns that convenience shape into the records/receipts `evaluate.py` reads;
it lives here, not in `evaluate.py`, so the evaluator keeps reading real receipts
only.

Adding a second state's pack needs no change here: both discovery loops glob
`obligations/packs/*/...` and pick up whatever fixtures and obligation files show
up on disk.
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
REPO_ROOT = CORE.parent
PACKS_DIR = REPO_ROOT / "obligations" / "packs"

sys.path.insert(0, str(CORE))
import evaluate  # noqa: E402

WARN_DAYS = 7  # matches the CLI default and core/tests/test_evaluate.py


def _load_obligations():
    """id -> obligation dict, for every obligations/packs/<pack>/<id>.json."""
    obligations = {}
    for path in sorted(PACKS_DIR.glob("*/*.json")):
        if path.parent.name == "fixtures":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        obligations[data["id"]] = data
    return obligations


def _load_fixtures():
    """(path, fixture dict) for every obligations/packs/<pack>/fixtures/*.json."""
    fixtures = []
    for path in sorted(PACKS_DIR.glob("*/fixtures/*.json")):
        fixtures.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return fixtures


def evaluate_fixture(obligation, fixture):
    """Evaluate one pack fixture against ``obligation`` and return its row.

    The adapter: a fixture record's ``published_at`` (lead rules) or ``approved``
    (lag/cadence rules) becomes the ``published_at`` of a synthetic receipt — the
    only server-side time ``evaluate.py`` will ever trust — and a record missing
    ``subjects`` is assumed to carry the obligation's own subjects, since a
    fixture's record is always meant to be a candidate for the rule it tests.
    """
    records, receipts = [], []
    for record in fixture["records"]:
        record = dict(record)
        record.setdefault("subjects", obligation.get("subjects", []))
        published = record.get("published_at") or record.get("approved")
        if published:
            receipts.append({"published_at": published, "records": {"added": [record["id"]]}})
        records.append(record)
    pubs = evaluate.publish_index(receipts)
    now = evaluate.parse_datetime(fixture["as_of"])
    return evaluate.evaluate_obligation(obligation, records, pubs, now, WARN_DAYS)


class PackFixturesAgreeWithTheEvaluator(unittest.TestCase):
    """Every pack fixture, run for real, must land on its own expected_state."""

    @classmethod
    def setUpClass(cls):
        cls.obligations = _load_obligations()
        cls.fixtures = _load_fixtures()

    def test_at_least_one_pack_fixture_was_discovered(self):
        # A glob that silently matches nothing would make every test below pass
        # vacuously — that is exactly the "never fake green" failure mode applied
        # to the test suite itself.
        self.assertGreater(len(self.fixtures), 0, "no pack fixtures found under obligations/packs/*/fixtures/")

    def test_every_fixture_names_a_known_obligation(self):
        for path, fixture in self.fixtures:
            with self.subTest(fixture=path.name):
                self.assertIn(
                    fixture["obligation_id"], self.obligations,
                    f"{path}: no obligations/packs/*/{fixture['obligation_id']}.json",
                )

    def test_every_fixture_matches_its_expected_state(self):
        for path, fixture in self.fixtures:
            with self.subTest(fixture=f"{path.parent.parent.name}/{path.name}"):
                obligation = self.obligations[fixture["obligation_id"]]
                row = evaluate_fixture(obligation, fixture)
                self.assertEqual(
                    row["state"], fixture["expected_state"],
                    f"{path}: expected {fixture['expected_state']!r}, evaluator said {row['state']!r} ({row})",
                )


class TheFixtureHarnessCanFail(unittest.TestCase):
    """A synthetic case (not a real pack fixture) proving the comparison above is
    a real assertion and not something that agrees with itself: a notice posted
    after its lead deadline is red, never green, no matter what a fixture claims."""

    def test_a_wrong_expected_state_is_caught(self):
        obligation = {
            "id": "synthetic-lead",
            "record_type": "notice",
            "subjects": ["x"],
            "lead": {"hours": 48},
        }
        fixture = {
            "obligation_id": "synthetic-lead",
            "as_of": "2026-10-04",
            "records": [{
                "id": "2026-10-03-late-notice",
                "type": "notice",
                "status": "approved",
                "effective": "2026-10-04",
                "published_at": "2026-10-03T10:00:00Z",  # 24h notice, not 48h — late
            }],
            "expected_state": "green",  # deliberately wrong
        }
        row = evaluate_fixture(obligation, fixture)
        self.assertEqual(row["state"], "red")
        self.assertNotEqual(row["state"], fixture["expected_state"])


if __name__ == "__main__":
    unittest.main()
