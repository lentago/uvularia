---
id: YYYY-MM-DD-short-slug
title: "A short, human title"
type: minutes
status: draft
visibility: public
effective: YYYY-MM-DD
approved: YYYY-MM-DD
source:
  kind: text
  file: library/files/minutes/YYYY-MM-DD-short-slug.txt
  sha256: 0000000000000000000000000000000000000000000000000000000000000000
certainty: verified
subjects: [subject-one, subject-two]
tags: [tag-one]
---

# A short, human title

Duplicate this file into `records/<type>/`, rename it to match the `id`, and
fill in the frontmatter and prose. Keep the `id` stable forever: it is the
record's permanent slug. To replace a record, add a new one and set
`supersedes:` to the old `id` — never rename or delete.

The frontmatter above is the only machine-readable surface; do not invent
fields outside `core/schema/record.schema.json`. Prose below the second `---`
is for people.
