# AI Office — operating manual

You are working inside the **American Group LLC AI office**. The company runs
43 mobile apps (Flutter, App Store + Google Play), a Supabase backend, and
https://www.americangroup.ai. This folder is the office; the work itself is
done with the scripts and data in the parent repo, `agl-manifest`
(`..`). Read `../CLAUDE.md` for the repo map.

## How work flows
1. A goal or issue arrives (founder message, or a GitHub issue labelled
   `ai-office` — see INBOX.md).
2. **chief-of-staff** plans it (skill: company-planning), delegates to roles in
   `.claude/agents/`, and consolidates.
3. Specialists do the work with evidence; **qa-reviewer** checks it.
4. Anything on the CHARTER's human-decision list becomes an approval request
   (skill: approval-workflow) and the office stops there.

## Standing procedures
- Daily: skill `daily-standup` (or workflow `daily-standup`).
- New rejection: skill/workflow `rejection-response`.
- Release: skill/workflow `release-train`.
- Monday: skill `weekly-review`.

## Non-negotiables (company/policies.md)
- Evidence before claims; "not verified" when you did not check.
- No fake data in apps; no demo logins; real users only.
- Check what the store checks (IPA, uploaded screenshots, live URL).
- Never `rsync --delete`, `supabase config push`, direct production SQL, or
  submission for review — `.claude/settings.json` blocks the worst of these.
- Secrets never in git or chat.

## Where things are
| Need | Path |
| --- | --- |
| Charter / decisions | CHARTER.md, company/decision-log.md |
| Staff | .claude/agents/ (34 roles) |
| Procedures | .claude/skills/, .claude/workflows/ |
| Script guide | RUNBOOKS/, ../docs/API_ACTIONS.md |
| Founder-only actions | ../docs/MANUAL_ACTIONS.md (MA-xxx) |
| Measured state | ../status.csv, ../docs/*.json |
| Reports | reports/ |
