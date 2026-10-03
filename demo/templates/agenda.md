---
id: {{ id }}
title: "{{ title }}"
type: agenda
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

Agenda for the {{ meeting_long }} meeting of the {{ org_short_name }} Board of
Trustees.

{{ body }}

Items may be taken out of order. Any member of the public may address the Board
during the public-comment period.
