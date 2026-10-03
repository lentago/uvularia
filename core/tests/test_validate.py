#!/usr/bin/env python3
"""Tests for core/validate.py.

One fixture builds a vault that passes every check; each remaining test mutates a
fresh copy to trip exactly one check, proving that check can fail. Fixtures are
built in a temp directory so sha256 hashes and git history stay correct without
anything being committed to the repo.

    python3 -m unittest core.tests.test_validate      (from the repo root)
    python3 core/tests/test_validate.py
"""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_CORE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_CORE_DIR))

import validate  # noqa: E402


PDF_BYTES = b"%PDF-1.4 fake minutes bytes for the fixture\n"
PDF_SHA = hashlib.sha256(PDF_BYTES).hexdigest()

MINUTES = """\
---
id: 2026-09-16-board-minutes
title: Board meeting minutes, 2026-09-16
type: minutes
status: approved
visibility: public
effective: 2026-09-16
approved: 2026-10-01
source: {{kind: pdf, file: library/files/minutes/2026-09-16-board-minutes.pdf, sha256: "{sha}"}}
certainty: verified
subjects: [budget, parking]
tags: [board, 2026]
corrections:
  - {{date: 2026-10-02, note: "Treasurer's figure corrected from $12,400 to $12,040."}}
---
# Board meeting minutes, 2026-09-16

The board approved the budget. The original is on file:
[the signed minutes](../../library/files/minutes/2026-09-16-board-minutes.pdf).
"""

POLICY = """\
---
id: 2026-01-15-coi-policy
title: Conflict-of-interest policy
type: policy
status: draft
visibility: public
effective: 2026-01-15
certainty: reported
subjects: [governance]
tags: [policy]
---
# Conflict-of-interest policy

A draft policy. No external links here.
"""

INDEX = """\
# Fixture records

- [September board minutes](records/minutes/2026-09-16-board-minutes.md)
"""

VALIDATE_TOML = """\
[privacy]
denylist = ["Jane Q. Resident", "Unit 4B"]
emails = true
phones = true
"""


def build_good_vault(root, *, extra_toml=VALIDATE_TOML):
    """Write a complete, valid vault under ``root`` and return it."""
    (root / "records" / "minutes").mkdir(parents=True)
    (root / "records" / "policy").mkdir(parents=True)
    (root / "library" / "files" / "minutes").mkdir(parents=True)
    (root / "library" / "text").mkdir(parents=True)
    (root / "obligations").mkdir()
    (root / "receipts").mkdir()
    (root / "intake").mkdir()

    pdf = root / "library" / "files" / "minutes" / "2026-09-16-board-minutes.pdf"
    pdf.write_bytes(PDF_BYTES)

    (root / "records" / "minutes" / "2026-09-16-board-minutes.md").write_text(
        MINUTES.format(sha=PDF_SHA), encoding="utf-8")
    (root / "records" / "policy" / "2026-01-15-coi-policy.md").write_text(POLICY, encoding="utf-8")
    (root / "index.md").write_text(INDEX, encoding="utf-8")
    (root / "intake" / "draft.md").write_text("# a work in progress\n", encoding="utf-8")

    manifest = (
        '{\n  "files": {\n    '
        f'"library/files/minutes/2026-09-16-board-minutes.pdf": "{PDF_SHA}"\n'
        "  }\n}\n")
    (root / "library" / "manifest.json").write_text(manifest, encoding="utf-8")
    (root / "validate.toml").write_text(extra_toml, encoding="utf-8")
    return root


def run_checks(root, base_ref=None):
    cfg = validate.load_config(Path(root), base_ref_override=base_ref)
    problems, _ran, _skipped = validate.validate_vault(Path(root), cfg)
    return problems


def git_init_commit(root):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(cmd, cwd=root, check=True,
                       env={**_os_environ(), **env}, capture_output=True)


def _os_environ():
    import os
    return dict(os.environ)


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "vault"
        build_good_vault(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    # --- the passing fixture ------------------------------------------------ #

    def test_good_vault_passes(self):
        # no_delete silently skips outside a git tree; every other check runs.
        self.assertEqual(run_checks(self.root), [])

    def test_good_vault_passes_in_git_with_no_deletion(self):
        git_init_commit(self.root)
        self.assertEqual(run_checks(self.root, base_ref="HEAD"), [])

    # --- one failing fixture per check -------------------------------------- #

    def test_schema_fails_on_bad_type(self):
        path = self.root / "records" / "minutes" / "2026-09-16-board-minutes.md"
        path.write_text(path.read_text().replace("type: minutes", "type: memo"), encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("2026-09-16-board-minutes.md" in p and "memo" in p for p in problems),
                        problems)

    def test_schema_fails_on_missing_frontmatter(self):
        path = self.root / "records" / "policy" / "2026-01-15-coi-policy.md"
        path.write_text("# Just a heading, no frontmatter\n", encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("coi-policy.md" in p and "frontmatter" in p for p in problems), problems)

    def test_approved_source_fails_on_sha_mismatch(self):
        path = self.root / "records" / "minutes" / "2026-09-16-board-minutes.md"
        wrong = "a" * 64
        path.write_text(path.read_text().replace(PDF_SHA, wrong, 1), encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("source.sha256 does not match" in p for p in problems), problems)

    def test_visibility_fails_on_non_public(self):
        # isolate the visibility check so we prove it (not schema) can fail.
        (self.root / "validate.toml").write_text(
            "[checks]\nschema = false\n" + VALIDATE_TOML, encoding="utf-8")
        path = self.root / "records" / "policy" / "2026-01-15-coi-policy.md"
        path.write_text(path.read_text().replace("visibility: public", "visibility: members"),
                        encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("visibility" in p and "coi-policy.md" in p for p in problems), problems)

    def test_links_fails_on_broken_relative_link(self):
        path = self.root / "records" / "policy" / "2026-01-15-coi-policy.md"
        path.write_text(path.read_text() + "\nSee [the appendix](./appendix-that-is-missing.md).\n",
                        encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("does not resolve" in p and "coi-policy.md" in p for p in problems),
                        problems)

    def test_privacy_fails_and_never_leaks_the_value(self):
        secret = "Jane Q. Resident"
        path = self.root / "records" / "policy" / "2026-01-15-coi-policy.md"
        path.write_text(path.read_text() + f"\nThanks to {secret} for the notes.\n", encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("privacy denylist" in p and "coi-policy.md" in p for p in problems),
                        problems)
        self.assertFalse(any(secret in p for p in problems),
                         "the matched denylist value must never appear in the message")

    def test_privacy_fails_on_email_without_leaking_it(self):
        email = "someone.real@example.org"
        text_file = self.root / "library" / "text" / "extract.txt"
        text_file.write_text(f"Call records show {email} in the thread.\n", encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("email-address pattern" in p and "extract.txt" in p for p in problems),
                        problems)
        self.assertFalse(any(email in p for p in problems),
                         "the matched email must never appear in the message")

    def test_no_delete_fails_when_published_record_removed(self):
        git_init_commit(self.root)
        # a published record present in the base ref, removed from the tree
        (self.root / "records" / "policy" / "2026-01-15-coi-policy.md").unlink()
        problems = run_checks(self.root, base_ref="HEAD")
        self.assertTrue(any("retract or supersede" in p and "coi-policy.md" in p for p in problems),
                        problems)

    def test_no_delete_skips_cleanly_outside_git(self):
        # Not a git tree: the check must skip, not crash or fake a pass.
        self.assertEqual(run_checks(self.root, base_ref="HEAD"), [])

    def test_intake_isolation_fails_on_reference(self):
        (self.root / "index.md").write_text(
            INDEX + "- [a draft](intake/draft.md)\n", encoding="utf-8")
        problems = run_checks(self.root)
        self.assertTrue(any("intake/" in p and "index.md" in p for p in problems), problems)

    def test_unique_obligation_ids_fails_on_duplicate(self):
        # Two obligation files — one YAML and one JSON — both declaring the same id.
        # Both filenames must appear in the problem message (naming both parties
        # to the conflict satisfies the "plain message naming both files" requirement).
        (self.root / "obligations" / "notice.yaml").write_text(
            "- id: shared-obligation\n"
            "  title: \"Notice rule (YAML)\"\n"
            "  pack: test\n"
            "  record_type: notice\n"
            "  subjects: [meetings]\n"
            "  source: \"test source\"\n"
            "  disclaimer_ref: policy.yaml#d\n"
            "  lead:\n"
            "    hours: 48\n",
            encoding="utf-8",
        )
        (self.root / "obligations" / "notice.json").write_text(
            '{"id": "shared-obligation", "title": "Notice rule (JSON)",'
            ' "pack": "test", "record_type": "notice", "subjects": ["meetings"],'
            ' "source": "test source", "disclaimer_ref": "policy.yaml#d",'
            ' "lead": {"hours": 48}}\n',
            encoding="utf-8",
        )
        problems = run_checks(self.root)
        self.assertTrue(
            any("notice.yaml" in p and "notice.json" in p for p in problems),
            f"expected both file names in one problem message, got: {problems}",
        )
        self.assertTrue(
            any("shared-obligation" in p for p in problems),
            f"expected the duplicate id in the message, got: {problems}",
        )

    # --- the toggle itself -------------------------------------------------- #

    def test_a_disabled_check_does_not_run(self):
        (self.root / "validate.toml").write_text(
            "[checks]\nprivacy = false\n", encoding="utf-8")
        path = self.root / "records" / "policy" / "2026-01-15-coi-policy.md"
        path.write_text(path.read_text() + "\nThanks to Unit 4B.\n", encoding="utf-8")
        problems = run_checks(self.root)
        self.assertFalse(any("privacy" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
