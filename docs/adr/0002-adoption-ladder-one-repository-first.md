# ADR-0002: Adoption is a ladder, and the first rung is one repository

**Status:** Accepted (2026-10-04)

## Context

[ADR-0009](https://github.com/lentago/.github/blob/main/docs/adr/0009-uvularia-client-owned-records-vault.md)
in `lentago/.github` fixed the shape of a uvularia installation: three
repositories per client (`<org>-records`, `<org>-ask-rules`, `<org>-site`),
three pipelines, three blast radii. That separation is still right once the
Ask box is on: a corpus change cannot alter a rule, a rule change cannot alter
a fact, a site change cannot smuggle either.

It is the wrong first thing for the reader to meet. The reader
([ADR-0008](https://github.com/lentago/.github/blob/main/docs/adr/0008-pro-bono-practice-one-reader.md))
is the one tech person at a volunteer organization. As written on 2026-10-03,
[`ADOPTION.md`](../../ADOPTION.md) opened with two repositories created from two
templates, and the full installation is three repositories, one AWS account,
one Grafana Cloud account, and about eight secrets and variables. The timed
dry-run ([receipt](../../receipts/2026-10-03-agent-run.md)) took 28 minutes of
working time for the two-repository Phase 0 and recorded the site's first
deploy racing the vault's Pages publish.

The public "Is it posted?" board was the only reason the site repository had to
exist on day one. Everything else the board needs is already published by the
records repository itself: the publish workflow writes `standing.json`,
`feed.xml`, `corpus-latest.json` and a receipt to a `published` branch served
by GitHub Pages. The board was an Astro page reading those same files from a
second repository.

The real complexity cliff is not the repository count. It is the AWS account
the Ask box needs, and the rules repository exists only because of the Ask
box. The site and the pane are each a further, optional step.

## Decision

1. **Adoption is a ladder of four rungs.** Each rung is one "Use this
   template" click (or one account), has its own guide page, and the reader
   may stop on any rung with a working, honest installation:

   | Rung | You get | You add |
   | :-- | :-- | :-- |
   | 1. The vault | records, the intake form, receipts, and a plain public board | one repository, `<org>-records` |
   | 2. A proper site | your own look, and the Ask widget once rung 3 exists | one repository, `<org>-site` |
   | 3. The Ask box | grounded answers from the records | one repository, `<org>-ask-rules`, and an AWS account |
   | 4. The operator pane | the left-to-right pipeline view and its alerts | a Grafana Cloud free-tier account |

2. **The records template publishes its own board.** The publish workflow
   writes a plain `index.html` to the `published` branch next to
   `standing.json`, rendered by a standard-library script with no JavaScript,
   no build step and no external assets, honouring invariant 5 (a missing
   standing is "no data", never green). The vault alone is therefore a
   complete rung 1. The site template remains the presentation layer and
   still builds only from the published bundle (invariant 1); it is no longer
   required for the board to exist.

3. **The Kit tier is earned at rung 1.** The timed dry-run that backs the Kit
   label is re-run against the one-repository rung and its receipt replaces
   the two-repository timing in `ADOPTION.md`. Until that run happens, the
   rung-1 time is marked as not yet measured, not estimated.

4. **The demonstration client shows all four rungs**, so the top of the
   ladder stays a receipt the practice can point at
   ([ADR-0001](0001-demo-identity-in-one-file-generated-seed.md)).

5. **The cost of ownership is said on rung 1.** A template copy belongs to
   the client and never receives the practice's later fixes on its own. The
   records template ships a core sync script and the guide says, in plain
   words, that updates are something the client chooses to pull.

ADR-0009's three-repository shape is unchanged as the shape of a *complete*
installation. What changes is the order the reader meets the parts in, and
that the first part stands alone.

## Alternatives

- **Keep the two-repository Phase 0.** Rejected: the second repository
  existed only to render files the first one already publishes, and its
  first deploy raced the vault's Pages publish in the dry-run.
- **Fold the rules repository into the records repository** with path-scoped
  reviewers, so the whole installation is two repositories. Rejected in
  ADR-0009 (rulesets and required checks are per repository, so the gates
  would merge) and rejected again here: the rules repository only arrives
  with the Ask box, which already costs an AWS account, so removing it saves
  the reader nothing on the rungs that matter.
- **One template that creates everything at once.** Rejected: GitHub's "Use
  this template" produces one repository, and a single repository is exactly
  the shape ADR-0009 ruled out for the complete installation.
- **Render the board in the records repository with the Astro site moved in
  beside it.** Rejected: that brings npm and a build into the vault, which a
  tech director must be able to read and run with nothing installed.

## Consequences

- `templates/records` gains `scripts/board.py` and a publish step that lays
  `index.html` on the `published` branch (uvularia#70).
- `ADOPTION.md` is rewritten as the four rungs, one page per rung, in the
  fleet voice; `README.md` and `docs/concept.md` describe the ladder; the
  lupinus picker row and the org profile describe rung 1 as the entry.
- `lentago/.github` ADR-0009 carries an amendment pointing here.
- The rung-1 dry-run is re-run and its receipt filed under `receipts/`.
- The site template's board page stays; an org on rung 2 gets the same board
  twice (plain on the vault's Pages, styled on the site's). That duplication
  is accepted: the plain page is the one that can never be down for a build
  reason.
