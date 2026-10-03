"""The vault template vendors core/ (see templates/records/core/CORE_VERSION).

A vendored copy that drifts from the canonical core/ would mean a client's CI
runs code nobody reviewed here. This test fails the PR when any vendored file
differs from its canonical counterpart, or when a canonical file the sync
script copies is missing from the template. Fix by re-running
templates/records/scripts/sync-core.sh (or copying the changed file), never by
editing the vendored copy by hand.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "core"
VENDORED = ROOT / "templates" / "records" / "core"

# Exactly the set scripts/sync-core.sh copies.
TOP = ["validate.py", "evaluate.py", "bundle.py", "README.md", "evaluate.md"]
SCHEMA = ["check_examples.py", "README.md"]


def _expected_files():
    for name in TOP:
        yield Path(name)
    for name in SCHEMA:
        yield Path("schema") / name
    for p in sorted((CANON / "schema").glob("*.schema.json")):
        yield Path("schema") / p.name
    for p in sorted((CANON / "schema" / "examples").iterdir()):
        if p.is_file():
            yield Path("schema") / "examples" / p.name


SITE_SCHEMA = ROOT / "templates" / "site" / "schema"
SITE_SCHEMAS = ["bundle.schema.json", "standing.schema.json"]


class VendoredCoreMatchesCanonical(unittest.TestCase):
    def test_site_template_schemas_are_byte_identical(self):
        """templates/site vendors the two schemas its build validates against."""
        drift = []
        for name in SITE_SCHEMAS:
            canon, vend = CANON / "schema" / name, SITE_SCHEMA / name
            if not vend.exists():
                drift.append(f"missing in site template: schema/{name}")
            elif canon.read_bytes() != vend.read_bytes():
                drift.append(f"differs from canonical: schema/{name}")
        self.assertEqual(drift, [], "templates/site/schema/ has drifted from core/schema/:\n  " + "\n  ".join(drift))

    def test_every_synced_file_is_byte_identical(self):
        drift = []
        for rel in _expected_files():
            canon, vend = CANON / rel, VENDORED / rel
            if not vend.exists():
                drift.append(f"missing in template: core/{rel}")
            elif canon.read_bytes() != vend.read_bytes():
                drift.append(f"differs from canonical: core/{rel}")
        self.assertEqual(
            drift, [],
            "templates/records/core/ has drifted from core/ — re-run "
            "templates/records/scripts/sync-core.sh rather than hand-editing:\n  "
            + "\n  ".join(drift),
        )

    def test_vendored_tree_has_no_extra_python(self):
        expected = {str(r) for r in _expected_files()}
        extras = sorted(
            str(p.relative_to(VENDORED))
            for p in VENDORED.rglob("*.py")
            if str(p.relative_to(VENDORED)) not in expected
        )
        self.assertEqual(extras, [], f"unexpected Python under the vendored core: {extras}")


if __name__ == "__main__":
    unittest.main()
