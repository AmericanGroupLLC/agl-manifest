# AI Office

An AI organisation for American Group LLC, built on Claude Code, living next to
the automation it runs (`agl-manifest`).

## Use it
```bash
cd ~/agl/agl-manifest/ai-office
claude            # the 39 roles, skills and workflows load from .claude/
```
Then ask in plain language — "run the standup", "handle the new rejection for
MyCard", "release train", "what is blocking AdMob?". The chief-of-staff routes
it.

## Departments (39 roles in `.claude/agents/`)
- **Executive:** chief-of-staff, strategy-analyst, project-coordinator, portfolio-director
- **Product & Engineering:** product-manager, technical-architect, software-developer, test-engineer, security-reviewer, release-manager, store-compliance, qa-screenshots, data-honesty, backend-supabase, web-domains, monetization, code-hygiene, privacy-engineer, appsec-engineer
- **Marketing:** marketing-manager, market-researcher, content-strategist, copywriter, seo-analyst, aso-specialist, store-creative
- **Sales & Support:** sales-manager, lead-researcher, outreach-specialist, support-analyst
- **Finance & Admin:** finance-manager, budget-analyst, business-analyst, hr-assistant
- **Operations:** operations-manager, workflow-designer, documentation-specialist, qa-reviewer, data-analyst

## Runs by itself
- `com.americangroupllc.aioffice` (launchd on this Mac): daily 07:45, refreshes the
  stand-up and has the local Claude Code login triage it — opens/updates/closes
  `ai-office` issues and writes `reports/<date>-office.md`. Load once with
  `launchctl load -w ~/Library/LaunchAgents/com.americangroupllc.aioffice.plist`.
- `ai-office-standup.yml` (agl-manifest Actions): daily 13:00 UTC, builds the
  stand-up from measured state and keeps the pinned issue "AI office: daily
  stand-up" current. No AI key needed.
- Add an `ANTHROPIC_API_KEY` repo secret to also let Claude triage the
  stand-up unattended (the job skips that step without it).

## What it will not do
See CHARTER.md: store submissions and replies, production database approval,
money, credentials, external contact, legal text, people decisions, removing
apps. It prepares them; the founder decides.

## Judgment agent (no yes/no pop-ups)

`scripts/judge.py` answers Claude Code permission prompts for the office, as a
`PermissionRequest` hook: fixed rules deny the CHARTER's founder-only actions and
known-destructive commands, allow routine work, and send anything else to a
tool-less `claude -p` (haiku) that must answer allow or deny with a reason. If
the judge cannot decide, the normal prompt appears. Decisions are logged to
`~/agl/.dist/ai-office/judge.log`. `python3 ai-office/scripts/judge.py --test`
checks the rule table. Installing the hook into `.claude/settings.json` is a
founder step (Claude may not change its own permissions).
