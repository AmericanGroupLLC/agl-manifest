#!/bin/bash
# Daily unattended AI office pass, run by launchd (com.americangroupllc.aioffice)
# with the Claude Code login on this Mac — no API key needed.
set -u
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.rbenv/shims:/usr/bin:/bin:$PATH"
M=/Users/spatchava/agl/agl-manifest
LOGDIR=/Users/spatchava/agl/.dist/ai-office; mkdir -p "$LOGDIR"
STAMP=$(date +%Y%m%d-%H%M%S)
{
  echo "=== $(date) ==="
  cd "$M" && python3 ai-office/scripts/standup.py
  cd "$M/ai-office" && claude -p "$(cat scripts/office_prompt.md)" \
    --max-turns 40 \
    --allowedTools "Read,Glob,Grep,Write(reports/**),Bash(gh issue *),Bash(gh run list *),Bash(gh run view *),Bash(gh label list *),Bash(date *),Bash(ls *),Bash(cat *)"
  echo "=== claude exit $? ==="
  # Keep the reports in git (the stand-up issue links them).
  cd "$M" && git add ai-office/reports && git commit -q -m "AI office daily pass $(date +%Y-%m-%d)" -- ai-office/reports \
    && git pull -q --rebase --autostash && git push -q && echo "reports committed"
} > "$LOGDIR/$STAMP.log" 2>&1
ln -sf "$LOGDIR/$STAMP.log" "$LOGDIR/latest.log"
