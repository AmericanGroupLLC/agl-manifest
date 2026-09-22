# Known issues

Open defects and risks, each one verified rather than inherited from an earlier
list. Resolved items move to the commit history, not here.

Priorities: **P0** security or data loss · **P1** release blocker ·
**P2** functional defect · **P3** minor · **P4** cleanup.

---

## P0 · Credentials workbook still fetchable from GitHub

Tracked in `MANUAL_ACTIONS.md` MA-001 because closing it needs credential
rotation and GitHub Support. Verified still open 2026-09-11.

---

## Resolved · The five identical shells now carry their own product

`CarDeal`, `HomeWise`, `NearServe`, `RideZap` and `portfolio-board` were one
939-line four-screen scaffold — home, search, profile, settings — on 2026-09-09.
They are not any more. Counted on 2026-09-13, both by
`scripts/audit_product_quality.py` and by hand with `find … | wc -l`, which
agree exactly:

| App | lib LOC then | lib LOC now | hand-written | lib files | test files |
| --- | ---: | ---: | ---: | ---: | ---: |
| CarDeal | 939 | 7,390 | 6,171 | 32 | 17 |
| NearServe | 939 | 6,408 | 5,250 | 32 | 21 |
| RideZap | 939 | 6,255 | 5,033 | 38 | 16 |
| HomeWise | 939 | 5,582 | 4,399 | 30 | 9 |
| portfolio-board | 939 | 5,522 | 4,734 | 22 | 9 |

*hand-written* excludes blank lines, comment-only lines and generated files.

Size alone would not settle it — five inflated copies would still be copies —
but the file lists have diverged into different domains: HomeWise has a mortgage
and affordability engine (`core/finance/mortgage.dart`,
`features/affordability/`), NearServe a provider booking flow
(`features/booking/booking_flow_screen.dart`), RideZap flight/hotel/ride quote
search (`features/search/*_search_form.dart`), CarDeal comparison and budget
screens (`features/compare/`, `features/budget/`), portfolio-board a
markdown-backed project board (`core/markdown/markdown_parser.dart`). No two of
the five share a file list, and no two apps in the portfolio now share both a
line count and a file count.

Whether five apps from one publisher still read as duplicates to a reviewer is a
judgement under guideline 4.3, not a measurement, and nothing here proves the
features work — only that the code is no longer shared.

---

## Resolved · The six non-Flutter apps are ported

`AGStudio`, `AeroSwift`, `ApexMarketWatch`, `BuddyPlay`, `MyCard` and
`PlantPulse` are now Flutter apps under `mobile/` in their own repositories,
each with a verified signed `.aab` and `.apk` published to a GitHub Release.
The portfolio is 43 of 43 Flutter.

Two of the six were not ports. AeroSwift's entire mobile app was a 57-line
placeholder rendering a title and a card, and ApexMarketWatch's was a single
280-line web page — both were built from the product spec rather than
translated. That distinction matters when judging how much behaviour was
preserved: for those two, there was none to preserve.

What each app cannot yet do is listed in its own commit message rather than
here, because it is app-specific: BLE peripheral mode, NFC, barcode scanning,
notifications, accounts and credits, and real hardware transports all need
either platform channels or credentials that do not exist.

---

## P2 · No iOS artefact has ever been produced or verified

Everything proven so far is Android. 37 signed `.aab` files exist and each has
had its certificate checked; the iOS equivalent is untested because there is no
distribution certificate (`MANUAL_ACTIONS.md` MA-005).

Treat every iOS readiness claim in the status tables as **structural** — the
Podfile, the Info.plist keys, the privacy manifest are present — not as evidence
that an `.ipa` builds. It has never been attempted.

---

## P2 · `radiotune` has two names

The product is "Ratio Tune" in the README, the pubspec (`ratio_tune`) and the
iOS `CFBundleDisplayName`. The repository and the Android `applicationId` say
`radiotune` (`com.americangroup.radiotune`), after a commit that fixed what was
recorded as a bundle-id typo.

Android's `app_name` was set to "Ratio Tune" to match the majority rather than
invent a fourth spelling, but one of the two has to give. Choosing is a product
decision, and it is cheap **only until a store record exists** — an
`applicationId` cannot be changed afterwards.

---

## P2 · Test coverage is very thin in the largest apps

Measured as lib LOC per test file on 2026-09-13 by
`scripts/audit_product_quality.py`. This has improved — each of these apps has
more test files than it had on 2026-09-09 — but the ratio is still poor:

| App | lib LOC | Test files | LOC per test file |
| --- | ---: | ---: | ---: |
| MyHealth | 45,370 | 22 | 2,062 |
| NexusTransferPay | 16,044 | 9 | 1,783 |
| PilotEnRoute | 40,100 | 26 | 1,542 |
| EventSpark | 19,585 | 13 | 1,507 |
| Photriya | 36,721 | 25 | 1,469 |

The suites pass, which says less than it appears to. A green run across 22 files
for 45,000 lines is thin signal — and this portfolio has already shipped an app
that passed analysis and tests while opening to a white screen. The measure
counts files, not assertions, so it cannot tell a real flow test from a one-line
smoke test.

Worth fixing by covering startup, navigation, auth and the primary flow, not by
generating tests to move a percentage.

---

## P3 · Build tooling is fragmented across the portfolio

Eight distinct Gradle/AGP pairs across 37 apps:

| Gradle | AGP | Apps |
| --- | --- | ---: |
| 9.1.0 | 9.0.1 | 24 |
| 8.14 | 8.11.1 | 5 |
| 8.14.2 | 8.11.1 | 2 |
| 8.12 | 8.7.3 | 2 |
| 9.3.1 | 9.0.1 | 1 |
| 8.9 | 8.7.0 | 1 |
| 8.14 | 8.13.1 | 1 |
| 8.11.1 | 8.9.1 | 1 |

All 37 build today, so this is maintenance debt rather than breakage: eight
toolchains means eight sets of upgrade notes and eight ways for the next Flutter
release to break something.

---

## P3 · Requested heap exceeds what a CI runner should be asked for

27 apps set `org.gradle.jvmargs=-Xmx8G -XX:MaxMetaspaceSize=4G`, which asks for
up to 12 GB. A GitHub-hosted `ubuntu-latest` runner has 16 GB total, so this is
survivable but leaves little headroom, and nothing in these apps justifies it —
they build here in well under that.

Not yet exercised in CI, because CI cannot build at all until MA-002 is
resolved. Worth reducing before it is.

---

## P3 · Two apps sit off the common iOS floor

`GroceryMatch` requires iOS 16.0 and `FashionFactory` declares no platform line
at all, against 15.0 everywhere else. A higher floor silently excludes devices;
an absent one takes CocoaPods' default, which is not the same thing as choosing.

*(An earlier version of this file claimed 23 apps were stuck on iOS 13.0. That
was a measuring error, not a defect: the audit regex matched the commented
`# platform :ios, '13.0'` line in Flutter's template. The regex is now anchored
and the real spread is 34 apps at 15.0.)*

---

## P3 · Store records do not line up with the apps

13 apps have no App Store Connect record; 11 records exist that match no live
bundle id. Each orphan is a rename-or-create decision, and creating the wrong
one is not reversible — see `docs/APP_IDENTIFIERS.md` before acting.

---

## P4 · 16 icon buttons remain deliberately unlabelled

`chevron_right`, `swap_horiz`, `replay_30`, `forward_10`, `north_west` and
others whose meaning depends on surrounding context. Left alone on purpose
(ADR-007) — a wrong label is worse than none — but they are still unnamed to a
screen reader, and someone who knows each screen could label them correctly.

## Photriya cannot move to target SDK 36 (2026-09-22)

Google Play now refuses an upload below target SDK 36. Three apps that pinned 35
(BodyQuest, GroceryMatch, yourtube) were moved to `flutter.targetSdkVersion` and
build clean; yourtube reached Play's internal track as a result.

Photriya cannot follow yet, and is deliberately left at 35:

* At `compileSdk 36` with its current Android Gradle plugin (8.11.1),
  `lintVitalReportProdRelease` dies with "Internal error: Unexpected lint
  invalid arguments".
* Raising the plugin to 8.13.1, the version GroceryMatch uses, moves the failure
  to `:flutter_native_splash:checkReleaseAarMetadata` — the plugin *modules* keep
  the old compile level and 20 AAR metadata checks fail.

Reverted to `compileSdk 35` / `targetSdk 35` / plugin 8.11.1, which builds:
a prod-flavour release bundle was produced at 68.4 MB after the revert. Photriya
has no Play entry yet so nothing is blocked today, but it cannot be uploaded
until the toolchain moves. The fix is to raise the plugin *and* give the plugin
modules a compile level, not to change the app alone.

Separately, Photriya carried a stale generated plugin registrant on disk
(gitignored, not tracked) that referenced a class no longer in sensors_plus and
broke every Android build with a Java compile error. Deleting it and running
`flutter pub get` regenerates it correctly.
