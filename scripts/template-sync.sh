#!/usr/bin/env bash
# ============================================================================
# template-sync.sh — copy one template subtree onto a branch of its template repo
# ============================================================================
# Usage: scripts/template-sync.sh <subtree> <target-repo-url> <branch> [<source-sha>]
#
#   subtree          templates/records | templates/ask-rules | templates/site
#   target-repo-url  the template repository: an https URL (with a token when
#                    pushing from Actions) or a file:// path (the tests)
#   branch           the branch to create or update on the target, e.g. sync/ab12cd3
#   source-sha       recorded in the commit message; defaults to the source HEAD
#
# The branch is built FROM THE TARGET'S DEFAULT BRANCH and the subtree is copied
# over it (rsync --delete, .git excluded), so the pull request is a plain content
# diff. Pushing a `git subtree split` history instead conflicts with the target's
# squash-merged history after the first sync (uvularia#28); this never does.
#
# Prints `changed=true` or `changed=false` (and appends the same to
# $GITHUB_OUTPUT when set). Exit 0 either way; non-zero only on a real failure.
# Reads the source tree, never writes to it. TEMPLATE_SYNC_SOURCE overrides the
# source checkout (the tests point it at a fixture).
# ============================================================================
set -euo pipefail

subtree="${1:?usage: template-sync.sh <subtree> <target-repo-url> <branch> [<source-sha>]}"
url="${2:?target repo url}"
branch="${3:?branch}"
src_root="${TEMPLATE_SYNC_SOURCE:-$(git rev-parse --show-toplevel)}"
sha="${4:-$(git -C "$src_root" rev-parse --short HEAD)}"

if [ ! -d "$src_root/$subtree" ]; then
  echo "template-sync: no such subtree: $src_root/$subtree" >&2
  exit 2
fi

work="$(mktemp -d)"
trap 'rm -rf "${work:?}"' EXIT

git clone --quiet "$url" "$work/repo"
cd "$work/repo" || exit 1
default="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || true)"
default="${default:-main}"
git checkout --quiet -B "$branch" "origin/$default"

# --checksum: rsync's default quick check (size + mtime) skips a changed file of the
# same length written in the same second; content is what must match here.
rsync -a --delete --checksum --exclude .git --exclude __pycache__ "$src_root/$subtree/" ./
git add -A

out() { echo "changed=$1"; if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "changed=$1" >> "$GITHUB_OUTPUT"; fi; }

if git diff --cached --quiet; then
  echo "template-sync: $subtree already matches $url ($default)"
  out false
  exit 0
fi

git -c user.name="${GIT_AUTHOR_NAME:-lentago-template-sync[bot]}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-lentago-template-sync[bot]@users.noreply.github.com}" \
    commit --quiet -m "Sync from lentago/uvularia@${sha}" \
    -m "Content of ${subtree} at lentago/uvularia@${sha}, copied over this repository's ${default}."
git push --quiet --force-with-lease origin "$branch"
echo "template-sync: pushed $branch to $url ($(git diff --stat "origin/$default" HEAD | tail -1 | sed 's/^ //'))"
out true
