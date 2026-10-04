// Proves the schema validation the build relies on actually passes the good
// artifacts and FAILS the bad ones — a check that cannot fail is not a check.
//
//   node tests/schema.test.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { validate } from "../scripts/validate.mjs";
import { missingOptionalFields } from "../scripts/fetch-published.mjs";

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

// The previous release's standing (rows without history) still validates — a
// site newer than its vault's core must build — and the build step can tell it
// is older: history is the optional field it leaves out. The current good file
// leaves nothing out.
expect(
  "previous-release standing.json (no history) validates",
  validate(standingSchema, fixture("previous", "standing.json"), standingSchema).length === 0,
);
expect(
  "previous-release standing.json is seen as older: missing optional field 'history'",
  JSON.stringify(missingOptionalFields(standingSchema, fixture("previous", "standing.json"))) === '["history"]',
);
expect(
  "current standing.json is not seen as older",
  missingOptionalFields(standingSchema, fixture("good", "standing.json")).length === 0,
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
