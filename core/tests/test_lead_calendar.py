#!/usr/bin/env python3
"""Tests for the weekdays-only / excluded-dates ``lead`` window (issue #13).

The Open Meeting Law asks for 48 hours' notice "excluding Saturdays, Sundays and
legal holidays". ``lead`` now carries ``weekdays_only`` and ``exclude_dates`` so a
rule can say that. These tests check the deadline arithmetic against dates worked
out by hand on a calendar (not read back from the code), run the fixture vault
``fixtures/lead-calendar`` end to end through ``evaluate()`` — the live row AND
the ``history`` track record — and prove the schema rejects malformed values.

October-November 2026, for reading the cases: Mon 12 Oct is Columbus Day;
Thu 22, Fri 23, Sat 24, Sun 25, Mon 26 Oct; Wed 28, Fri 30 Oct; Wed 4, Fri 6 Nov;
Thu 26 Nov is Thanksgiving, Mon 30 Nov.
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

VAULT = HERE / "fixtures" / "lead-calendar"
NOW = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)  # every deadline is past


def _utc(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc)


class DeadlineArithmetic(unittest.TestCase):
    """``lead_deadline`` against calendar-derived instants."""

    def test_plain_rule_is_unchanged(self):
        # No flags: exactly event - 48h, weekend or not.
        self.assertEqual(evaluate.lead_deadline({"hours": 48}, _utc(2026, 10, 26)), _utc(2026, 10, 24))

    def test_monday_meeting_skips_the_weekend(self):
        # Sun and Sat cost nothing; Fri and Thu spend 24h each -> start of Thursday.
        spec = {"hours": 48, "weekdays_only": True}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 26)), _utc(2026, 10, 22))

    def test_days_and_hours_agree(self):
        spec = {"days": 2, "weekdays_only": True}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 26)), _utc(2026, 10, 22))

    def test_friday_meeting_has_no_weekend_to_skip(self):
        spec = {"hours": 48, "weekdays_only": True}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 30)), _utc(2026, 10, 28))

    def test_partial_day_hours(self):
        # 30 weekday hours before a Monday: all of Friday, then 6h of Thursday.
        spec = {"hours": 30, "weekdays_only": True}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 26)), _utc(2026, 10, 22, 18))

    def test_monday_holiday_pushes_back_a_day(self):
        # Tuesday 13 Oct: Mon 12 (Columbus Day), Sun, Sat skipped; Fri, Thu spent.
        spec = {"hours": 48, "weekdays_only": True, "exclude_dates": ["2026-10-12"]}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 13)), _utc(2026, 10, 8))

    def test_thanksgiving_mid_window(self):
        # Monday 30 Nov: Sun, Sat skipped; Fri 27 spent; Thu 26 skipped; Wed 25 spent.
        spec = {"hours": 48, "weekdays_only": True, "exclude_dates": ["2026-11-26"]}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 11, 30)), _utc(2026, 11, 25))

    def test_a_holiday_on_a_weekend_is_not_skipped_twice(self):
        # Sat 4 Jul 2026 is already a weekend day; listing it changes nothing.
        spec = {"hours": 48, "weekdays_only": True}
        listed = dict(spec, exclude_dates=["2026-07-04"])
        event = _utc(2026, 7, 6)
        self.assertEqual(evaluate.lead_deadline(listed, event), evaluate.lead_deadline(spec, event))
        self.assertEqual(evaluate.lead_deadline(listed, event), _utc(2026, 7, 2))

    def test_exclude_dates_works_without_weekdays_only(self):
        # Only the listed date is skipped; the weekend counts as usual.
        spec = {"hours": 48, "exclude_dates": ["2026-10-25"]}
        self.assertEqual(evaluate.lead_deadline(spec, _utc(2026, 10, 26)), _utc(2026, 10, 23))


# The fixture vault's expected board, written out by hand. A change to the walk
# that moves any deadline by a day, or flips any state, breaks a row here.
EXPECTED = {
    #                         state    deadline      gap  breaches
    "fri-mon-plain":         ("green", "2026-10-24", -1, 0),
    "fri-mon-weekdays":      ("red",   "2026-10-22",  1, 1),
    "fri-mon-weekdays-days": ("red",   "2026-10-22",  1, 1),
    "wed-fri-weekdays":      ("green", "2026-10-28",  0, 0),
    "wed-fri-late-weekdays": ("red",   "2026-11-04",  0, 1),
    "holiday-weekdays-only": ("green", "2026-10-09", -1, 0),
    "holiday-excluded":      ("red",   "2026-10-08",  0, 1),
}


class FixtureVault(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["id"]: r for r in evaluate.evaluate(VAULT, now=NOW)}

    def test_every_rule_is_present(self):
        self.assertEqual(set(self.rows), set(EXPECTED))

    def test_rows_match_the_hand_derived_board(self):
        for oid, (state, deadline, gap, _) in EXPECTED.items():
            with self.subTest(obligation=oid):
                row = self.rows[oid]
                self.assertEqual((row["state"], row["deadline"], row["gap"]), (state, deadline, gap))
                # A late notice is red with the record present: never satisfied_by.
                if state == "red":
                    self.assertIsNone(row["satisfied_by"])
                else:
                    self.assertIsNotNone(row["satisfied_by"])

    def test_friday_evening_for_monday_is_late_only_under_weekdays(self):
        self.assertEqual(self.rows["fri-mon-plain"]["state"], "green")
        self.assertEqual(self.rows["fri-mon-weekdays"]["state"], "red")

    def test_the_holiday_is_what_makes_it_late(self):
        self.assertEqual(self.rows["holiday-weekdays-only"]["state"], "green")
        self.assertEqual(self.rows["holiday-excluded"]["state"], "red")

    def test_history_uses_the_same_window(self):
        # The track record judges each posting with the same calendar, so the
        # same Friday-evening posting is a breach under one rule and not the other.
        for oid, (_, _, _, breaches) in EXPECTED.items():
            with self.subTest(obligation=oid):
                self.assertEqual(
                    self.rows[oid]["history"],
                    {"window_days": evaluate.DEFAULT_HISTORY_DAYS, "evaluated": 1, "breaches": breaches},
                )

    def test_output_validates_against_the_standing_schema(self):
        schema = json.loads((CORE / "schema" / "standing.schema.json").read_text())
        self.assertEqual(schema_validate(schema, list(self.rows.values()), schema), [])


class SchemaAcceptsAndRejects(unittest.TestCase):
    """The new ``lead`` fields validate when well formed and fail when not."""

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((CORE / "schema" / "obligation.schema.json").read_text())

    def _errors(self, lead):
        ob = {
            "id": "x", "title": "x", "pack": "test", "record_type": "notice",
            "subjects": [], "source": "x", "disclaimer_ref": "x", "lead": lead,
        }
        return schema_validate(self.schema, ob, self.schema)

    def test_well_formed_lead_passes(self):
        self.assertEqual(self._errors({"hours": 48, "weekdays_only": True, "exclude_dates": ["2026-10-12"]}), [])

    def test_non_boolean_weekdays_only_is_rejected(self):
        self.assertNotEqual(self._errors({"hours": 48, "weekdays_only": "yes"}), [])

    def test_non_iso_exclude_date_is_rejected(self):
        self.assertNotEqual(self._errors({"hours": 48, "exclude_dates": ["10/12/2026"]}), [])

    def test_flags_alone_are_not_a_window(self):
        self.assertNotEqual(self._errors({"weekdays_only": True}), [])

    def test_unknown_lead_field_is_still_rejected(self):
        self.assertNotEqual(self._errors({"hours": 48, "business_hours": True}), [])


if __name__ == "__main__":
    unittest.main()
