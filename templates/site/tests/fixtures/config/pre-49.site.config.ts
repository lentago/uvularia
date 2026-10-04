// A client's site.config.ts in the current values-only shape, written before the
// template gained askUrl and askDisclaimer (#49). It must type-check and build
// against today's src/config-schema.ts unchanged.

import type { SiteConfig } from "./src/config-schema";

export const config: SiteConfig = {
  publishedBaseUrl: "https://raw.githubusercontent.com/older-org/older-org-records/published/",
  orgName: "Older Values Org",
  contact: "records@example.org",
  accent: "#2f6f4f",
  site: "https://older-org.github.io",
  base: "/older-org-site",
};
