// A config with a misspelled setting (askURL for askUrl). The type-check must
// reject it: this is the fixture that proves the config check can fail.

import type { SiteConfig } from "./src/config-schema";

export const config: SiteConfig = {
  publishedBaseUrl: "https://raw.githubusercontent.com/older-org/older-org-records/published/",
  orgName: "Misspelled Org",
  contact: "records@example.org",
  accent: "#2f6f4f",
  askURL: "https://ask.example.invalid/",
};
