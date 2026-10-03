#!/usr/bin/env python3
"""Tests for the per-row ``history`` track record in core/evaluate.py.

The board row shows the *current* standing of a rule, so one timely posting
retires the red that late ones earned. ``history`` carries what the row cannot:
how many past deadlines in a trailing window had a receipt-dated outcome, and how
many of those were breaches. These tests prove the window math and the one
invariant the issue names — a breach counts even after a later timely posting —
against a fixture whose numbers are worked out by hand, not read back from the
code.

The fixture (``fixtures/history``) holds a six-notice rule with late and timely
postings across three years, a rule whose only deadline is still in the future,
and a rule whose only record was never published.
"""

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(CORE / "schema"))

import evaluate  # noqa: E402
from check_examples import validate as schema_validate  # noqa: E402

VAULT = HERE / "fixtures" / "history"
NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)


def history_by_id(window_days):
    rows = evaluate.evaluate(VAULT, now=NOW, warn_days=7, history_days=window_days)
    return {r["id"]: r["history"] for r in rows}


class WindowMath(unittest.TestCase):
    """The six-notice rule, at three window widths, against a hand-derived oracle.

    Postings (deadline = meeting − 48h): 2025-03 late, 2025-08 on time,
    2025-11 late, 2026-02 late, 2026-05 on time (the later timely one), and a
    2026-09 notice whose deadline is still ahead of ``now`` (2026-07-01)."""

    def test_two_year_window_counts_every_past_deadline(self):
        # Window start 2024-07-01: all five past deadlines; the 2026-09 one is
        # still in the future and is not counted.
        self.assertEqual(
            history_by_id(730)["notice-history"],
            {"window_days": 730, "evaluated": 5, "breaches": 3},
        )

    def test_one_year_window_drops_the_oldest(self):
        # Window start 2025-07-01: the 2025-03 late notice falls out, so four
        # deadlines remain and two of them were breaches.
        self.assertEqual(
            history_by_id(365)["notice-history"],
            {"window_days": 365, "evaluated": 4, "breaches": 2},
        )

    def test_six_month_window_keeps_only_the_recent_two(self):
        # Window start 2026-01-02: only the 2026-02 (late) and 2026-05 (timely)
        # deadlines remain.
        self.assertEqual(
            history_by_id(180)["notice-history"],
            {"window_days": 180, "evaluated": 2, "breaches": 1},
        )

    def test_a_breach_counts_even_after_a_later_timely_posting(self):
        # The issue's named invariant. In the one-year window the 2025-11 and
        # 2026-02 notices were late; the 2026-05 notice was on time and later than
        # both. The later timely posting does not retire the earlier breaches.
        hist = history_by_id(365)["notice-history"]
        self.assertEqual(hist["breaches"], 2)
        self.assertLess(hist["breaches"], hist["evaluated"])


class NoHistoryYet(unittest.TestCase):
    """A window with no past, receipt-dated deadline is ``null`` — "no history
    yet" — never a fabricated zero-breach row (invariant 5)."""

    def test_a_future_only_deadline_has_no_history(self):
        # Published early, but the deadline is still ahead of now: a receipt-dated
        # outcome, yet no *past* deadline to summarise.
        self.assertIsNone(history_by_id(730)["future-only"])

    def test_an_unpublished_record_has_no_history(self):
        # A past deadline, but the record was never published: no receipt-dated
        # outcome, so it is never counted and never invented from the calendar.
        self.assertIsNone(history_by_id(730)["unpublished-only"])

    def test_null_is_not_zero_breaches(self):
        # The distinction the board draws: null renders "no history yet", which is
        # not the same as a real {evaluated: n, breaches: 0}.
        self.assertIsNone(history_by_id(730)["unpublished-only"])
        self.assertIsNotNone(history_by_id(730)["notice-history"])


class HistoryIsAdditive(unittest.TestCase):
    """History must not disturb a row's current-state fields, and every row still
    validates against the standing schema with ``history`` present."""

    def test_current_state_fields_are_untouched(self):
        rows = evaluate.evaluate(VAULT, now=NOW)
        for row in rows:
            with self.subTest(obligation=row["id"]):
                for field in ("id", "state", "satisfied_by", "deadline", "published_at", "gap"):
                    self.assertIn(field, row)
                self.assertIn(row["state"], ("green", "amber", "red", "no-data"))

    def test_output_validates_against_the_standing_schema(self):
        rows = evaluate.evaluate(VAULT, now=NOW)
        schema = json.loads((CORE / "schema" / "standing.schema.json").read_text())
        errors = schema_validate(schema, rows, schema)
        self.assertEqual(errors, [], f"standing output failed its schema: {errors}")


class SchemaRejectsMalformedHistory(unittest.TestCase):
    """Prove the new schema branch can fail: a row whose history is the wrong
    shape must be rejected, so the check is not vacuous."""

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((CORE / "schema" / "standing.schema.json").read_text())

    def _row(self, history):
        return [{
            "id": "x", "state": "green", "satisfied_by": None,
            "deadline": None, "published_at": None, "gap": None, "history": history,
        }]

    def test_valid_history_object_passes(self):
        row = self._row({"window_days": 365, "evaluated": 4, "breaches": 2})
        self.assertEqual(schema_validate(self.schema, row, self.schema), [])

    def test_null_history_passes(self):
        self.assertEqual(schema_validate(self.schema, self._row(None), self.schema), [])

    def test_missing_field_is_rejected(self):
        row = self._row({"window_days": 365, "evaluated": 4})
        self.assertNotEqual(schema_validate(self.schema, row, self.schema), [])

    def test_negative_breaches_is_rejected(self):
        row = self._row({"window_days": 365, "evaluated": 4, "breaches": -1})
        self.assertNotEqual(schema_validate(self.schema, row, self.schema), [])

    def test_extra_property_is_rejected(self):
        row = self._row({"window_days": 365, "evaluated": 4, "breaches": 2, "oops": 1})
        self.assertNotEqual(schema_validate(self.schema, row, self.schema), [])

    def test_omitting_history_entirely_is_rejected(self):
        row = [{
            "id": "x", "state": "green", "satisfied_by": None,
            "deadline": None, "published_at": None, "gap": None,
        }]
        self.assertNotEqual(schema_validate(self.schema, row, self.schema), [])


if __name__ == "__main__":
    unittest.main()
