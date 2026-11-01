// How current the board is. A standing row is true only as of the instant it was
// evaluated: with nothing new published, an amber still turns red the day its
// deadline passes. The vault re-evaluates four times a day; a row evaluated more
// than FRESH_HOURS ago is shown as "unknown", never as the colour it last had.
// The same limit as FRESH_HOURS in the vault's core/evaluate.py
// (core/schema/README.md, "standing.schema.json").

export const FRESH_HOURS = 24;

// When the board was evaluated, as an ISO string, or null if nothing says. The
// rows' own evaluated_at (the oldest, if they ever differ). A vault whose core
// predates the field evaluated only when it published, so the bundle's
// published_at stands in for it.
/**
 * @param {Array<{ evaluated_at?: string }> | null} rows
 * @param {{ published_at?: string } | null} bundle
 * @returns {string | null}
 */
export function evaluatedAt(rows, bundle) {
  if (rows && rows.length && rows.every((r) => r.evaluated_at && !isNaN(Date.parse(r.evaluated_at)))) {
    return rows.map((r) => /** @type {string} */ (r.evaluated_at))
      .reduce((a, b) => (Date.parse(a) <= Date.parse(b) ? a : b));
  }
  const at = bundle?.published_at;
  return at && !isNaN(Date.parse(at)) ? at : null;
}

// The build's clock. UVULARIA_NOW pins it for the tests, like evaluate.py --now.
export function buildNow() {
  const pinned = process.env.UVULARIA_NOW;
  return pinned ? Date.parse(pinned) : Date.now();
}

// True when the board was evaluated more than FRESH_HOURS before `now`, or when
// nothing says when it was evaluated.
/**
 * @param {string | null} evaluated
 * @param {number} now  milliseconds since the epoch
 */
export function isStale(evaluated, now) {
  const at = evaluated ? Date.parse(evaluated) : NaN;
  return isNaN(at) || now - at > FRESH_HOURS * 3600 * 1000;
}

// "1 November 2026, 06:17 UTC"
/** @param {string} iso */
export function words(iso) {
  const d = new Date(iso);
  const month = d.toLocaleString("en-GB", { month: "long", timeZone: "UTC" });
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${d.getUTCDate()} ${month} ${d.getUTCFullYear()}, ${hh}:${mm} UTC`;
}
