# Real apps — every app a distinct product, not a template

**Goal (founder, 2026-10-12):** "Make every application a real mobile application if
the store is rejecting it like a template. The AI office should work on all the issues."

**Why:** Apple rejected 26 apps under 4.3 Spam / 4.2.6 App Generation Services
("created from a commercialized template… indistinguishable from what's already
available") and 16 under 5.6. A reply alone cannot fix 4.2.6; the apps have to stop
looking like one scaffold reskinned 43 times, and each has to do a real job well.

**Owner:** chief-of-staff. Chain per app: product-manager (spec) → software-developer
(build, push after tests) → qa-reviewer (independent check, one repair round).
Portfolio-director: overlap and consolidation recommendation (founder decides).

## Acceptance criteria — every app

1. **Core job works end to end** on a fresh install. Every visible control does
   something real. No placeholder, "coming soon", dead or empty-shell screens: finish
   them or remove them.
2. **Signature feature.** At least one substantial capability specific to this app
   (its honest angle against the named competitors), implemented — not claimed.
3. **Depth.** The core flow persists what the user makes (history, saved items),
   has search/filter and share/export where they fit, and real empty, error and
   offline states.
4. **Own identity — template tells removed.** Its own colour scheme, typography and
   shape language; a home layout that fits its domain rather than the shared
   scaffold; its own onboarding and settings copy. Boilerplate repeated across
   apps that does not serve this app goes. Legally required pieces stay (privacy,
   account deletion, ads consent).
5. **Honest.** Real data only — on-device, Supabase `smvvjivvlprjhzhoizym`, or a
   keyless public API that resolves (`scripts/verify_api_hosts.py`). No fake data,
   no demo logins, no remote switches, no reviewer detection (5.6).
6. **Proven.** `flutter analyze` clean, every test passes, new tests cover the new
   behaviour, no test deleted or skipped to go green. Committed path-limited and
   pushed to main.
7. **Store impact written down** in the spec: copy changes, screenshots to retake,
   review-notes changes. store-compliance applies them afterwards.

## Founder decisions this project will raise (not taken by the office)

- Merging or retiring overlapping apps (Charter §8) — portfolio-director's
  recommendation goes to `reports/approvals/`.
- Replying to Apple and resubmitting (Charter §1; 5.6 freeze, MA-043).

## Records

- Specs: `specs/<repo>.md`
- Template-tell diagnosis: `diagnosis.md`
- Run report: `../../reports/<date>-real-apps.md`
- Tracking issue: GitHub `ai-office` issue "Real apps: every app a distinct product"
