#!/bin/bash
# Wrapper for the scheduled store_watch pass.
#
# launchd runs with almost no environment: no PATH beyond /usr/bin:/bin, no
# shell profile, no AGL_ROOT. Everything the pass needs is set here, because
# a scheduled job that silently does nothing is worse than no job at all.
set -uo pipefail

MANIFEST="/Users/spatchava/agl/agl-manifest"
LOGDIR="/Users/spatchava/agl/.dist/store-watch"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/$(date +%Y%m%d-%H%M%S).log"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.rbenv/shims:$HOME/google-cloud-sdk/bin"

# ROOT flips to agl-manifest/work the moment a checkout exists there, and
# every path-derived lookup goes with it — including the Flutter SDK. Pin it.
export AGL_ROOT="/Users/spatchava/agl"
export FASTLANE_USER="srikanth.patchava@outlook.com"

cd "$MANIFEST" || exit 1

# App Store Connect credentials. Without these the pass reads nothing and
# would report an empty portfolio as though it were healthy.
# shellcheck disable=SC1091
[ -f scripts/testflight/env.sh ] && . scripts/testflight/env.sh

{
  echo "=== store_watch $(date -Iseconds) ==="
  python3 scripts/store_watch.py --remediate
  echo "=== exit $? ==="
} >>"$LOG" 2>&1

# Keep a month of passes and no more.
find "$LOGDIR" -name '*.log' -mtime +30 -delete 2>/dev/null

# A stable path for "what happened last time".
ln -sf "$LOG" "$LOGDIR/latest.log"
