// Builds the site twice and inspects the rendered /board/ HTML:
//
//   1. with the good fixture — a two-record bundle and a standing.json carrying
//      one row per state — and asserts every state's WORD appears, each
//      obligation id appears, and a green badge is actually rendered.
//   2. with standing.json ABSENT — and asserts the board falls back to "no data"
//      and renders NO green badge (invariant 5: never a fake green).
//   3. with the PREVIOUS release's standing.json (rows without history) — and
//      asserts the build succeeds, says the vault's core is behind, and the board
//      reads "no history yet" for every row.
//   4. with a MALFORMED standing.json — and asserts the build still stops.
//   5. with the build's clock a day past the board's evaluated_at — and asserts
//      every row reads "unknown", no green badge is visible, and the page says
//      when it was last re-checked (uvularia#115: never a stale green).
//
//   node tests/board.test.mjs
//
// The build is driven against local fixtures via UVULARIA_PUBLISHED_BASE, so this
// never touches the network.

import { execFileSync } from "node:child_process";
import vm from "node:vm";
import { cpSync, mkdtempSync, readFileSync, rmSync, existsSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ASTRO = join(ROOT, "node_modules", ".bin", "astro");
const GOOD = join(HERE, "fixtures", "good");
const BOARD = join(ROOT, "dist", "board", "index.html");

// The green badge's background is unique to the green state (StateBadge.astro), so
// its presence is a reliable "a green badge was rendered" signal.
const GREEN_SWATCH = "#1b7a3d";

// The good fixture was published, and evaluated, at 2026-10-01T14:03:11Z. Builds
// run with the clock pinned an hour later unless a test says otherwise.
const FRESH_NOW = "2026-10-01T15:03:11Z";

// The page as a reader sees it: every element carrying `hidden` removed.
function visible(html) {
  let out = html;
  for (;;) {
    const m = out.match(/<(\w+)\b[^>]*\shidden(?:=""|="hidden"|(?=[\s>]))[^>]*>/);
    if (!m) return out;
    const tag = m[1];
    let depth = 0;
    const re = new RegExp(`<${tag}\\b[^>]*>|</${tag}>`, "g");
    re.lastIndex = m.index;
    let end = -1;
    for (let t; (t = re.exec(out)); ) {
      depth += t[0].startsWith("</") ? -1 : 1;
      if (depth === 0) { end = re.lastIndex; break; }
    }
    out = out.slice(0, m.index) + (end < 0 ? "" : out.slice(end));
  }
}

function tbody(html) {
  const m = html.match(/<tbody>([\s\S]*?)<\/tbody>/);
  return m ? m[1] : "";
}

let failures = 0;
function expect(label, cond) {
  if (cond) console.log(`ok    ${label}`);
  else {
    failures++;
    console.log(`FAIL  ${label}`);
  }
}

function build(base, { log = false, now = FRESH_NOW } = {}) {
  rmSync(join(ROOT, "dist"), { recursive: true, force: true });
  const out = execFileSync(ASTRO, ["build"], {
    cwd: ROOT,
    env: { ...process.env, UVULARIA_PUBLISHED_BASE: base, UVULARIA_NOW: now },
    stdio: log ? ["ignore", "pipe", "inherit"] : "inherit",
    encoding: "utf8",
  });
  if (log) process.stdout.write(out);
  if (!existsSync(BOARD)) throw new Error(`build produced no board page at ${BOARD}`);
  const html = readFileSync(BOARD, "utf8");
  return log ? { html, log: out } : html;
}

// The good fixture with one artifact swapped for another file, in a temp dir.
function withStanding(source, fn) {
  const tmp = mkdtempSync(join(tmpdir(), "uvularia-standing-"));
  try {
    cpSync(GOOD, tmp, { recursive: true });
    cpSync(source, join(tmp, "standing.json"));
    return fn(tmp);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

// --- 1. the good fixture: one row per state ---------------------------------
console.log("# building against the good fixture");
const good = build(GOOD);

for (const word of ["green", "amber", "red", "no data"]) {
  expect(`board shows the word "${word}"`, good.includes(`>${word}</span>`));
}
for (const id of [
  "open-meeting-notice-48h",
  "minutes-within-30-days",
  "annual-report-filed",
  "conflict-of-interest-annual",
]) {
  expect(`board lists obligation ${id}`, good.includes(id));
}
expect("board renders a real green badge", tbody(visible(good)).includes(GREEN_SWATCH));
expect("board says when it was evaluated", good.includes('Evaluated <time datetime="2026-10-01T14:03:11Z">1 October 2026, 14:03 UTC</time>'));
expect("board says when it was last published", /Last published <time datetime="2026-10-01T14:03:11Z">/.test(good));
expect("a fresh board shows no visible unknown row", !tbody(visible(good)).includes(">unknown</span>"));
expect("a fresh board carries the stale variant, hidden, for the script", (tbody(good).match(/>unknown<\/span>/g) || []).length === 4);
expect("each row carries its valid_until for the script",
  (good.match(/class="row-state" data-valid-until="2026-10-02T14:03:11Z"/g) || []).length === 4);
expect("board links the satisfying record", good.includes("records/2026-09-16-board-minutes/"));
expect("board says when data was last fetched", /data last fetched/i.test(good));

// --- the track record column (history) --------------------------------------
// The good fixture carries one row with breaches (12 evaluated, 2 late), one
// clean row (8 evaluated, 0 late), and two rows with null history. Assert the
// late phrase, the clean phrase, and the "no history yet" fallback all render —
// and that a null history is never dressed up as a zero-breach phrase.
expect('board shows a late track record ("late 2 of the last 12")', good.includes("late 2 of the last 12"));
expect('board shows a clean track record ("none late in the last 8")', good.includes("none late in the last 8"));
expect('board falls back to "no history yet" for a null history', good.includes("no history yet"));
expect("a null history never renders as a zero-breach phrase", !/late 0 of the last/.test(good));

// --- 2. standing.json absent: no data, never a fake green -------------------
console.log("\n# building with standing.json absent");
const tmp = mkdtempSync(join(tmpdir(), "uvularia-nostanding-"));
try {
  cpSync(GOOD, tmp, { recursive: true });
  rmSync(join(tmp, "standing.json"), { force: true });
  const nostanding = build(tmp);

  expect('absent standing falls back to "no data"', nostanding.includes(">no data</span>"));
  expect("absent standing says the board could not read standing.json", /could not read/i.test(nostanding));
  expect("absent standing renders NO green badge (never a fake green)", !nostanding.includes(GREEN_SWATCH));
  expect("absent standing still says when data was last fetched", /data last fetched|last fetched/i.test(nostanding));
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

// --- 3. the previous release's standing.json: builds, "no history yet" -------
// A site newer than its vault's core must not fail on rows that predate history.
console.log("\n# building against the previous release's standing.json (no history)");
withStanding(join(HERE, "fixtures", "previous", "standing.json"), (tmp) => {
  let built = null;
  try {
    built = build(tmp, { log: true });
  } catch (err) {
    console.log(`  build failed: ${err.message.split("\n")[0]}`);
  }
  expect("previous-release standing builds", built !== null);
  if (!built) return;
  const board = built.html;
  const fallbacks = (board.match(/no history yet/g) || []).length;
  expect('every row reads "no history yet" (4 rows)', fallbacks === 4);
  expect("no row invents a track record", !/late \d+ of the last|none late in the last/.test(board));
  expect("current state still renders (a real green badge)", tbody(visible(board)).includes(GREEN_SWATCH));
  expect("build log says the vault's core is behind", /core is behind/.test(built.log));
  expect("rows with no evaluated_at are dated by the publish", /Evaluated <time datetime="2026-10-01T14:03:11Z">/.test(board));
});

// --- 5. a board not re-checked within the day: unknown, never a stale green --
console.log("\n# building a day and a second after the board was evaluated");
{
  const stale = build(GOOD, { now: "2026-10-02T14:03:12Z" });
  const shown = tbody(visible(stale));
  expect("a stale board shows NO visible green badge", !shown.includes(GREEN_SWATCH));
  expect('every row reads "unknown" (4 rows)', (shown.match(/>unknown<\/span>/g) || []).length === 4);
  expect("each row keeps its last colour in words", ["green", "amber", "red", "no data"].every((w) => shown.includes(`(was ${w})`)));
  expect("the page says when it was last re-checked", visible(stale).includes("since the board was last re-checked, at"));
  const fresh = build(GOOD, { now: "2026-10-02T14:03:11Z" });
  expect("exactly at valid_until is still current", tbody(visible(fresh)).includes(GREEN_SWATCH));
}

// Run a page's inline summary script against a minimal fake DOM at a given
// clock, and report which half of the summary is left visible.
function runSummaryScript(html, nowIso) {
  const script = (html.match(/<script>([\s\S]*?)<\/script>/g) || [])
    .map((s) => s.replace(/^<script>|<\/script>$/g, ""))
    .find((s) => s.includes('getElementById("board-summary")'));
  if (!script) return null;
  const until = (html.match(/id="board-summary" data-valid-until="([^"]*)"/) || [])[1] ?? "";
  const live = { hidden: false }, stale = { hidden: true };
  const el = { getAttribute: () => until, querySelector: (q) => (q === ".live" ? live : stale) };
  const RealDate = Date;
  const FixedDate = class extends RealDate { static now() { return RealDate.parse(nowIso); } };
  vm.runInNewContext(script, { document: { getElementById: (id) => (id === "board-summary" ? el : null) }, Date: FixedDate });
  return live.hidden && !stale.hidden ? "stale" : !live.hidden && stale.hidden ? "live" : "both";
}

// --- the home page's one-line summary follows the same rule (uvularia#127) ---
console.log("\n# the home page summary, current and lapsed");
{
  const HOME = join(ROOT, "dist", "index.html");
  build(GOOD);
  const current = visible(readFileSync(HOME, "utf8"));
  expect("a current home page counts the colours", current.includes("1 green, 1 amber, 1 red, 1 no-data"));
  expect("a current home page counts no unknown rows", !current.includes(" unknown"));
  const page = readFileSync(HOME, "utf8");
  expect("in the browser, the counts stay before the earliest valid_until",
    runSummaryScript(page, "2026-10-02T14:03:11Z") === "live");
  expect("in the browser, the counts give way to the pointer after it",
    runSummaryScript(page, "2026-10-02T14:03:12Z") === "stale");
  build(GOOD, { now: "2026-10-02T14:03:12Z" });
  const lapsed = readFileSync(HOME, "utf8");
  expect("a lapsed home page counts every row as unknown", visible(lapsed).includes("0 green, 0 amber, 0 red, 0 no-data, 4 unknown"));
  expect("the summary carries the earliest valid_until for the browser check",
    /id="board-summary" data-valid-until="2026-10-02T14:03:11Z"/.test(lapsed));
}

// --- 6. one row lapses at midnight, the others hold ---------------------------
console.log("\n# building with one row that changes at the next midnight");
{
  const rows = JSON.parse(readFileSync(join(GOOD, "standing.json"), "utf8"));
  rows[0].valid_until = "2026-10-02T00:00:00Z";        // the green row
  const tmp = mkdtempSync(join(tmpdir(), "uvularia-lapse-"));
  try {
    cpSync(GOOD, tmp, { recursive: true });
    writeFileSync(join(tmp, "standing.json"), JSON.stringify(rows));
    const page = build(tmp, { now: "2026-10-02T00:00:01Z" });
    const shown = tbody(visible(page));
    expect("the lapsed green row reads unknown", shown.includes("(was green)") && !shown.includes(GREEN_SWATCH));
    expect("the rows still inside valid_until keep their colours", shown.includes(">amber</span>") && shown.includes(">red</span>"));
    expect("the notice says a row may have changed", visible(page).includes("A row marked unknown may have changed"));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

// --- 4. a malformed standing.json: the build still stops ---------------------
// Older is tolerated; malformed is not. bad/standing.json has state "yellow".
console.log("\n# building against a malformed standing.json (expect the build to stop)");
withStanding(join(HERE, "fixtures", "bad", "standing.json"), (tmp) => {
  let reason = null;
  try {
    execFileSync(ASTRO, ["build"], {
      cwd: ROOT,
      env: { ...process.env, UVULARIA_PUBLISHED_BASE: tmp },
      stdio: "pipe",
      encoding: "utf8",
    });
  } catch (err) {
    reason = `${err.stdout || ""}${err.stderr || ""}`;
  }
  expect("malformed standing stops the build", reason !== null);
  expect("the build stops on the schema check", /standing does not match its schema/.test(reason || ""));
});

console.log("");
if (failures) {
  console.error(`${failures} board test(s) failed.`);
  process.exit(1);
}
console.log("all board tests passed.");
