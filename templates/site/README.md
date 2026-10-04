# Your public site

This is the uvularia **site** template — the `<org>-site` repository. It is a
small, static website that shows your organization's published records, your
announcements, and a live **"Is it posted?"** board, and it deploys itself to
GitHub Pages.

It builds **only** from what your records vault has published — a corpus file, a
standing file, a feed, and a receipt served on the vault's `published` branch. It
never reads the vault's working files, so the site can never show a fact the vault
has not published. There is no database and no server. The only JavaScript in your
readers' browsers is the optional Ask box (section 4), and the site works without it.

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

## 4. Turn on the Ask box (optional)

**What you are about to do:** put a question box on your home page that answers
from your published records and links the records it used.

**Why bother:** people ask the same questions over and over. The box answers them
from what you have published and points to the record behind each answer.

**How long:** five minutes, once your Ask function is deployed (the
`ask-function` template, deployed from your rules repo).

1. Copy the Function URL your Ask deploy printed. It ends in
   `.lambda-url.<region>.on.aws/`.
2. In [`site.config.ts`](site.config.ts), set `askUrl` to that URL.
3. Set `askDisclaimer` to the `disclaimer` text in your rules repo's `policy.yaml`,
   so the box says what its rules say. The site never reads the rules repo itself.
4. Make sure the function's `allowed_origin` is this site's origin
   (`https://<org>.github.io`). It refuses questions from any other page.
5. Commit to `main`.

**How you know it worked:** the home page shows **Ask the records**. Ask something
your records cover. The reply is labelled in words (**Answered**, **Incident**,
**Escalated**, or **Declined**) and lists only the records the function cited, each
linked to its page.

What a reader sees in other cases:

- If the box is switched off in `policy.yaml`, or the function is not set up or
  cannot be reached, they see "The Ask box is off right now" and a link to the
  records index.
- If the day's question limit is reached, they see a line asking them to try
  again tomorrow.
- If there is an active incident, the notice appears first, above the answer.
- If JavaScript is off, there is no box. They get a link to the records index,
  and every other page works the same.

The box sends only the question: no cookies and no referrer. It logs nothing.
The conversation is kept in the browser tab's session storage and is gone when
the tab closes. Leave `askUrl` empty and the site has no Ask box at all.

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

Everything a check runs, you can run. You need **Node 22 or newer**.

```
npm install        # once
npm run dev        # preview locally at http://localhost:4321
npm run build      # build the static site into dist/
npm run check      # type-check (astro check)
npm test           # schema, board, and Ask box tests (used by build-check on every PR)
```

To preview against your real vault, `npm run dev` uses your `site.config.ts`. To
build against a local copy of some artifacts instead, set `UVULARIA_PUBLISHED_BASE`
to a directory (or a different URL) and it overrides the configured source.

The [`build-check`](.github/workflows/build-check.yml) workflow runs `astro check`,
the schema validation, real builds of the board and the home page (with and without
the Ask box), and the Ask box's rendering tests on every pull request, so a broken
change cannot reach `main`.

---

> Part of [uvularia](https://github.com/lentago/uvularia) by Lentago Labs.
> Firing us is a fork: this template runs in your org, on your account, for free.
