// The Ask box's two settings, read at build time from site.config.ts (via
// src/config.ts, which accepts every shape that file has had).
//
// UVULARIA_ASK_URL overrides askUrl when it is set (even to ""), the same way
// UVULARIA_PUBLISHED_BASE overrides the data source — the tests use it to build
// the page with and without the widget. An empty askUrl means no widget at all.
import { config } from "../config.ts";

export function askUrl() {
  const fromEnv = process.env.UVULARIA_ASK_URL;
  return String(fromEnv !== undefined ? fromEnv : config.askUrl || "").trim();
}

export function askDisclaimer() {
  return String(config.askDisclaimer || "").trim();
}
