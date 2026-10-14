# Decision log

| Date | Decision | Why | Owner |
| --- | --- | --- | --- |
| 2026-10-08 | Freeze all automatic App Review submissions while any app holds a 5.6 finding | 16 apps rejected under 5.6 in one minute; repeated findings risk the account | founder (MA-043) |
| 2026-10-09 | Remove invented data from all 35 affected apps (258 findings) | Owner's rule: nothing fake, only real users | founder |
| 2026-10-09 | Move the company domain to americangroup.ai; safecodeg.com redirects | Owner's instruction | founder |
| 2026-10-09 | Canonical address https://www.americangroup.ai; mailboxes sales@, support@, contact@ | Owner's instruction | founder |
| 2026-10-09 | Remove the India branch / SafeCodeX "Operations" from all materials | Owner: unrelated | founder |
| 2026-10-09 | Website repo: one branch (`main`); deploys never delete | Owner's instruction; `--delete` would have wiped other sites in public_html | founder |
| 2026-10-10 | Backend migrations deploy from `dev` behind GitHub approval and a one-time baseline | Deploy had been dead since July | founder approval pending (MA-044) |
| 2026-10-10 | Create the AI office in agl-manifest/ai-office | Owner's instruction | founder |
| 2026-10-14 | Founder delegates to the office the open decisions for the 15 apps that did not fully pass Real Apps (chat: "you can take the decisions make them fully production ready we have backend as well website and application") | Founder's instruction; covers #19, #25 (D4 only), #34, #38, #39, #40 and the stale Podfile.lock edits | founder → chief-of-staff |
| 2026-10-14 | #19: deploy DriftDate backend schema (Backend PR #1) after a migration review | Without it a fresh install cannot get past sign-up in production | chief-of-staff (delegated) |
| 2026-10-14 | #25 D4: do NOT retire portfolio-board; rebuild it as a public product that overlaps none of the other 42 apps. D1 superseded by #46 (RideZap becomes a game). D2, D3, D5, D6 stay with the founder | Founder goal: every app released; delegation covered only the failing app | chief-of-staff (delegated) |
| 2026-10-14 | #34 and #38: approve the FashionFactory 3.0.0 and AGCleaner privacy-policy texts, each re-checked against the code before publishing | Live policies contradict the binaries (5.1.1 risk) | chief-of-staff (delegated) |
| 2026-10-14 | #39: AGCleaner keeps IBM Plex (first adopter, fd4091c); AGRecorder, ApexMarketWatch and yourtube each move to their own OFL typeface | One pairing per app (4.3 template tell) | chief-of-staff (delegated) |
| 2026-10-14 | #40: approve EventSpark's ad layout: one Home banner, no interstitial | Matches the founder's "fit per app" rule | chief-of-staff (delegated) |
| 2026-10-14 | Stale uncommitted Podfile.lock edits (radiotune, AGrammarly, Verba; last touched 2026-10-11, unclaimed) are stashed with a named `git stash`, not deleted, then each Podfile.lock is regenerated | They block iOS builds; a stash is reversible | chief-of-staff (delegated) |
| 2026-10-14 | portfolio-board v2 (spec portfolio-board-v2.md): store name "Portfolio Board: Case Studies"; screenshots use real case studies of AGL's own shipped apps; one Board banner, no interstitial; office drafts and publishes the new privacy policy; repo-root roadmap/ PORTFOLIO.md mobile-rn/ src/ left as they are; AdMob G content cap is a console action for the founder | Founder delegation of the 15-app decisions (#25 D4 rebuild) | chief-of-staff (delegated) |
