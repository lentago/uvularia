# Dry-run runbook — templates to a green board

**What you're about to do:** starting from nothing but a GitHub account and one
document, stand up a records vault and its public board **in a fresh organization**
— one repository created from the template — and carry one record from the
**Add a record** form all the way to a **green** row on the live board, with
every check along the way turning green. That is rung 1 of
[ADOPTION.md](ADOPTION.md). An optional second drill below adds the branded site
(rung 2) and times it separately.

**Why bother:** running this once before a real engagement surfaces the slow
steps — the first publish, enabling Pages on a branch that only just appeared,
the approval gate — while nothing is at stake. Find the stumble here, not in
front of the organization you are helping. The number you record at the bottom is
the first honest answer to "how long does this take?"

**Time:** however long the drill takes you, start to finish — that *is* the
receipt. Fill in the table at the bottom when you're done, and commit the same
values under [`receipts/`](receipts/README.md).

## Before you start the clock

- [ ] You have a GitHub account with permission to create repositories in the
      target org (GitHub Free is enough).
- [ ] The records repo will be **public** (branch protection is free only on
      public repos — see [ADOPTION.md](ADOPTION.md)).
- [ ] You have **one document** to file as the first record (a PDF), and you know
      its type, effective date, a title, a two-sentence summary, and its subjects.
- [ ] You have a browser. (Obsidian is optional and not used in this drill.)
- [ ] You know which obligation in the pack that first record is meant to satisfy,
      so you can watch the right row go green.

## The drill

Start the clock. Record the elapsed time at each checkpoint.

| # | Step | Check it's green | Elapsed | ✅ |
|---|---|---|---|---|
| 1 | **Create the vault** — **Use this template** on [`lentago/uvularia-records-template`](https://github.com/lentago/uvularia-records-template) → *Create a new repository*, named `<org>-records`, visibility **Public**. | Repo exists under the target org and is public. | | |
| 2 | **Name your org** — edit `index.md` to name the organization. | File saved; no placeholder org name left. | | |
| 3 | **Set your reviewers** — in `.github/CODEOWNERS`, replace every `@REPLACE-WITH-YOUR-REVIEWER` with your team or usernames. | No `REPLACE` string remains in the file. | | |
| 4 | **Keep the obligations that apply** — in `obligations/`, keep the rules that apply to you and delete the rest (the template ships one example). | `obligations/` holds only rules you mean to show. | | |
| 5 | **Merge the first change** — commit steps 2–4 to `main` (directly is fine; no protection yet). | The **publish** workflow runs green; a `published` branch now exists. | | |
| 6 | **Turn on the vault's Pages** — Settings → Pages → Source = branch **`published`**, folder **`/ (root)`**. | `https://<org>.github.io/<org>-records/` shows the board page (every row **no data** or green so far), and `…/standing.json`, `…/feed.xml`, `…/corpus-latest.json` resolve. | | |
| 7 | **Protect `main`** — Settings → Branches: require a pull request and "Require review from Code Owners". | Rule saved. (Add the **validate** required check after step 9 — see Notes.) | | |
| 8 | **File the first record** — Issues → New issue → **Add a record**; pick the type, date, title, two-sentence summary, and subjects, and attach the PDF. | Within a minute the issue gets a comment linking a pull request *Intake for #N*. | | |
| 9 | **Check the record's PR** — open the linked pull request. | The **validate** check is green; the record is scaffolded as `status: draft`. | | |
| 10 | **Approve and merge** — on the PR, set `status: approved` and the `approved` date, then merge. | The **publish** workflow runs; a new receipt appears under `receipts/` and `standing.json` updates. | | |
| 11 | **Open the board** — visit `https://<org>.github.io/<org>-records/` (reload; Pages can take a minute after the publish). | The obligation your record satisfies reads **green**, in words, with the record linked and **Last published** showing the server-side time. | | |

Stop the clock. That is the rung-1 receipt.

## Optional second drill — rung 2, the branded site

**Skip this if** the plain board is enough for the organization. Start a second
clock; this time is recorded separately so the rung-1 number stays honest.

| # | Step | Check it's green | Elapsed | ✅ |
|---|---|---|---|---|
| A | **Create the site** — **Use this template** on [`lentago/uvularia-site-template`](https://github.com/lentago/uvularia-site-template) → named `<org>-site`. | Repo exists under the target org. | | |
| B | **Turn on the site's Pages** — Settings → Pages → Source = **GitHub Actions**. | Setting saved. | | |
| C | **Point the site at the vault** — edit `site.config.ts`: set `publishedBaseUrl` to the vault's published URL, plus `orgName`, `contact`, `accent`, and `base` = `/<org>-site`. Commit to `main`. | No placeholders left; `deploy-pages` runs on the push. | | |
| D | **Watch the deploy** — Actions tab, the **deploy-pages** workflow. | Workflow is green; it reports the live URL. | | |
| E | **Open the styled board** — visit `/board/` on the live site. | The same obligation reads **green** here too, with the record linked and its publish time. | | |

Stop the second clock.

## Receipt

| Field | Value |
|---|---|
| Date of drill | |
| Operator | |
| Target org | |
| **Total elapsed time, rung 1** | |
| Total elapsed time, rung 2 (if run) | |
| All checks green? (Y/N) | |
| Slowest step (bottleneck) | |
| Notes / follow-ups | |

## Notes

> **Heads up.** The **validate** required status check can only be added to the
> branch-protection rule *after it has run at least once*. It is triggered by
> pull requests, so it first runs on the intake PR in step 8–9. Finish step 10,
> then return to Settings → Branches and add **validate** to the required checks.

> **Heads up.** The `published` branch does not exist until step 5's merge runs
> the publish workflow. You cannot select it in Pages (step 6) before then — merge
> first.

> **Heads up (rung 2).** The site's board redeploys on a 30-minute schedule. If
> step E's row is not green yet, either wait up to half an hour or run
> **deploy-pages** by hand from the site's Actions tab. The vault's own board
> (step 11) has no such delay beyond Pages publishing the branch.

> **Heads up (rung 2).** A `base` mismatch in step C is the most common cause of
> "why is my CSS missing" — a project Pages site needs `base: "/<org>-site"`.

Re-running the drill after any template change keeps the recorded time honest.

## How you know it worked

Every row in the rung-1 drill is checked, the vault's published URLs resolve, your
first record is approved and in the corpus with a stamped receipt, and the vault's
own board shows its obligation **green** — in words, with the record linked and the
server-side publish time. If you ran the second drill, the styled board says the
same thing. That is what you're signing off on when you fill in the
[Receipt](#receipt) and commit it under [`receipts/`](receipts/README.md).
