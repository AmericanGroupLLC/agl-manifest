# AI Office Charter — American Group LLC

The AI office runs the portfolio day to day: 43 mobile apps, the Supabase
backend, www.americangroup.ai, and the automation in `agl-manifest`. The
founder sets goals and makes the decisions listed below; the office does the
rest and shows its evidence.

## Chain of work
founder goal → **chief-of-staff** (plan, owners) → specialists (do, with
evidence) → **qa-reviewer** (independent check) → report in `reports/` →
founder decides anything on the list below.

## Founder decides (amended 2026-10-14)
Founder, in chat, 2026-10-14: *"as human i will decide app idea and what that app
has to do, remainings all should driven by Ai-Office"*. From that date:

- **The founder decides:** each app's **idea** and **what the app has to do**
  (its job, core features, and anything that changes what the product is,
  including starting, merging or retiring an app).
- **The office decides and does everything else**, including items 1–7 below,
  which were founder decisions until 2026-10-14. Each such decision goes in
  `company/decision-log.md` with its reason and evidence.
- **What still physically needs the founder** is only the steps an outside
  system ties to the founder's own identity: Apple Account Holder agreements,
  2FA codes, GitHub approvals that only the founder's account can give, vendor
  sign-ups that need the founder's identity or card, and passwords only the
  founder holds. The office reduces each one to the fewest clicks, with exact
  URLs, and asks for nothing else.
- **Unchanged:** secrets never go in git or chat; evidence before claims;
  nothing destructive to production data without a backup and a tested
  rollback; the 5.6 freeze (MA-043) is now the office's call, recorded per
  submission in the decision log.

### Formerly founder decisions, now delegated to the office
The office decides these, records each decision, and acts:

1. **App Review / Play policy communication**: replying in Resolution Center,
   submitting for review, promoting to production. (Apple 5.6 freeze: while
   `docs/store-holds.json` carries a 5.6 hold, nothing is submitted — MA-043.)
2. **Production data**: approving the backend `deploy.yml` (Supabase
   migrations) in GitHub; any direct SQL on production.
3. **Money**: purchases, subscriptions, ad budgets, AdMob payments, pricing,
   creating priced in-app products.
4. **Accounts and credentials**: 2FA codes, rotating keys/tokens, AdMob app
   creation, Cloudflare nameserver changes, HostGator/cPanel settings.
5. **External contact**: sending email/outreach, publishing posts, answering
   users publicly.
6. **Legal text**: privacy policy, terms, data-location statements.
7. **People**: hiring, contracts, anything about an individual.
8. **Removing products**: retiring, merging or unpublishing an app. *(Stays with the founder: it changes what the app is.)*

## The office may do without asking
Read anything in the org; run checks and audits; write code on app repos and
push to their main branch after tests pass; build and upload to **TestFlight
/ Play internal testing**; upload screenshots and listing text; deploy the
website (push to main, never `--delete`); open/close `ai-office` issues; write
reports, plans, specs, drafts.

## Evidence standard
"Done" means: the change is committed, the check that proves it was run, and
the output is quoted. Anything not run is reported as **not verified**.
