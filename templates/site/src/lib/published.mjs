// Readers for the artifacts fetch-published.mjs dropped into .published/.
//
// Every reader degrades to null/empty when its artifact is absent — a vault that
// has published nothing yet must still produce a site that builds, with an empty
// records index and a board that reads "no data" (invariant 5). Pages decide what
// an absence means to the reader; this module only reports it honestly.

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

const DIR = join(process.cwd(), ".published");

function readText(name) {
  const path = join(DIR, name);
  return existsSync(path) ? readFileSync(path, "utf8") : null;
}

function readJson(name) {
  const text = readText(name);
  return text === null ? null : JSON.parse(text);
}

// When the data was last fetched, and which artifacts were present, as recorded
// by the build step. Always exists after a build; falls back for safety.
export function meta() {
  return readJson("meta.json") || { fetched_at: null, source: null, present: {} };
}

// The corpus bundle, or null if nothing has been published.
export function bundle() {
  return readJson("corpus-latest.json");
}

// The published records (bundle entries), or [] if nothing has been published.
export function records() {
  const b = bundle();
  return b ? b.records : [];
}

// The standing rows, or null if standing.json is absent/unreadable. null is the
// board's "no data for anything" signal — distinct from [] (an empty obligation
// set that was published).
export function standing() {
  return readJson("standing.json");
}

// Raw Atom feed text, or null if no feed has been published.
export function feedXml() {
  return readText("feed.xml");
}

// The frontmatter of the receipt that published the current corpus, or null.
export function receipt() {
  const dir = join(DIR, "receipts");
  if (!existsSync(dir)) return null;
  const files = readdirSync(dir).filter((f) => f.endsWith(".md"));
  if (!files.length) return null;
  const text = readFileSync(join(dir, files[0]), "utf8");
  return parseReceipt(text);
}

// The record type is the folder a record lives in: records/<type>/<id>.md.
export function typeOf(entry) {
  const parts = (entry.path || "").split("/");
  const i = parts.indexOf("records");
  return i >= 0 && parts.length > i + 2 ? parts[i + 1] : "other";
}

// --------------------------------------------------------------------------- //
// Receipt frontmatter. The receipt is Markdown with a YAML frontmatter block
// (core/bundle.py's receipt_markdown). We only need a few scalar fields and the
// three id lists; this is a deliberately small reader for that known shape, not a
// general YAML parser.
// --------------------------------------------------------------------------- //

function parseReceipt(text) {
  const lines = text.split("\n");
  if (lines[0].trim() !== "---") return null;
  const end = lines.indexOf("---", 1);
  if (end < 0) return null;
  const fm = lines.slice(1, end);

  const out = { records: { added: [], changed: [], retracted: [] } };
  let section = null;
  const scalar = (v) => v.trim().replace(/^"(.*)"$/, "$1").replace(/\\"/g, '"').replace(/\\\\/g, "\\");
  const idList = (v) =>
    v.trim().replace(/^\[|\]$/g, "").split(",").map((s) => scalar(s)).filter(Boolean);

  for (const line of fm) {
    const top = line.match(/^(\w+):\s*(.*)$/);
    const nested = line.match(/^\s+(\w+):\s*(.*)$/);
    if (top) {
      section = top[1];
      const val = top[2];
      if (val !== "") {
        if (["digest", "published_at", "run_url", "commit"].includes(section)) out[section] = scalar(val);
        section = null;
      }
    } else if (nested && section === "records") {
      out.records[nested[1]] = idList(nested[2]);
    }
  }
  return out;
}
