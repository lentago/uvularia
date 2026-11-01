// The Ask box's rendering, as a pure function: one turn (the question, the HTTP
// status, the parsed reply) in, one HTML string out. No DOM, no network, no
// storage — the widget's browser script (components/Ask.astro) does those and
// calls this, and tests/ask.test.mjs calls it directly with fixture replies.
//
// The reply contract is the Ask function's (templates/ask-function/src/handler.py):
//   { kind: answered|incident|escalated|declined|maintenance,
//     reply: string, source_ids: string[], degraded_signals: string[] }
// with status 200, 403 (wrong origin / failed bot check), 429 (daily cap reached),
// or 503 (not set up yet). Anything else — a network failure, a non-JSON body —
// is treated as "the Ask box is off", never as an answer.
//
// Citations: ONLY the ids in the reply's source_ids are shown. The function's
// citation gate has already dropped any id that is not a real record, and the
// function sends no "answered" reply without one; this side links an id only
// when this site has a page for it, and shows it as plain text otherwise.
// Nothing the widget sent is ever echoed back as a source.
//
// A real id means the record exists, not that it says what the reply says. So
// wherever sources are shown, the reader is asked to check them, and the way to
// reach the organization (ctx.contact, from site.config.ts) sits beside them.

// Each outcome in words. The word is what a reader scans for; the line says what
// it means for them.
export const OUTCOMES = {
  answered: { word: "Answered", line: "Linked to the published records it cites." },
  incident: { word: "Incident", line: "There is an active notice that affects this question. Read it first." },
  escalated: { word: "Escalated", line: "This one needs a person. Please contact the organization directly." },
  declined: { word: "Declined", line: "This box only answers questions about the published records." },
};

export const MAINTENANCE_LINE = "The Ask box is off right now. The records and the board are still available.";
export const CAP_LINE = "The Ask box has answered all the questions it can for today. Please try again tomorrow.";
export const CHECK_LINE = "Check the linked records before you rely on this answer.";

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ESC[c]);
}

// Plain text with paragraph breaks. The reply is never treated as HTML.
function paragraphs(text) {
  return String(text)
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => `<p>${escapeHtml(p).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function strings(list) {
  if (!Array.isArray(list)) return [];
  return [...new Set(list.filter((x) => typeof x === "string" && x.trim()))];
}

// The escalation path, as the end of a sentence: how to reach the organization.
// The contact is site.config.ts's (an email address or a web address). It is
// linked only as mailto: or http(s):, and said in words when there is none.
export function contactHtml(contact) {
  const c = typeof contact === "string" ? contact.trim() : "";
  if (!c) return "contact the organization directly.";
  const href = /^https?:\/\//i.test(c) ? c : /^[^\s:/@]+@[^\s:/@]+$/.test(c) ? `mailto:${c}` : "";
  const shown = escapeHtml(c);
  return href ? `contact the organization: <a href="${escapeHtml(href)}">${shown}</a>.` : `contact the organization: ${shown}.`;
}

// Decide what a turn IS, from the status and the body alone.
//   → { kind, reply, sourceIds, degraded }
// kind is one of the four outcomes, or "maintenance" / "capped" / "off".
export function classify(status, body) {
  const b = body && typeof body === "object" ? body : {};
  const reply = typeof b.reply === "string" ? b.reply : "";
  if (status === 429) return { kind: "capped", reply: "", sourceIds: [], degraded: [] };
  if (status === 503 || b.kind === "maintenance") return { kind: "maintenance", reply, sourceIds: [], degraded: [] };
  if ((status === 200 || status === 400 || status === 403) && Object.hasOwn(OUTCOMES, b.kind)) {
    // Only an answer or an incident carries citations; a refusal never does.
    const cites = b.kind === "answered" || b.kind === "incident";
    return {
      kind: b.kind,
      reply,
      sourceIds: cites ? strings(b.source_ids) : [],
      degraded: strings(b.degraded_signals),
    };
  }
  return { kind: "off", reply: "", sourceIds: [], degraded: [] };
}

// ctx: { recordsBase: "/<org>-site/records/", knownIds: Set<string> | string[],
//        contact?: string }
export function renderTurn(turn, ctx) {
  const { question, status, body } = turn;
  const recordsBase = ctx.recordsBase;
  const known = ctx.knownIds instanceof Set ? ctx.knownIds : new Set(ctx.knownIds || []);
  const t = classify(status, body);
  const out = [];

  out.push(`<div class="ask-turn" data-kind="${escapeHtml(t.kind)}">`);
  out.push(`<p class="ask-q"><strong>You asked:</strong> ${escapeHtml(question)}</p>`);

  if (t.kind === "capped" || t.kind === "maintenance" || t.kind === "off") {
    const line = t.kind === "capped" ? CAP_LINE : MAINTENANCE_LINE;
    out.push(`<p class="ask-status"><span class="ask-word">${t.kind === "capped" ? "Limit reached" : "Off"}</span> ${escapeHtml(line)}</p>`);
    if (t.kind === "maintenance" && t.reply) out.push(`<div class="ask-reply muted">${paragraphs(t.reply)}</div>`);
    out.push(`<p class="muted">In the meantime, <a href="${escapeHtml(recordsBase)}">browse the records index</a>.</p>`);
    out.push(`</div>`);
    return out.join("");
  }

  const o = OUTCOMES[t.kind];
  // An incident's banner comes first, before anything else about the answer.
  if (t.kind === "incident") {
    out.push(`<div class="ask-banner" role="alert"><strong>Active notice.</strong> ${paragraphs(t.reply) || ""}</div>`);
  }
  out.push(`<p class="ask-status"><span class="ask-word">${o.word}</span> ${escapeHtml(o.line)}</p>`);
  if (t.kind !== "incident" && t.reply) out.push(`<div class="ask-reply">${paragraphs(t.reply)}</div>`);

  if (t.sourceIds.length) {
    out.push(`<p class="ask-sources-h"><strong>Sources</strong></p><ul class="ask-sources">`);
    for (const id of t.sourceIds) {
      out.push(
        known.has(id)
          ? `<li><a href="${escapeHtml(recordsBase + encodeURIComponent(id) + "/")}"><code>${escapeHtml(id)}</code></a></li>`
          : `<li><code>${escapeHtml(id)}</code> <span class="muted">(not on this site yet)</span></li>`,
      );
    }
    out.push(`</ul>`);
    // The sources and the escalation path, together.
    out.push(`<p class="muted ask-check">${escapeHtml(CHECK_LINE)} If they don't settle it, ${contactHtml(ctx.contact)}</p>`);
  } else if (t.kind === "escalated") {
    out.push(`<p class="ask-contact">To ask a person, ${contactHtml(ctx.contact)}</p>`);
  }

  if (t.degraded.length) {
    out.push(
      `<p class="muted ask-degraded">Some live checks could not be reached (${t.degraded.map(escapeHtml).join(", ")}). ` +
        `This answer may not reflect the very latest notices.</p>`,
    );
  }

  out.push(`</div>`);
  return out.join("");
}
