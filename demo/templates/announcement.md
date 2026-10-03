---
id: {{ id }}
title: "{{ title }}"
type: announcement
status: {{ status }}
visibility: public
effective: {{ effective }}
approved: {{ approved }}
publish_at: "{{ publish_at }}"
source:
  kind: text
  file: {{ source_file }}
  sha256: {{ source_sha }}
certainty: {{ certainty }}
subjects: {{ subjects }}
tags: {{ tags }}
{{ corrections_block }}---

# {{ title }}

{{ body }}

Posted by {{ org_short_name }}. Current trail and visitor-center status is kept
up to date at {{ status_url }}.
