// How current the board is. A standing row is true only as of the instant it was
// evaluated: with nothing new published, an amber still turns red the day its
// deadline passes. Each row says until when it stays current (valid_until: the
// next UTC midnight if it would change then, otherwise a day after it was
// evaluated). Past that, the board shows it as "unknown", never as the colour it
// last had. FRESH_HOURS is the vault core's limit (core/evaluate.py), used here
// only for rows from an older core that carry no valid_until.

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

// When a row stops being current, as an ISO string, or null if nothing says: its
// own valid_until, or for an older core's row, FRESH_HOURS after the board was
// evaluated.
/**
 * @param {{ valid_until?: string }} row
 * @param {string | null} evaluated
 * @returns {string | null}
 */
export function rowLapse(row, evaluated) {
  if (row.valid_until && !isNaN(Date.parse(row.valid_until))) return row.valid_until;
  const at = evaluated ? Date.parse(evaluated) : NaN;
  return isNaN(at) ? null : new Date(at + FRESH_HOURS * 3600 * 1000).toISOString().replace(/\.\d{3}Z$/, "Z");
}

// True when `now` is past the row's lapse, or when nothing says when it lapses.
/**
 * @param {string | null} lapse
 * @param {number} now  milliseconds since the epoch
 */
export function isStale(lapse, now) {
  const at = lapse ? Date.parse(lapse) : NaN;
  return isNaN(at) || now > at;
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
