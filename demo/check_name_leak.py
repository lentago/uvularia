#!/usr/bin/env python3
"""Fail if the demonstration client's identity has leaked outside its one home.

Per docs/adr/0001, the demo's name, short name, and domain live in exactly one
file — ``demo/org.yaml`` — and every record that uses them is produced by
``demo/seed.py`` into ``demo/generated/``. Anywhere else in the repository, those
strings are a leak: a hand-written occurrence of the name that the one-file
rename would miss. This check reads the three strings from ``org.yaml`` (it never
hardcodes them, so the check itself renames for free) and scans the rest of the
tree for them.

    python3 demo/check_name_leak.py            # scan the repo; non-zero on a leak
    python3 demo/check_name_leak.py --selftest # prove the scanner catches a leak

The scan excludes ``.git/``, ``demo/org.yaml`` (the one allowed home), and
``demo/generated/`` (the generated output, where the identity is expected). The
``--selftest`` mode plants the identity strings in a throwaway temp directory and
asserts the scanner flags them — a fixture that proves the check can fail,
without committing a leak to the tree.

Python 3.12, standard library only.
"""

import argparse
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ORG_YAML = REPO_ROOT / "demo" / "org.yaml"
GENERATED = REPO_ROOT / "demo" / "generated"

# Design documents name the demonstration client as a matter of record: the
# architecture in docs/concept.md chose it, docs/adr/0001 — the decision that
# created THIS very rule — names it in its own Context, and README.md introduces
# it. That prose is not part of the generated vault and a rename never touches
# it, so it is not scanned. Everything else — seed.py, the templates, the
# obligations, the core, the CI, and any stray record outside demo/generated/ —
# is. The guard is on the construction surface, where a hand-written name would
# actually survive a one-file rename; it is not a style rule on the prose.
DOC_DIRS = [REPO_ROOT / "docs"]
DOC_FILES = [REPO_ROOT / "README.md"]

# Only these identity fields are forbidden outside org.yaml and generated/. The
# accent colour and the logo markup are not names and are not checked.
IDENTITY_FIELDS = ("name", "short_name", "domain")


def read_identity(org_yaml=ORG_YAML):
    """Return the forbidden strings from org.yaml's flat scalar fields."""
    needles = []
    for raw in org_yaml.read_text(encoding="utf-8").split("\n"):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if key in IDENTITY_FIELDS and value and value != "|":
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            needles.append((key, value))
    found = {k for k, _ in needles}
    missing = [f for f in IDENTITY_FIELDS if f not in found]
    if missing:
        raise SystemExit(f"org.yaml is missing identity field(s): {', '.join(missing)}")
    return needles


def _is_excluded(path, excluded_dirs, excluded_files):
    if any(part == ".git" for part in path.parts):
        return True
    for d in excluded_dirs:
        try:
            path.relative_to(d)
            return True
        except ValueError:
            pass
    return path.resolve() in excluded_files


def scan(root, needles, excluded_dirs=(), excluded_files=()):
    """Return a list of (relpath, lineno, field, value) for each leak found."""
    excluded_dirs = [Path(d).resolve() for d in excluded_dirs]
    excluded_files = {Path(f).resolve() for f in excluded_files}
    lowered = [(field, value, value.lower()) for field, value in needles]
    hits = []
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_excluded(path, excluded_dirs, excluded_files):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable — nothing a name can hide in as text
        for lineno, line in enumerate(text.split("\n"), 1):
            low = line.lower()
            for field, value, needle in lowered:
                if needle in low:
                    rel = path.relative_to(root).as_posix()
                    hits.append((rel, lineno, field, value))
    return hits


def selftest():
    needles = read_identity()
    with tempfile.TemporaryDirectory() as tmp:
        planted = Path(tmp) / "leaked.md"
        planted.write_text(
            "A stray mention of " + needles[0][1] + " and " + needles[-1][1] + ".\n",
            encoding="utf-8")
        hits = scan(tmp, needles)
        fields_hit = {field for _, _, field, _ in hits}
        if "name" not in fields_hit or "domain" not in fields_hit:
            print("SELFTEST FAILED: the scanner did not catch a planted leak", file=sys.stderr)
            return 1
    print("selftest ok: the scanner catches a planted leak "
          f"({len(hits)} hit(s) across the planted fixture)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fail on a demo identity leak.")
    parser.add_argument("--selftest", action="store_true",
                        help="prove the scanner catches a leak, then exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    needles = read_identity()
    hits = scan(REPO_ROOT, needles,
                excluded_dirs=[GENERATED, *DOC_DIRS],
                excluded_files=[ORG_YAML, *DOC_FILES])
    if hits:
        print("Demo identity leaked outside demo/org.yaml and demo/generated/:\n")
        for rel, lineno, field, value in hits:
            print(f"  {rel}:{lineno}: contains the demo {field} ({value!r})")
        print("\nMove the text into a template token, or into org.yaml if it is "
              "identity. The demo renames from one file; a hardcoded name breaks that.")
        return 1
    print(f"No demo identity leak. Scanned the repository for "
          f"{len(needles)} identity string(s); all occurrences are in "
          f"demo/org.yaml and demo/generated/ as intended.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
