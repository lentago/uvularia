# Adoption receipt — <YYYY-MM-DD>

Copy this file to `receipts/<YYYY-MM-DD>-<operator>.md` and fill it in after
running [`DRY-RUN.md`](../DRY-RUN.md) end to end. Leave a field blank only if it
genuinely does not apply, and say why in the notes. Do not invent a run.

| Field | Value |
|---|---|
| Date of drill | |
| Operator | |
| Target org | |
| Records repo | `<org>-records` |
| Site repo | `<org>-site` |
| **Total elapsed time** | |
| All checks green? (Y/N) | |
| Slowest step (bottleneck) | |

## Per-step elapsed

The fifteen drill steps, with the time each took. Use this to find the
bottleneck and to keep later runs honest.

| # | Step | Green? | Elapsed |
|---|---|---|---|
| 1 | Create the vault from the template | | |
| 2 | Name your org in `index.md` | | |
| 3 | Set reviewers in `CODEOWNERS` | | |
| 4 | Keep the obligations that apply | | |
| 5 | Merge the first change (publish runs) | | |
| 6 | Turn on the vault's Pages (`published`) | | |
| 7 | Protect `main` | | |
| 8 | File the first record (Issue form) | | |
| 9 | Check the record's PR (validate green) | | |
| 10 | Approve and merge the record | | |
| 11 | Create the site from the template | | |
| 12 | Turn on the site's Pages (Actions) | | |
| 13 | Point the site at the vault (`site.config.ts`) | | |
| 14 | Watch the deploy go green | | |
| 15 | Open the board — green row | | |

## Notes / follow-ups

- What was slower than expected, and why?
- Anything in [`ADOPTION.md`](../ADOPTION.md) or [`DRY-RUN.md`](../DRY-RUN.md)
  that was wrong, unclear, or missing a prerequisite?
- Any trap you hit that is not already in the "Heads up" lists?
