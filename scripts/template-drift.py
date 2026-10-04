#!/usr/bin/env python3
"""Is each template repository carrying what this repo has under templates/<name>?

For every pair, compare the git tree hash of the subtree at --source-ref with the
tree hash of the template repository's default branch. Identical hashes mean
identical content, name for name, byte for byte. A mismatch is still fine when a
``sync/*`` branch on the template repository matches: that is a sync pull request
in flight, waiting on its checks. Anything else is drift, and the exit code is 1.

    python3 scripts/template-drift.py                      # pairs below, HEAD
    python3 scripts/template-drift.py --source-ref origin/main
    python3 scripts/template-drift.py --pairs templates/records=file:///tmp/t.git

Standard library plus git. Clones are shallow; nothing is written anywhere but a
temporary directory.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

OWNER_URL = "https://github.com/lentago"
PAIRS = {
    "templates/records": f"{OWNER_URL}/uvularia-records-template.git",
    "templates/ask-rules": f"{OWNER_URL}/uvularia-rules-template.git",
    "templates/site": f"{OWNER_URL}/uvularia-site-template.git",
}


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                          capture_output=True).stdout.strip()


def source_tree(source: Path, ref: str, subtree: str) -> str:
    return git("rev-parse", f"{ref}:{subtree}", cwd=source)


def remote_trees(url: str, tmp: Path) -> tuple[str, str, dict[str, str]]:
    """(default branch, its tree hash, {sync branch: tree hash}) for one template repo."""
    clone = tmp / "clone"
    git("clone", "--quiet", "--depth", "1", url, str(clone))
    default = git("rev-parse", "--abbrev-ref", "HEAD", cwd=clone)
    main_tree = git("rev-parse", "HEAD^{tree}", cwd=clone)
    syncs: dict[str, str] = {}
    heads = git("ls-remote", "--heads", "origin", "refs/heads/sync/*", cwd=clone)
    for line in heads.splitlines():
        _sha, ref = line.split("\t", 1)
        name = ref.removeprefix("refs/heads/")
        git("fetch", "--quiet", "--depth", "1", "origin", name, cwd=clone)
        syncs[name] = git("rev-parse", "FETCH_HEAD^{tree}", cwd=clone)
    return default, main_tree, syncs


def check(source: Path, ref: str, pairs: dict[str, str]) -> bool:
    ok = True
    for subtree, url in pairs.items():
        want = source_tree(source, ref, subtree)
        with tempfile.TemporaryDirectory() as tmp:
            default, have, syncs = remote_trees(url, Path(tmp))
        if have == want:
            print(f"ok       {subtree} == {url} ({default} {have[:12]})")
            continue
        in_flight = [name for name, tree in syncs.items() if tree == want]
        if in_flight:
            print(f"in-flight {subtree}: {url} {default} differs, but {in_flight[0]} matches "
                  f"(a sync pull request is open)")
            continue
        ok = False
        print(f"DRIFT    {subtree}: {ref} has tree {want[:12]}, {url} {default} has {have[:12]}"
              + (f"; open sync branches {sorted(syncs)} match neither" if syncs else "; no sync branch open"))
    return ok


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", default=".", help="this repository's checkout (default: .)")
    p.add_argument("--source-ref", default="HEAD", help="ref whose subtrees the template repos must match")
    p.add_argument("--pairs", nargs="*", metavar="SUBTREE=URL",
                   help="override the built-in subtree=template-repo pairs")
    a = p.parse_args(argv)
    pairs = dict(x.split("=", 1) for x in a.pairs) if a.pairs else PAIRS
    source = Path(git("rev-parse", "--show-toplevel", cwd=Path(a.source)))
    good = check(source, a.source_ref, pairs)
    if not good:
        print("\nOne or more template repositories do not carry what this repo's subtree holds, and no sync "
              "pull request is open for it. Run the template-sync workflow (Actions → template-sync → "
              "Run workflow) or sync by hand: docs/runbooks/template-sync-github-app.md", file=sys.stderr)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
