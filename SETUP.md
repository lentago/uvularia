# Post-create setup (delete this file when done)

A GitHub template copies **files, not settings**. After creating a repo from
`repo-template`, the file skeleton is in place but the repo is on GitHub
defaults. Apply fleet settings, then delete this file.

## 0. Write the repo description

Every Lentago Labs repo description follows a tiered template. The invariant
across all tiers: **the repo's function appears in the first five words after
the name, and no quality adjectives** ("robust", "modern", "clean", etc.).

| Tier | Template |
|---|---|
| **Platform products** | `<Codename> — the Lentago Labs <plain-English role>: <what it does today, concretely>. <One distinctive mechanism or rule>.` |
| **Sites** | `Site content for <domain> — <what the site is>; <stack> on the solidago AWS stack (OIDC → ECR/ECS/ALB).` |
| **Tools & config** | `<Outcome-first description of what it does>. <Distinctive mechanism>.` |
| **Kit templates** | `Template: <offering> kit — runs entirely in your org's own accounts; <what it does>.` |

Set the description in the repo's About panel (or via `gh repo edit
lentago/<repo> --description "..."`) before your first PR.

## 1. Fill in the skeleton

- `README.md` — name, description, keep the Claude co-authorship disclosure at
  the top.
- `CLAUDE.md` — persona, what-this-repo-is, conventions.
- `.github/workflows/claude-code-review.yml` — **replace the placeholder
  `review_prompt`** with one written for THIS repo. Do not ship the boilerplate.

The skeleton also ships these files that are ready to use as-is:

- `.github/dependabot.yml` — weekly Dependabot updates for GitHub Actions
  (github-actions ecosystem only; add npm/pip blocks if the repo gains manifests).
  Third-party action pins in workflows will be auto-PRed when new versions drop.

## 2. Apply fleet settings

If the **org-level `fleet-baseline` ruleset** exists (see
`dotgithub/fleet-ops/`), branch protection is already inherited automatically —
skip the per-repo ruleset. Otherwise, and for the merge-button/topics that
rulesets don't cover, run the fleet script from `~/repos`:

```bash
dotgithub/fleet-ops/fleet-apply.sh --apply --repo <new-repo-name>
```

That sets squash-only merge + auto-merge + delete-branch-on-merge and ensures
the `lentago` + `claude` spine topics. Add this repo's signature topics by
hand:

```bash
gh repo edit lentago/<new-repo-name> --add-topic <signature-tag> ...
```

## 3. Replace the brand banner

`assets/banner.svg` is the repo-template banner copied from `lentago/.github`. Replace it with one generated for your repo: add the new repo name to `brand/fleet.json` in `lentago/.github`, run `python3 brand/generate.py --repo <name>`, and copy the resulting `brand/generated/<name>/banner.svg` into `assets/`.

## 4. Add the repo to the fleet inventory

Add the new repo name to the Lentago Labs org list in `~/repos/CLAUDE.md`.

## 5. Know the canonical locations

For any content you add to a new repo, use these paths — they're where the
fleet expects to find things:

| Content | Canonical path | Notes |
|---|---|---|
| Architecture decision records | `docs/adr/` | Nygard style, numbered (`0001-title.md`). |
| Agent instructions | `CLAUDE.md` | One file at the repo root. |

Some existing repos use other paths for historical reasons. Those are not being
churned — these locations are the convention for **new repos** only.

## 6. Keep the skeleton current (anti-drift)

Whatever the fleet standardizes — pinned action SHAs, a grouped
`dependabot.yml`, security headers for site repos, required status checks —
must land in this skeleton in the **same wave** as the sweep that introduces
it. Template drift silently un-standardizes every future repo: a new repo
created the day after a fleet sweep will miss whatever didn't make it into the
skeleton.

The skeleton currently carries:

- `.github/dependabot.yml` — weekly GitHub Actions updates, grouped into
  `actions-routine` (minor/patch) and `actions-major` (major) to make breaking
  bumps reviewable at a glance.
- CI wrappers that delegate to `lentago/shared-workflows@main` — no
  third-party action references to pin at this layer; pinning lives inside the
  shared workflows.

When you run a fleet-wide sweep, open a follow-up PR against this repo in the
same sprint.

## 7. Delete this file

```bash
git rm SETUP.md && git commit -m "Remove template setup notes" && git push
```
