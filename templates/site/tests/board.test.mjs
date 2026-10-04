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
//
//   node tests/board.test.mjs
//
// The build is driven against local fixtures via UVULARIA_PUBLISHED_BASE, so this
// never touches the network.

import { execFileSync } from "node:child_process";
import { cpSync, mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
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

let failures = 0;
function expect(label, cond) {
  if (cond) console.log(`ok    ${label}`);
  else {
    failures++;
    console.log(`FAIL  ${label}`);
  }
}

function build(base, { log = false } = {}) {
  rmSync(join(ROOT, "dist"), { recursive: true, force: true });
  const out = execFileSync(ASTRO, ["build"], {
    cwd: ROOT,
    env: { ...process.env, UVULARIA_PUBLISHED_BASE: base },
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
expect("board renders a real green badge", good.includes(GREEN_SWATCH));
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
  expect("current state still renders (a real green badge)", board.includes(GREEN_SWATCH));
  expect("build log says the vault's core is behind", /core is behind/.test(built.log));
});

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
