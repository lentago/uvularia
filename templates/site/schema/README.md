# Vendored schemas

These two files are **verbatim copies** of the canonical schemas in
[lentago/uvularia](https://github.com/lentago/uvularia)'s `core/schema/`:

| File | Validates |
|---|---|
| `bundle.schema.json` | `corpus-latest.json` — the published records |
| `standing.schema.json` | `standing.json` — the board rows |

The site's build step ([`../scripts/fetch-published.mjs`](../scripts/fetch-published.mjs))
validates the corpus and the standing file against these before it renders a page,
and fails the build on an invalid artifact rather than ship a partial site.

**Why a copy, and why validate in JavaScript.** This template is a single-toolchain
Node/Astro repo — you install Node and run `npm run build`, nothing else. Rather
than carry the core's Python validator and a Python runtime, the build re-expresses
*only the subset of JSON Schema these two schemas use* in JavaScript
([`../scripts/validate.mjs`](../scripts/validate.mjs)), a direct port of
`core/schema/check_examples.py`'s `validate()`. The **rules** are the canonical
rules (these files); only the **engine** is re-expressed.

**Keeping them current.** If the upstream bundle or standing schema changes, copy
the new files here. The site reads the vault's published output, so an out-of-date
copy would reject a valid new artifact (loudly) rather than accept a bad one — the
safe direction to fail.

**When the vault is behind the site.** Your vault and your site update core at
different times. A field a release adds is optional in the schema until the next
release (`core/schema/README.md`, "Compatibility between releases"), so a
`standing.json` from the previous release still validates here. When rows lack
such a field, the build log says the vault's core is behind and the board shows
the fallback — "no history yet" for the track-record column. Updating the vault's
core and publishing again fills it in. A file that breaks the schema any other way
still stops the build.
