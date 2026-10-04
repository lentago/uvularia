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
| `ma-oml-meeting-notice` | Meeting notice posted at least 48 hours before the meeting, not counting Saturdays, Sundays, or the statewide legal holidays in [`holidays/`](holidays/) | M.G.L. c. 30A, § 20(b); M.G.L. c. 4, § 7, cl. 18 | The meeting's time of day: a record carries only the date, so the 48 hours count back from the start of that day, which is stricter than the statute for a 7 p.m. meeting (see [How the 48 hours are counted](#how-the-48-hours-are-counted)); days are UTC calendar days, not Eastern time; holidays in years with no `holidays/` file (outside 2024–2026) count as working days; Suffolk County's Evacuation Day and Bunker Hill Day; additional posting locations beyond the principal office; remote-participation notice requirements | verified |
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

### How the 48 hours are counted

M.G.L. c. 30A, § 20(b) asks for notice "at least 48 hours prior to such meeting,
excluding Saturdays, Sundays and legal holidays." The rule encodes that as
`lead: {hours: 48, weekdays_only: true, exclude_dates: [...]}`: Saturdays,
Sundays, and every listed holiday are skipped, and the 48 hours come from the
days around them. A notice for a Monday meeting has to be up by the start of
the previous Thursday. For a Tuesday meeting after a Monday holiday, that's
also the Thursday before.

A record carries only the meeting's date, not its time, so the evaluator counts
back from the start of the meeting day. That is stricter than the statute for
an evening meeting: a notice posted Wednesday morning for a Friday 7 p.m.
meeting meets the law but shows red here. Post a day early and the question
never comes up.

### Legal holidays are data

[`holidays/`](holidays/) holds one file per year (2024, 2025, 2026) listing the
statewide legal holidays in M.G.L. c. 4, § 7, cl. 18, with a fixed-date holiday
that falls on a Sunday moved to the Monday. Each file cites its source; the 2026
dates were checked against the Secretary of the Commonwealth's published list.
`ma-oml-meeting-notice.json` carries the same dates in `exclude_dates`.
`obligations/check_packs.py` fails if the two ever disagree.

**Before each new year:** add `holidays/<year>.json` and copy its dates into the
rule's `exclude_dates`. It takes about ten minutes. Until you do, that year's
holidays count as working days, so a notice posted over a holiday weekend can
show green when it was late. You'll know it worked when
`python3 obligations/check_packs.py` prints `ok` for the holidays line.

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

Each rule has at least one fixture pair in [`fixtures/`](fixtures/):

- `<rule-id>.pass.json` — a minimal record set that `evaluate.py` should evaluate
  as the stated `expected_state` (typically `green`).
- `<rule-id>.fail.json` — a minimal record set that `evaluate.py` should evaluate
  as a non-green `expected_state` (`red` or `no-data`).

A rule may carry extra named cases (`<rule-id>.pass-<case>.json`,
`<rule-id>.fail-<case>.json`). `ma-oml-meeting-notice` has three: a Friday-evening
notice for a Monday meeting (`fail-weekend`, red), a Thursday notice for a Tuesday
meeting after Columbus Day (`fail-holiday`, red), and a notice up at the start of
Wednesday for a Friday meeting (`pass-midweek`, green).

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
