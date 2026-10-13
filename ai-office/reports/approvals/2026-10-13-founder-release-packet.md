# Founder release packet — what only you can do to reach production

**Decision needed:** work through the actions below, top to bottom. The office
cannot do any of them (Charter §1–8), and each one blocks store production for
some or all of the 43 apps.

**Why now:** the founder goal is every app released and in production. The
office is finishing the Real Apps work (issue #24) and keeps every build behind
the pre-delivery checklist. Past that point, every remaining blocker is on this
list.

Measured state on 2026-10-13: Apple — 0 of 43 live, 42 rejected (26 under
4.3/4.2.6, 16 under 5.6, which froze the account). Google Play — 6 live in
production (CalcMaster, iMaps, iMeasure, TripNest, Uscis-Case, VirtuBand), 37
production drafts staged.

## A. Unfreeze Apple (blocks every iOS submission)

1. **#13 — reply to the 16 Guideline 5.6 rejections** in App Store Connect →
   each app → App Review → Resolution Center. Suggested content is in
   `docs/MANUAL_ACTIONS.md` MA-043: the app has no hidden, remotely switched or
   reviewer-dependent features; every feature is reachable from launch; offer a
   call. Do not cancel and resubmit. Then tell the office, and it clears the
   holds (`store_watch.py --clear-hold <app>`).
2. **#11 — answer the 4.3 questions for 26 apps.** In each
   `store/apps/<App>.json` `differentiation`, write questions 3 (a named
   competitor and a named difference), 4 (beta testing that really happened —
   TestFlight shows **0 feedback items** on all 26, so do not claim feedback you
   cannot show), 6 and 9. The office has filled 1, 2, 5, 7 and 8 from measurements.
3. **#25 — decide the consolidations** (D1–D6, six overlapping apps). Apple's
   questions 5 and 6 ask exactly this; merging or retiring is yours (§8).

## B. Make the backend work in production

4. **#12 — Supabase Site URL is `http://localhost:3000`**: auth emails send
   users to localhost. Supabase dashboard → Authentication → URL Configuration.
5. **#14 — apply `delete_user()`** (`AmericanGroupLLC-Backend/supabase/migrations/20261009_delete_user.sql`):
   16 apps fail Apple 5.1.1(v) until it exists.
6. **#19 — approve the DriftDate schema** (Backend PR #1); **#5** — the backend
   deploy cannot reach the database (pooler tenant not found); **#10** —
   anonymous sign-ins are disabled.
7. **#18 — merge the privacy-policy PR** (website PR #1) so the policies disclose
   the crash and analytics data the App Privacy labels already declare.

## C. Google Play production

8. **App content declarations for the 37 draft apps**, then **Publish**. Every
   answer is pre-filled per app in `docs/console-answers/<App>.md`; Play has no
   API for these forms.
9. **#22 — reset the Play upload key for 8 apps** (MA-048).

## D. Each delivery: the pre-delivery checklist

10. For every build the office stages, a person tests it on a physical iPhone
    and signs the human checks:
    `python3 scripts/predelivery.py <App> --sign 5.1 --by "<name>" --device "<iPhone, iOS>" --evidence "<what you did>"`.
    The upload gate refuses a build without them (your rule, 2026-10-12).
11. **Accept the TestFlight invitations.** BodyQuest's internal group (and
    others) shows both testers as INVITED, so nobody can install yet.

## E. Revenue

12. **#15 — create the AdMob apps** in the AdMob UI (MA-047; the API refuses).
13. **Affiliate and API sign-ups** — per app in `store/vendors/apps/<App>.csv`,
    P1 rows first (Google Sign-In iOS client IDs for 12 apps, Amazon Associates,
    Impact, Travelpayouts, Expedia/Booking, Rakuten). Put only vault reference
    names in the CSV.
14. **#8 — iMeasure in-app purchase products** in App Store Connect, or the office
    removes the purchase code.

**What the office does as each item lands:** clears holds and drafts replies
(A), re-runs the checks that the item unblocks, builds and stages each app
through the pre-delivery checklist (D), and reports per app what is live.

**Evidence:** `docs/play-production-blockers.json` (live Play API, 2026-10-12),
`docs/store-holds.json`, `docs/asc-build-state.json`, `docs/beta-evidence.json`,
`docs/predelivery/*.md`, the issues linked above.

**Risks / undo:** none of these is taken by the office. Replies to Apple cannot
be unsent, so read the MA-043 draft before sending; Play declarations can be
edited afterwards.
