"""The template sync (scripts/template-sync.sh) and the drift check
(scripts/template-drift.py), run against throwaway local repositories.

    python3 -m unittest discover -s scripts/tests -p "test_*.py" -v

No network, no GitHub: the "template repository" is a bare repo on disk and
the "source" is a fixture tree committed into a second repo. What is held:

  * the sync branch starts from the target's main and ends up with exactly the
    subtree's content (a stale file in the target is removed, a nested file and a
    workflow file arrive, the tree hashes are equal);
  * a target that already matches gets no branch and `changed=false`;
  * the drift check passes on a matching main, fails on a differing one, and
    passes again when a sync branch carries the right content.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / "scripts" / "template-sync.sh"
DRIFT = ROOT / "scripts" / "template-drift.py"
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True,
                          env=ENV).stdout.strip()


def write(root: Path, files: dict[str, str]):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


class Fixture:
    """A source repo with templates/records, and a bare target seeded with old content."""

    def __init__(self, tmp: Path):
        self.source = tmp / "source"
        self.source.mkdir()
        git("init", "-q", "-b", "main", cwd=self.source)
        write(self.source, {
            "templates/records/README.md": "# vault\nnew\n",
            "templates/records/.github/workflows/publish.yml": "name: publish\n",
            "templates/records/scripts/sub/tool.py": "print('new')\n",
            "README.md": "# source, not a template\n",
        })
        git("add", "-A", cwd=self.source)
        git("commit", "-q", "-m", "source", cwd=self.source)
        self.sha = git("rev-parse", "--short", "HEAD", cwd=self.source)

        self.bare = tmp / "target.git"
        git("init", "-q", "--bare", "-b", "main", str(self.bare), cwd=tmp)
        seed = tmp / "seed"
        git("clone", "-q", str(self.bare), str(seed), cwd=tmp)
        write(seed, {"README.md": "# vault\nold\n", "stale.txt": "should be deleted\n"})
        git("add", "-A", cwd=seed)
        git("commit", "-q", "-m", "old template", cwd=seed)
        git("push", "-q", "origin", "HEAD:main", cwd=seed)
        self.target_main = git("rev-parse", "HEAD", cwd=seed)

    @property
    def url(self):
        return f"file://{self.bare}"

    def subtree_tree(self):
        return git("rev-parse", "HEAD:templates/records", cwd=self.source)

    def branch_tree(self, branch):
        return git("rev-parse", f"{branch}^{{tree}}", cwd=self.bare)

    def branches(self):
        return git("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=self.bare).split()

    def sync(self, branch="sync/test"):
        env = {**ENV, "TEMPLATE_SYNC_SOURCE": str(self.source)}
        return subprocess.run([str(SYNC), "templates/records", self.url, branch, self.sha],
                              cwd=self.source, text=True, capture_output=True, env=env)

    def drift(self):
        return subprocess.run(["python3", str(DRIFT), "--source", str(self.source),
                               "--pairs", f"templates/records={self.url}"],
                              text=True, capture_output=True, env=ENV)


class Sync(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_branch_carries_exactly_the_subtree(self):
        r = self.fx.sync()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("changed=true", r.stdout)
        self.assertIn("sync/test", self.fx.branches())
        self.assertEqual(self.fx.branch_tree("sync/test"), self.fx.subtree_tree())
        files = git("ls-tree", "-r", "--name-only", "sync/test", cwd=self.fx.bare).split()
        self.assertNotIn("stale.txt", files)
        self.assertIn(".github/workflows/publish.yml", files)
        self.assertIn("scripts/sub/tool.py", files)

    def test_branch_starts_from_target_main_so_the_diff_is_plain(self):
        self.fx.sync()
        self.assertEqual(git("rev-parse", "sync/test^", cwd=self.fx.bare), self.fx.target_main)
        self.assertIn(self.fx.sha, git("log", "-1", "--format=%s", "sync/test", cwd=self.fx.bare))

    def test_matching_target_gets_no_branch(self):
        first = self.fx.sync("sync/one")
        self.assertIn("changed=true", first.stdout)
        # Land it on main, as a merged pull request would, then sync again.
        git("update-ref", "refs/heads/main", "refs/heads/sync/one", cwd=self.fx.bare)
        second = self.fx.sync("sync/two")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("changed=false", second.stdout)
        self.assertNotIn("sync/two", self.fx.branches())

    def test_rerun_updates_the_same_branch(self):
        self.fx.sync("sync/same")
        write(self.fx.source, {"templates/records/README.md": "# vault\nnewer\n"})
        git("commit", "-q", "-am", "newer", cwd=self.fx.source)
        self.fx.sha = git("rev-parse", "--short", "HEAD", cwd=self.fx.source)
        r = self.fx.sync("sync/same")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.fx.branch_tree("sync/same"), self.fx.subtree_tree())

    def test_unknown_subtree_is_an_error_not_an_empty_sync(self):
        env = {**ENV, "TEMPLATE_SYNC_SOURCE": str(self.fx.source)}
        r = subprocess.run([str(SYNC), "templates/nope", self.fx.url, "sync/x", "abc"],
                           cwd=self.fx.source, text=True, capture_output=True, env=env)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.fx.branches(), ["main"])


class Drift(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_differing_main_with_no_sync_branch_is_drift(self):
        r = self.fx.drift()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DRIFT", r.stdout)

    def test_open_sync_branch_with_the_right_content_is_in_flight(self):
        self.fx.sync("sync/pending")
        r = self.fx.drift()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("in-flight", r.stdout)

    def test_matching_main_is_ok(self):
        self.fx.sync("sync/landed")
        git("update-ref", "refs/heads/main", "refs/heads/sync/landed", cwd=self.fx.bare)
        git("update-ref", "-d", "refs/heads/sync/landed", cwd=self.fx.bare)
        r = self.fx.drift()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ok ", r.stdout)

    def test_a_stale_sync_branch_does_not_mask_drift(self):
        self.fx.sync("sync/old")
        write(self.fx.source, {"templates/records/README.md": "# vault\nnewer still\n"})
        git("commit", "-q", "-am", "newer still", cwd=self.fx.source)
        r = self.fx.drift()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("match neither", r.stdout)


if __name__ == "__main__":
    unittest.main()
