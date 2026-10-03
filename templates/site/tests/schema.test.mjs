// Proves the schema validation the build relies on actually passes the good
// artifacts and FAILS the bad ones — a check that cannot fail is not a check.
//
//   node tests/schema.test.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { validate } from "../scripts/validate.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const schema = (name) => JSON.parse(readFileSync(join(HERE, "..", "schema", `${name}.schema.json`), "utf8"));
const fixture = (which, name) => JSON.parse(readFileSync(join(HERE, "fixtures", which, name), "utf8"));

let failures = 0;
function expect(label, cond) {
  if (cond) {
    console.log(`ok    ${label}`);
  } else {
    failures++;
    console.log(`FAIL  ${label}`);
  }
}

const bundleSchema = schema("bundle");
const standingSchema = schema("standing");

// Good artifacts validate.
expect(
  "good corpus-latest.json validates",
  validate(bundleSchema, fixture("good", "corpus-latest.json"), bundleSchema).length === 0,
);
expect(
  "good standing.json validates",
  validate(standingSchema, fixture("good", "standing.json"), standingSchema).length === 0,
);

// Bad artifacts FAIL — the whole point of the check.
expect(
  "bad corpus-latest.json is rejected (digest not a sha256)",
  validate(bundleSchema, fixture("bad", "corpus-latest.json"), bundleSchema).length > 0,
);
expect(
  "bad standing.json is rejected (state 'yellow' is not a valid state)",
  validate(standingSchema, fixture("bad", "standing.json"), standingSchema).length > 0,
);

console.log("");
if (failures) {
  console.error(`${failures} schema test(s) failed.`);
  process.exit(1);
}
console.log("all schema tests passed.");
