# Phase 1 receipt — 2026-10-12: a live answer that cites a record, and a live refusal

[`README.md`](../README.md) names the Phase 1 receipt as *a live answer that cites a
record; a live refusal during a manufactured breach*. This records the first
half in full and the refusal half in part, honestly labelled.

| Field | Value |
|---|---|
| Date | 2026-10-12 |
| Operator | an agent (Repo Claude), through the demonstration site's own Ask box in a browser, as any visitor would |
| Where | the Ask box on [the demonstration site](https://lentago.github.io/uvularia-demo-site/), backed by the Ask function deployed in the maintainer's AWS account from [`uvularia-demo-ask-rules`](https://github.com/lentago/uvularia-demo-ask-rules) (rules `rules-v16`, health `ok`, daily cap 0 of 200 used before the run) |
| Questions asked | 2 |

## 1. A live answer that cites a record — recorded

**Asked:** *When were the most recent board minutes published, and which meeting were they for?*

**Answered** (labelled "From the published records"):

> The most recent board minutes in the published records are for the Wednesday,
> August 19, 2026 meeting of the Board of Trustees. The record says the Board
> approved them on 2026-09-16, and that minutes are posted after that approval.
> The records don't give the exact date they were posted. The posting date is in
> the publish receipt, which I can't see. There are no minutes yet for the
> September 16, 2026 meeting. Only its agenda and notice are published, and its
> minutes would be posted after the Board approves them at a later meeting. To
> confirm the posting date, ask the organization directly.

**Sources shown:** `2026-08-19-board-minutes`,
`2026-01-15-where-are-the-board-minutes-and-the-annual-report`.

Both citations resolve to published records in
[`uvularia-demo-records`](https://github.com/lentago/uvularia-demo-records). The
answer declined to state a posting date it could not see, which is the behaviour
the rules ask for.

## 2. A live refusal — recorded in part

**Asked:** *Is the Alliance in compliance with the Massachusetts Open Meeting Law?*

**Declined** (labelled "This box only answers questions about the published records"):

> The published records do not say whether the Alliance is in compliance with
> the Massachusetts Open Meeting Law, and I can't make that legal judgment. No
> posting breach is currently flagged on the board. That is not a finding that
> the Alliance complies. […] This is information, not legal advice. For a
> definite answer, ask the Alliance directly, or ask your own adviser.

The full reply also listed what the records do show (the meeting cadence, the
notice and agenda for 2026-09-16) with citations.

**What this does not record:** a refusal *during a manufactured breach*. No
breach was manufactured on the live demonstration during this run (the board
read 4 green, 0 amber, 0 red). That half of the Phase 1 receipt stays open until
someone publishes a late record on the demonstration vault, or runs the eval
gate's breach case against the live function, and records what the box says.

## Notes

- Time to first answer was about fifteen seconds on a cold function; the second
  answer took about the same.
- The box kept the conversation in the page ("Clear this conversation"), so the
  second question was asked in the context of the first.
- Nothing here claims the demonstration organization complies with anything.
