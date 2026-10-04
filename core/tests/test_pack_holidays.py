#!/usr/bin/env python3
"""Tests for the holidays/ consistency check in obligations/check_packs.py.

A pack ships legal holidays as data (``holidays/<year>.json``) and a rule copies
them into ``lead.exclude_dates``. If the two drift, a holiday is silently counted
as a working day and a late notice can read as on time. These tests prove the
real Massachusetts pack is consistent and that each kind of drift is caught.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
MA_PACK = REPO_ROOT / "obligations" / "packs" / "ma"

sys.path.insert(0, str(REPO_ROOT / "obligations"))
from check_packs import check_pack_holidays  # noqa: E402


class RealPack(unittest.TestCase):
    def test_massachusetts_holidays_agree_with_the_rule(self):
        self.assertEqual(check_pack_holidays(MA_PACK), [])

    def test_the_2026_list_is_present(self):
        data = json.loads((MA_PACK / "holidays" / "2026.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["holidays"]), 12)
        self.assertIn("c. 4, § 7", data["source"])


class DriftIsCaught(unittest.TestCase):
    """Copy the real pack to a scratch dir, break it one way, expect a problem."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pack = self.tmp / "ma"
        shutil.copytree(MA_PACK, self.pack, ignore=shutil.ignore_patterns("fixtures", "*.md"))
        self.rule = self.pack / "ma-oml-meeting-notice.json"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _edit_rule(self, fn):
        data = json.loads(self.rule.read_text(encoding="utf-8"))
        fn(data["lead"]["exclude_dates"])
        self.rule.write_text(json.dumps(data), encoding="utf-8")

    def test_a_holiday_missing_from_the_rule(self):
        self._edit_rule(lambda dates: dates.remove("2026-11-26"))
        problems = check_pack_holidays(self.pack)
        self.assertTrue(any("missing" in p and "2026-11-26" in p for p in problems), problems)

    def test_a_date_no_holidays_file_lists(self):
        self._edit_rule(lambda dates: dates.append("2026-03-17"))
        problems = check_pack_holidays(self.pack)
        self.assertTrue(any("2026-03-17" in p for p in problems), problems)

    def test_a_new_year_file_not_copied_into_the_rule(self):
        (self.pack / "holidays" / "2027.json").write_text(json.dumps({
            "pack": "ma", "year": 2027, "source": "test",
            "holidays": [{"date": "2027-01-01", "name": "New Year's Day"}],
        }), encoding="utf-8")
        problems = check_pack_holidays(self.pack)
        self.assertTrue(any("2027-01-01" in p for p in problems), problems)

    def test_a_date_outside_its_year(self):
        path = self.pack / "holidays" / "2026.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["holidays"][0]["date"] = "2025-01-01"
        path.write_text(json.dumps(data), encoding="utf-8")
        problems = check_pack_holidays(self.pack)
        self.assertTrue(any("not a 2026 date" in p for p in problems), problems)

    def test_a_file_with_no_source(self):
        path = self.pack / "holidays" / "2026.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["source"] = ""
        path.write_text(json.dumps(data), encoding="utf-8")
        problems = check_pack_holidays(self.pack)
        self.assertTrue(any("source" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
