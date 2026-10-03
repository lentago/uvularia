# {{ org_name }} — public records

This is the records vault of {{ org_name }} ({{ org_short_name }}): minutes,
notices, agendas, bylaws, policies, filings, reports, announcements, and
answers to common questions. Every file here is a public record. The original
of each is kept under `library/` with a checksum; obligations are declared under
`obligations/` and evaluated on every publish; `standing.json` is the current
state of the board.

- **Website:** {{ domain }}
- **Contact:** {{ contact }}
- **Current trail and visitor-center status:** {{ status_url }}

> This vault is generated for demonstration. It is fictional. A real
> organization keeps real records here; it does not start from this seed.

## Records by type

{{ record_sections }}

## How this vault is organized

- `records/<type>/` — one Markdown file per record; the frontmatter is the
  machine-readable surface, the prose is for people.
- `library/` — the original document behind each record, with `manifest.json`
  listing a checksum for each.
- `obligations/` — the posting rules this organization holds itself to, drawn
  from the Massachusetts pack.
- `receipts/` — one append-only receipt per publish, recording when each record
  went public (server-side time).
- `standing.json` — the current board: one row per obligation, green / amber /
  red / no-data.
- `intake/` — the staging door; never built or published.
