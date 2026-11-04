"""The client-side update door (templates/*/scripts/template-update.py), run
against throwaway local repositories, plus the shape of what ships with it.

    python3 -m unittest discover -s scripts/tests -p "test_*.py" -v

No network, no GitHub: the "template repository" is a bare repo on disk and the
"client" is a repo whose first commit has exactly the template's tree, which is
what "Use this template" makes. What is held (uvularia#112, ADR-0003):

  * a file the client never changed becomes the template's; a file the template
    added arrives; a file the template removed goes; the base is recorded;
  * a file the client changed and the template did not stays the client's;
    both changed on different lines merge; on the same lines, conflict markers
    and a count; the client's removals and the template's removals of changed
    files are left alone and listed;
  * nothing under `keep`, nor the config, is ever added, changed or removed;
  * no base (first commit matches nothing) means nothing is removed and every
    replacement is listed; an up-to-date repository gets no change at all;
  * in the template repository itself, a dirty checkout, and modes: the script
    does nothing, refuses, and keeps the executable bit;
  * the three templates ship identical copies of the script and the workflow,
    each config names its own template and keeps what must never change, and
    the workflow is pinned, keeps the token out of every step that does not
    push, and asks for no write permission it does not use.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ("records", "ask-rules", "site")
SCRIPT = ROOT / "templates" / "records" / "scripts" / "template-update.py"
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example", "GITHUB_REPOSITORY": "client-org/client-records"}
ENV.pop("GITHUB_OUTPUT", None)

CONFIG = """source = "example/records-template"
branch = "main"
keep = ["records/", "index.md", "LICENSE"]
"""
DOC = "".join(f"line {i}\n" for i in range(1, 13))


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True,
                          env=ENV).stdout.strip()


def write(root: Path, files: dict[str, str | None]):
    for rel, text in files.items():
        p = root / rel
        if text is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


class Fixture:
    """A bare template repo at v1, and a client made from it ("Use this template")."""

    V1 = {
        ".github/template-update.toml": CONFIG,
        ".github/workflows/ci.yml": "name: ci\n",
        "README.md": "# template\nv1\n",
        "doc.md": DOC,
        "old.txt": "the template will remove this\n",
        "tweaked.txt": "the client will change this; the template will remove it\n",
        "gone.txt": "the client will remove this; the template will change it\n",
        "scripts/tool.sh": "#!/bin/sh\necho v1\n",
        "records/.gitkeep": "",
        "index.md": "# Your organization\n",
        "LICENSE": "MIT\n",
    }

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.bare = tmp / "template.git"
        git("init", "-q", "--bare", "-b", "main", str(self.bare), cwd=tmp)
        self.work = tmp / "template"
        git("clone", "-q", str(self.bare), str(self.work), cwd=tmp)
        self.v1 = self.template_commit(self.V1, "v1")
        os.chmod(self.work / "scripts/tool.sh", 0o755)
        git("add", "-A", cwd=self.work)
        git("commit", "-q", "-m", "v1 exec", cwd=self.work)
        git("push", "-q", "origin", "HEAD:main", cwd=self.work)
        self.v1 = git("rev-parse", "HEAD", cwd=self.work)

        # The client: a fresh repository whose one commit is the template's tree.
        self.client = tmp / "client"
        self.client.mkdir()
        git("init", "-q", "-b", "main", cwd=self.client)
        git("--work-tree", str(self.client), "checkout", "-q", self.v1, "--", ".",
            cwd=self.work)
        git("add", "-A", cwd=self.client)
        git("commit", "-q", "-m", "Initial commit", cwd=self.client)

    @property
    def url(self):
        return f"file://{self.bare}"

    def template_commit(self, files, msg):
        write(self.work, files)
        git("add", "-A", cwd=self.work)
        git("commit", "-q", "-m", msg, cwd=self.work)
        git("push", "-q", "origin", "HEAD:main", cwd=self.work)
        return git("rev-parse", "HEAD", cwd=self.work)

    def client_commit(self, files, msg="client change"):
        write(self.client, files)
        git("add", "-A", cwd=self.client)
        git("commit", "-q", "-m", msg, cwd=self.client)

    def run(self, *extra, env=None):
        r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.client),
                            "--template-url", self.url, "--body", str(self.tmp / "body.md"),
                            "--issue-body", str(self.tmp / "issue.md"), *extra],
                           capture_output=True, text=True, env=env or ENV)
        out = dict(line.split("=", 1) for line in r.stdout.splitlines()
                   if re.fullmatch(r"[a-z]+=\S*", line))
        return r, out

    def read(self, rel):
        return (self.client / rel).read_text()

    def staged(self):
        return git("diff", "--cached", "--name-status", cwd=self.client)

    def body(self):
        return (self.tmp / "body.md").read_text()


class UpdateDoor(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.f = Fixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_untouched_files_follow_the_template_and_the_base_is_recorded(self):
        v2 = self.f.template_commit({"README.md": "# template\nv2\n", "new.txt": "added\n",
                                     "old.txt": None}, "v2")
        r, out = self.f.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(out["changed"], "true")
        self.assertEqual(out["attention"], "0")
        self.assertEqual(self.f.read("README.md"), "# template\nv2\n")
        self.assertEqual(self.f.read("new.txt"), "added\n")
        self.assertFalse((self.f.client / "old.txt").exists())
        self.assertIn(v2, self.f.read(".github/template-base"))
        self.assertIn("(inferred)", r.stdout)
        body = self.f.body()
        self.assertIn("`README.md (updated)`", body)
        self.assertIn("`new.txt (added)`", body)
        self.assertIn("`old.txt (removed)`", body)
        self.assertIn(f"compare/{self.f.v1}...{v2}", body)

    def test_the_keep_list_and_the_config_are_never_touched(self):
        self.f.template_commit({"records/.gitkeep": "changed\n", "records/new.md": "x\n",
                                "index.md": "# New placeholder\n", "LICENSE": None,
                                ".github/template-update.toml": CONFIG + "# new default\n",
                                "README.md": "# template\nv2\n"}, "v2")
        r, out = self.f.run()
        self.assertEqual(out["changed"], "true", r.stderr)
        staged = self.f.staged()
        for path in ("records/", "index.md", "LICENSE", "template-update.toml"):
            self.assertNotIn(path, staged)
        self.assertFalse((self.f.client / "records/new.md").exists())
        self.assertEqual(self.f.read("LICENSE"), "MIT\n")
        self.assertEqual(self.f.read(".github/template-update.toml"), CONFIG)
        for path in ("records/.gitkeep", "records/new.md", "index.md", "LICENSE",
                     ".github/template-update.toml"):
            self.assertIn(f"`{path}`", self.f.body().split("Not touched")[1])

    def test_a_file_only_you_changed_stays_yours(self):
        self.f.client_commit({".github/workflows/ci.yml": "name: ci\non: push\n"})
        self.f.template_commit({"README.md": "# template\nv2\n"}, "v2")
        r, out = self.f.run()
        self.assertEqual(out["changed"], "true", r.stderr)
        self.assertEqual(self.f.read(".github/workflows/ci.yml"), "name: ci\non: push\n")

    def test_both_changed_different_lines_merge(self):
        self.f.client_commit({"doc.md": DOC.replace("line 1\n", "line 1 (ours)\n")})
        self.f.template_commit({"doc.md": DOC.replace("line 12\n", "line 12 (template)\n")},
                               "v2")
        r, out = self.f.run()
        self.assertEqual(out["attention"], "0", r.stderr)
        doc = self.f.read("doc.md")
        self.assertIn("line 1 (ours)", doc)
        self.assertIn("line 12 (template)", doc)
        self.assertIn("Merged with your changes", self.f.body())

    def test_both_changed_same_lines_conflict_and_say_so(self):
        self.f.client_commit({"doc.md": DOC.replace("line 6\n", "line 6 (ours)\n")})
        self.f.template_commit({"doc.md": DOC.replace("line 6\n", "line 6 (template)\n")},
                               "v2")
        r, out = self.f.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(out["attention"], "1")
        doc = self.f.read("doc.md")
        self.assertIn("<<<<<<< yours", doc)
        self.assertIn(">>>>>>> template now", doc)
        self.assertIn("Needs you", self.f.body())

    def test_removals_of_changed_files_are_left_and_listed(self):
        self.f.client_commit({"tweaked.txt": "ours now\n", "gone.txt": None})
        self.f.template_commit({"tweaked.txt": None, "gone.txt": "template changed it\n"},
                               "v2")
        r, out = self.f.run()
        self.assertEqual(out["changed"], "false", r.stderr)
        self.assertEqual(self.f.read("tweaked.txt"), "ours now\n")
        self.assertFalse((self.f.client / "gone.txt").exists())
        self.assertIn("`tweaked.txt`", self.f.body().split("Left as you have them")[1])
        self.assertIn("`gone.txt`", self.f.body().split("Left removed")[1])

    def test_up_to_date_changes_nothing(self):
        r, out = self.f.run()
        self.assertEqual(out["changed"], "false", r.stderr)
        self.assertEqual(self.f.staged(), "")
        self.assertFalse((self.f.client / ".github/template-base").exists())

    def test_a_recorded_base_is_used(self):
        v2 = self.f.template_commit({"README.md": "# template\nv2\n"}, "v2")
        # The client took v2 by hand and recorded it; v3 changes doc.md only.
        self.f.client_commit({"README.md": "# template\nv2\n",
                              ".github/template-base": f"# by hand\n{v2}\n"})
        self.f.template_commit({"doc.md": DOC + "line 13\n"}, "v3")
        r, out = self.f.run()
        self.assertIn("(recorded)", r.stdout)
        self.assertIn("compare/" + v2, self.f.body())
        self.assertEqual(self.f.staged().split(), ["M", ".github/template-base", "M", "doc.md"])

    def test_without_a_base_nothing_is_removed_and_replacements_are_listed(self):
        # A client whose first commit is not a template commit: a hand copy, edited.
        write(self.f.client, {"README.md": "# ours\n"})
        git("commit", "-q", "-a", "--amend", "-m", "hand copy", cwd=self.f.client)
        self.f.template_commit({"old.txt": None, "new.txt": "added\n"}, "v2")
        r, out = self.f.run()
        self.assertEqual(out["changed"], "true", r.stderr)
        self.assertIn("unknown", r.stdout)
        self.assertEqual(out["attention"], "2", "each no-base replacement needs a look")
        self.assertTrue((self.f.client / "old.txt").exists())
        self.assertEqual(self.f.read("README.md"), "# template\nv1\n")
        listed = self.f.body().split("replaced without a base")[1]
        self.assertIn("`README.md`", listed)
        self.assertIn("`new.txt`", listed)

    def test_the_template_itself_does_nothing(self):
        self.f.template_commit({"README.md": "# template\nv2\n"}, "v2")
        r, out = self.f.run(env={**ENV, "GITHUB_REPOSITORY": "Example/Records-Template"})
        self.assertEqual(out["changed"], "false", r.stderr)
        self.assertIn("this is the template itself", r.stdout)
        self.assertEqual(self.f.staged(), "")

    def test_a_dirty_checkout_is_refused(self):
        self.f.template_commit({"README.md": "# template\nv2\n"}, "v2")
        (self.f.client / "doc.md").write_text("uncommitted\n")
        r, _ = self.f.run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("uncommitted changes", r.stderr)

    def test_dry_run_changes_nothing(self):
        self.f.template_commit({"README.md": "# template\nv2\n"}, "v2")
        r, out = self.f.run("--dry-run")
        self.assertEqual(out["changed"], "true", r.stderr)
        self.assertEqual(self.f.staged(), "")
        self.assertEqual(self.f.read("README.md"), "# template\nv1\n")

    def test_the_executable_bit_comes_with_the_file(self):
        self.f.template_commit({"scripts/tool.sh": "#!/bin/sh\necho v2\n"}, "v2")
        self.f.run()
        mode = git("ls-files", "-s", "scripts/tool.sh", cwd=self.f.client).split()[0]
        self.assertEqual(mode, "100755")
        self.assertTrue(os.access(self.f.client / "scripts/tool.sh", os.X_OK))


class WhatShips(unittest.TestCase):
    """The copies, the configs and the workflow in templates/*."""

    def test_the_three_templates_carry_identical_script_and_workflow(self):
        for rel in ("scripts/template-update.py", ".github/workflows/template-update.yml"):
            copies = {t: (ROOT / "templates" / t / rel).read_bytes() for t in TEMPLATES}
            self.assertEqual(len(set(copies.values())), 1,
                             f"templates/*/{rel} have drifted; edit the records copy and "
                             "copy it over the other two")
        for t in TEMPLATES:
            self.assertTrue(os.access(ROOT / "templates" / t / "scripts/template-update.py",
                                      os.X_OK), t)

    def test_each_config_names_its_own_template_and_keeps_what_is_the_clients(self):
        must_keep = {
            "records": {"records/", "receipts/", "library/", "index.md", "validate.toml",
                        ".github/CODEOWNERS"},
            "ask-rules": {"policy.yaml", "instructions.md", "signals/", "evals/golden.jsonl",
                          ".github/CODEOWNERS"},
            "site": {"site.config.ts", ".github/CODEOWNERS"},
        }
        drift = (ROOT / "scripts" / "template-drift.py").read_text()
        for t in TEMPLATES:
            with self.subTest(template=t):
                cfg = tomllib.loads((ROOT / "templates" / t / ".github/template-update.toml")
                                    .read_text())
                self.assertIn(f'"templates/{t}": f"{{OWNER_URL}}/{cfg["source"].split("/")[1]}.git"',
                              drift, "source must be the repository template-sync keeps current")
                self.assertTrue(cfg["source"].startswith("lentago/"))
                self.assertEqual(cfg.get("branch"), "main")
                self.assertLessEqual(must_keep[t], set(cfg["keep"]))
                for k in cfg["keep"]:
                    self.assertTrue((ROOT / "templates" / t / k.rstrip("/")).exists(),
                                    f"{t}: keep entry {k!r} names nothing in the template")

    def test_the_workflow_is_pinned_and_keeps_the_token_where_it_belongs(self):
        wf = (ROOT / "templates/records/.github/workflows/template-update.yml").read_text()
        for line in re.findall(r"uses:\s*(\S+)", wf):
            self.assertRegex(line, r"@[0-9a-f]{40}$", "every action is pinned to a commit")
        self.assertIn("persist-credentials: false", wf)
        perms = re.search(r"^permissions:\n((?:  .*\n)+)", wf, re.M).group(1)
        grants = dict(re.findall(r"^  ([a-z-]+): (\w+)", perms, re.M))
        self.assertEqual(grants, {"contents": "read", "pull-requests": "read",
                                  "issues": "write"})
        uses = re.findall(r"secrets\.TEMPLATE_UPDATE_TOKEN([^}]*)}}", wf)
        self.assertEqual(len(uses), 2, "the token is named twice: whether it is set, and the "
                                       "one step that pushes and opens the pull request")
        steps = re.split(r"\n      - ", wf)
        holders = [s.splitlines()[0] for s in steps if "secrets.TEMPLATE_UPDATE_TOKEN }}" in s]
        self.assertEqual(holders, ["name: Open the pull request with your token"])
        push = next(s for s in steps if s.startswith("name: Open the pull request"))
        self.assertNotIn("--force", push, "a closed update's branch may hold your work")
        self.assertNotRegex(push, r"https://[^\s\"]*@github\.com", "no token in a URL")
        self.assertIn("steps.update.outputs.attention", push)


if __name__ == "__main__":
    unittest.main()
