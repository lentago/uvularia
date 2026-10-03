// Prefix an in-site path with Astro's configured base, so links work whether the
// site is served at a domain root ("/") or under a project path ("/<org>-site/").
const BASE = import.meta.env.BASE_URL; // always has a trailing slash

export function url(path = "") {
  return BASE.replace(/\/$/, "") + "/" + String(path).replace(/^\//, "");
}
