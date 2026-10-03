// Re-serve the vault's published Atom feed at /feed.xml, so readers subscribe to
// the site, not to a raw branch URL. The content is exactly what the vault
// published; the site adds nothing. If nothing has been published yet, serve a
// minimal empty-but-valid Atom document rather than a 404.
import type { APIRoute } from "astro";
import { feedXml } from "../lib/published.mjs";

const EMPTY = `<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>urn:uvularia:feed:empty</id>
  <title>Announcements</title>
  <updated>1970-01-01T00:00:00Z</updated>
</feed>
`;

export const GET: APIRoute = () => {
  const xml = feedXml() ?? EMPTY;
  return new Response(xml, { headers: { "Content-Type": "application/atom+xml; charset=utf-8" } });
};
