"""The ``due`` timing kind: the same date every year (uvularia#116).

A 12-month cadence measures from the last posting, so a filing made late on
December 15 for a November 1 deadline keeps the row green until the next
December. A fixed date does not move: each November 1 needs its own filing, a
late filing is that year's late filing, and the row stays red until the next
November 1 is met on time. These tests pin that down, plus the warning window,
amendments, a vault with no history, February 29, and the track record.

    python3 -m unittest core.tests.test_due -v
"""

import sys
import unittest
from datetime import date
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(CORE / "schema"))

import evaluate  # noqa: E402

WARN = 7
RULE = {
    "id": "annual-report-november-1", "title": "Annual report filed by November 1",
    "pack": "test", "record_type": "report", "subjects": ["annual-report"],
    "source": "test", "disclaimer_ref": "policy.disclaimer",
    "due": {"month": 11, "day": 1},
}


def report(record_id):
    return {"id": record_id, "type": "report", "status": "approved",
            "effective": record_id[:10], "subjects": ["annual-report"]}


def judge(postings, now, rule=RULE):
    """``postings`` is ``[(record id, published_at), ...]``."""
    records = [report(rid) for rid, _ in postings]
    receipts = [{"published_at": at, "records": {"added": [rid]}} for rid, at in postings]
    pubs = evaluate.publish_index(receipts)
    when = evaluate.parse_datetime(now)
    row = evaluate.evaluate_obligation(rule, records, pubs, when, WARN)
    row["history"] = evaluate.obligation_history(rule, records, pubs, when, 730)
    return row


ON_TIME_2025 = ("2025-10-20-annual-report", "2025-10-20T12:00:00Z")


class FixedDateEveryYear(unittest.TestCase):
    def test_met_on_time_is_green_until_the_window_then_amber_then_red(self):
        for now, state, deadline in (
                ("2026-10-24T12:00:00Z", "green", "2026-11-01"),
                ("2026-10-25T12:00:00Z", "amber", "2026-11-01"),
                ("2026-11-01T23:59:00Z", "amber", "2026-11-01"),   # due today
                ("2026-11-02T00:00:00Z", "red", "2026-11-01")):    # missed
            with self.subTest(now=now):
                row = judge([ON_TIME_2025], now)
                self.assertEqual((row["state"], row["deadline"]), (state, deadline))

    def test_a_filing_this_year_is_green_for_this_due_date(self):
        row = judge([ON_TIME_2025, ("2026-10-15-annual-report", "2026-10-15T09:00:00Z")],
                    "2026-10-30T12:00:00Z")
        self.assertEqual((row["state"], row["satisfied_by"], row["gap"]),
                         ("green", "2026-10-15-annual-report", -17))

    def test_a_late_filing_stays_red_until_the_next_due_date_is_met(self):
        # The cadence proxy's failure: filed December 15 for November 1.
        late = ("2026-12-15-annual-report", "2026-12-15T10:00:00Z")
        row = judge([ON_TIME_2025, late], "2027-03-01T12:00:00Z")
        self.assertEqual((row["state"], row["deadline"], row["published_at"], row["gap"]),
                         ("red", "2026-11-01", "2026-12-15T10:00:00Z", 44))
        self.assertIsNone(row["satisfied_by"])
        # Still red in the next warning window: the late filing was last year's.
        self.assertEqual(judge([ON_TIME_2025, late], "2027-10-28T12:00:00Z")["state"], "red")
        # The next November 1 met on time turns it green.
        row = judge([ON_TIME_2025, late, ("2027-10-01-annual-report", "2027-10-01T10:00:00Z")],
                    "2027-10-28T12:00:00Z")
        self.assertEqual((row["state"], row["satisfied_by"]), ("green", "2027-10-01-annual-report"))

    def test_a_skipped_year_is_settled_first(self):
        # 2025 on time, nothing for 2026, one filing on 2027-10-15. It settles the
        # skipped 2026 date (late), not 2027: one filing cannot be both, and the
        # board does not guess the kinder reading.
        postings = [ON_TIME_2025, ("2027-10-15-annual-report", "2027-10-15T10:00:00Z")]
        row = judge(postings, "2027-10-20T12:00:00Z")
        self.assertEqual((row["state"], row["deadline"], row["published_at"]),
                         ("red", "2026-11-01", "2027-10-15T10:00:00Z"))
        # A second filing settles 2027.
        row = judge(postings + [("2027-10-25-annual-report", "2027-10-25T10:00:00Z")],
                    "2027-10-28T12:00:00Z")
        self.assertEqual((row["state"], row["satisfied_by"]), ("green", "2027-10-25-annual-report"))

    def test_an_amendment_in_the_same_year_does_not_count_for_the_next(self):
        amended = [ON_TIME_2025, ("2025-10-28-annual-report", "2025-10-28T12:00:00Z")]
        row = judge(amended, "2026-11-02T00:00:00Z")
        self.assertEqual(row["state"], "red", "the 2025 amendment is not the 2026 filing")

    def test_no_history_is_no_data_then_amber_and_never_an_invented_red(self):
        self.assertEqual(judge([], "2026-10-01T00:00:00Z")["state"], "no-data")
        self.assertEqual(judge([], "2026-10-30T00:00:00Z")["state"], "amber")
        # The day after: still nothing posted, but nothing to date a breach from.
        row = judge([], "2026-11-02T00:00:00Z")
        self.assertEqual((row["state"], row["deadline"]), ("no-data", "2027-11-01"))

    def test_a_first_ever_filing_after_the_date_counts_for_the_next_year(self):
        # History starts at the first posting: no breach is invented before it.
        row = judge([("2026-12-15-annual-report", "2026-12-15T10:00:00Z")], "2027-03-01T12:00:00Z")
        self.assertEqual((row["state"], row["deadline"]), ("green", "2027-11-01"))

    def test_february_29_falls_on_the_28th_in_a_common_year(self):
        rule = dict(RULE, due={"month": 2, "day": 29})
        self.assertEqual(evaluate.due_date(rule["due"], 2027), date(2027, 2, 28))
        self.assertEqual(evaluate.due_date(rule["due"], 2028), date(2028, 2, 29))
        row = judge([("2027-02-27-annual-report", "2027-02-27T10:00:00Z")], "2027-02-28T12:00:00Z",
                    rule=rule)
        self.assertEqual((row["state"], row["deadline"]), ("green", "2027-02-28"))

    def test_history_counts_each_due_date_once_and_keeps_a_late_one(self):
        postings = [("2024-10-20-annual-report", "2024-10-20T12:00:00Z"),
                    ("2025-12-15-annual-report", "2025-12-15T10:00:00Z"),   # late for 2025
                    ("2026-10-01-annual-report", "2026-10-01T10:00:00Z")]
        # On 2026-11-02 the 730-day window starts 2024-11-02, so it holds the
        # 2025 due date (filed late) and the 2026 one (on time).
        row = judge(postings, "2026-11-02T00:00:00Z")
        self.assertEqual(row["history"], {"window_days": 730, "evaluated": 2, "breaches": 1})
        # A day earlier, 2024-11-01 is in the window and 2026-11-01 is not yet past.
        row = judge(postings, "2026-10-31T00:00:00Z")
        self.assertEqual(row["history"], {"window_days": 730, "evaluated": 2, "breaches": 1})

    def test_the_row_validates_against_the_standing_schema(self):
        import json
        from check_examples import validate
        schema = json.loads((CORE / "schema" / "standing.schema.json").read_text())
        row = judge([ON_TIME_2025], "2026-10-25T12:00:00Z")
        self.assertEqual(validate(schema, [row], schema), [])


if __name__ == "__main__":
    unittest.main()
