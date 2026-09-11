# Branch consolidation — one branch per repo

Goal: every mobile repo on a single branch. Status as of 2026-09-09.

**All 42 mobile apps are now on a single branch.** Kinnav is the one
exception, and deliberately so: its second branch is `deploy`, which cPanel
builds the live site from (see below). Of the 44 repos, 41 have exactly one
branch; the three that do not are Kinnav, `www.safecodeg.com` (both `deploy`)
and this repo (`main` and the `match-certificates` orphan).

Getting there deleted 51 redundant branches and merged 13 carrying unique work.
The last four were not merges — they were salvages, because in each case the
branch was old enough that merging it would have *removed* work the default had
since gained. Those are recorded below.

---

## What was done

| Step | Count | Rule |
| --- | --- | --- |
| Deleted, already contained in default | 26 | `rev-list default..branch` was 0 — deleting loses nothing |
| Deleted, dependabot bumps | 25 | Regenerable; dependabot reopens them if still relevant |
| Merged cleanly, then deleted | 7 | No conflicts |
| Merged after resolving generated-file conflicts | 6 | Conflicts confined to `fastlane/`, `.github/workflows/`, lockfiles, `.gitignore`, `.metadata` — the default already carries the standardised version |

Every merged repo was re-verified with `flutter analyze` (0 errors) and
`flutter test` (passing) **before** the push, and the source branch was only
deleted once the remote confirmed it was contained.

## Deliberately left alone

### `deploy` branches — Kinnav, www.safecodeg.com

These are **not stale**. They are build output with `.cpanel.yml`, committed as
"Build website from &lt;sha&gt;", and cPanel deploys the live site from them.
They have unrelated histories to `main` by design. Merging or deleting them
would break deployment.

> Consequence worth knowing: the policy pages merged into
> `www.safecodeg.com/main` are **not live** until the site is rebuilt and
> pushed to its `deploy` branch.

### `match-certificates` — AmericanGroupLLC-Backend

Fastlane `match` storage. An orphan branch with unrelated history, holding
encrypted signing material. Merging it into `dev` would dump certificates into
the source tree.

## How the last twelve were resolved

Twelve repos were still multi-branch when this document was first written, each
with a real code conflict an automated merge would have had to guess at. All
twelve are now settled:

| Repo | Branch | Outcome |
| --- | --- | --- |
| radiotune | `feat/production-ready-redesign` (+11) and 3 others | Feature branch made mainline — it was the real app |
| MyHealth | `chore/store-details`, `feat/supabase-login` | Merged / retired; the branch's 284 unique files were the deleted React Native surface |
| BodyQuest | `main` (+4) | Merged |
| TripNest | `chore/store-details` (+2) | Merged |
| Verba | `chore/store-details` (+7) | Cherry-picked (metadata, marketing, iOS icons) rather than a 13-file merge |
| CalcMaster | `local-wip` | Salvaged — see below |
| HomeWise | `chore/store-details` | Salvaged — see below |
| daily-pulse | `local-master-2026-09-06` | Salvaged — see below |
| yourtube | `agl/ai-docs-logo`, `local-master-2026-09-06` | Salvaged — see below |
| Kinnav, www.safecodeg.com | `deploy` | Kept — cPanel deploys from them |
| AmericanGroupLLC-Backend | `main` vs `dev` | Still open — a project decision |

### The four salvages

These branches could not be merged: each was many commits behind its default
and would have deleted files the default had since gained. Each was inspected
file by file, the genuinely unique work taken, and the branch retired.

| Repo | Branch | Taken | Deliberately not taken |
| --- | --- | --- | --- |
| CalcMaster | `local-wip` (+1, −21) | Crash reporter, diagnostics screen, contrast helper, golden render tests, accessibility suite | Its deletion of `lib/app_env.dart`, `ios/Flutter/Profile.xcconfig` and the Play screenshots; two tests referencing APIs this app lacks |
| HomeWise | `chore/store-details` | 30 files: launcher icons for both platforms, source `app_icon.png`, proguard rules, seed property data | `mobile/test/widget_test.dart`, which pumps a `HomeWiseApp` class that does not exist |
| daily-pulse | `local-master-2026-09-06` (+2, −21) | `store/capture.sh`; its sign-up flow, rewritten against master's auth surface | Its Supabase auth — an earlier variant of what master already has, in different directories |
| yourtube | `agl/ai-docs-logo` (+2), `local-master-2026-09-06` (+3), both −19 | The two logo SVG sources | Everything else was superseded by the `yourtube_app/` → root move; and `70dc09a`, which strips the launch storyboards Apple requires |

**radiotune** was resolved separately: `feat/production-ready-redesign` was
proven to be the real app (44 lib files against master's 23) and made mainline.

### CalcMaster's accessibility suite found three real defects

Worth recording, because the same patterns are likely elsewhere. The salvaged
suite failed on landing against defects in shipping code, not in itself:

- a pill control measured 41dp tall, under the 48dp tap-target minimum on both
  platforms;
- a card overflowed by 2.9px at 2.0× text scale, because its title was
  fixed-height while only its subtitle could give way;
- `textDim` at 42% white composites to a 4.11 contrast ratio on black, under
  the 4.5 AA minimum for the 11px tab-bar labels.

All three are fixed. Any app without an accessibility test is not known to be
free of them — it is only untested.

### The one question still open

**Is `dev` or `main` canonical for this repo?** `main` is 7 commits ahead.
Until that is answered this repo keeps both.

## Note on the count

The org has 44 repos: **42 mobile apps**, one backend
(`AmericanGroupLLC-Backend`) and one website (`www.safecodeg.com`).

An earlier revision counted 41 by treating `PlantPulse` as non-mobile. That was
wrong — PlantPulse is a plant-health monitoring app. It currently exists only as
a React web client (Radix UI + Drizzle + an Express server) with no mobile
surface at all: no `pubspec.yaml`, no `app.json`, no Xcode project. So it needs
a Flutter app built, not merely ported.

Of the 42 mobile apps, **36 are Flutter** and **6 are not**: AGStudio,
ApexMarketWatch, BuddyPlay, CodeDeal, MyCard and PlantPulse.
