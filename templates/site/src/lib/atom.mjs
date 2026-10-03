// A minimal Atom reader for the announcement feed.
//
// The feed has a known, simple shape — core/bundle.py's build_feed writes it with
// one <entry> per announcement, each with <id>, <title>, <updated>, and a plain
// <content type="text">. Node's stdlib has no XML parser, and a dependency is out
// of scope, so this extracts those fields directly. It handles the five XML
// entities bundle.py's escape() emits (& < > " ') and nothing more exotic; a feed
// it cannot parse yields an empty list, never a crashed build.

function unescapeXml(s) {
  return s
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

function tagText(block, tag) {
  const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`));
  return m ? unescapeXml(m[1].trim()) : null;
}

export function parseAtom(xml) {
  if (!xml) return [];
  const entries = [];
  const re = /<entry>([\s\S]*?)<\/entry>/g;
  let m;
  while ((m = re.exec(xml)) !== null) {
    const block = m[1];
    entries.push({
      id: tagText(block, "id"),
      title: tagText(block, "title") || "Announcement",
      updated: tagText(block, "updated"),
      content: tagText(block, "content") || "",
    });
  }
  return entries;
}
