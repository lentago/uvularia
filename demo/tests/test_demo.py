#!/usr/bin/env python3
"""Tests for the demonstration vault: that seed.py produces a vault the core
validator passes and the core evaluator reads into an honest board, that it does
so deterministically, and that the name-leak guard actually catches a leak.

Standard library only (unittest). Run from the repo root:

    python3 -m unittest discover -s demo/tests -p "test_*.py" -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "demo"))
sys.path.insert(0, str(REPO_ROOT / "core"))

import seed  # noqa: E402
import check_name_leak  # noqa: E402
import validate as core_validate  # noqa: E402
import evaluate as core_evaluate  # noqa: E402
from check_examples import validate as schema_validate  # noqa: E402


class SeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vault, cls.rows = seed.generate()

    def test_core_validator_passes(self):
        cfg = core_validate.load_config(self.vault)
        problems, ran, _skipped = core_validate.validate_vault(self.vault, cfg)
        self.assertEqual(problems, [], "generated vault must pass core/validate.py")
        # The checks that keep a public vault honest must actually be running.
        for name in ("schema", "approved_source", "visibility", "privacy"):
            self.assertIn(name, ran)

    def test_board_has_a_red_and_an_amber(self):
        states = {row["state"] for row in self.rows}
        self.assertIn("red", states, "the board must show at least one red")
        self.assertIn("amber", states, "the board must show at least one amber")
        # And never fake green: a satisfied row carries the record and a time.
        for row in self.rows:
            if row["state"] == "green":
                self.assertIsNotNone(row["satisfied_by"])
                self.assertIsNotNone(row["published_at"])

    def test_standing_matches_the_schema(self):
        schema = json.loads(
            (REPO_ROOT / "core" / "schema" / "standing.schema.json").read_text())
        self.assertEqual(schema_validate(schema, self.rows, schema), [])

    def test_committed_standing_is_reproduced(self):
        committed = json.loads((self.vault / "standing.json").read_text())
        fresh = core_evaluate.evaluate(self.vault, now=seed.ASOF, warn_days=seed.WARN_DAYS)
        self.assertEqual(committed, fresh)

    def test_generation_is_deterministic(self):
        before = _tree_digest(self.vault)
        seed.generate()
        self.assertEqual(before, _tree_digest(self.vault),
                         "regenerating with the same seed must be byte-identical")


class NameLeakTest(unittest.TestCase):
    def test_catches_a_planted_leak(self):
        needles = check_name_leak.read_identity()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "minutes.md").write_text(
                "The board met; see " + ", ".join(v for _, v in needles) + ".\n")
            hits = check_name_leak.scan(tmp, needles)
        fields = {field for _, _, field, _ in hits}
        for field, _ in needles:
            self.assertIn(field, fields)
        self.assertIn("short_name_slug", fields)

    def test_selftest_exits_zero(self):
        self.assertEqual(check_name_leak.selftest(), 0)

    def test_repository_has_no_live_leak(self):
        needles = check_name_leak.read_identity()
        hits = check_name_leak.scan(
            REPO_ROOT, needles,
            excluded_dirs=[check_name_leak.GENERATED, *check_name_leak.DOC_DIRS],
            excluded_files=[check_name_leak.ORG_YAML, *check_name_leak.DOC_FILES])
        self.assertEqual(hits, [], f"identity leaked outside its home: {hits}")


def _tree_digest(root):
    import hashlib
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(path.read_bytes())
    return h.hexdigest()


if __name__ == "__main__":
    unittest.main()
