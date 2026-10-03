// Builds the site twice and inspects the rendered /board/ HTML:
//
//   1. with the good fixture — a two-record bundle and a standing.json carrying
//      one row per state — and asserts every state's WORD appears, each
//      obligation id appears, and a green badge is actually rendered.
//   2. with standing.json ABSENT — and asserts the board falls back to "no data"
//      and renders NO green badge (invariant 5: never a fake green).
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

function build(base) {
  rmSync(join(ROOT, "dist"), { recursive: true, force: true });
  execFileSync(ASTRO, ["build"], {
    cwd: ROOT,
    env: { ...process.env, UVULARIA_PUBLISHED_BASE: base },
    stdio: "inherit",
  });
  if (!existsSync(BOARD)) throw new Error(`build produced no board page at ${BOARD}`);
  return readFileSync(BOARD, "utf8");
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

console.log("");
if (failures) {
  console.error(`${failures} board test(s) failed.`);
  process.exit(1);
}
console.log("all board tests passed.");
