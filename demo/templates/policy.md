---
id: {{ id }}
title: "{{ title }}"
type: policy
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

Conflict-of-interest policy of {{ org_name }} ({{ org_short_name }}), effective
{{ effective }}.

{{ body }}

The Board reviews this policy and each trustee's disclosure annually. Earlier
versions remain in the vault marked `superseded`.
