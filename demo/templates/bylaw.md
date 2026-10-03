---
id: {{ id }}
title: "{{ title }}"
type: bylaw
status: {{ status }}
visibility: public
effective: {{ effective }}
approved: {{ approved }}
source:
  kind: text
  file: {{ source_file }}
  sha256: {{ source_sha }}
certainty: verified
{{ supersedes_line }}subjects: {{ subjects }}
tags: {{ tags }}
{{ corrections_block }}---

# {{ title }}

Bylaws of {{ org_name }}, a Massachusetts nonprofit corporation, effective
{{ effective }}.

{{ body }}

The current bylaws are the most recent version in this chain. Earlier versions
remain in the vault marked `superseded`; they are never deleted.
