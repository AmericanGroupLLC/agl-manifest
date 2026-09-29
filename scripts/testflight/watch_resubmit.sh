#!/bin/zsh
# Keep resubmitting the rejected apps until Apple accepts them.
#
# After a rejection the version stays attached to its submission, which sits in
# UNRESOLVED_ISSUES. Resubmitting that submission is the right call and is what
# submit_production.rb now does, but Apple answers "Version is not ready to be
# submitted yet, please try again later" for a while afterwards — all 23 said
# exactly that on 2026-09-28. There is nothing to fix; it has to be retried.
#
# Runs for 24 hours, once every 30 minutes, and stops early once nothing is
# blocked. Every attempt is appended to the log with a timestamp.
source ~/agl/agl-manifest/scripts/testflight/env.sh
cd ~/agl/agl-manifest/scripts/testflight || exit 1
LOG=~/agl/.dist/resubmit-watch.log
end=$(( $(date +%s) + 24*3600 ))
while [ $(date +%s) -lt $end ]; do
  echo "[watch_resubmit $(date '+%m-%d %H:%M')] attempt" >> "$LOG"
  bundle exec ruby submit_production.rb >> "$LOG" 2>&1
  blocked=$(grep -c "cannot resubmit yet" "$LOG".tmp 2>/dev/null || tail -40 "$LOG" | grep -c "cannot resubmit yet")
  if [ "${blocked:-0}" -eq 0 ]; then
    echo "[watch_resubmit $(date '+%m-%d %H:%M')] nothing blocked; stopping" >> "$LOG"
    break
  fi
  sleep 1800
done
