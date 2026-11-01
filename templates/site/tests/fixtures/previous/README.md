# The previous release's standing.json

`standing.json` here is the good fixture's board rows as a vault on the previous
core release wrote them: the same four rows, with no `history` and no
`evaluated_at` key. With no `evaluated_at`, the board dates the rows by the
corpus bundle's `published_at`, which is when an older core evaluated. A site built
from this template must still build against it and show "no history yet"
(`core/schema/README.md`, "Compatibility between releases"). `board.test.mjs`
swaps it in over the good fixture; `schema.test.mjs` checks that it validates.
