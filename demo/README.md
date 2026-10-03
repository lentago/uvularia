# demo — the demonstration client

This directory is a working demonstration of the records product: a fictional
land trust with two years of public records, a validator that passes on them,
and a compliance board that shows an honest mix of green, amber, and red. It
exists so the board, the receipts, and (later) the Ask box have something real
to run against, and so anyone can fork a realistic vault as a reference.

It is **not** a starting point for a real organization. A real client
instantiates the empty records template and fills it with their own records; it
never copies this seed. See [docs/adr/0001](../docs/adr/0001-demo-identity-in-one-file-generated-seed.md)
for why the demo is generated rather than hand-written.

## What's here

| Path | What it is |
|---|---|
| `org.yaml` | The **only** place the demo's identity lives: name, short name, domain, contact, accent colour, and an SVG logo. |
| `templates/` | The record templates. Tokens like `{{ org_name }}` are filled in at generation time; the identity never appears literally here. |
| `seed.py` | Reads `org.yaml`, renders the templates, and writes the vault under `generated/`. Standard library only; deterministic. |
| `generated/` | The generated vault, committed so it is browsable and so CI can diff it. In the same layout a real vault uses. |
| `check_name_leak.py` | Fails if the identity appears anywhere it should not. |
| `tests/` | Behavioural tests, including a fixture that proves the name-leak guard can fail. |

## Regenerate it

> **What:** rebuild `generated/` from `org.yaml` and `templates/`.
> **Why:** the committed vault must always match its source — CI fails if it
> drifts. **How long:** a second or two. **How you know it worked:** it prints
> the record count and the board summary, and `git status` is clean.

```sh
python3 demo/seed.py
```

## Rename or rebrand it — one edit, one re-run

> **What:** change the demonstration client's identity everywhere at once.
> **Why:** to prove the product's central promise — that a client's identity
> lives in one file. **How long:** under a minute. **How you know it worked:**
> the regenerated `generated/` carries the new identity, the diff touches
> nothing outside `generated/`, and the name-leak check stays green.

1. Edit the five identity fields at the top of [`org.yaml`](org.yaml)
   (`name`, `short_name`, `domain`, `contact`, `accent`). The logo picks up the
   new short name and accent automatically.
2. Run `python3 demo/seed.py`.
3. Commit. The diff is the new identity flowing through the generated vault and
   nothing else.

That is the whole rename. Nothing else in the repository carries the identity,
and CI (`demo/check_name_leak.py`) fails if anything ever does — which is what
makes the one-file rename trustworthy.

## The board is a fixed snapshot

The demo is evaluated as of a pinned instant (`python3 demo/seed.py --print-asof`),
not the calendar day CI happens to run on, so the board is reproducible. As of
that instant the board shows, against the Massachusetts obligations pack:

- **red** — the most recent board-meeting notice was posted the day before the
  meeting, inside the 48-hour window. Two notices in the history are late on
  purpose (see `LATE_NOTICE_INDICES` in `seed.py`); the most recent one is why
  the current row is red.
- **amber** — the annual charity (Form PC) filing comes due within the warning
  window of the pinned instant.
- **green** — the annual report to the Secretary and the most recent minutes
  were posted on time.

A real vault is evaluated at real "now"; the pin is only so the demonstration
stays still. The receipts under `generated/.../receipts/` each carry the board
as it honestly stood at that publish, so the history shows the state changing
over time, never a retroactively faked green.

## How CI checks it

[`.github/workflows/demo.yml`](../.github/workflows/demo.yml) runs on every pull
request: it regenerates and fails on drift, runs `core/validate.py` and
`core/evaluate.py` over the generated vault, requires a red and an amber on the
board, runs `check_name_leak.py`, and runs the tests in `tests/`. The name-leak
guard reads the forbidden strings from `org.yaml` at runtime, so it renames
along with the demo; design documents that name the demonstration client
(`README.md`, `docs/`) are prose, not part of the generated vault, and are not
scanned.
