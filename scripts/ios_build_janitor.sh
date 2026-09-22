#!/bin/zsh
# Reclaim disk while a long iOS sweep runs.
#
# Each app leaves ~240 MB of build/ behind and DerivedData grows without bound;
# a 43-app sweep exhausted a 900 GB disk twice and killed the run mid-build.
#
# Two rules learned the hard way:
#   * never touch the app currently building — deleting its tree under
#     xcodebuild fails the build;
#   * never delete *.noindex from DerivedData. Those are shared Xcode caches,
#     not per-project output. Removing SDKStatCaches.noindex mid-sweep failed a
#     build with "Stat cache file ... not found".
#
#   scripts/ios_build_janitor.sh ~/agl/.dist/ios-logs/rebuild.log
LOG="${1:?usage: ios_build_janitor.sh <build-log-path>}"
DD=~/Library/Developer/Xcode/DerivedData
while pgrep -f '[b]uild_ipa.py' >/dev/null; do
  current=$(grep -E '^\[[0-9]+/' "$LOG" 2>/dev/null | tail -1 |
            sed -E 's/^\[[0-9]+\/[0-9]+\] ([^ ]+).*/\1/')
  for d in /Users/spatchava/agl/*/build /Users/spatchava/agl/*/*/build; do
    [ -d "$d" ] || continue
    repo=$(echo "$d" | sed 's|/Users/spatchava/agl/||; s|/.*||')
    [ "$repo" = "$current" ] && continue
    rm -rf "$d" 2>/dev/null
  done
  for p in $DD/*(N/); do
    case "${p:t}" in *.noindex) continue ;; esac
    [ -z "$(find "$p" -maxdepth 0 -mmin -8)" ] && rm -rf "$p" 2>/dev/null
  done
  sleep 70
done
