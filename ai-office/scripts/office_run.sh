#!/bin/bash
# Daily unattended AI office pass, run by launchd (com.americangroupllc.aioffice)
# with the Claude Code login on this Mac — no API key needed.
#
# Runs in its own git worktree, ~/agl/.ai-office-worktree, which nothing else
# edits. It used to run in ~/agl/agl-manifest, where other sessions' uncommitted
# files sat in the tree: one autostash conflict there (docs/store-checklist.json,
# 2026-10-15) made every later `git pull` refuse, and 35 report commits piled up
# unpushed until 2026-10-17.
set -u
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.rbenv/shims:/usr/bin:/bin:$PATH"
W=/Users/spatchava/agl/.ai-office-worktree
LOGDIR=/Users/spatchava/agl/.dist/ai-office; mkdir -p "$LOGDIR"
STAMP=$(date +%Y%m%d-%H%M%S)
{
  echo "=== $(date) ==="
  # Start from what GitHub has. Rebase, not reset: a report commit whose push
  # failed last time is kept and goes out with this one.
  cd "$W" && git fetch -q origin && git rebase -q origin/master \
    || { git rebase --abort 2>/dev/null; echo "rebase onto origin/master failed; working on the old tree"; }
  cd "$W" && python3 ai-office/scripts/standup.py
  cd "$W/ai-office" && claude -p "$(cat scripts/office_prompt.md)" \
    --max-turns 40 \
    --allowedTools "Read,Glob,Grep,Write(reports/**),Bash(gh issue *),Bash(gh run list *),Bash(gh run view *),Bash(gh label list *),Bash(date *),Bash(ls *),Bash(cat *)"
  echo "=== claude exit $? ==="
  # Keep the reports in git (the stand-up issue links them).
  cd "$W" && git add ai-office/reports && git commit -q -m "AI office daily pass $(date +%Y-%m-%d)" -- ai-office/reports
  cd "$W" && git pull -q --rebase origin master && git push -q origin HEAD:master && echo "reports pushed"
} > "$LOGDIR/$STAMP.log" 2>&1
ln -sf "$LOGDIR/$STAMP.log" "$LOGDIR/latest.log"
