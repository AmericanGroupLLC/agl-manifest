---
name: daily-standup
description: "Morning stand-up for the AI office — refresh measured state, write the report, open issues for failures, list founder decisions. Use first thing each day or when asked 'standup'."
---

1. Refresh what Apple holds and the gates (each command from the agl-manifest root):
   - `. scripts/testflight/env.sh && bundle exec ruby scripts/asc_build_state.rb`
   - `bundle exec ruby scripts/testflight/asc_screenshots.rb && python3 scripts/screenshot_audit.py`
   - `python3 scripts/apple_requirements.py`
   - `python3 scripts/monitor_domains.py`
2. `python3 ai-office/scripts/standup.py` → `ai-office/reports/<date>-standup.md`.
3. For every failing automation or gate without an open issue, open one:
   `gh issue create -R AmericanGroupLLC/agl-manifest -l ai-office -t "<what failed>" -b "<evidence>"`,
   and assign the owning role in the body (see `.claude/agents/`).
4. Hand the report to the chief-of-staff: what moved, what is blocked, the
   "Waiting on the founder" list. Never mark anything done without evidence.
