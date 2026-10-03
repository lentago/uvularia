# Your public site

This is the uvularia **site** template — the `<org>-site` repository. It is a
small, static website that shows your organization's published records, your
announcements, and a live **"Is it posted?"** board, and it deploys itself to
GitHub Pages.

It builds **only** from what your records vault has published — a corpus file, a
standing file, a feed, and a receipt served on the vault's `published` branch. It
never reads the vault's working files, so the site can never show a fact the vault
has not published. There is no database, no server, and (in this first version) no
JavaScript running in your readers' browsers.

You edit exactly one file: [`site.config.ts`](site.config.ts).

---

## 1. Use this template

**What you are about to do:** make your own copy of this site in your GitHub
organization and turn on GitHub Pages.

**Why bother:** this is the public face of your records. Setting it up once means
every future publish from your vault appears here on its own — you never touch this
repository again.

**How long:** about ten minutes.

1. Click **Use this template → Create a new repository**. Name it `<your-org>-site`.
2. In **Settings → Pages**, set the source to **GitHub Actions**.
3. That is all the repository setup. The next section points it at your vault.

**How you know it worked:** the repository exists and Pages is set to build from
GitHub Actions. Nothing is deployed yet — that happens once you point it at your
vault and merge.

---

## 2. Point it at your vault

**What you are about to do:** tell the site where your published records live, and
set your name, contact, and colour.

**Why bother:** this one file is the only link between your two repositories, and
the only place your identity lives. There is nothing else to hunt down.

**How long:** two minutes.

1. Open [`site.config.ts`](site.config.ts) and set:
   - `publishedBaseUrl` — your records repo's published artifacts. Use either its
     Pages URL (`https://<org>.github.io/<org>-records/`) or the raw branch URL
     (`https://raw.githubusercontent.com/<org>/<org>-records/published/`).
   - `orgName`, `contact`, and `accent` (a hex colour).
   - `site` (`https://<org>.github.io`) and `base` (`/<org>-site`) so links resolve
     under your Pages path.
2. Commit the change to `main`.

**How you know it worked:** the **deploy-pages** workflow runs on that push. When
it finishes, your site is live at the URL it reports, and the footer shows the time
it last fetched your vault's data.

---

## 3. See your first green row

**What you are about to do:** watch the board reflect your vault.

**Why bother:** the board is the point — a reader (or a funder, or a member) can
see at a glance whether each posting obligation is met, with the record that
satisfies it and the server-side time it went public.

**How long:** up to half an hour, hands-off.

1. In your **vault**, publish a record that satisfies an obligation (merge a pull
   request; the vault's publish workflow writes a new `standing.json`).
2. The site redeploys **on a 30-minute schedule**, so within half an hour the board
   picks up the new standing without any commit here. You can also run the
   **deploy-pages** workflow by hand from the **Actions** tab to see it immediately.

**How you know it worked:** open `/board/` on your site. The obligation's row reads
**green**, in words, with the satisfying record linked and its publish time shown.

> **Heads up.** The site shows only what your vault has published. An **empty board
> means "nothing published yet"** — it does **not** mean everything is in order. A
> missing standing file renders every row as **"no data"**, never a green. That is
> deliberate: the board never claims compliance it cannot show.

---

## What builds, and from where

On every push to `main` and every 30 minutes, [`deploy-pages.yml`](.github/workflows/deploy-pages.yml)
runs [`scripts/fetch-published.mjs`](scripts/fetch-published.mjs), which pulls these
from your `publishedBaseUrl`:

| Artifact | Becomes |
|---|---|
| `corpus-latest.json` | the records index and one page per record |
| `standing.json` | the **"Is it posted?"** board |
| `feed.xml` | the announcements page and `/feed.xml` |
| the current receipt | the "how this was published" note on each record page |

The corpus and standing file are checked against the
[vendored schemas](schema/README.md) first; an invalid artifact **fails the build**
rather than ship a broken site.

---

## Run it yourself

Everything a check runs, you can run. You need **Node 20 or newer**.

```
npm install        # once
npm run dev        # preview locally at http://localhost:4321
npm run build      # build the static site into dist/
npm run check      # type-check (astro check)
npm test           # schema + board tests (used by build-check on every PR)
```

To preview against your real vault, `npm run dev` uses your `site.config.ts`. To
build against a local copy of some artifacts instead, set `UVULARIA_PUBLISHED_BASE`
to a directory (or a different URL) and it overrides the configured source.

The [`build-check`](.github/workflows/build-check.yml) workflow runs `astro check`,
the schema validation, and two real builds of the board on every pull request, so a
broken change cannot reach `main`.

---

> Part of [uvularia](https://github.com/lentago/uvularia) by Lentago Labs.
> Firing us is a fork: this template runs in your org, on your account, for free.
