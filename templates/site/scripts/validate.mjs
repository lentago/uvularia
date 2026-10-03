// A tiny JSON Schema (draft 2020-12 subset) validator, in JavaScript.
//
// WHY THIS EXISTS. The uvularia core ships a stdlib-only Python validator at
// core/schema/check_examples.py. This site template is a single-toolchain
// Node/Astro repo — a maintainer installs Node and runs `npm run build`, nothing
// else. Rather than drag a Python runtime and the whole core into the site, this
// file re-implements *only the subset of JSON Schema the bundle and standing
// schemas use* — a direct port of that Python `validate()`. The two schema files
// it checks against are vendored verbatim in ../schema/ (see schema/README.md),
// so the rules are the canonical rules; only the engine is re-expressed here.
//
// Supported keywords (same subset as the Python original): type (incl. unions and
// null, integer vs. number, boolean exclusion), enum, const, pattern, minLength,
// maxLength, minimum, maximum, minItems, maxItems, properties, required,
// additionalProperties (boolean), items, allOf, anyOf, oneOf, not, if/then/else,
// and local $ref ("#/$defs/...").
//
// Returns an array of human-readable error strings; empty means valid.

function typeOk(instance, t) {
  switch (t) {
    case "object":
      return instance !== null && typeof instance === "object" && !Array.isArray(instance);
    case "array":
      return Array.isArray(instance);
    case "string":
      return typeof instance === "string";
    case "integer":
      return typeof instance === "number" && Number.isInteger(instance);
    case "number":
      return typeof instance === "number";
    case "boolean":
      return typeof instance === "boolean";
    case "null":
      return instance === null;
    default:
      throw new Error(`unknown type keyword in schema: ${JSON.stringify(t)}`);
  }
}

function resolveRef(ref, root) {
  if (!ref.startsWith("#/")) {
    throw new Error(`only local refs are supported, got ${JSON.stringify(ref)}`);
  }
  let node = root;
  for (let part of ref.slice(2).split("/")) {
    part = part.replace(/~1/g, "/").replace(/~0/g, "~");
    node = node[part];
  }
  return node;
}

function typeName(instance) {
  if (instance === null) return "null";
  if (Array.isArray(instance)) return "array";
  if (Number.isInteger(instance)) return "integer";
  return typeof instance;
}

export function validate(schema, instance, root, path = "$") {
  const errors = [];

  if (schema === true) return errors;
  if (schema === false) return [`${path}: schema forbids any value here`];

  if ("$ref" in schema) {
    errors.push(...validate(resolveRef(schema.$ref, root), instance, root, path));
    const rest = { ...schema };
    delete rest.$ref;
    if (Object.keys(rest).length) errors.push(...validate(rest, instance, root, path));
    return errors;
  }

  if ("type" in schema) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((t) => typeOk(instance, t))) {
      return [`${path}: expected type ${JSON.stringify(schema.type)}, got ${typeName(instance)}`];
    }
  }

  if ("const" in schema && !deepEqual(instance, schema.const)) {
    errors.push(`${path}: expected const ${JSON.stringify(schema.const)}, got ${JSON.stringify(instance)}`);
  }

  if ("enum" in schema && !schema.enum.some((v) => deepEqual(v, instance))) {
    errors.push(`${path}: ${JSON.stringify(instance)} is not one of ${JSON.stringify(schema.enum)}`);
  }

  if (typeof instance === "string") {
    // new RegExp(p).test(s) is unanchored, matching Python's re.search.
    if ("pattern" in schema && !new RegExp(schema.pattern).test(instance)) {
      errors.push(`${path}: ${JSON.stringify(instance)} does not match pattern ${JSON.stringify(schema.pattern)}`);
    }
    if ("minLength" in schema && instance.length < schema.minLength) {
      errors.push(`${path}: shorter than minLength ${schema.minLength}`);
    }
    if ("maxLength" in schema && instance.length > schema.maxLength) {
      errors.push(`${path}: longer than maxLength ${schema.maxLength}`);
    }
  }

  if (typeof instance === "number") {
    if ("minimum" in schema && instance < schema.minimum) {
      errors.push(`${path}: ${instance} is below minimum ${schema.minimum}`);
    }
    if ("maximum" in schema && instance > schema.maximum) {
      errors.push(`${path}: ${instance} is above maximum ${schema.maximum}`);
    }
  }

  if (Array.isArray(instance)) {
    if ("minItems" in schema && instance.length < schema.minItems) {
      errors.push(`${path}: fewer than minItems ${schema.minItems}`);
    }
    if ("maxItems" in schema && instance.length > schema.maxItems) {
      errors.push(`${path}: more than maxItems ${schema.maxItems}`);
    }
    if ("items" in schema) {
      instance.forEach((element, i) => {
        errors.push(...validate(schema.items, element, root, `${path}[${i}]`));
      });
    }
  }

  if (instance !== null && typeof instance === "object" && !Array.isArray(instance)) {
    for (const name of schema.required || []) {
      if (!(name in instance)) errors.push(`${path}: missing required property '${name}'`);
    }
    const props = schema.properties || {};
    for (const [name, subschema] of Object.entries(props)) {
      if (name in instance) errors.push(...validate(subschema, instance[name], root, `${path}.${name}`));
    }
    if (schema.additionalProperties === false) {
      for (const name of Object.keys(instance)) {
        if (!(name in props)) errors.push(`${path}: property '${name}' is not allowed`);
      }
    }
  }

  if ("allOf" in schema) {
    for (const sub of schema.allOf) errors.push(...validate(sub, instance, root, path));
  }
  if ("anyOf" in schema) {
    if (schema.anyOf.every((sub) => validate(sub, instance, root, path).length)) {
      errors.push(`${path}: does not match any of the anyOf branches`);
    }
  }
  if ("oneOf" in schema) {
    const matched = schema.oneOf.filter((sub) => validate(sub, instance, root, path).length === 0).length;
    if (matched !== 1) errors.push(`${path}: matched ${matched} of the oneOf branches, exactly 1 required`);
  }
  if ("not" in schema && validate(schema.not, instance, root, path).length === 0) {
    errors.push(`${path}: must not match the 'not' schema`);
  }

  if ("if" in schema) {
    if (validate(schema.if, instance, root, path).length === 0) {
      if ("then" in schema) errors.push(...validate(schema.then, instance, root, path));
    } else if ("else" in schema) {
      errors.push(...validate(schema.else, instance, root, path));
    }
  }

  return errors;
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (a && b && typeof a === "object") {
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const ka = Object.keys(a), kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    return ka.every((k) => deepEqual(a[k], b[k]));
  }
  return false;
}
