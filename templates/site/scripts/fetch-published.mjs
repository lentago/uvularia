// fetch-published.mjs — the site's build step.
//
// WHAT IT DOES. Before Astro renders a page, this pulls the four published
// artifacts a records vault serves on its `published` branch and drops them into
// a local `.published/` directory the pages read:
//
//   corpus-latest.json   the published records (schema/bundle.schema.json)
//   standing.json        the board rows      (schema/standing.schema.json)
//   feed.xml             the announcement Atom feed
//   receipts/<name>.md   the receipt that published the current corpus
//
// The site builds ONLY from these artifacts, never from a vault checkout
// (invariant 1: the site cannot smuggle a fact). It is run as an Astro build hook
// (see astro.config.mjs, which reads the base URL from site.config.ts) and can
// also be run by hand or by the tests:  node scripts/fetch-published.mjs <base>
//
// VALIDATION. corpus-latest.json and standing.json are validated against the
// vendored schemas. An artifact that is PRESENT but INVALID fails the build —
// we never render a partial or malformed site (task requirement). An artifact
// that is ABSENT is not a failure: a vault that has published nothing yet, or a
// `published` branch that does not exist, yields an empty records index and a
// board that honestly reads "no data" (invariant 5 — never a fake green). The
// difference between "absent" and "invalid" is the whole point.
//
// RECEIPTS. The `published` branch carries one receipt per publish under
// receipts/, named <YYYY-MM-DDTHHMMSSZ>-<digest>.md, but serves no directory listing over
// a raw or Pages URL, and we must not modify the vault template to add an index.
// So we fetch exactly the receipt that attests the *current* corpus: its name is
// derivable from corpus-latest.json (published_at's date + digest, the same shape
// core/bundle.py writes). That is the receipt that published the corpus every
// record on the site currently belongs to. Older receipts remain on the branch.

import { readFile, writeFile, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";

import { validate } from "./validate.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCHEMA_DIR = join(HERE, "..", "schema");

// --------------------------------------------------------------------------- //
// Reading a named artifact from a base that may be an http(s) URL, a file:// URL,
// or a local directory path. Returns { ok, text }. ok=false means "not found".
// Any OTHER failure (network error, read error) throws — a flaky fetch must not
// be silently rendered as an empty site.
// --------------------------------------------------------------------------- //

function isHttp(base) {
  return /^https?:\/\//i.test(base);
}

async function readArtifact(base, name) {
  if (isHttp(base)) {
    const url = base.replace(/\/+$/, "") + "/" + name;
    const res = await fetch(url);
    if (res.status === 404) return { ok: false };
    if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status} ${res.statusText}`);
    return { ok: true, text: await res.text() };
  }
  // Local directory or file:// URL.
  const root = base.startsWith("file://") ? fileURLToPath(base) : base;
  const path = join(root, name);
  if (!existsSync(path)) return { ok: false };
  return { ok: true, text: await readFile(path, "utf8") };
}

async function loadSchema(name) {
  return JSON.parse(await readFile(join(SCHEMA_DIR, `${name}.schema.json`), "utf8"));
}

function requireValid(name, schema, instance) {
  const errors = validate(schema, instance, schema);
  if (errors.length) {
    throw new Error(
      `the fetched ${name} does not match its schema — the build is stopped rather ` +
        `than render an invalid site:\n  - ${errors.join("\n  - ")}`,
    );
  }
}

// The receipt filenames core/bundle.py has written, newest convention first:
//   "<YYYY-MM-DDTHHMMSSZ>-<digest>.md"  (publish instant; one file per publish)
//   "<YYYY-MM-DD>-<digest>.md"          (older vaults; a same-day republish could overwrite)
// We try the instant form, then fall back to the day form, so a site newer than
// its vault's core still finds the receipt.
function receiptNames(bundle) {
  const at = String(bundle.published_at || "");
  const day = at.slice(0, 10);
  const stamp = at.replace("+00:00", "Z").replace(/[^0-9TZ]/g, "");
  const instant = stamp.length >= 15
    ? `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}T${stamp.slice(9, 15)}Z`
    : null;
  const names = [];
  if (instant) names.push(`${instant}-${bundle.digest}.md`);
  names.push(`${day}-${bundle.digest}.md`);
  return names;
}

// --------------------------------------------------------------------------- //
// The build step.
// --------------------------------------------------------------------------- //

export async function fetchPublished({ baseUrl, outDir }) {
  if (!baseUrl) {
    throw new Error("fetchPublished: no base URL — set publishedBaseUrl in site.config.ts");
  }
  const out = resolve(outDir);
  await rm(out, { recursive: true, force: true });
  await mkdir(join(out, "receipts"), { recursive: true });

  const meta = {
    source: baseUrl,
    // Build-time clock; shown on the board as "data last fetched".
    fetched_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    present: { corpus: false, standing: false, feed: false, receipt: false },
  };

  const log = (m) => console.log(`[fetch-published] ${m}`);
  log(`source ${baseUrl}`);

  // --- corpus ---------------------------------------------------------------
  let bundle = null;
  const corpus = await readArtifact(baseUrl, "corpus-latest.json");
  if (corpus.ok) {
    bundle = JSON.parse(corpus.text);
    requireValid("corpus bundle", await loadSchema("bundle"), bundle);
    await writeFile(join(out, "corpus-latest.json"), corpus.text);
    meta.present.corpus = true;
    log(`corpus ${bundle.records.length} record(s), digest ${bundle.digest.slice(0, 12)}…`);
  } else {
    log("corpus-latest.json not published yet — the records index will be empty");
  }

  // --- standing -------------------------------------------------------------
  const standing = await readArtifact(baseUrl, "standing.json");
  if (standing.ok) {
    const rows = JSON.parse(standing.text);
    requireValid("standing", await loadSchema("standing"), rows);
    await writeFile(join(out, "standing.json"), standing.text);
    meta.present.standing = true;
    log(`standing ${rows.length} obligation row(s)`);
  } else {
    // Absent is not a failure: the board renders every row as "no data".
    log("standing.json not published yet — the board will read 'no data'");
  }

  // --- feed -----------------------------------------------------------------
  const feed = await readArtifact(baseUrl, "feed.xml");
  if (feed.ok) {
    await writeFile(join(out, "feed.xml"), feed.text);
    meta.present.feed = true;
    log("feed.xml fetched");
  } else {
    log("feed.xml not published yet — the announcements page will be empty");
  }

  // --- the current corpus's receipt ----------------------------------------
  if (bundle) {
    let name = null, receipt = { ok: false };
    for (const candidate of receiptNames(bundle)) {
      receipt = await readArtifact(baseUrl, `receipts/${candidate}`);
      if (receipt.ok) { name = candidate; break; }
    }
    if (!name) name = receiptNames(bundle)[0];
    if (receipt.ok) {
      await writeFile(join(out, "receipts", name), receipt.text);
      meta.present.receipt = true;
      meta.receipt_name = name;
      log(`receipt ${name}`);
    } else {
      log(`receipt receipts/${name} not found — record pages will omit the receipt link`);
    }
  }

  await writeFile(join(out, "meta.json"), JSON.stringify(meta, null, 2) + "\n");
  return meta;
}

// --------------------------------------------------------------------------- //
// CLI:  node scripts/fetch-published.mjs <base> [outDir]
// --------------------------------------------------------------------------- //

if (import.meta.url === `file://${process.argv[1]}`) {
  const base = process.argv[2] || process.env.UVULARIA_PUBLISHED_BASE;
  const outDir = process.argv[3] || ".published";
  fetchPublished({ baseUrl: base, outDir }).catch((err) => {
    console.error(`error: ${err.message}`);
    process.exit(1);
  });
}
