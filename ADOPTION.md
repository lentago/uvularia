# Adopting uvularia — Phase 0: the vault and the board

**What you're about to do:** stand up your organization's public records as a
plain Markdown vault in your own GitHub, and a public **"Is it posted?"** board
on your own GitHub Pages. You create two repositories from templates, edit one
file in each, file your first record through a web form, approve it, and watch
the board go green.

**Why bother:** when you're done you own everything — both repositories, the
published records, the board. Nothing is hosted by the person who set it up for
you, so nobody can take it down. Adding or correcting a record becomes a
two-minute pull request with a small blast radius, and you can show, live and
with a timestamp, that what had to be posted was posted on time.

**How long:** not yet timed — no operator has recorded a receipt yet. Treat any
guess as a guess until the table in [Receipt](#receipt) says otherwise. See
[DRY-RUN.md](DRY-RUN.md) for the step-by-step drill that produces that number.

**Status of this runbook:** never run — see [Receipt](#receipt).

## What you get

Two repositories in **your** GitHub organization, created from the templates in
this product:

- **`<org>-records`** — the vault. Your public records as one Markdown file each,
  with provenance; the obligation rules about what must be posted and when; and
  the workflows that validate every change and, on merge, publish a corpus, a
  standing file, an announcement feed, and a stamped receipt with a server-side
  timestamp.
- **`<org>-site`** — the public site and the **"Is it posted?"** board. A small
  static site that builds **only** from what the vault has published, and deploys
  itself to GitHub Pages.

A change to a record cannot alter a rule; a site change cannot smuggle a fact.
That separation is the point of two repositories rather than two folders.

| What | Who owns it |
|---|---|
| Both GitHub repositories | You |
| The published records, corpus, feed, and receipts | You |
| The live board and the site | You |
| The GitHub account and org they run in | You |

The Ask box, the operator dashboard, and the funder-report pipeline are later
phases. Phase 0 has no AI in it and stands entirely on its own.

## What this is not

- **Not a place for private records.** Everything in the vault is published;
  the `visibility` field exists so a mistake fails a check rather than ships.
  Members-only or internal records are out of scope in this phase.
- **Not a CMS.** There is no admin panel, no database, and no login. You add a
  record through a GitHub Issue form (or by editing Markdown) and a reviewer
  merges a pull request.
- **Not legal advice.** The obligation packs encode *posting mechanics* — which
  record type, how often, by when — not legal interpretation. Thresholds stay
  with your counsel. This is stated once, here.

## Prerequisites

**Accounts:**
- A GitHub account with permission to create repositories in your target
  organization (or personal account). GitHub **Free** is enough.

**Tools:**
- A web browser. That is the whole requirement for the default path.
- [Obsidian](https://obsidian.md) is **optional** — it makes editing the vault
  pleasant, but the repository never depends on it, and a plain text editor or
  the GitHub web editor works just as well.
- To run the checks on your own machine (optional), Python 3.12 for the vault
  and Node 22+ for the site. You do not need either to adopt; the checks run in
  GitHub Actions.

**Access you must already have:** permission to enable GitHub Pages, GitHub
Actions, and branch protection in the two repositories you create.

**Cost:** **$0.** The vault, the publish workflow, the site, and the board run
entirely on GitHub Free, GitHub Actions, and GitHub Pages — all free for public
repositories. The model-backed Ask box that would incur a bill is a later phase
and not part of this.

> **What changes if the records repo must be private.** Branch protection — the
> rule that forces a pull request and a reviewer before anything merges — is free
> only on **public** repositories. The vault is designed to be public: it holds
> only public records. If you must keep the records repository private, you need
> a paid GitHub plan (Team or higher) for branch protection, or you forgo the
> review gate. There is no other cost difference.

## The two repositories, and the one file you edit in each

You click **Use this template** twice, in this order.

1. **`<org>-records`** (the vault), made from `templates/records/`. Create it
   **public**. The file you edit is **`.github/CODEOWNERS`** — replace the
   `@REPLACE-WITH-YOUR-REVIEWER` placeholder with the GitHub team or usernames in
   your org who must approve a change. (You also give your org a name in
   `index.md`, keep the obligation rules in `obligations/` that apply to you, and
   glance at `validate.toml` — but the one file that gates safety is CODEOWNERS.)
2. **`<org>-site`** (the site and board), made from `templates/site/`. The file
   you edit is **`site.config.ts`** — point `publishedBaseUrl` at your vault's
   published artifacts and set `orgName`, `contact`, `accent`, and `base`.

Then, in order: turn on **Pages** for the vault's `published` branch and for the
site; file your first record through the **Add a record** Issue form; approve it
on the pull request; and watch the board row go green. The full sequence, with a
check and an elapsed-time blank at every step, is [DRY-RUN.md](DRY-RUN.md).

## Swap list

**Empty for Phase 0.** A swap list is the set of *our* opinionated values you
must replace with *yours*. The templates ship with none: by design, no Lentago
hostname, account, or brand value is baked into anything under `templates/`. The
files you edit — `CODEOWNERS`, `validate.toml`, `site.config.ts`, `index.md` —
contain labeled **placeholders**, not Lentago defaults, and filling them in is
part of the drill above, not a swap-out. There is nothing of ours to find and
remove.

## Verify it works

- The vault's `published` branch exists and serves `corpus-latest.json`,
  `standing.json`, and `feed.xml` at your Pages URL.
- A pull request on the vault shows a green **validate** check.
- Your first record is approved, merged, and appears in the corpus; a new receipt
  under `receipts/` carries its server-side `published_at`.
- The site is live over HTTPS, and `/board/` shows the obligation your record
  satisfies as **green**, in words, with the record linked and its publish time.

## Receipt

Nobody has run this end to end yet. When you do, fill this in — and commit the
same values as a dated receipt under [`receipts/`](receipts/README.md), which is
what the tier picker in [lupinus](https://github.com/lentago/lupinus) cites.

| Field | Value |
|---|---|
| Date | |
| Operator | |
| Target org | |
| **Total elapsed** | |
| All checks green? (Y/N) | |
| Slowest step | |
| Notes | |

## Dependencies and exits

Three GitHub services, and how to leave each. Everything you own is plain files
or open formats — there is no proprietary store to escape.

| Dependency | What it does | How to leave |
|---|---|---|
| **GitHub** (repos) | holds the vault and the site | The vault is plain Markdown, YAML, and the original files; `git clone` and it is yours anywhere. Mirror or move the repository to any git host. |
| **GitHub Actions** | runs the checks and the publish/deploy | Every check is a short, dependency-free Python or Node script in the repo you can run by hand (`python3 core/validate.py .`, `npm run build`). Delete the workflows and you still have the records and can build the artifacts locally. |
| **GitHub Pages** | serves the published artifacts and the site | The published artifacts are **JSON** (`corpus-*.json`, `standing.json`) and **Atom** (`feed.xml`); the site is **static HTML** in `dist/`. Host them on any static host, or none. Turn Pages off in Settings and nothing is lost but the URL. |

To tear the whole thing down: in each repo, **Settings → Pages → Source: None**
takes it offline immediately; **Settings → Danger Zone** archives (keeps history
readable) or deletes the repository. Your records survive in any clone you kept.

## Heads up — the traps we found

Reading the two templates surfaced these. Each has a plainer sibling in
[DRY-RUN.md](DRY-RUN.md)'s checks.

- **Make the records repo public.** Branch protection — the review gate — is free
  only on public repos (see the cost note above). A private vault means a paid
  plan or no gate.
- **Replace the CODEOWNERS placeholder, then turn the rule on.** Until you
  replace `@REPLACE-WITH-YOUR-REVIEWER` *and* enable "Require review from Code
  Owners" in branch protection, anyone with write access can merge a record
  unreviewed. The placeholder alone does nothing.
- **The two Pages settings are different.** The **vault's** Pages source is the
  **`published` branch**, folder `/ (root)`. The **site's** Pages source is
  **GitHub Actions**. Setting either the wrong way is the most common stumble.
- **The `published` branch only exists after your first merge.** You cannot point
  the vault's Pages at `published` until a merge to `main` has run the publish
  workflow and created that branch. Merge first, then set Pages.
- **Nothing goes live on its own.** Both intake doors create a record as a
  **draft**. It becomes public only when a reviewer sets `status: approved` and
  the `approved` date on the pull request and merges. Approving is the step that
  makes the board go green.
- **The validate check appears in branch protection only after it has run once.**
  The **validate** check is triggered by pull requests; GitHub won't let you add
  it as a required check until it has run at least once. Open your first intake
  PR, let validate run, then come back and add it to the rule.
- **A missing file is "no data", never green.** An empty or absent
  `standing.json` renders every board row as "no data". The board never claims
  compliance it cannot show, so an empty board means "nothing published yet", not
  "all in order".
- **The site needs Node 22+ and lags up to 30 minutes.** The site build requires
  Node 22 or newer (the workflows pin it). The board redeploys on a 30-minute
  schedule, so after you approve a record you may wait up to half an hour — or
  run **deploy-pages** by hand from the Actions tab to see it at once.
- **A `base` mismatch hides your CSS.** A project Pages site at
  `you.github.io/<org>-site/` needs `base: "/<org>-site"` in `site.config.ts`; a
  user/org site at the domain root needs `/`. The wrong value is the usual cause
  of an unstyled page.
- **The `demo/` vault is a lab fixture, not a starting point.** It is a generated
  demonstration with a fictional client's records. A real vault starts empty from
  the template; never copy the demo seed.

## Getting help

Open an issue on [this repository](https://github.com/lentago/uvularia).
Include the step you were on, the exact action, the full output, and your
platform. If a step was wrong, unclear, or missing a prerequisite, that is the
most valuable issue you can file — it is what turns a never-run runbook into a
timed one.

---

> Part of [uvularia](https://github.com/lentago/uvularia) by Lentago Labs.
> Firing us is a fork: these templates run in your org, on your account, for free.
