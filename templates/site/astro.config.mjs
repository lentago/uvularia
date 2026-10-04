// astro.config.mjs
//
// The site is a static build. Its only client-side JavaScript is the optional Ask
// box, present only when site.config.ts sets askUrl. It reads
// its identity and its data source from site.config.ts (the one file you edit),
// and runs fetch-published.mjs as a build hook so every build starts by pulling
// the current published artifacts from your vault. Set UVULARIA_PUBLISHED_BASE in
// the environment to override the configured source (the tests use this to build
// against local fixtures without touching the network).

import { defineConfig } from "astro/config";
import config from "./site.config.ts";
import { fetchPublished } from "./scripts/fetch-published.mjs";

const publishedBase = process.env.UVULARIA_PUBLISHED_BASE || config.publishedBaseUrl;

const fetchArtifacts = {
  name: "uvularia-fetch-published",
  hooks: {
    "astro:config:setup": async ({ command }) => {
      // Populate .published/ before the dev server reads it, too.
      if (command === "dev") await fetchPublished({ baseUrl: publishedBase, outDir: ".published" });
    },
    "astro:build:start": async () => {
      await fetchPublished({ baseUrl: publishedBase, outDir: ".published" });
    },
  },
};

export default defineConfig({
  site: config.site,
  base: config.base || "/",
  trailingSlash: "always",
  build: { format: "directory" },
  integrations: [fetchArtifacts],
});
