# Adopting uvularia — the ladder

**What you're about to do:** put your organization's public records in a plain
Markdown vault in your own GitHub, with a public **"Is it posted?"** board on your
own GitHub Pages. That is one repository, and it is the whole first rung. Three
more rungs are there when you want them: a branded site, an Ask box that answers
from the records, and an operator's dashboard. You climb one rung at a time and
stop wherever you like.

**Why bother:** when you're done you own everything. Nothing is hosted by the
person who set it up for you, so nobody can take it down. Adding or correcting a
record becomes a two-minute pull request with a small blast radius, and you can
show, live and with a timestamp, that what had to be posted was posted on time.

**How long:** the first rung is one repository and one file to edit. The first
timed run of the *two*-repository version took about half an hour of working time
and under fifteen minutes to the first green row ([receipt](#receipt)); the
one-repository rung has **not yet been timed**. Your run is the one that counts;
[DRY-RUN.md](DRY-RUN.md) is the drill that produces the number.

**Status of this runbook:** rung 1 rewritten 2026-10-04 after
[ADR-0002](docs/adr/0002-adoption-ladder-one-repository-first.md); the two-repository
version was run once, 2026-10-03 — see [Receipt](#receipt).

## The ladder

A **repository** is a folder GitHub keeps the full history of. Each rung below
is one click of **Use this template**, or one account, and each rung is a
working stopping point.

| Rung | You get | You add | Guide |
| :-- | :-- | :-- | :-- |
| **1. The vault** | your records, a web form to add one, receipts with server-side timestamps, and a plain public board | one repository, `<org>-records` | this page |
| **2. A proper site** | the same board with your own name, colours and pages, and a place for the Ask widget | one repository, `<org>-site` | the [site template README](templates/site/README.md) |
| **3. The Ask box** | grounded answers from your records, with citations, that refuse what the records don't say | one repository, `<org>-ask-rules`, and an AWS account | the [rules template README](templates/ask-rules/README.md) and the [Ask function README](templates/ask-function/README.md) |
| **4. The operator pane** | one row, left to right: intake, review, publish, serve, ask; alerts that open Issues | a free Grafana Cloud account | the records template's **Watch the pipeline** section and drosera's [event contract](https://github.com/lentago/drosera/blob/main/docs/clients/uvularia.md) |

Why separate repositories at all, once you climb? Because GitHub's review rules
and required checks are per repository. Keeping records, rules and site apart
means a change to a record cannot alter a rule, a rule change cannot alter a
fact, and a site change cannot smuggle either. On rung 1 none of that matters
yet; there is one repository and it holds facts.

**Heads up:** the hard step is not a repository, it is rung 3's AWS account.
Everything on rungs 1 and 2 runs on GitHub Free. Rung 3 is the only one that
can incur a bill (a few dollars a month for the Ask box's model calls, with a
hard cap), and the only one that needs a second cloud login.

## What this is not

- **Not a place for private records.** Everything in the vault is published;
  the `visibility` field exists so a mistake fails a check rather than ships.
- **Not a CMS.** No admin panel, no database, no login. You add a record
  through a GitHub Issue form (or by editing Markdown) and a reviewer merges a
  pull request.
- **Not legal advice.** The obligation packs encode *posting mechanics* —
  which record type, how often, by when — not legal interpretation. Thresholds
  stay with your counsel. This is stated once, here.

---

# Rung 1 — the vault

**What you're about to do:** create one repository from a template, edit one
file, turn on GitHub Pages, file your first record through a web form, approve
it, and watch your public board go green.

**You'll need:** a GitHub account that can create repositories in your
organization (or your personal account). GitHub **Free** is enough. A web
browser is the whole tool requirement. [Obsidian](https://obsidian.md) is
optional and pleasant; the repository never depends on it.

**Time:** not yet timed for one repository. The two-repository version took
about 28 minutes of working time ([receipt](#receipt)).

**Cost:** **$0.** The vault, its checks, its publish workflow and its board run
on GitHub Free, GitHub Actions and GitHub Pages, all free for public
repositories.

> **If the records repository must be private.** Branch protection, the rule
> that forces a pull request and a reviewer before anything merges, is free only
> on **public** repositories. The vault is designed to be public: it holds only
> public records. A private vault needs a paid GitHub plan (Team or higher) for
> that gate, or you go without it. There is no other cost difference.

## What you get

One repository in **your** GitHub organization, `<org>-records`, made from
[`lentago/uvularia-records-template`](https://github.com/lentago/uvularia-records-template)
(a copy of [`templates/records/`](templates/records/) here). It holds:

- your public records, one Markdown file each, with where it came from;
- the **obligation rules** about what must be posted and when, next to the
  records that satisfy them;
- an **Add a record** web form that turns into a pull request for you;
- workflows that check every change and, on merge, publish a corpus, a
  standing file, an announcement feed, a stamped receipt with a server-side
  time, and the **public board** page, all to your own GitHub Pages address.

| What | Who owns it |
| :-- | :-- |
| The repository | You |
| The published records, corpus, feed and receipts | You |
| The live board | You |
| The GitHub account and org they run in | You |

## The steps

1. **Create the repository.** On the template, click **Use this template →
   Create a new repository**. Name it `<your-org>-records`. Make it **public**.
2. **Edit one file.** `.github/CODEOWNERS`: replace `@REPLACE-WITH-YOUR-REVIEWER`
   with the GitHub team or usernames who must approve a change. (Also give your
   organization a name in `index.md`, and glance at `obligations/` to keep the
   rules that apply to you. The one file that gates safety is CODEOWNERS.)
3. **Merge something, then turn on Pages.** The `published` branch only exists
   after your first merge to `main` runs the publish workflow. Merge the
   CODEOWNERS edit, then **Settings → Pages → Source: Deploy from a branch →
   `published`, folder `/ (root)`**.
4. **File your first record.** **Issues → New issue → Add a record.** Fill the
   form and attach the original document. The workflow scaffolds the record as
   a draft and either opens the pull request for you or comments a one-click
   link to open it (see **Heads up** below).
5. **Approve it.** On the pull request, set `status: approved` and the
   `approved` date, let the **validate** check go green, and merge. Approving
   is the step that makes the board go green.
6. **Turn on the review gate.** Once **validate** has run once, add it as a
   required check in branch protection and tick *Require review from Code
   Owners*. Until then anyone with write access can merge unreviewed.

The checkpointed version, with a box to tick and an elapsed-time blank at every
step, is [DRY-RUN.md](DRY-RUN.md).

## How you know it worked

- `https://<your-org>.github.io/<your-org>-records/` shows your board: one row
  per obligation, the record that satisfies it linked, and **Last published**
  with a UTC time taken from the publish run, not from anyone's laptop.
- The same address serves `standing.json`, `corpus-latest.json` and `feed.xml`.
- A pull request on the repository shows a green **validate** check.
- A new file under `receipts/` on the `published` branch carries your record's
  `published_at`.

An empty board says **no data**, in words. It never says green until a published
record earns it.

## Swap list

**Empty.** A swap list is the set of *our* values you must replace with *yours*.
The template ships with none: no Lentago hostname, account or brand is baked
into anything under `templates/`. The files you touch (`CODEOWNERS`,
`index.md`, `validate.toml`) carry labelled placeholders, not our defaults.

## Heads up — the traps we found

- **Allow Actions to open pull requests.** GitHub ships *Settings → Actions →
  General → Workflow permissions → Allow GitHub Actions to create and approve
  pull requests* **off**, and an org admin may have to set it at the org level.
  With it off the form still works: it scaffolds the record, pushes the branch
  `intake/<issue number>`, and comments a **one-click compare link** to open
  the pull request yourself. Turning it on just saves the click.
- **The `published` branch only exists after your first merge.** Merge first,
  then set Pages (step 3).
- **Nothing goes live on its own.** A record is a **draft** until a reviewer
  approves it on the pull request and merges.
- **The validate check appears in branch protection only after it has run
  once.** Open your first pull request, let it run, then come back (step 6).
- **A missing file is "no data", never green.** An empty board means "nothing
  published yet", not "all in order".
- **Your copy is yours, and that includes updates.** A template copy never
  receives our later fixes on its own. The vault carries a small script,
  `scripts/sync-core.sh`, that pulls the latest checks from this repository
  when *you* choose to run it, and the template's own history shows what
  changed. We will not reach into your repository; you pull.
- **The `demo/` vault is a lab fixture, not a starting point.** It is a
  generated demonstration with a fictional client's records. A real vault
  starts empty from the template.

---

# Rung 2 — a proper site

**Skip this if** the plain board on your vault's Pages address is enough. Many
organizations will stop here.

**What you get:** `<org>-site`, from
[`lentago/uvularia-site-template`](https://github.com/lentago/uvularia-site-template):
a small static site with your name, colours and pages, the same board styled,
and the slot for rung 3's Ask widget. It builds **only** from what your vault
has published; it never reads the vault repository itself.

**You add:** one repository and one file to edit, `site.config.ts`, pointing
`publishedBaseUrl` at your vault's Pages address and setting `orgName`,
`contact`, `accent` and `base`. Pages for this repository is set to **GitHub
Actions**, not a branch: the two Pages settings differ, and getting one wrong
is the most common stumble. The site needs Node 22+ in its workflows (not on
your machine) and redeploys on a 30-minute schedule; run **deploy-pages** from
the Actions tab to see a change at once. A `base` mismatch hides your CSS.

**Guide:** the [site template README](templates/site/README.md).

---

# Rung 3 — the Ask box

**Skip this if** you do not want a model answering questions from your records.
Rungs 1 and 2 have no AI in them and stand on their own.

**What you get:** a small function in **your** AWS account that answers a
question only from the published records, cites the record ids it used, and
refuses what the records don't say. Its rules (what it may talk about, what it
always refuses, the model it uses, a daily cap, a kill switch) live in a third
repository, `<org>-ask-rules`, from
[`lentago/uvularia-rules-template`](https://github.com/lentago/uvularia-rules-template),
so a rule change is reviewed like a record and can never alter a fact.

**You add:** that repository, the Ask function code copied into it as
`ask-function/` (the template README says how), an AWS account with a budget
alert, and one API key stored in AWS, never in GitHub. This is the only rung
that can cost money: a few dollars a month at a small organization's volume,
with a hard daily cap you set.

**Guides:** the [rules template README](templates/ask-rules/README.md) and the
[Ask function README](templates/ask-function/README.md).

---

# Rung 4 — the operator pane

**Skip this if** GitHub Issues and email are all the alerting you need. The
vault's **watch** workflow already opens an Issue when an obligation goes amber,
when the Ask box serves stale records, or when the daily cap is nearly spent,
with nothing but GitHub.

**What you get:** one dashboard in a free Grafana Cloud account that shows the
whole pipeline left to right (intake, reviewed, published, served, asked) and
three alert rules, fed by one short event each stage sends.

**You add:** a free Grafana Cloud account, its log-store URL and a write token
as a variable and a secret in your records and rules repositories, and the
dashboard JSON applied to your account. The records template README's **Watch
the pipeline** section walks through it; the event contract is drosera's
[`docs/clients/uvularia.md`](https://github.com/lentago/drosera/blob/main/docs/clients/uvularia.md).

---

## Receipt

The first timed run, of the earlier two-repository rung 1:
[2026-10-03, agent run](receipts/2026-10-03-agent-run.md) — **13 min 39 s to the
first green row**, about **28 min of working time** (55 min wall clock including
the operator's own network outage), all pull-request checks green, four
adoption-path defects found and filed. The one-repository rung has not yet been
timed; when it is, its receipt is added to [`receipts/`](receipts/) and the
newest run is what the tier row in lupinus cites.

## Dependencies and exits

Three GitHub services on rungs 1 and 2, and how to leave each. Everything you
own is plain files or open formats; there is no proprietary store to escape.

| Dependency | What it does | How to leave |
| :-- | :-- | :-- |
| **GitHub** (repositories) | holds the vault and, if you climbed, the site and rules | The vault is plain Markdown, YAML and the original files; `git clone` and it is yours anywhere. Move the repository to any git host. |
| **GitHub Actions** | runs the checks, the publish and the deploy | Every check is a short, dependency-free Python or Node script you can run by hand (`python3 core/validate.py .`, `npm run build`). Delete the workflows and you still have the records and can build the artifacts locally. |
| **GitHub Pages** | serves the board and the published artifacts | The artifacts are **JSON**, **Atom** and one **static HTML** page. Host them on any static host, or none. Turn Pages off and nothing is lost but the URL. |

Rung 3 adds AWS (delete the stack; the rules repository is plain files) and
rung 4 adds Grafana Cloud (delete the account; the events were a copy, the
records are the source).

To tear a repository down: **Settings → Pages → Source: None** takes it offline
immediately; **Settings → Danger Zone** archives or deletes it. Your records
survive in any clone you kept.

## Getting help

Open an issue on [this repository](https://github.com/lentago/uvularia).
Include the rung you were on, the step, the exact action, the full output, and
your platform. If a step was wrong, unclear, or missing a prerequisite, that is
the most valuable issue you can file.

---

> Part of [uvularia](https://github.com/lentago/uvularia) by Lentago Labs.
> Firing us is a fork: these templates run in your org, on your account, for free.
