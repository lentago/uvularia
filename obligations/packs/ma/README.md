# Massachusetts obligations pack (`ma`)

> **Not legal or tax advice.** This pack encodes posting mechanics derived from
> the statutes and regulations cited in each rule. Whether any specific obligation
> applies to your organization, and whether you have met it, requires advice from
> qualified legal counsel. See your rules repo's `policy.yaml` for the full
> disclaimer.

---

## Rules in this pack

Two columns say how far to trust a row, and they answer different questions.
**Mechanics** is whether the rule computes what this table says it computes:
`fixtures pass` means the cases in [`fixtures/`](fixtures/) run green through the
evaluator in CI. **Legal scope** is what a green row asserts about the law. Three
rules here are **proxies**: 12-month reminders standing in for a due date the
rule cannot know. A proxy's green row says a record was posted within 12 months
of the last one, nothing more, and its `scope_note` says so under its title on the
board.

| Rule ID | What it encodes | Source | What it does NOT cover | Mechanics | Legal scope |
|---|---|---|---|---|---|
| `ma-oml-meeting-notice` | Meeting notice posted at least 48 hours before the meeting, not counting Saturdays, Sundays, or the statewide legal holidays in [`holidays/`](holidays/) | M.G.L. c. 30A, § 20(b); M.G.L. c. 4, § 7, cl. 18 | The meeting's time of day: a record carries only the date, so the 48 hours count back from the start of that day, which is stricter than the statute for a 7 p.m. meeting (see [How the 48 hours are counted](#how-the-48-hours-are-counted)); days are UTC calendar days, not Eastern time; a window in a year with no `holidays/` file (outside 2024–2027) is no-data; Suffolk County's Evacuation Day and Bunker Hill Day; additional posting locations beyond the principal office; remote-participation notice requirements | fixtures pass | Statutory timing, encoded stricter than the statute |
| `ma-oml-minutes-timely` | Minutes created and approved within a configurable lag (default: 30 days) | M.G.L. c. 30A, § 22(a) | The statute says "timely manner" without fixing a number of days; the 30-day default is an operator configuration, not a statutory requirement (see [Configurable lag](#configurable-lag-for-ma-oml-minutes-timely)) | fixtures pass | Operator target: the statute sets no number |
| `ma-ag-charity-annual-filing` | Annual filing of Form PC with the Attorney General at most 12 months after the previous one | M.G.L. c. 12, § 8F; 940 CMR 2.00 | Specific due date (determined by fiscal year end); late-filing fees; exemptions for certain organizations; registration threshold | fixtures pass | **Proxy**: a 12-month reminder, not the fiscal-year due date |
| `ma-corp-annual-report` | Annual report filed with the Secretary of the Commonwealth at most 12 months after the previous one | M.G.L. c. 180, § 26A | The fixed due date (November 1); late fees; dissolution consequences; which organizations it applies to | fixtures pass | **Proxy**: a 12-month reminder, not the November 1 due date (see [The annual report's fixed date](#the-annual-reports-fixed-date)) |
| `ma-condo-annual-budget` | Annual budget for common expenses prepared and made available to unit owners at most 12 months after the previous one | M.G.L. c. 183A, § 10(b) | Specific timing relative to fiscal year start; distribution method; line-item content requirements | fixtures pass | **Proxy**: a 12-month reminder, not the fiscal-year timing |
| `ma-condo-meeting-notice` | Annual or special meeting notice posted at least 7 days before the meeting | M.G.L. c. 183A, § 11 and typical condominium trust bylaws | Exact day count varies across trust declarations and bylaws; special-meeting notice periods, which may differ from annual-meeting periods | fixtures pass | Typical bylaws, not the statute: check your declaration |

**Legal scope key:**
- **Statutory timing** — the rule encodes a timing the cited statute states. Where
  it differs (here, stricter), the "does NOT cover" column says how.
- **Operator target** — the statute sets no number; the rule checks one you chose.
- **Proxy** — a reminder on a fixed cycle, standing in for a due date the rule
  cannot know. A green row is not standing with the agency.
- **Typical bylaws** — derived from standard form documents (trust declarations,
  model bylaws) rather than a statute; your governing documents may differ. This
  replaces the `reported` label earlier versions of this table used.

No row in this table is a legal finding. Whether a rule applies to your
organization, and whether you have met it, is for qualified counsel. A qualified
legal read of this pack waits for a real adopter.

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

[`holidays/`](holidays/) holds one file per year (2024 through 2027) listing the
statewide legal holidays in M.G.L. c. 4, § 7, cl. 18, with a fixed-date holiday
that falls on a Sunday moved to the Monday. Each file cites its source. The 2026
dates were checked against the Secretary of the Commonwealth's published list.
The 2027 dates were computed from the statute's rules, the same computation that
reproduces 2026; check them against the Secretary's 2027 list once it is out.
`ma-oml-meeting-notice.json` carries the same dates in `exclude_dates`, and the
years in `calendar_years`. `obligations/check_packs.py` fails if either ever
disagrees with the files.

A notice whose 48 hours reach into a year with no file is **no-data** on the
board, never green: the evaluator will not count a year's holidays as working
days because nobody listed them.

**Before each new year:** add `holidays/<year>.json`, copy its dates into the
rule's `exclude_dates`, and add the year to `calendar_years`. It takes about ten
minutes. `check_packs.py` starts failing on 1 October for the coming year, so CI
tells you in time. You'll know it worked when
`python3 obligations/check_packs.py` prints `ok` for the holidays line.

### The annual report's fixed date

`ma-corp-annual-report` is a 12-month cadence, so a report filed late on
December 15 keeps its row green until the next December. The Commonwealth's
actual due date for the organizations it applies to is November 1. Which
organizations those are is a legal question this pack does not answer.

Once counsel has confirmed the date applies to yours, replace the rule's timing
in your vault's copy with the fixed-date kind:

```json
"due": { "month": 11, "day": 1 }
```

in place of `"cadence": { "months": 12 }`, and change its `scope_note` to say
what your counsel confirmed. Each November 1 then needs its own filing. A filing
after a missed November 1 is that year's late filing, and the row stays red until
the next November 1 is met on time ([`core/evaluate.md`](../../../core/evaluate.md),
"due").

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
`<rule-id>.fail-<case>.json`). `ma-oml-meeting-notice` has four: a Friday-evening
notice for a Monday meeting (`fail-weekend`, red), a Thursday notice for a Tuesday
meeting after Columbus Day (`fail-holiday`, red), a notice up at the start of
Wednesday for a Friday meeting (`pass-midweek`, green), and a notice for a 2028
meeting, a year with no `holidays/` file (`fail-no-calendar`, no-data).

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
