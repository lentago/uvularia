# Adoption receipts

This folder holds uvularia's **own** adoption receipts: the record of a human
operator running [`DRY-RUN.md`](../DRY-RUN.md) end to end — from **Use this
template** to a green row on a live board — and writing down how long it took and
whether every check went green.

A receipt is how a tier claim earns the right to be made. The tier picker in
[lupinus](https://github.com/lentago/lupinus) cites the **latest** receipt here
as its evidence that this product is adoptable; until one exists, uvularia claims
no tier and [README.md](../README.md) says Phase 0 is complete *pending its first
timed dry-run*.

> These are not the vault's *publish* receipts. Those are a different thing — one
> per publish, written automatically by the vault's publish workflow and defined
> by [`core/schema/receipt.schema.json`](../core/schema/receipt.schema.json). The
> receipts here are written **by hand, by the person who ran the drill**, and are
> about adopting the product, not about publishing a record.

## How to file one

1. Run [`DRY-RUN.md`](../DRY-RUN.md) all the way through, filling in its drill
   table and its receipt block as you go.
2. Copy [`TEMPLATE.md`](TEMPLATE.md) to `receipts/<YYYY-MM-DD>-<operator>.md` —
   the date you ran it and your GitHub handle, lowercased, e.g.
   `2026-10-15-cpitzi.md`.
3. Transcribe the drill's receipt values, add the per-step elapsed times and any
   notes, and commit it in a pull request.

Receipts are **append-only**: file a new one for each run; never edit or delete a
past receipt. The history of runs is itself evidence that the time stays honest
across template changes.
