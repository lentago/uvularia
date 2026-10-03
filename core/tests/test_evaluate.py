#!/usr/bin/env python3
"""Tests for core/evaluate.py — stdlib unittest, no third-party libraries.

The fixture vault under ``fixtures/vault`` carries one obligation per rule kind
in each of the four states (plus a late-notice that is red even though the record
exists). The EXPECTED table below is derived by hand, not read back from the code,
so a regression in the evaluator makes a test fail rather than silently agreeing
with itself. Each expectation is also, in effect, a fixture that proves its state
can be produced — flip the logic and the matching row stops matching.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(CORE / "schema"))

import evaluate  # noqa: E402
from check_examples import validate as schema_validate  # noqa: E402

VAULT = HERE / "fixtures" / "vault"
NOW = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)
WARN = 7

# id -> (state, satisfied_by, deadline, published_at, gap)
EXPECTED = {
    # lead — notice ≥ 48h before the meeting (event = record.effective)
    "lead-green":   ("green",   "2026-11-01-lead-green-notice", "2026-10-30", "2026-10-01T09:00:00Z", -29),
    "lead-red":     ("red",     None,                           "2026-09-14", "2026-09-15T10:00:00Z", 1),
    "lead-amber":   ("amber",   None,                           "2026-10-04", None,                   -1),
    "lead-nodata":  ("no-data", None,                           None,         None,                   None),
    # lag — minutes within 30 days after the meeting
    "lag-green":    ("green",   "2026-09-20-lag-green-minutes", "2026-10-20", "2026-09-25T11:00:00Z", -25),
    "lag-red":      ("red",     None,                           "2026-08-31", "2026-09-20T12:00:00Z", 20),
    "lag-amber":    ("amber",   None,                           "2026-10-10", None,                   -7),
    "lag-nodata":   ("no-data", None,                           None,         None,                   None),
    # cadence — policy reviewed every 12 months (deadline = next due)
    "cadence-green":  ("green",   "2026-05-01-cad-green-policy", "2027-05-01", "2026-05-02T09:00:00Z", -210),
    "cadence-red":    ("red",     None,                          "2026-01-01", "2025-01-02T09:00:00Z", 275),
    "cadence-amber":  ("amber",   "2025-10-05-cad-amber-policy", "2026-10-05", "2025-10-06T09:00:00Z", -2),
    "cadence-nodata": ("no-data", None,                          None,         None,                   None),
    # one_off — a filing due on a fixed date
    "oneoff-green":  ("green",   "2026-09-28-oneoff-green-filing", "2026-09-30", "2026-09-28T09:00:00Z", -2),
    "oneoff-red":    ("red",     None,                             "2026-09-01", "2026-09-15T09:00:00Z", 14),
    "oneoff-amber":  ("amber",   None,                             "2026-10-08", None,                   -5),
    "oneoff-nodata": ("no-data", None,                             "2026-12-31", None,                   None),
}


class EvaluateMatrix(unittest.TestCase):
    """Every rule kind, every state, against the fixture vault."""

    @classmethod
    def setUpClass(cls):
        cls.rows = evaluate.evaluate(VAULT, now=NOW, warn_days=WARN)
        cls.by_id = {r["id"]: r for r in cls.rows}

    def test_every_obligation_has_exactly_one_row(self):
        self.assertEqual(sorted(self.by_id), sorted(EXPECTED))
        self.assertEqual(len(self.rows), len(EXPECTED))

    def test_rows_match_the_hand_derived_oracle(self):
        for oid, (state, satisfied_by, deadline, published_at, gap) in EXPECTED.items():
            with self.subTest(obligation=oid):
                row = self.by_id[oid]
                self.assertEqual(row["state"], state)
                self.assertEqual(row["satisfied_by"], satisfied_by)
                self.assertEqual(row["deadline"], deadline)
                self.assertEqual(row["published_at"], published_at)
                self.assertEqual(row["gap"], gap)

    def test_a_balanced_board_of_all_four_states(self):
        counts = {s: 0 for s in ("green", "amber", "red", "no-data")}
        for row in self.rows:
            counts[row["state"]] += 1
        self.assertEqual(counts, {"green": 4, "amber": 4, "red": 4, "no-data": 4})

    def test_late_notice_is_red_even_though_the_record_exists(self):
        # The invariant the issue calls out by name: a record that published after
        # its lead deadline is red, and the lateness is visible (published_at set),
        # never a green and never a null.
        row = self.by_id["lead-red"]
        self.assertEqual(row["state"], "red")
        self.assertIsNone(row["satisfied_by"])
        self.assertIsNotNone(row["published_at"])
        self.assertGreater(row["gap"], 0)

    def test_no_receipt_never_renders_as_green(self):
        # A present-but-unpublished record (lead/lag amber) and an approved policy
        # with no receipt (cadence no-data) must never be green: with no server-side
        # time there is nothing that proves the obligation was met.
        for oid in ("lead-amber", "lag-amber", "cadence-nodata"):
            with self.subTest(obligation=oid):
                self.assertNotEqual(self.by_id[oid]["state"], "green")
                self.assertIsNone(self.by_id[oid]["satisfied_by"])

    def test_output_validates_against_the_standing_schema(self):
        schema = json.loads((CORE / "schema" / "standing.schema.json").read_text())
        errors = schema_validate(schema, self.rows, schema)
        self.assertEqual(errors, [], f"standing output failed its schema: {errors}")


class EmptyAndMissing(unittest.TestCase):
    """A vault with rules but no records or receipts is all no-data, never green —
    invariant 5. Missing directories must not crash the evaluator."""

    def test_rules_but_no_records_or_receipts_is_all_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "obligations").mkdir()
            (root / "obligations" / "r.yaml").write_text(
                "- id: lonely\n"
                "  title: \"A rule with nothing to show\"\n"
                "  pack: test\n"
                "  record_type: notice\n"
                "  subjects: [x]\n"
                "  source: \"test\"\n"
                "  disclaimer_ref: policy.yaml#d\n"
                "  lead:\n"
                "    hours: 48\n",
                encoding="utf-8",
            )
            rows = evaluate.evaluate(root, now=NOW)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["state"], "no-data")
            self.assertIsNone(rows[0]["satisfied_by"])

    def test_entirely_empty_vault_is_empty_standing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = evaluate.evaluate(Path(tmp), now=NOW)
            self.assertEqual(rows, [])


class YamlReader(unittest.TestCase):
    """The carried YAML subset reader: mappings, nested mappings, block and flow
    sequences, sequences of mappings, comments, quotes, scalar typing."""

    def test_reads_an_obligation_list(self):
        text = (
            "# a comment\n"
            "- id: one\n"
            "  record_type: notice\n"
            "  subjects: [a, b]\n"
            "  lead:\n"
            "    hours: 48\n"
            "- id: two\n"
            "  one_off:\n"
            "    due: 2026-12-31\n"
        )
        data = evaluate.load_yaml(text)
        self.assertEqual(data[0]["id"], "one")
        self.assertEqual(data[0]["subjects"], ["a", "b"])
        self.assertEqual(data[0]["lead"], {"hours": 48})
        self.assertEqual(data[1]["one_off"], {"due": "2026-12-31"})

    def test_reads_frontmatter_with_nested_map_and_seq_of_maps(self):
        text = (
            "---\n"
            "id: 2026-09-16-x\n"
            'title: "A: colon in a quoted string"\n'
            "type: notice\n"
            "status: approved\n"
            "source:\n"
            "  kind: pdf\n"
            "  sha256: deadbeef\n"
            "subjects: [meetings]\n"
            "corrections:\n"
            "  - date: 2026-09-17\n"
            '    note: "fixed"\n'
            "---\n"
            "prose below is ignored\n"
        )
        data = evaluate._frontmatter(text, Path("x.md"))
        self.assertEqual(data["id"], "2026-09-16-x")
        self.assertEqual(data["title"], "A: colon in a quoted string")
        self.assertEqual(data["source"], {"kind": "pdf", "sha256": "deadbeef"})
        self.assertEqual(data["subjects"], ["meetings"])
        self.assertEqual(data["corrections"], [{"date": "2026-09-17", "note": "fixed"}])

    def test_scalar_typing_and_hash_outside_quotes(self):
        self.assertEqual(evaluate._parse_scalar("48"), 48)
        self.assertEqual(evaluate._parse_scalar("-3"), -3)
        self.assertEqual(evaluate._parse_scalar("1.5"), 1.5)
        self.assertIs(evaluate._parse_scalar("true"), True)
        self.assertIsNone(evaluate._parse_scalar("null"))
        self.assertEqual(evaluate._parse_scalar('"2026"'), "2026")
        # a '#' flush against text is part of the value; a ' #' starts a comment
        self.assertEqual(evaluate._strip_comment("ref: policy.yaml#anchor"), "ref: policy.yaml#anchor")
        self.assertEqual(evaluate._strip_comment("x: 1  # trailing"), "x: 1")


class TimeHelpers(unittest.TestCase):

    def test_add_months_clamps_day_of_month(self):
        from datetime import date
        self.assertEqual(evaluate.add_months(date(2025, 1, 31), 1), date(2025, 2, 28))
        self.assertEqual(evaluate.add_months(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(evaluate.add_months(date(2026, 5, 1), 12), date(2027, 5, 1))
        self.assertEqual(evaluate.add_months(date(2026, 11, 15), 3), date(2027, 2, 15))

    def test_parse_datetime_normalises_to_utc(self):
        self.assertEqual(evaluate.parse_datetime("2026-10-01T09:00:00Z"),
                         datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc))
        self.assertEqual(evaluate.parse_datetime("2026-10-01"),
                         datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(evaluate.parse_datetime("2026-10-01T05:00:00-04:00"),
                         datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc))
        self.assertIsNone(evaluate.parse_datetime("not a time"))


if __name__ == "__main__":
    unittest.main()
