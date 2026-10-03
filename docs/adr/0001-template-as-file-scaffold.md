# ADR-0001: Template repo carries files; org settings are applied externally

**Status:** Accepted (2026-06-14; reconstructed 2026-08-13)

## Context

GitHub's "Use this template" creates a new repository by copying the template's files verbatim.
It does not copy repository settings — branch protection, squash-only merge button, topics, and
related configuration are not part of what GitHub transfers. Without an explicit post-create step
every derived repo starts on GitHub defaults, which fall short of fleet requirements.

The fleet needed a repeatable way to apply consistent settings to every new repo without per-repo
manual drift.

## Decision

Split the scaffold into two halves:

1. **File half** — `repo-template` ships the file skeleton: `README.md`, `CLAUDE.md`, `SETUP.md`,
   CI workflow wrappers, `LICENSE`, and `assets/`. These are inherited automatically on
   "Use this template."

2. **Settings half** — applied externally after creation by running
   `dotgithub/fleet-ops/fleet-apply.sh --apply --repo <name>`, which sets squash-only merge,
   auto-merge, delete-branch-on-merge, and org topics. `SETUP.md` documents this step and is
   deleted from each derived repo once setup is complete.

Evidence (verified against current repo):

- `SETUP.md` line 3: "A GitHub template copies **files, not settings**."
- `SETUP.md` step 2: the `fleet-apply.sh` invocation.
- `README.md` patterns table: "Settings-as-code is external to the template — SETUP.md step 2."
- PR #1 (merged 2026-06-20) confirms the two-part design pre-dates that PR; #1 only corrected
  a stale path in SETUP.md (`~/repos/fleet-ops/` → `dotgithub/fleet-ops/`) without changing the
  design.

## Alternatives

**GitHub Actions `repository` creation trigger** *(retrospective — not considered at the time)* —
Fire `fleet-apply.sh` automatically when a new repo is created from the template. Removes the
manual step, but requires a long-lived org-level token with admin write access and a persistent
actor to run the workflow. *Worse*: standing admin credentials to save one documented manual
step — and the fleet's later settings-as-code Terraform path closed the same gap without them.

**Cookiecutter / Copier** *(retrospective — not considered at the time)* — Both tools support
parametrized scaffolding (named slots, interactive prompts, conditional sections) and can run
post-generate hooks. They require the CLI installed on the operator's machine and are off the
GitHub-native "Use this template" creation path. Copier additionally supports template upgrades
post-creation. *Lateral*: better parametrization and upgrade story, but neither tool eliminates
the settings gap — GitHub repository settings are not managed by copier/cookiecutter without a
custom post-hook, so the two-half problem remains. Loses the zero-install, browser-accessible
creation flow.

## Consequences

- Every new repo requires a manual post-create step before it is fully fleet-compliant. `SETUP.md`
  is the reminder; it is deleted once setup is done.
- `SETUP.md` must stay accurate as fleet-ops paths evolve. PR #1 is a recorded instance of that
  maintenance cost.
- The template itself is always compliant by definition. `fleet-apply.sh` is the single
  enforcement point for settings-as-code.
