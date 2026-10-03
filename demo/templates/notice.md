---
id: {{ id }}
title: "{{ title }}"
type: notice
status: {{ status }}
visibility: public
effective: {{ effective }}
approved: {{ approved }}
source:
  kind: text
  file: {{ source_file }}
  sha256: {{ source_sha }}
certainty: verified
subjects: {{ subjects }}
tags: {{ tags }}
{{ corrections_block }}---

# {{ title }}

{{ org_name }} ({{ org_short_name }}) gives notice of a public meeting of its
Board of Trustees.

- **Meeting:** {{ meeting_long }}
- **Time:** {{ meeting_time }}
- **Place:** {{ place }}
- **Attending:** open to the public; remote-participation details are posted at
  {{ meeting_url }}.

The agenda is posted as a separate record. Minutes are posted after the Board
approves them at a later meeting. When this notice was posted is recorded in the
publish receipt, and the board shows whether it met the posting window — this
record does not assert that itself.
