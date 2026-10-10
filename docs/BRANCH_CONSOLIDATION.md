# Branch consolidation — one branch per repo

Goal: every repo on a single branch.

## Status 2026-09-28

**42 of the 43 mobile apps are on a single branch**, and 43 of the 46 org
repos are. The exception among the apps is Kinnav, which keeps a `deploy`
branch that cPanel builds its live site from. The three repos with more than
one branch are listed below; each is deliberate or pending a decision.

The 2026-09-09 pass (recorded further down) had achieved this once. It came
back because the production-readiness work all landed on a shared branch,
`production-readiness-2026-09-12`, which ended up on 44 repos.

What was done this time, and the rule for each:

| Step | Count | Rule |
| --- | --- | --- |
| Default fast-forwarded to the work branch, then the branch deleted | 13 | `merge-base --is-ancestor` held, so no merge commit was needed |
| Work branch deleted, default already identical | 30 | `compare` returned `identical` — deleting loses nothing |
| `main` deleted where the default was `master` and it held nothing | 2 | AeroSwift, BodyQuest — `ahead=0` |
| dependabot branches deleted | 7 | Regenerable; dependabot reopens them if still relevant |
| `main` merged into `dev`, then deleted | 1 | AmericanGroupLLC-Backend — `main` held two real documentation commits, so deleting it would have dropped them |

Nothing was deleted without first asking GitHub to compare it against the
default in that same pass. Every branch removed was either `identical`,
`behind`, or a dependabot bump.

### The three repos that still have more than one branch

| Repo | Extra branch | Why it is still there |
| --- | --- | --- |
| Kinnav | `deploy` | cPanel builds the live marketing site from it. Contains `.cpanel.yml`, `.htaccess` and a built site, with no common ancestor with `master`. Deleting it takes the site down |
| www.americangroup.ai | `deploy` | Same arrangement for the main website |
| AmericanGroupLLC-Backend | `match-certificates` | An orphan branch that self-documents as `fastlane match` storage — "do not merge into dev or main". Currently holds only its README. Unused, because provisioning profiles now come from the App Store Connect API (`scripts/ios_profile_map.rb`), but it is deliberate structure and relates to the unresolved iOS signing certificate. **Decision needed** — it is safe to delete if match is not going to be used |

### Default branch names are not consistent

35 repos use `main`, 10 use `master`, and AmericanGroupLLC-Backend uses `dev`.
This was left alone: renaming a default branch rewrites clone instructions, CI
refs and any bookmarked URL, and nothing currently depends on the names
matching. Worth doing deliberately, not as a side effect of this pass.

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

### `deploy` branches — Kinnav, www.americangroup.ai

These are **not stale**. They are build output with `.cpanel.yml`, committed as
"Build website from &lt;sha&gt;", and cPanel deploys the live site from them.
They have unrelated histories to `main` by design. Merging or deleting them
would break deployment.

> Consequence worth knowing: the policy pages merged into
> `www.americangroup.ai/main` are **not live** until the site is rebuilt and
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
| Kinnav, www.americangroup.ai | `deploy` | Kept — cPanel deploys from them |
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
(`AmericanGroupLLC-Backend`) and one website (`www.americangroup.ai`).

An earlier revision counted 41 by treating `PlantPulse` as non-mobile. That was
wrong — PlantPulse is a plant-health monitoring app. It currently exists only as
a React web client (Radix UI + Drizzle + an Express server) with no mobile
surface at all: no `pubspec.yaml`, no `app.json`, no Xcode project. So it needs
a Flutter app built, not merely ported.

Of the 42 mobile apps, **36 are Flutter** and **6 are not**: AGStudio,
ApexMarketWatch, BuddyPlay, CodeDeal, MyCard and PlantPulse.
