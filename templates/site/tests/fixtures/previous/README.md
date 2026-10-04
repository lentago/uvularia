# The previous release's standing.json

`standing.json` here is the good fixture's board rows as a vault on the previous
core release wrote them: the same four rows, with no `history` key. A site built
from this template must still build against it and show "no history yet"
(`core/schema/README.md`, "Compatibility between releases"). `board.test.mjs`
swaps it in over the good fixture; `schema.test.mjs` checks that it validates.
