// src/config.ts — the one place the site reads site.config.ts. Template-owned.
//
// Every page, the build hook, and the Ask box import `config` from here rather
// than from site.config.ts directly. That keeps the shape of your file a detail
// this module absorbs: the current shape (`export const config`) and the shape
// earlier versions of the template shipped (`export default config`, with the
// interface in the same file) both work, so syncing the template never breaks
// the build of a site.config.ts you have not touched.

import * as values from "../site.config";
import type { SiteConfig } from "./config-schema";

const found = values as { config?: SiteConfig; default?: SiteConfig };

if (!found.config && !found.default) {
  throw new Error(
    "site.config.ts must export your settings as `export const config: SiteConfig = { … }`",
  );
}

export const config: SiteConfig = (found.config ?? found.default) as SiteConfig;
export type { SiteConfig };
