# AI Office

An AI organisation for American Group LLC, built on Claude Code, living next to
the automation it runs (`agl-manifest`).

## Use it
```bash
cd ~/agl/agl-manifest/ai-office
claude            # the 34 roles, skills and workflows load from .claude/
```
Then ask in plain language — "run the standup", "handle the new rejection for
MyCard", "release train", "what is blocking AdMob?". The chief-of-staff routes
it.

## Departments (34 roles in `.claude/agents/`)
- **Executive:** chief-of-staff, strategy-analyst, project-coordinator, portfolio-director
- **Product & Engineering:** product-manager, technical-architect, software-developer, test-engineer, security-reviewer, release-manager, store-compliance, qa-screenshots, data-honesty, backend-supabase, web-domains, monetization
- **Marketing:** marketing-manager, market-researcher, content-strategist, copywriter, seo-analyst
- **Sales & Support:** sales-manager, lead-researcher, outreach-specialist, support-analyst
- **Finance & Admin:** finance-manager, budget-analyst, business-analyst, hr-assistant
- **Operations:** operations-manager, workflow-designer, documentation-specialist, qa-reviewer, data-analyst

## Runs by itself
- `ai-office-standup.yml` (agl-manifest Actions): daily 13:00 UTC, builds the
  stand-up from measured state and keeps the pinned issue "AI office: daily
  stand-up" current. No AI key needed.
- Add an `ANTHROPIC_API_KEY` repo secret to also let Claude triage the
  stand-up unattended (the job skips that step without it).

## What it will not do
See CHARTER.md: store submissions and replies, production database approval,
money, credentials, external contact, legal text, people decisions, removing
apps. It prepares them; the founder decides.
