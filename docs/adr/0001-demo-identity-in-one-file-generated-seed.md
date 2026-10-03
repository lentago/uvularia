# ADR-0001: The demonstration client's identity lives in one file and its records are generated

**Status:** Accepted (2026-10-03)

## Context

The product needs a demonstration client: a vault full of realistic public
records, a board that shows real amber and green, an Ask box with something to
answer from. The previous receipt for this pattern was a real community's
site, which turned out not to be available for the practice to show, even at
no cost. That must not happen again, and the demonstration must survive a
change of name, domain, or look without a rewrite.

The fictional client is Stillwater Brook Watershed Alliance, from the lupinus
adoption stories. Fiction removes the consent problem; it does not by itself
make the demo renameable, because two years of minutes and notices would carry
the name in prose hundreds of times.

## Decision

1. The demonstration client's identity — legal name, short name, domain,
   contact address, accent colour, logo — lives in exactly one file,
   `demo/org.yaml`.
2. Seed records are **generated** by `demo/seed.py` from record templates that
   reference identity fields, never hand-written with the name in them. The
   generated vault is committed under `demo/generated/` so the demo is
   browsable, and CI regenerates and diffs it so it cannot drift from its
   source.
3. CI fails on any occurrence of the organization's name, short name, or
   domain anywhere in the repository outside `demo/org.yaml` and
   `demo/generated/`.
4. The same `org.yaml` fields feed the vault index, the site template, the
   rules persona, and the obligation pack's organization fields, so a real
   client's adoption is the same mechanism with their own values and an empty
   `records/`.
5. A real client never starts from the seed. The seed is a demonstration and a
   lab fixture.

## Alternatives

- **Hand-written seed records.** Realistic and fast to produce, and
  impossible to rename without a sweep that would miss things. Rejected.
- **Placeholder tokens in committed Markdown** (`{{org.name}}` in the vault
  itself). Breaks the rule that the vault is plain Markdown a person can read
  in Obsidian without a build step. Rejected; tokens live in the templates the
  generator reads, not in the vault.
- **No demonstration client; rely on labs run against an empty template.** A
  board with no obligations and a box with no records demonstrates nothing.
  Rejected.

## Consequences

- `demo/seed.py` is a Phase 0 deliverable alongside the validator, and the
  name-leak check is part of the repo's CI from the first PR that adds the
  demo.
- Renaming or rebranding the demo is a one-file PR plus a regenerate, and the
  PR diff shows every place the identity reaches.
- Realism is bounded by what a generator can produce; some hand-tuned texture
  (a contentious vote, a late notice) goes into the templates as parameters,
  not into generated files.
