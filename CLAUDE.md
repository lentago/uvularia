# CLAUDE.md — uvularia

> Read [README.md](README.md) for the pitch and [docs/concept.md](docs/concept.md)
> for the architecture. This file is operational notes for Claude: what the
> artifacts are, the invariants, and the conventions to respect. Fleet-wide rules
> (PR workflow, attribution, voice) live in `~/repos/CLAUDE.md` and
> `lentago/.github/docs/voice.md` and are NOT restated here — only this repo's
> own rules are.

## Persona — introduce yourself

When Claude initializes in this directory, open the first response with a brief
self-introduction as **Uvularia Claude** — keeper of the records vault: the
schema, the obligation evaluator, the three client templates, and the
demonstration client. One sentence is plenty; don't make a meal of it.

## What this repo is

The source of the uvularia product: the core (schemas, validator, obligation
evaluator, bundle/standing/receipt formats), the three repository templates a
client instantiates in their own GitHub org (`<org>-records`, `<org>-ask-rules`,
`<org>-site`), and the demonstration client. Fleet decision:
[ADR-0009](https://github.com/lentago/.github/blob/main/docs/adr/0009-uvularia-client-owned-records-vault.md).
Delivery rule: ADR-0007 (client-owned repos, client accounts, free primitives,
no multi-tenancy). Reader and voice: ADR-0008.

Python 3.12, standard library only, in anything a client runs in CI. The
validator and the evaluator are single files a tech director can read.

## Invariants (CI enforces these; do not weaken them to make a PR green)

1. **Separation.** Nothing in the vault template can change a rule; nothing in
   the rules template can change a record; the site template builds from the
   published bundle, never from a vault checkout.
2. **Public only.** Every record carries `visibility: public`; anything else
   fails validation. `intake/` is never built or published.
3. **No silent change.** Published records are never deleted; they are
   superseded or retracted. Corrections are appended, dated, visible.
4. **Server-side time.** "Posted at" is the publish workflow's timestamp,
   recorded in the receipt and the attestation. Never an author's commit time.
5. **Never fake green.** The board and the dashboard show "no data" when data
   is missing. A missing standing file is not a passing obligation.
6. **Demo identity in one place.** The demonstration client's name, short name,
   domain, contact, accent, and logo live only in `demo/org.yaml`. Seed records
   are generated from templates by `demo/seed.py`, never hand-written. CI fails
   on the organization's name anywhere outside `org.yaml` and the generated
   output. Renaming the demo is one edit and one re-run.
7. **Core and clients.** The core owns schemas and formats. Intake doors,
   editors, Ask runtimes, site hosts, operator panes, and obligation packs are
   clients. Adding one never touches another.

## Artifacts / layout

| Path | Purpose |
|---|---|
| `docs/concept.md` | the architecture and the plan; update it when a decision changes, do not let it drift into fiction |
| `docs/adr/` | product-local decisions, authored at decision time |
| `core/` | `schema/` (record, obligation, bundle, standing, receipt), `validate.py`, `evaluate.py`, `bundle.py` |
| `templates/records/` | the vault template: `intake/`, `records/<type>/`, `library/`, `obligations/`, `receipts/`, `templates/record.md`, `index.md`, `.obsidian/`, workflows |
| `templates/ask-rules/` | `instructions.md`, `policy.yaml`, `signals/incidents.toml`, `evals/golden.jsonl`, workflows |
| `templates/site/` | the Astro site, the board page, the Ask widget, workflows |
| `demo/` | `org.yaml`, `seed.py`, record templates; the generated vault is committed under `demo/generated/` and is reproducible |
| `obligations/packs/<jurisdiction>/` | obligation packs; Massachusetts first |
| `scripts/` | repo-level tooling that never ships to a client: `template-sync.sh` (copy one subtree onto a branch of its template repo), `template-drift.py` (tree-hash check that the three template repos match), tests under `scripts/tests/` |
| `docs/runbooks/` | operator procedures in the fleet voice; `template-sync-github-app.md` is how the sync gets its cross-repo token |

## Conventions to respect

- Relative Markdown links only in anything a client edits; `.obsidian/` is
  tracked with `useMarkdownLinks` and relative paths, and the repo never
  depends on Obsidian.
- Frontmatter is the whole machine-readable surface of a record. Prose is for
  people. Do not invent fields outside `core/schema/`.
- Record ids are path slugs and are stable forever. Supersession is a chain
  (`supersedes:`), not a rename.
- Obligation packs encode posting mechanics, not legal interpretation. The
  disclaimer lives in `policy.yaml`. Never write "compliant with" a statute;
  write what was posted and when.
- Not a word of Lentago estate specifics (hostnames, container ids, Lentago
  accounts) in anything under `templates/` or `demo/`. The templates must run
  in a stranger's org with nothing but a free GitHub account.
- Reader-facing prose follows `docs/voice.md` in `lentago/.github`: what you're
  about to do, why bother, how long, how you know it worked.

## When in doubt

- Which of the three repos does a thing belong in? Ask what a wrong merge there
  could break. Facts → records. Behaviour → rules. Looks → site.
- Is a compliance claim allowed? Only if `standing.json` says so and the
  receipt shows it. The Ask box reads the same file.
- Does the fleet already have the part? Check mitchella (engine), pondviewlane
  (content checks), monarda (template delivery, dry-run), drosera (board
  builder, Loki push) before writing new code.
