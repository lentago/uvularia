// The shapes of the published artifacts, named once. The data is read from JSON
// at build time (lib/published.mjs); these types describe it so the pages and
// components that render it are type-checked.

// A standing row's state (schema/standing.schema.json).
export type State = "green" | "amber" | "red" | "no-data";

// One bundle entry (schema/bundle.schema.json).
export interface Entry {
  doc_id: string;
  title: string;
  tags: string[];
  volatility: string;
  body: string;
  path: string;
  certainty: string;
  archived: boolean;
}

// The corpus bundle (schema/bundle.schema.json), as far as the site reads it.
export interface Bundle {
  digest: string;
  records: Entry[];
}

// Published records grouped by record type.
export type Groups = Record<string, Entry[]>;

// A standing row's track record over a trailing window (schema/standing.schema.json).
export interface History {
  window_days: number;
  evaluated: number;
  breaches: number;
}

// One standing row (schema/standing.schema.json). `history` is optional until
// the release after it landed: an older vault omits it.
export interface Row {
  id: string;
  state: State;
  satisfied_by: string | null;
  deadline: string | null;
  published_at: string | null;
  gap: number | null;
  history?: History | null;
}

// The receipt fields the site reads (lib/published.mjs parseReceipt).
export interface Receipt {
  digest?: string;
  published_at?: string;
  run_url?: string;
  commit?: string;
  records: { added: string[]; changed: string[]; retracted: string[] };
}

// What the build step recorded about the fetch (scripts/fetch-published.mjs).
export interface Meta {
  fetched_at: string | null;
  source: string | null;
  present: Record<string, boolean>;
}

// The Ask function's reply fields (templates/ask-function/src/handler.py).
export interface AskBody {
  kind: string;
  reply: string;
  source_ids: string[];
  degraded_signals: string[];
}

// One question and what came back: status 0 is "unreachable".
export interface AskTurn {
  question: string;
  status: number;
  body: AskBody | null;
}
