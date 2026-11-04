# ADR-0003: Later template changes reach a client through an update door the client owns

**Status:** Accepted (2026-11-04)

## Context

A client's installation is made with "Use this template" from three template
repositories (`uvularia-records-template`, `uvularia-rules-template`,
`uvularia-site-template`). Since 2026-10-06 those templates track
`templates/<name>` in this repository automatically: every merge here opens and
auto-merges a sync pull request on each template repository
([uvularia#28](https://github.com/lentago/uvularia/issues/28)).

That covers the templates. It doesn't cover a repository a client has already
made from one. "Use this template" makes a copy with its own history, and the
copy never hears about a later validator rule, workflow fix or clearer guide.
[ADR-0002](0002-adoption-ladder-one-repository-first.md) Decision 5 said so on
rung 1 and gave the vault one partial remedy, `scripts/sync-core.sh`, which
re-downloads `core/` and nothing else. The demonstration repositories are the
first case. They were generated on 2026-10-03 and kept current only by hand
syncs (most recently on 2026-11-02, lentago/uvularia-demo-records#21).

A client's copy is also never a clean copy. It holds the client's records,
settings and reviewers, and the client may have edited a template file on
purpose. ADR-0007 (client-owned delivery) requires that whatever keeps it
current runs in the client's own accounts. It also forbids a Lentago control
plane serving many client organizations.

[uvularia#112](https://github.com/lentago/uvularia/issues/112) set out three
options. The maintainer chose the second on 2026-11-04.

## Decision

1. **Each template ships an update door**: the workflow
   `.github/workflows/template-update.yml`, the script
   `scripts/template-update.py` (standard library and git only, the same file
   in all three templates), and the config `.github/template-update.toml`.
   The workflow runs weekly and on demand in the client's repository, fetches
   the template named in the config, and opens **one pull request** in the
   client's repository. The client's own checks gate it and the client merges
   it. The pull request is the record of the change.

2. **The client's own token.** The pull request is pushed and opened with a
   secret the client sets, `TEMPLATE_UPDATE_TOKEN`: a fine-grained personal
   access token for that one repository, with Contents, Pull requests and
   Workflows read-write. The built-in workflow token can't be used, because it
   can't change files under `.github/workflows/` and pull requests it opens
   don't trigger the client's checks. Without the secret, the workflow opens
   one issue saying an update is waiting and how to set the token. It doesn't
   fail.

3. **A three-way, file-by-file update.** The repository records the template
   commit it last took in `.github/template-base`. Before its first update,
   that base is inferred: the first commit "Use this template" makes has
   exactly the template's tree. A recorded base that is damaged or can't be
   fetched stops the run. It is never treated as "no base", because that path
   replaces files instead of merging them. For each file, the base, the
   template now and the client's version are compared:
   - a file the client never changed becomes the template's;
   - a file the template didn't change stays the client's;
   - where both changed it, the two are merged line by line, and overlapping
     changes are left between conflict markers, with the pull request opened
     as a draft;
   - a file the template removed is removed only if the client hadn't
     changed it;
   - anything else is left as the client has it and listed in the pull
     request.

4. **A keep list the client owns.** Paths in the config's `keep` list are
   never added, changed or removed, and neither are the config and the base
   file. The templates ship these defaults:
   - **records:** the records, receipts and library, `index.md`,
     `validate.toml`, `CODEOWNERS` and `LICENSE`. Invariant 3 (no silent
     change) is never left to a merge.
   - **rules:** the behaviour files `policy.yaml`, `instructions.md`,
     `signals/` and `evals/golden.jsonl`, with `CODEOWNERS` and `LICENSE`.
     A change to how the client's Ask box behaves is always the client's
     decision.
   - **site:** `site.config.ts`, `CODEOWNERS` and `LICENSE`.

5. **One pull request at a time, and no for an answer.** While an update pull
   request is open, the workflow does nothing. Each update has its own branch,
   `template-update/<template commit>`, and is never force-pushed. A client
   who closes an update pull request without merging it is not offered that
   template commit again (its branch, and anything they pushed to it, stays),
   and the next template change opens a new one. A pull request that holds
   conflict markers, or files replaced without a base, opens as a draft.

6. **The demonstration client takes updates through the door.** Its three
   repositories carry the door, with keep lists that add the files its
   generator (`demo/seed.py`) owns. Files the generator owns are still
   hand-synced from `demo/generated/`, and everything else arrives as an update
   pull request.

## Alternatives

Weighed in uvularia#112:

- **Templates are starting points, with a release note per change.** Honest
  and free, but every client drifts from the first day, and the note asks the
  one tech person to work out the change themselves.
- **Versioned template releases that a client pins and bumps with a runbook.**
  Deliberate, but each bump is a manual procedure per repository, and the
  template repositories would need a release process the sync doesn't have
  today.

Considered while building it:

- **Overwrite every non-kept file with the template's version** (the sync
  reversed, as `rsync --delete`). Simpler, but it reverts every deliberate
  client edit and deletes every file the client added. Rejected for the
  three-way update above.
- **The practice's GitHub App opens the pull requests.** No token for the
  client to make, but one App installed across many client organizations is a
  Lentago system serving many clients, which ADR-0007's multi-tenancy line
  rules out. Updates would also stop the day the client fires the practice.

## Consequences

- `templates/{records,ask-rules,site}` carry the door. A test in
  `scripts/tests/test_template_update.py` (run by the template-sync workflow's
  drift job) holds the update rules against local repositories, and holds the
  three copies of the script and the workflow byte-identical.
- `ADOPTION.md` gains **Getting later template changes**, and each template
  README says how its door works. The rung-1 heads-up no longer says the
  client must pull by hand.
- `scripts/sync-core.sh` stays, for a client who wants to pin `core/` to a
  specific upstream ref. Such a client adds `core/` to `keep`.
- The rules repository's `ask-function/` folder isn't in any template, so the
  door doesn't update it. It's still copied from this repository as the Ask
  function README describes.
- A repository made before the door existed installs it once by hand, by
  copying the three files from its template. The demonstration repositories
  did this first.
- The token expires on the date its owner chose. When it does, the push is
  refused and the run fails with a message saying to make a new one.
