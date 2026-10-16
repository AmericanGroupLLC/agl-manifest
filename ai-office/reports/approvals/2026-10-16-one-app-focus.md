# Approval request — work one app at a time: keep one app, archive the other 42 locally

Date: 2026-10-16 · Prepared by: chief-of-staff (AI office) · Founder instruction (chat, 2026-10-16):
*"we will work on app by app out of 43 you can delete 42 and keep one app first. keep other three websites because we need them to work on website and backend and agl-manifest to deliver."*

## Decision needed
1. **Which app first** (the founder decides app scope, per the charter).
2. **What "delete" means** for the other 42.

## Evidence (measured 2026-10-16 on this Mac)
- `~/agl` holds the 43 app repos plus `agl-manifest`, `AmericanGroupLLC-Backend` and `americangroup.ai` (all three stay).
- Every app repo has a GitHub remote, so committed history is safe in every option.
- **Local-only work that a plain delete would destroy:**
  - 39 apps have uncommitted edits (12–34 files each);
  - 5 apps have stashes (AGrammarly, FashionFactory, portfolio-board, radiotune, Verba: the stale edits stashed on 2026-10-14 instead of deleted);
  - FashionFactory has 1 unpushed commit.
- The app folders take about 120 GB (MyHealth alone is 17.5 GB, mostly build output).
- Apple (2026-10-15): 35 apps rejected under 4.3(a) Spam, with an Extended Review warning about the account. Submissions are held until about 2026-10-21, at most 3 apps a week (decision log).
- 34 apps have a new build `202610152200` on TestFlight internal (verified in App Store Connect). CI run 38836939609 is re-running the rest.

## Recommendations
**Q1 — first app: PilotEnRoute** (office recommendation; the founder decides)
- A distinct niche (student and private pilots: day minimums, the Go Card, logbook, live METAR/TAF).
- The most tests in the portfolio: 768 passing (`0e4322a`, `b5e88a3`).
- It ran cleanly on Apple's own rejection device class (iPhone 17 Pro Max, iOS 27.0, 11 cold launches).
- A new build is on TestFlight.
- No backend or vendor key dependency (public aviationweather.gov data).

Alternatives:
- **ChefCount:** already live, so it has the lowest risk but adds no new app to the store.
- **DriftDate:** blocked on the production database deploy and moderation setup.
- **RideZap:** the largest build left (Godot milestones 2–3 plus a pipeline lane).

**Q2 — "delete" = archive locally** (recommended). For each of the 42:
1. `git stash push -u` if dirty.
2. `git bundle create ~/agl/.archive/<repo>.bundle --all`, which keeps branches, tags and stashes.
3. Verify the bundle with `git bundle verify`.
4. Remove the folder.

This frees about 115 GB, and any app comes back with `git clone ~/agl/.archive/<repo>.bundle` or from GitHub. **GitHub repos and App Store / Play listings are not touched.** Deleting GitHub repos or store listings is irreversible, and the office does not recommend it.

## Exact action
Reply, for example: **"approve: keep PilotEnRoute, archive the other 42 locally"** (or name another app). The office will then:
1. Archive and verify each bundle before removing anything.
2. Update `apps.json`-driven tooling (CI and scripts) so it builds only the focus app. The other 42 stay buildable from GitHub.
3. Report the freed space.

## Risks / undo
- Archive: fully reversible (bundle or GitHub).
- CI runs that loop over all apps will skip the archived ones locally. CI itself clones from GitHub, so it isn't affected.
