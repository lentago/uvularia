# Architecture decision records

The decisions below were reconstructed on 2026-08-13 from **this template repository's own**
commit history, merged pull requests, and CLAUDE.md contents. Dates in each record reflect the
original decision date, not the reconstruction date. Evidence anchors (PR numbers, file lines)
have been verified against the current repo state; anything that could not be confirmed is marked
uncertain.

> **Scaffolding note — for repos created from this template:** ADRs 0001/0002 and their index
> rows document the template repo itself, not your new repo. On setup (see `SETUP.md`), delete
> those two records and their rows, keep this file as your repo's ADR log, and use the format
> guide below for your own decisions.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-template-as-file-scaffold.md) | Template repo carries files; org settings are applied externally | Accepted | 2026-06-14 |
| [0002](0002-governance-baked-in-structurally.md) | Template ships governance as structure, not convention | Accepted | 2026-06-14 |

---

## How to add an ADR to this repo

Create `docs/adr/NNNN-<short-slug>.md` and add a row to the index above. Use this structure:

```markdown
# ADR-NNNN: <Title>

**Status:** Accepted (<date>)

## Context

Why was a decision needed? What constraints and forces were in play?

## Decision

What was decided, and how does it address the context?

## Alternatives

List the options that were actually weighed, then add one or two marked
*"retrospective — not considered at the time"* with an honest assessment
(worse / better / lateral) and a short reason.

## Consequences

What does this decision make easier or harder going forward? What are the
known trade-offs or scars?
```

**Recorded vs. retrospective alternatives:** Alternatives that were actually weighed at decision
time go in the list without special marking. Options added later for completeness must be
explicitly labelled *"retrospective — not considered at the time"* so future readers know they
were not part of the original deliberation. Honest assessment (worse / better / lateral) is
required — do not present retrospective options as neutral.
