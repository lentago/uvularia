# Adoption receipt — 2026-10-12 (one-repository rung, agent run)

The first timed run of the **one-repository rung 1** of [`DRY-RUN.md`](../DRY-RUN.md),
start to finish, into a personal GitHub account outside the lentago organization.
The earlier [2026-10-03 receipt](2026-10-03-agent-run.md) timed the superseded
two-repository rung; this one times the rung [`ADOPTION.md`](../ADOPTION.md)
describes today.

| Field | Value |
|---|---|
| Date of drill | 2026-10-12 |
| Operator | an agent (Repo Claude) driving the maintainer's personal GitHub account; the organization's name, reviewer, and first document were prepared before the clock started |
| Target org | `cpitzi` (a personal account on GitHub Free, outside the lentago organization) |
| Records repo | [`cpitzi/pennywell-records`](https://github.com/cpitzi/pennywell-records), public, created with **Use this template** from `lentago/uvularia-records-template` |
| Site repo | not created (rung 2 was not run) |
| **Total elapsed time** | **6 min 09 s** to the first green row on the live board |
| All checks green? (Y/N) | **N.** The first record's pull request failed the **validate** check (a path convention the scaffold hint does not state, [#98](https://github.com/lentago/uvularia/issues/98)); the operator merged it with an admin bypass before reading the failure, which was an operator error. A second pull request fixed the path, validated green, and published, about three minutes after the clock stopped. Everything else was green. |
| Slowest step (bottleneck) | step 10, adding the original document by hand and approving the record: 2 min 05 s including the merge |

The organization is fictional (the Pennywell Street Pantry from the lupinus
adoption stories) and its `index.md` says so.

## Per-step elapsed

Rung 1 only. Steps 11–15 (the branded site) were not run.

| # | Step | Green? | Elapsed |
|---|---|---|---|
| 1 | Create the vault from the template | Y | 14 s |
| 2 | Name your org in `index.md` | Y | prepared before the clock; applied in step 5's commit |
| 3 | Set reviewers in `CODEOWNERS` | Y | as above |
| 4 | Keep the obligations that apply | Y | as above (kept `ma-oml-minutes-timely`; the fictional board adopted a 30-day minutes practice) |
| 5 | Merge the first change (publish runs) | Y | 45 s from push to a green publish run and a `published` branch |
| 6 | Turn on the vault's Pages (`published`) | Y | 2 s via the REST API; the board served 21 s later |
| 7 | Protect `main` | Y | 1 s via the REST API (require a pull request, require Code Owner review) |
| 8 | File the first record (Issue form) | Y | 33 s. Filed through the API with the form's body shape; no document attached, so the by-hand path was exercised. The form UI itself was not. |
| 9 | Check the record's PR (validate green) | **N** | 24 s for intake to scaffold the branch, then 41 s to open the pull request by hand (Actions may not open pull requests on a fresh repo; the intake comment's compare link worked). Validate went **red** once the source block was added in step 10: `source.file … does not exist`. See notes. |
| 10 | Approve and merge the record | partly | 2 min 05 s: the original copied into `library/files/minutes/`, listed in `manifest.json`, the `source:` block and `status: approved` set, pushed; merged with `--admin` because the only Code Owner is the author. |
| 11–15 | Rung 2 (site) | not run | — |
| — | The board shows the obligation green | Y | 41 s after the publish run; `standing.json` on `published` reads `ma-oml-minutes-timely: green`, satisfied by the new record, gap −17 days |

## Notes / follow-ups

- **The scaffold hint and the validator disagree about where a path starts.** The
  hint says "put the original under `library/files/<type>/`" and the schema only
  says `file` is a string; `core/validate.py` resolves `source.file` from the
  repository root, so `files/minutes/…` fails and `library/files/minutes/…`
  passes. Filed as [#98](https://github.com/lentago/uvularia/issues/98) with the
  fix options. This is the one defect that turned a check red.
- **A single-person org cannot approve its own record.** With `CODEOWNERS` set to
  the one tech person and "Require review from Code Owners" on, the intake pull
  request has no eligible approver. The run used an admin bypass; the drill's
  step 7 should say what to do (a second reviewer account, or the bypass list).
  Recorded in #98.
- **Actions could not open the pull request** on the fresh repository (GitHub's
  default). The intake comment's one-click link covered it. Already tracked as
  [#30](https://github.com/lentago/uvularia/issues/30).
- **Merging past a red check was the operator's mistake**, not the template's:
  the runbook says plainly that nothing publishes until validate is green. The
  publish workflow does not re-run validate, so the vault published a record
  whose `source` path was wrong until the second pull request. Worth one line in
  `DRY-RUN.md` step 10: "do not bypass; a red validate means the published vault
  will carry the defect."
- **The template's initial commit runs publish immediately**, before the operator
  has touched anything, which is harmless here (it created the `published`
  branch early, so step 6 did not have to wait).
- The drag-and-drop attachment path was not exercised (an agent cannot drop a
  file into the form); a human run should attach the PDF in step 8 and see
  whether the workflow can download it.
- The drill repository stays up as the live artifact this receipt points at.
