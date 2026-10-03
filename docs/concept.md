# uvularia — concept

A client-owned records vault with a grounded Ask box and a live compliance board.

**Status:** accepted 2026-10-03 as [ADR-0009](https://github.com/lentago/.github/blob/main/docs/adr/0009-uvularia-client-owned-records-vault.md) in `lentago/.github`. This document is the living architecture; update it when a decision changes.
**Supersedes:** [.github#128](https://github.com/lentago/.github/issues/128) (Ask-the-Records kit, closed into [.github#200](https://github.com/lentago/.github/issues/200)). **Feeds:** .github#130 (funder-report fact pipeline), .github#122 (Good-Standing Kit), lupinus story 03 (Stillwater Brook).
**Codename:** *uvularia* (bellwort, a New England native; the bell is the announcement).

---

## 1. What it is, in one paragraph

A nonprofit, HOA, land trust, or town committee keeps its public records — minutes, notices, bylaws, policies, filings, announcements — as an Obsidian-compatible Markdown vault in its own GitHub organization. Three separate pipelines consume that vault: one publishes the corpus, one governs the model rules for an Ask box that answers only from the corpus, and one builds the public site and announcement feed. Obligations ("meeting notice posted at least 48 hours ahead", "minutes posted within 30 days", "conflict-of-interest policy reviewed annually") are declared as code next to the records that satisfy them, evaluated on every publish, and shown live on a public "Is it posted?" board and on an operator dashboard in the org's own Grafana Cloud free tier. The tech director's job is to drop a document and a sentence into intake and merge a pull request. Everything else is a receipt.

It is the pondviewlane pattern with the parts that made it one community's site removed, mitchella's engine put behind it, and compliance evidence made a by-product of publishing rather than a separate chore.

## 2. Who it is for, and what "demonstrate compliance" means to them

The one reader (ADR-0008): the single tech person at an organization with **posting obligations and people who ask the same questions over and over**.

| Organization | Obligations they must show, live | Questions they field |
|---|---|---|
| Condo / HOA board | notice of meetings, annual budget, approved minutes, current rules, assessment history | "what are the rules on X", "when is the next meeting", "what did the board decide about Y" |
| Nonprofit with a board | 990 availability, conflict-of-interest policy, board minutes to members, annual report, state charity filing | "where's the annual report", "who's on the board", "what's your refund policy" |
| Town board or committee (MA Open Meeting Law) | 48-hour meeting notice, minutes within the statutory window, agendas | "is the hearing still on", "what's on the agenda" |
| Land trust / watershed group | stewardship reports, permits, easement terms, trail status | "is the trail open", "what does the easement allow" |

"Demonstrate" means three things, and the design produces each one automatically:

1. **A public board** that says, for every obligation, green / amber / red, with the timestamp and the record that satisfies it. Hosted on GitHub Pages. No login, no Grafana, no AI.
2. **A receipt per publish**: what changed, when it was published (server-side timestamp from the Actions run, not the author's clock), what the obligations stood at, and a signed provenance statement that this corpus came from that commit.
3. **An Ask box that will not contradict the board.** If the board says September minutes are overdue, the Ask box says so before it answers anything about September. That is mitchella's signals-first rule applied to compliance state.

## 3. The four nouns

Everything in the system is one of these, and each has one home.

| Noun | Where it lives | What it is |
|---|---|---|
| **Record** | `records/<type>/YYYY-MM-DD-slug.md` in the vault | One file per record. Plain-English summary plus extracted text; the original PDF in `library/` with a sha256 in `library/manifest.json`. |
| **Obligation** | `obligations/*.yaml` in the vault | A rule about records: which type, how often, relative to what, with what lead time. Jurisdiction packs (MA first, per #122). |
| **Announcement** | a record with `type: announcement` and `publish_at` | Rendered to the site, an Atom feed, and the board. Latency from merge to live is measured. |
| **Rule** | the rules repo | The Ask box's frozen instructions, persona, allowed subjects, refusal policy, manual incident overrides, the golden question set, the model pin, and the budget caps. |

Record frontmatter (the whole schema; everything else is prose):

```yaml
id: 2026-09-16-board-minutes          # path slug; stable forever
title: Board meeting minutes, 2026-09-16
type: minutes                         # minutes|notice|agenda|policy|bylaw|filing|report|announcement|faq
status: approved                      # draft|approved|superseded|retracted
visibility: public                    # only "public" is ever published; anything else fails CI in this repo
effective: 2026-09-16
approved: 2026-10-01
source: {kind: pdf, file: library/files/minutes/2026-09-16-board-minutes.pdf, sha256: "…"}
certainty: verified                   # verified|reported   (theoria's labels; mitchella reads them)
supersedes: 2026-06-18-board-minutes  # optional; builds the version chain for policies and bylaws
subjects: [budget, parking, annual-meeting]   # what the Ask box matches incidents and announcements against
tags: [board, 2026]
corrections:                          # append-only, dated, visible (essex-crossing's rule)
  - {date: 2026-10-02, note: "Treasurer's figure corrected from $12,400 to $12,040; source p.3."}
```

This is the lowest common denominator of theoria, essex-crossing-hoa, and the lupinus ops vault: relative Markdown links, minimal YAML, one index page, explicit sources, one fact in one place, dated corrections, append-only journals, a tracked `.obsidian/` folder the repo does not depend on, and never a credential in the vault.

## 4. Three repositories, three pipelines

Three repos rather than three folders, because the point is that they have **different reviewers, different required checks, and different blast radii**, and GitHub rulesets are per-repo. All three are created in the client's own GitHub org from templates ("Use this template", as monarda does). All three can be public; the vault must be, because it holds only public records and because branch protection is free only on public repos.

```
 ┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
 │  <org>-records  (vault)  │    │  <org>-ask-rules         │    │  <org>-site              │
 │  Obsidian-compatible     │    │  governance              │    │  presentation            │
 ├──────────────────────────┤    ├──────────────────────────┤    ├──────────────────────────┤
 │ intake/   (never built)  │    │ instructions.md (frozen) │    │ pages/, theme, voice     │
 │ records/<type>/*.md      │    │ policy.yaml  subjects,   │    │ overrides (pondview's    │
 │ library/  files+manifest │    │   refusals, disclaimer,  │    │   base + overlay)        │
 │ obligations/*.yaml       │    │   caps, model pin,       │    │ Ask widget config        │
 │ templates/record.md      │    │   enabled: true|false    │    │                          │
 │ index.md  .obsidian/     │    │ signals/incidents.toml   │    │ reads corpus.json by     │
 │ receipts/ (append-only)  │    │ evals/golden.jsonl       │    │   digest; never reads    │
 └───────────┬──────────────┘    └───────────┬──────────────┘    │   the vault directly     │
             │ CI on PR:                     │ CI on PR:         └───────────┬──────────────┘
             │  schema · links · privacy     │  eval run vs the              │ CI: build · a11y ·
             │  tripwires · obligations ·    │  CURRENT published            │ facts parity · deploy
             │  golden-eval diff (read-only) │  corpus; prompt diff          │ to the org's Pages
             ▼                               ▼                               ▼
   PUBLISH on merge:                RELEASE on merge:                 site + Atom feed +
   corpus-<digest>.json             rules-<version>                   "Is it posted?" board
   standing.json · feed.xml                                           (built from standing.json)
   receipt + provenance attestation
             │                               │
             └──────────────┬────────────────┘
                            ▼
              ┌──────────────────────────────┐
              │  Ask function (client AWS)   │   mitchella core: wiki loader, DECISION_SCHEMA,
              │  pins corpus digest + rules  │   citation gate, signals-first, turn log
              │  version; polls for new ones │   signals = standing.json + incidents.toml + announcements
              └──────────────┬───────────────┘
                             │ turn events, publish events, standing changes
                             ▼
              ┌──────────────────────────────┐
              │  org's Grafana Cloud free    │   drosera: pipeline dashboard JSON, left to right:
              │  tier (Loki push, HTTPS)     │   intake → reviewed → published → served → asked
              └──────────────────────────────┘   alerts → GitHub Issues (ADR-0007's runtime)
```

### 4.1 Corpus pipeline (the vault)

**In.** Three doors, all ending in a pull request:

- **GitHub Issue form, "Add a record".** Type, date, title, two-sentence summary, PDF attached. An Action turns the issue into a branch and PR with the file scaffolded, the PDF saved to `library/` with its sha256, and the issue linked. No git knowledge needed. This is the default door for the tech director and the one the dry-run times.
- **Obsidian.** Open the vault, duplicate `templates/record.md`, fill the frontmatter, commit with Obsidian Git or GitHub Desktop. Same PR.
- **Demand loop.** mitchella's promote job clusters the Ask box's unanswered questions weekly and opens intake Issues: "11 people asked about parking permits; no record covers it." The tech director answers by adding a record. The corpus grows where the questions are.

**Gate (CI on the PR).** One stdlib Python script, no dependencies, same as drosera's status page builder:

- frontmatter schema, including that `status: approved` records have `source` and `approved`;
- relative-link check (the shared `check_docs_links.py`);
- privacy tripwires generalized from pondview's C3/C5/C6: a configurable denylist (resident names, unit numbers, emails, phone patterns) that fails the build if matched anywhere in records or extracted text;
- `visibility: public` on every record, because this repo is public;
- no deletion of a published record (retract or supersede instead; "retire, don't orphan");
- obligations evaluated against the candidate tree, result posted as a PR comment;
- the golden question set from the rules repo run **read-only** against the candidate corpus, with a diff of any answer that changed. A corpus PR cannot change the rules, but it can see what its facts do to the answers.

**Out (on merge).** The publish workflow builds `corpus-<digest>.json` (mitchella's entry format, from the wiki loader), `standing.json`, `feed.xml`, writes an append-only receipt under `receipts/` (what changed, obligations state, Actions run URL, server-side timestamp), and attaches a GitHub artifact attestation (free on public repos) so anyone can verify the corpus came from that commit. Artifacts land on a `published` branch served by Pages, so every consumer reads by URL and digest.

**Blast radius.** Nothing in `intake/` or any non-approved record is ever built. One record is one file. The Ask function pins a digest and only advances on a green publish. Rollback is `git revert`, which publishes the previous tree under a new receipt. A broken schema blocks the PR; it cannot reach the site or the box.

### 4.2 Rules and governance pipeline

Everything that shapes *how the box answers*, and nothing that shapes *what is true*:

- `instructions.md` — the frozen system block (mitchella's `system[0]`), under its own CODEOWNERS (board secretary, counsel if they have one).
- `policy.yaml` — allowed subjects, refusal classes, the not-legal-advice disclaimer, daily cap, model pin, `enabled: true|false` (the kill switch: the box returns a maintenance line and nothing else).
- `signals/incidents.toml` — manual overrides in mitchella's existing format: "annual meeting postponed; suppress answers on `annual-meeting` until 2026-10-20 and show this notice."
- `evals/golden.jsonl` — questions with the expected outcome kind and required source ids. A PR here must pass the thresholds against the **currently published** corpus, and the run posts the prompt diff and the answer diff.

Versioned releases (`rules-v12`), pinned by the Ask function, rolled back by pinning the previous one. A rules change can never edit a record; a record change can never edit a rule.

### 4.3 Site content pipeline

The site repo holds presentation only: page templates, theme, the voice overlays pondview uses (base prose plus per-skin overrides, with the facts-parity check that every figure, date, and citation in the base appears in the variant), and the Ask widget's endpoint. It **builds from the published corpus artifact, never from the vault checkout**, so site changes cannot smuggle a fact and the site can be rebuilt from any past digest. Deploys to the org's GitHub Pages (monarda's default), optionally S3 (monarda's opt-in). Static, no client-side JavaScript except the Ask widget.

The **"Is it posted?" board** is a page on this site built from `standing.json` and the receipts: one row per obligation, green / amber / red, the satisfying record linked, the publish timestamp shown. It is drosera's status-page kit with the data source swapped from Mimir probes to the standing file. Its rule carries over: if the data is missing, the row says "no data", never a fake green.

## 5. The Ask box

**Engine: mitchella, unchanged in its core.** The pieces already exist and are tested: the `wiki` corpus loader (reads a Markdown tree in place, title from the H1, tags from frontmatter and parent folder, certainty from the evidence line), the whole-corpus-in-prompt render behind a single cache breakpoint (ADR-0002), the four-outcome structured schema with the code-level citation gate (ids that do not exist are dropped), signals checked before the corpus (ADR-0001), no tools and no write access (ADR-0005), the append-only turn log, and the promote job.

**What changes:**

- **Signal providers.** Drop the drosera status provider. Add a `StandingProvider` that reads `standing.json`: any obligation in breach becomes an incident whose subjects are the obligation's subjects. Add an `AnnouncementProvider` that surfaces active announcements matching the question's subjects. Keep the manual override provider, now fed from the rules repo. This is the single most valuable change: the box structurally cannot claim compliance the board denies.
- **Runtime.** A Python Lambda with a Function URL in the client's AWS account (solidago's `ask-lambda` module lineage, hardened): API key in an SSM SecureString rather than a plaintext env var; a durable daily cap in a DynamoDB free-tier table rather than per-container memory; prompt caching on; a Turnstile or equivalent bot check in front; model pinned to Sonnet, not Opus, for a public box. Lambda and DynamoDB are always-free at this volume; the Anthropic spend cap is the hard ceiling. Pondview's browser-side keyword prefilter stays available as the fallback once a corpus passes ADR-0002's soft ceiling.
- **Telemetry.** Turn-log lines go to the org's Grafana Cloud Loki over HTTPS push (the path betula already uses from the Firewalla), not to local disk. Question text truncated per pondview ADR-0003; no identity.
- **Citations.** The widget renders the sources the model actually cited and the gate verified, not the passages that were sent. Pondview has this backwards today.

**Cost shape.** Lambda, DynamoDB, Pages, Actions, Grafana Cloud: free tier. Model tokens: a corpus of a few hundred records sits well under the cache ceiling, and cache reads cost roughly a tenth of input price, so a question costs pennies and the daily cap bounds the month. The org holds its own Anthropic key and sees its own bill.

## 6. Visibility in drosera, left to right

Two panes, two audiences.

**Public board** (section 4.3): the compliance view, zero dependencies, on Pages.

**Operator pane** in the org's own Grafana Cloud free tier, provisioned the drosera way (dashboard JSON applied by Terraform, in the client's Grafana, from the client's repo). Every pipeline stage emits one structured event to Loki over HTTPS push with a `logs:write` token in Actions secrets. GitHub Actions has no path into Loki today; this adds one, as a reusable composite step, which is itself a drosera deliverable and the first non-estate drosera source (drosera#131).

One row, left to right, each cell a count and an age:

| Intake | Reviewed | Published | Served | Asked |
|---|---|---|---|---|
| open intake Issues and PRs, oldest age | PRs with green checks awaiting a human | latest digest, minutes since publish, obligations green/amber/red | digest the Ask function is serving (**alerts if ≠ published for > 30 min**) | last 24h: answered / incident / escalated / declined, p50 latency, cap remaining |

Below it: announcements (merge-to-live latency per announcement), the obligation timeline (each deadline as a vertical line, each satisfying record as a dot before or after it), and the demand loop (top unanswered subjects this week).

Alerts follow ADR-0007's preferred runtime: an obligation going amber opens a GitHub Issue and sends email; the Ask function serving a stale digest opens an Issue; the daily cap hitting 80 % opens an Issue. Grafana alert rules exist in the JSON for orgs that want them, but the Issue path works with nothing but GitHub.

## 7. Agnosticism and the first client

Core and clients, per the fleet principle. Adding a client must not touch another.

| Core (uvularia owns) | First client | Other clients, when asked |
|---|---|---|
| record schema, obligation schema, corpus bundle format, standing format, receipt format, the validator, the obligation evaluator | — | — |
| intake door | GitHub Issue form | Obsidian, drop folder, email-to-issue |
| editor | Obsidian | any Markdown editor; the repo never depends on Obsidian |
| Ask runtime | AWS Lambda Function URL | Cloudflare Worker, a container on the org's own box |
| site host | GitHub Pages | S3/CloudFront |
| operator pane | Grafana Cloud free tier via drosera | none (the public board stands alone) |
| obligation pack | Massachusetts (Open Meeting Law, charities filing, condo statute) | one directory per jurisdiction |

**Demonstration client: Stillwater Brook Watershed Alliance**, the fictional land trust from lupinus story 03, **renameable by construction.** Its identity (name, short name, domain, contact, accent, logo) lives in exactly one file, `demo/org.yaml`, consumed by the vault index, the site, the rules persona, and the obligation pack's organization fields. Seed records are generated from templates by `demo/seed.py`, which reads `org.yaml`; they are never hand-written with the name in them. CI fails on any occurrence of the organization's name outside `org.yaml` and the generated output. Renaming or rebranding the demo is one edit and one re-run. Seed the vault with two years of realistic public records: bylaws, monthly board minutes, meeting notices (some late, so the board shows amber honestly), a conflict-of-interest policy with one revision, an annual report, a stewardship permit, trail-status announcements, a dozen FAQs. Fictional by construction, so it carries no real community's name and can be forked by anyone as a starting point. It also gives mitchella its first live API call (the "M1" the stories keep asking for) and monarda-style timed dry-run its first receipt.

## 8. Boundaries, stated plainly

- **Public records only, in v1.** Members-only or internal records are out of scope. The vault is public, the `visibility` field exists so a mistake fails CI rather than ships, and a private working repo is the org's own affair. Private-vault support would need paid GitHub for branch protection; say so in ADOPTION.md rather than pretend.
- **Not legal advice.** Obligation packs encode posting mechanics, not legal interpretation; the disclaimer is in `policy.yaml`, and thresholds stay with the org's counsel (same stance as #122).
- **Timestamps are server-side.** "Posted at" is the publish workflow's time, recorded in the receipt and the attestation, never the author's commit time.
- **No multi-tenancy.** One org, one set of repos, one function, one key, one Grafana stack. Lentago operates nothing.
- **The corpus ceiling is a known cliff.** ADR-0002's path (keyword prefilter, then rerank) is the documented step when a vault outgrows the prompt; the bundle format carries an `archived` flag from day one so old minutes can drop out of the prompt without leaving the record.

## 9. Phasing, with the receipt each phase must produce

| Phase | Scope | Receipt | Tier |
|---|---|---|---|
| **0 · Vault + board** (2–3 weeks) | vault template, schema, validator, obligation evaluator, Issue-form intake, publish workflow with receipts and attestation, "Is it posted?" board on Pages, Stillwater seed data, ADOPTION.md, timed dry-run | the board live for Stillwater; a dry-run receipt with elapsed time | Kit |
| **1 · Ask box** (3–4 weeks) | rules repo + eval gate, mitchella providers for standing and announcements, Lambda module hardened, widget with verified citations, turn log to Loki | a live answer that cites a record; a live refusal during a manufactured breach | Platform |
| **2 · Operator pane** (2 weeks) | Actions → Loki composite step, pipeline dashboard JSON, alerts → Issues, stale-digest alert | the left-to-right dashboard in a fresh Grafana free-tier stack | Pattern → Kit |
| **3 · Consumers** | funder-report pipeline (#130) and Good-Standing reconciliation (#122) reading the same vault; multi-voice pages | one program number committed once, cited in three outputs | — |

Phase 0 has value without any AI and is where the "add to it, correct it, quickly, low blast radius" requirement is actually met; phases 1–3 add consumers to a vault that already works.

## 10. What is being reused, and from where

| From | Taken |
|---|---|
| **mitchella** | engine, contract, wiki loader, structured outcomes, citation gate, signals-first, turn log, promote job |
| **site-pondviewlane-com** | library manifest with sha256, base + overlay content with facts parity, privacy tripwires (generalized), Ask widget, question-truncation logging rule |
| **solidago** | `ask-lambda` Terraform module (hardened as above) |
| **monarda** | template delivery, intake questionnaire pattern, timed dry-run and receipt format, Pages-default/S3-opt-in |
| **drosera** | status-page builder pattern (stdlib, never fake green), dashboards-as-JSON Terraform, Loki HTTPS push |
| **lupinus / theoria / essex-crossing-hoa** | vault conventions, certainty labels, retire-don't-orphan, append-only corrections, sources index |
| **.github** | repo-template, rulesets, issue forms (#196 lineage), ADR-0007 delivery rule |

## 11. Decisions taken (2026-10-03)

1. Codename: *uvularia*.
2. Three repositories per client, not one repo with path-scoped reviewers.
3. Phase 0 first, with no AI in it, as the first deliverable and the first receipt.
4. Stillwater Brook Watershed Alliance as the demonstration client, seeded with generated fictional records, renameable from one file.
5. .github#128 retired into this product; .github#130 and .github#122 depend on the Phase 0 vault.
