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
one-repository rung was timed once, on 2026-10-12: **6 min 09 s** to the first green row ([receipt](receipts/2026-10-12-agent-run-rung1.md)). Your run is the one that counts;
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
| **3. The Ask box** | a source-linked assistant: answers that link the records they cite, for readers to check, and refuse what the records don't say | one repository, `<org>-ask-rules`, and an AWS account | the [rules template README](templates/ask-rules/README.md) and the [Ask function README](templates/ask-function/README.md) |
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

**Time:** the one timed run to the first green row for one repository, on
2026-10-12, took **6 min 09 s** ([receipt](receipts/2026-10-12-agent-run-rung1.md)).
If you are coming from the earlier two-repository version, that one took about
28 minutes of working time ([receipt](#receipt)). Your run is the one that counts.

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
  receives our later fixes on its own. Your vault carries a workflow that
  offers them to you once a week as a pull request, opened with a token *you*
  make, and nothing changes until you merge it. We never reach into your
  repository. Setting it up takes about three minutes:
  [Getting later template changes](#getting-later-template-changes).
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

**What you get:** a small function in **your** AWS account that answers
questions about the published records, links every answer to the records it
cites, and refuses what the records don't say. Its rules (what it may talk
about, what it always refuses, the model it uses, a daily cap, a kill switch)
live in a third repository, `<org>-ask-rules`, from
[`lentago/uvularia-rules-template`](https://github.com/lentago/uvularia-rules-template),
so a rule change is reviewed like a record and can never alter a fact.

It is a source-linked assistant, not an authority. The links let a reader check
an answer, the widget asks them to, and your contact sits beside the sources. An
answer with no real record behind it goes back to the reader as one that needs a
person. Questions are logged, cut short, in your own accounts, and are sent to
the model provider; the
[Ask function README](templates/ask-function/README.md#questions-and-privacy)
says how to shorten or turn off that logging.

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

# Getting later template changes

**What you're about to do:** let each of your repositories receive our later
fixes (a sharper check, a clearer guide, a repaired workflow) as a pull request
in your own repository, which you review and merge like any other.

**Why bother:** a repository made with **Use this template** is a copy. Without
this, it never hears about a fix. With it, a pull request shows up when there
is something new, your checks run on it, and the diff shows every line.

**How long:** about three minutes per repository, once.

**Skip this if** you would rather copy changes by hand from the template's
history. Nothing breaks if you never set this up; the workflow just opens an
issue saying an update is waiting.

## The steps

Do this in each repository you made from a template: the vault, and the site
and rules repositories if you climbed that far.

1. **Make a token.** A token is a password for one program, with only the
   powers you give it. On GitHub, open your picture → **Settings → Developer
   settings → Personal access tokens → Fine-grained tokens → Generate new
   token**. Set **Resource owner** to your organization, **Repository access**
   to *Only select repositories* and pick this one repository, and under
   **Repository permissions** set **Contents**, **Pull requests** and
   **Workflows** to *Read and write*. Pick an expiry date and put it in your
   calendar.
2. **Give it to the repository.** In the repository, **Settings → Secrets and
   variables → Actions → New repository secret**. Name it
   `TEMPLATE_UPDATE_TOKEN` and paste the token. GitHub never shows it again,
   and the workflow uses it only to push the update branch and open the pull
   request.
3. **Run it once.** **Actions → template-update → Run workflow**. After that it
   runs every Monday on its own.

> **Heads up:** your organization may need to allow fine-grained tokens, or
> approve this one, before it works. An organization owner does that under the
> organization's **Settings → Personal access tokens**. If your token is still
> pending, the run fails with a refused push.

## How you know it worked

The run ends green, and either it says the repository is already up to date or
a pull request titled **Template update: …** is open with your checks running on
it. Its description lists every file it changed and why.

## What the pull request changes, and what it never touches

For each file it compares three versions: the template at your last update, the
template now, and yours.

| If… | then |
| :-- | :-- |
| you never changed the file | it becomes the template's new version |
| the template didn't change it | yours stays exactly as it is |
| you both changed it, on different lines | the two are merged and both changes are kept |
| you both changed the same lines | both versions are left in the file between `<<<<<<<` and `>>>>>>>` markers, the pull request opens as a draft, and its description names the files; pick what you want, delete the markers, push |
| the template removed it | it is removed, unless you had changed it; then it stays and is listed |

Some paths are never touched at all: your records, receipts and library, your
`index.md`, settings and reviewers in the vault; your `policy.yaml`,
`instructions.md`, incidents and golden questions in the rules repository; your
`site.config.ts` in the site. The list is `keep` in
`.github/template-update.toml`. That file is yours, and an update never changes
it, so add a path when you've made a template file your own.

> **Heads up:** while an update pull request is open, no new one opens. Closing
> one without merging means "not this one": that update is not offered again,
> and the next change to the template opens a fresh pull request. Delete its
> `template-update/…` branch if you change your mind.

- **If you pin `core/`** with `scripts/sync-core.sh` (see the vault README), add
  `"core/"` to `keep`, or the update will bring the template's `core/` instead.
- **The rules repository's `ask-function/`** is not part of any template, so an
  update never touches it. Copy it again from this repository when you want a
  newer one, as the [Ask function README](templates/ask-function/README.md)
  says.
- **Made your repository before November 2026?** It doesn't have the workflow
  yet. Copy three files from your template into it:
  `.github/workflows/template-update.yml`, `scripts/template-update.py` and
  `.github/template-update.toml`. Commit them, then follow the steps above.
  The first run works out which template version you started from on its own.

Why it works this way is recorded in
[ADR-0003](docs/adr/0003-template-updates-reach-clients-through-an-update-door.md).

---

## Receipt

The first timed run, of the earlier two-repository rung 1:
[2026-10-03, agent run](receipts/2026-10-03-agent-run.md) — **13 min 39 s to the
first green row**, about **28 min of working time** (55 min wall clock including
the operator's own network outage), all pull-request checks green, four
adoption-path defects found and filed. The one-repository rung was timed on
[2026-10-12, agent run](receipts/2026-10-12-agent-run-rung1.md): **6 min 09 s to the
first green row**, with the first record's validate check red on a path
convention the scaffold hint does not state (#98), fixed in a second pull request.
The newest run is what the tier row in lupinus cites.

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
