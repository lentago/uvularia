---
id: {{ id }}
title: "{{ title }}"
type: minutes
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

Minutes of the {{ meeting_long }} meeting of the {{ org_short_name }} Board of
Trustees. Approved by the Board on {{ approved }}.

**Present:** {{ present }} of 7 trustees. Staff present: {{ staff_present }}.

{{ body }}

The meeting adjourned at {{ adjourned }}. These minutes were approved at the
following regular meeting and posted after that approval.
