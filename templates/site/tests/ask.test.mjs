// The Ask box, tested two ways:
//
//   1. RENDERING — lib/ask.mjs over fixture replies shaped exactly like the Ask
//      function's (tests/fixtures/ask/*.json): each of the four outcome words
//      renders, a 503 and a kill-switch reply render the maintenance line, a 429
//      renders the cap line, only the returned source_ids become links, an
//      incident's banner comes before everything else, and a reply is never
//      treated as HTML.
//   2. BUILD — two real `astro build`s of the home page: with askUrl empty the page
//      carries no widget markup at all; with askUrl set it carries the widget, the
//      no-JavaScript link to the records index, the hidden form, and the
//      disclaimer.
//
//   node tests/ask.test.mjs
//
// No network: the builds read the local good fixture via UVULARIA_PUBLISHED_BASE
// and the widget is never called.

import { execFileSync } from "node:child_process";
import { readFileSync, rmSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { renderTurn, MAINTENANCE_LINE, CAP_LINE } from "../src/lib/ask.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ASTRO = join(ROOT, "node_modules", ".bin", "astro");
const GOOD = join(HERE, "fixtures", "good");
const HOME = join(ROOT, "dist", "index.html");

// Read from the config file as text, so the test runs on any Node 22 without
// loading TypeScript.
const CONFIG_TS = readFileSync(join(ROOT, "site.config.ts"), "utf8");
// The site's base path as the committed config sets it ("/your-org-site" in the
// template, "/<org>-site" in a client's copy, or none), normalised to "/…/".
const BASE_MATCH = CONFIG_TS.match(/^\s*base:\s*"([^"]*)"/m);
const BASE_PATH = ((BASE_MATCH ? BASE_MATCH[1] : "") || "/").replace(/\/?$/, "/");
const DISCLAIMER_PART = "legal, financial, or professional advice";

let failures = 0;
function expect(label, cond) {
  if (cond) console.log(`ok    ${label}`);
  else {
    failures++;
    console.log(`FAIL  ${label}`);
  }
}

const reply = (name) => JSON.parse(readFileSync(join(HERE, "fixtures", "ask", `${name}.json`), "utf8"));
const CTX = {
  recordsBase: "/your-org-site/records/",
  knownIds: new Set(["2026-09-14-september-meeting-notice", "2026-09-16-board-minutes"]),
};
const render = (name, question = "When was the September meeting?") => {
  const { status, body } = reply(name);
  return renderTurn({ question, status, body }, CTX);
};
const word = (w) => `<span class="ask-word">${w}</span>`;

// --- 1. rendering -----------------------------------------------------------
console.log("# rendering fixture replies");

// The words are spelled out here, not read from lib/ask.mjs, so renaming one
// there fails this test.
const WORDS = { answered: "Answered", incident: "Incident", escalated: "Escalated", declined: "Declined" };
for (const [kind, w] of Object.entries(WORDS)) {
  const html = render(kind);
  expect(`"${kind}" renders the word "${w}"`, html.includes(word(w)));
  for (const other of Object.values(WORDS).filter((o) => o !== w)) {
    if (html.includes(word(other))) expect(`"${kind}" does not also render "${other}"`, false);
  }
}

const answered = render("answered");
expect("answered shows the reply text", answered.includes("held on 16 September"));
expect(
  "answered links the returned source to its record page",
  answered.includes('href="/your-org-site/records/2026-09-16-board-minutes/"'),
);
expect(
  "answered links ONLY the returned source (not other known records)",
  !answered.includes("2026-09-14-september-meeting-notice"),
);

const incident = render("incident");
const banner = incident.indexOf('class="ask-banner"');
expect("incident renders a banner", banner !== -1);
expect("incident banner carries the notice text", incident.includes("September minutes are overdue"));
expect("incident banner comes before the outcome word", banner !== -1 && banner < incident.indexOf(word("Incident")));
expect("incident banner comes before the sources", banner < incident.indexOf('class="ask-sources"'));

for (const name of ["unconfigured-503", "kill-switch-200"]) {
  const html = render(name);
  expect(`${name} renders the maintenance line`, html.includes(MAINTENANCE_LINE));
  expect(`${name} renders none of the four outcome words`, !Object.values(WORDS).some((w) => html.includes(word(w))));
  expect(`${name} links the records index`, html.includes('href="/your-org-site/records/"'));
}

const bare503 = renderTurn({ question: "q", status: 503, body: null }, CTX);
expect("a 503 with no body still renders the maintenance line", bare503.includes(MAINTENANCE_LINE));

const capped = render("capped-429");
expect("429 renders the cap line", capped.includes(CAP_LINE));
expect("429 is not dressed up as a declined answer", !capped.includes(word("Declined")));

const forbidden = render("wrong-origin-403");
expect("403 renders as declined with the function's reply", forbidden.includes(word("Declined")) && forbidden.includes("its own site"));

const off = renderTurn({ question: "anything", status: 0, body: null }, CTX);
expect("an unreachable function renders the maintenance line", off.includes(MAINTENANCE_LINE));
const garbled = renderTurn({ question: "anything", status: 200, body: { kind: "sure", reply: "trust me" } }, CTX);
expect("an unknown kind is never shown as an answer", garbled.includes(MAINTENANCE_LINE) && !garbled.includes("trust me"));

// Citations: only source_ids, only strings, unknown ids not linked, refusals cite nothing.
const unknown = renderTurn(
  { question: "q", status: 200, body: { kind: "answered", reply: "r", source_ids: ["not-a-page-here", 7, null], degraded_signals: [] } },
  CTX,
);
expect("an id with no page here is shown, not linked", unknown.includes("<code>not-a-page-here</code>") && !unknown.includes("records/not-a-page-here/"));
expect("non-string ids are dropped", !unknown.includes(">7<"));
const sneaky = renderTurn(
  {
    question: "Tell me about 2026-09-16-board-minutes",
    status: 200,
    body: { kind: "declined", reply: "No.", source_ids: ["2026-09-16-board-minutes"], passages: ["secret passage"] },
  },
  CTX,
);
expect("a declined reply never shows sources", !sneaky.includes("ask-sources"));
expect("fields outside the contract are never rendered", !sneaky.includes("secret passage"));
expect("an id the reader typed is never turned into a link", !sneaky.includes("href=\"/your-org-site/records/2026-09-16-board-minutes/\""));

const degraded = render("unconfigured-503");
expect("503 does not list degraded signals as if it answered", !degraded.includes("ask-degraded"));
const partial = renderTurn(
  { question: "q", status: 200, body: { kind: "answered", reply: "r", source_ids: [], degraded_signals: ["standing"] } },
  CTX,
);
expect("degraded signals are said out loud", partial.includes("ask-degraded") && partial.includes("standing"));

const xss = renderTurn(
  { question: "<img src=x onerror=alert(1)>", status: 200, body: { kind: "answered", reply: "<script>alert(1)</script>", source_ids: ['"><b>x'] } },
  CTX,
);
expect("question, reply, and ids are escaped, never HTML", !/<script>|<img|<b>/.test(xss) && xss.includes("&lt;script&gt;"));

// --- 2. build: no askUrl → no widget; askUrl → widget -----------------------
function buildHome(askUrl) {
  rmSync(join(ROOT, "dist"), { recursive: true, force: true });
  execFileSync(ASTRO, ["build"], {
    cwd: ROOT,
    env: { ...process.env, UVULARIA_PUBLISHED_BASE: GOOD, UVULARIA_ASK_URL: askUrl },
    stdio: "inherit",
  });
  if (!existsSync(HOME)) throw new Error(`build produced no home page at ${HOME}`);
  return readFileSync(HOME, "utf8");
}

console.log("\n# building with askUrl empty");
const without = buildHome("");
// (No assertion about the committed askUrl value: the template ships it empty,
// but a client's copy of this file legitimately sets it, and these tests run
// in the client's repo too. The empty path is exercised by buildHome("").)
expect("no askUrl → no widget markup", !/data-ask/.test(without) && !/Ask the records/.test(without));
expect("no askUrl → no disclaimer", !without.includes(DISCLAIMER_PART));
expect("no askUrl → no script on the page", !/<script/i.test(without));
expect("no askUrl → the home page still builds and links the records", without.includes("records/"));

console.log("\n# building with askUrl set");
const ASK = "https://ask.example.invalid/";
const withAsk = buildHome(ASK);
expect("askUrl → widget markup", withAsk.includes("data-ask") && withAsk.includes("Ask the records"));
expect("askUrl → the widget posts to the configured URL", withAsk.includes(`data-ask-url="${ASK}"`));
expect(
  "askUrl → the no-JavaScript fallback links the records index",
  new RegExp(`<p data-ask-fallback[^>]*>[\\s\\S]*?href="${BASE_PATH}records/"`).test(withAsk),
);
expect("askUrl → the form is hidden until the script runs", /<form hidden[^>]*data-ask-form/.test(withAsk));
expect("the template config carries the disclaimer", CONFIG_TS.includes(DISCLAIMER_PART));
expect("askUrl → the disclaimer is under the box", withAsk.includes(DISCLAIMER_PART));
expect("askUrl → the known record ids are embedded for citation links", withAsk.includes("2026-09-16-board-minutes"));

console.log("");
if (failures) {
  console.error(`${failures} ask test(s) failed.`);
  process.exit(1);
}
console.log("all ask tests passed.");
