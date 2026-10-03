"""The publish build step, end to end, on a two-record fixture vault.

This is the same ``core/bundle.py build`` the vault template's publish workflow
runs. It proves the build produces every artifact a publish must — the corpus
bundle, the standing file, the Atom feed, and the receipt — and that each one
validates against its schema. (The fifth publish output, the provenance
attestation, is produced by ``actions/attest-build-provenance`` in CI over the
corpus file; it needs GitHub's OIDC and cannot be made locally, so this test
asserts the corpus it would attest exists and is valid, and the workflow wires
the attestation.)
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_DIR = CORE_DIR / "schema"
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(SCHEMA_DIR))

import bundle  # noqa: E402
from check_examples import validate as schema_validate  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "publish"
PUBLISHED_AT = "2026-10-01T14:03:11Z"
RUN_URL = "https://github.com/example-org/example-records/actions/runs/123456"
COMMIT = "0a1b2c3"


def _schema(name):
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


class PublishBuildTest(unittest.TestCase):
    def setUp(self):
        # Copy the fixture so the build's working receipts/ write never touches
        # the committed tree.
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.vault = self.tmp / "vault"
        shutil.copytree(FIXTURE, self.vault)
        self.out = self.tmp / "out"
        self.result = bundle.build(
            vault=self.vault, out_dir=self.out, published_at=PUBLISHED_AT,
            run_url=RUN_URL, commit=COMMIT)

    def test_all_four_artifacts_exist(self):
        self.assertTrue((self.out / self.result["corpus"]).is_file())
        self.assertTrue((self.out / "standing.json").is_file())
        self.assertTrue((self.out / "feed.xml").is_file())
        self.assertTrue((self.out / self.result["receipt"]).is_file())

    def test_corpus_validates_and_names_by_digest(self):
        corpus = json.loads((self.out / self.result["corpus"]).read_text(encoding="utf-8"))
        self.assertEqual(schema_validate(_schema("bundle"), corpus, _schema("bundle")), [])
        self.assertEqual(self.result["corpus"], f"corpus-{corpus['digest']}.json")
        self.assertEqual(corpus["published_at"], PUBLISHED_AT)
        # Two approved, public records in, two entries out, in id order.
        self.assertEqual([e["doc_id"] for e in corpus["records"]],
                         ["2026-09-01-trail-open", "2026-09-16-board-minutes"])
        minutes = corpus["records"][1]
        self.assertEqual(minutes["title"], "Board meeting minutes, 2026-09-16")  # the H1
        self.assertIn("minutes", minutes["tags"])                                 # parent folder
        self.assertEqual(minutes["volatility"], "stable")
        self.assertEqual(minutes["certainty"], "verified")
        self.assertEqual(corpus["records"][0]["certainty"], "inferred")           # reported -> inferred
        self.assertFalse(minutes["archived"])

    def test_standing_validates_and_has_no_fake_green(self):
        standing = json.loads((self.out / "standing.json").read_text(encoding="utf-8"))
        self.assertEqual(schema_validate(_schema("standing"), standing, _schema("standing")), [])
        by_id = {row["id"]: row for row in standing}
        # The minutes are published on time by this run's receipt -> green.
        self.assertEqual(by_id["demo-minutes-timely"]["state"], "green")
        self.assertEqual(by_id["demo-minutes-timely"]["published_at"], PUBLISHED_AT)
        # No report record exists -> no-data, never a green with nothing behind it.
        self.assertEqual(by_id["demo-annual-report"]["state"], "no-data")
        self.assertIsNone(by_id["demo-annual-report"]["satisfied_by"])

    def test_receipt_validates_and_is_server_stamped(self):
        receipt_path = self.out / self.result["receipt"]
        # Named for the publish day and the digest.
        self.assertEqual(receipt_path.name, f"2026-10-01-{self.result['digest']}.md")
        # Its frontmatter is the receipt object; read it the way the evaluator does.
        import evaluate
        fm = evaluate._frontmatter(receipt_path.read_text(encoding="utf-8"), receipt_path)
        self.assertEqual(schema_validate(_schema("receipt"), fm, _schema("receipt")), [])
        self.assertEqual(fm["published_at"], PUBLISHED_AT)
        self.assertEqual(fm["run_url"], RUN_URL)
        self.assertEqual(sorted(fm["records"]["added"]),
                         ["2026-09-01-trail-open", "2026-09-16-board-minutes"])
        self.assertEqual(fm["standing"], {"green": 1, "amber": 0, "red": 0, "no_data": 1})

    def test_feed_is_well_formed_atom(self):
        feed_text = (self.out / "feed.xml").read_text(encoding="utf-8")
        self.assertEqual(bundle._feed_is_valid(feed_text), [])
        # The one announcement is an entry; the minutes are not.
        self.assertIn("urn:uvularia:record:2026-09-01-trail-open", feed_text)
        self.assertNotIn("2026-09-16-board-minutes", feed_text)

    def test_digest_is_stable_across_runs(self):
        again = self.tmp / "out2"
        second = bundle.build(vault=self.vault, out_dir=again, published_at="2027-01-01T00:00:00Z",
                              run_url=RUN_URL, commit="deadbee")
        # Same records, same digest, regardless of publish time.
        self.assertEqual(self.result["digest"], second["digest"])


if __name__ == "__main__":
    unittest.main()


class ReceiptNamesAreUniquePerPublish(unittest.TestCase):
    """Two publishes over an unchanged corpus must leave two receipts (issue: a
    day-plus-digest name let the second overwrite the first and erase provenance)."""

    def test_same_digest_different_instant_gives_different_names(self):
        import importlib.util
        from pathlib import Path
        spec = importlib.util.spec_from_file_location("bundle_mod", Path(__file__).resolve().parents[1] / "bundle.py")
        bundle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bundle)
        a = bundle.receipt_name("2026-10-03T21:57:30Z", "f" * 64)
        b = bundle.receipt_name("2026-10-03T22:42:56Z", "f" * 64)
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("2026-10-03T215730Z-"), a)
        self.assertTrue(b.startswith("2026-10-03T224256Z-"), b)
        self.assertEqual(a[-len("f" * 64) - 3:], "f" * 64 + ".md")
