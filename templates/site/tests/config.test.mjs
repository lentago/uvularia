// A template sync must never break a client's site.config.ts.
//
// The template owns src/config-schema.ts (what the settings are) and
// src/config.ts (how the site reads them). The client owns site.config.ts (the
// values) and never overwrites it on a sync. So for each fixture below, this
// copies the template into a scratch directory, swaps in the fixture as
// site.config.ts, and runs the same `astro check` and `astro build` the client's
// build-check runs:
//
//   pre-49           values-only, written before askUrl/askDisclaimer existed →
//                    must type-check and build, with no Ask box on the page
//   legacy-pre-51    the old file verbatim (interface inside, default export) →
//                    must type-check and build
//   misspelled       a misspelled setting (askURL) → `astro check` must FAIL,
//                    proving the type-check can catch a bad config
//
//   node tests/config.test.mjs
//
// No network: the builds read the local good fixture via UVULARIA_PUBLISHED_BASE.

import { spawnSync } from "node:child_process";
import { cpSync, copyFileSync, existsSync, mkdtempSync, readFileSync, rmSync, symlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative, sep } from "node:path";
import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ASTRO = join(ROOT, "node_modules", ".bin", "astro");
const GOOD = join(HERE, "fixtures", "good");
const FIXTURES = join(HERE, "fixtures", "config");

// Never copied into the scratch site: dependencies are linked, build output and
// fetched artifacts are regenerated, and the tests are not part of the site.
const SKIP = new Set(["node_modules", "dist", ".astro", ".published", "tests"]);

let failures = 0;
function expect(label, cond) {
  if (cond) console.log(`ok    ${label}`);
  else {
    failures++;
    console.log(`FAIL  ${label}`);
  }
}

function scratchSite(fixture) {
  const dir = mkdtempSync(join(tmpdir(), "uvularia-site-config-"));
  cpSync(ROOT, dir, {
    recursive: true,
    filter: (src) => {
      const top = relative(ROOT, src).split(sep)[0];
      return !SKIP.has(top);
    },
  });
  symlinkSync(join(ROOT, "node_modules"), join(dir, "node_modules"), "dir");
  copyFileSync(join(FIXTURES, fixture), join(dir, "site.config.ts"));
  return dir;
}

function astro(dir, args) {
  const env = { ...process.env, UVULARIA_PUBLISHED_BASE: GOOD };
  delete env.UVULARIA_ASK_URL; // the fixture's own askUrl (or its absence) decides
  const r = spawnSync(ASTRO, args, { cwd: dir, env, encoding: "utf8" });
  return { ok: r.status === 0, out: `${r.stdout || ""}${r.stderr || ""}` };
}

function survives(fixture, orgName) {
  console.log(`\n# ${fixture}: must type-check and build`);
  const dir = scratchSite(fixture);
  try {
    const check = astro(dir, ["check"]);
    if (!check.ok) console.log(check.out);
    expect(`${fixture} passes astro check`, check.ok);

    const build = astro(dir, ["build"]);
    if (!build.ok) console.log(build.out);
    expect(`${fixture} builds`, build.ok);

    const home = join(dir, "dist", "index.html");
    const html = existsSync(home) ? readFileSync(home, "utf8") : "";
    expect(`${fixture} → the home page carries the fixture's orgName`, html.includes(orgName));
    expect(`${fixture} → no askUrl means no Ask box`, html !== "" && !/data-ask/.test(html));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

survives("pre-49.site.config.ts", "Older Values Org");
survives("legacy-pre-51.site.config.ts", "Pre-Schema Org");

console.log("\n# misspelled.site.config.ts: astro check must fail");
{
  const dir = scratchSite("misspelled.site.config.ts");
  try {
    const check = astro(dir, ["check"]);
    expect("a misspelled setting fails astro check", !check.ok);
    // Strip colour codes; the error must be in site.config.ts and name askURL.
    const plain = check.out.replace(/\x1b\[[0-9;]*m/g, "");
    expect("the failure is in site.config.ts and names askURL", /site\.config\.ts:\d+:\d+ - error[\s\S]*askURL/.test(plain));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

console.log("");
if (failures) {
  console.error(`${failures} config test(s) failed.`);
  process.exit(1);
}
console.log("all config tests passed.");
