---
id: {{ id }}
title: "{{ title }}"
type: faq
status: {{ status }}
visibility: public
effective: {{ effective }}
approved: {{ approved }}
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
