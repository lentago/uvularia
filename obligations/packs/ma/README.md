# Massachusetts obligations pack (`ma`)

> **Not legal or tax advice.** This pack encodes posting mechanics derived from
> the statutes and regulations cited in each rule. Whether any specific obligation
> applies to your organization, and whether you have met it, requires advice from
> qualified legal counsel. See your rules repo's `policy.yaml` for the full
> disclaimer.

---

## Rules in this pack

| Rule ID | What it encodes | Source | What it does NOT cover | Certainty |
|---|---|---|---|---|
| `ma-oml-meeting-notice` | Meeting notice posted at least 48 hours before the meeting | M.G.L. c. 30A, § 20(b) | Exclusion of Saturdays, Sundays, and legal holidays from the 48-hour window (see [Known limitation](#known-limitation-oml-48-hour-calendar-exclusion)); additional posting locations beyond the principal office; remote-participation notice requirements | verified |
| `ma-oml-minutes-timely` | Minutes created and approved within a configurable lag (default: 30 days) | M.G.L. c. 30A, § 22(a) | The statute says "timely manner" without fixing a number of days; the 30-day default is an operator configuration, not a statutory requirement (see [Configurable lag](#configurable-lag-for-ma-oml-minutes-timely)) | verified |
| `ma-ag-charity-annual-filing` | Annual filing of Form PC with the Attorney General at most 12 months after the previous one | M.G.L. c. 12, § 8F; 940 CMR 2.00 | Specific due date (determined by fiscal year end); late-filing fees; exemptions for certain organizations; registration threshold | verified |
| `ma-corp-annual-report` | Annual report filed with the Secretary of the Commonwealth at most 12 months after the previous one | M.G.L. c. 180, § 26A | Specific due date (November 1 in the fiscal year following each fiscal year); late fees; dissolution consequences | verified |
| `ma-condo-annual-budget` | Annual budget for common expenses prepared and made available to unit owners at most 12 months after the previous one | M.G.L. c. 183A, § 10(b) | Specific timing relative to fiscal year start; distribution method; line-item content requirements | verified |
| `ma-condo-meeting-notice` | Annual or special meeting notice posted at least 7 days before the meeting | M.G.L. c. 183A, § 11 and typical condominium trust bylaws | Exact day count varies across trust declarations and bylaws; special-meeting notice periods, which may differ from annual-meeting periods | reported |

**Certainty key:**
- `verified` — rule reflects a requirement stated directly in the cited statute or regulation.
- `reported` — rule reflects typical practice derived from standard form documents (trust declarations, model bylaws) rather than a direct statutory requirement; the day count or specific mechanic may differ in any given organization's governing documents.

---

## Notes

### Known limitation: OML 48-hour calendar exclusion

M.G.L. c. 30A, § 20(b) requires that the 48-hour notice period for public body
meetings exclude Saturdays, Sundays, and legal holidays. The obligation schema's
`lead` type accepts only a plain number of hours or days, with no parameter for
excluded calendar days. This rule encodes a plain 48-hour window. Issue [#13](https://github.com/lentago/uvularia/issues/13) proposes extending
the `lead` type with an `exclude_weekends_and_holidays` parameter so the
evaluator can apply the correct calendar arithmetic.

### Configurable lag for `ma-oml-minutes-timely`

The Open Meeting Law requires that minutes be created and approved "in a timely
manner" but does not state a number of days. The rule encodes `lag: {days: 30}`
as a reasonable default. An operator may override this value in their vault's
obligation configuration to reflect their board's practice or their counsel's
guidance. The board's target and any variance should be explained in the plain-
English description the board secretary maintains — that prose is not part of the
obligation schema.

### `ma-condo-meeting-notice` is derived from typical bylaws

Most Massachusetts condominium trust declarations and bylaws require 7 to 14 days'
written notice of the annual or special meeting of unit owners. The rule encodes
7 days as the shorter end of this range. An organization whose governing documents
require longer notice should update this rule or note the difference in their vault.
Because the requirement comes from bylaws rather than directly from M.G.L. c. 183A,
this rule carries `certainty: reported` in the table above.

---

## Fixtures

Each rule has a fixture pair in [`fixtures/`](fixtures/):

- `<rule-id>.pass.json` — a minimal record set that `evaluate.py` should evaluate
  as the stated `expected_state` (typically `green`).
- `<rule-id>.fail.json` — a minimal record set that `evaluate.py` should evaluate
  as a non-green `expected_state` (`red` or `no-data`).

Fixture records include only the fields the evaluator needs:

| Timing kind | Required fields in fixture records |
|---|---|
| `lead` | `id`, `type`, `status`, `effective` (event date), `published_at` (server-side publish time) |
| `lag` | `id`, `type`, `status`, `effective` (event date), `approved` (record approval date) |
| `cadence` | `id`, `type`, `status`, `effective`, `approved` |

`published_at` is a test-convenience field injected by the test harness; in
production it comes from the publish receipt.

---

## Adding another state

Each jurisdiction lives in its own subdirectory under `obligations/packs/`. Adding
a second state creates `obligations/packs/<code>/` and does not touch this
directory. The check script at `obligations/check_packs.py` discovers all packs
automatically.
