# Current status

The one file to read at the start of a session, after `CLAUDE.md`. Kept short on
purpose. Numbers here are measured; if one disagrees with `STATUS.md`, `STATUS.md`
is right and this file is stale.

**As of 2026-09-12.**

## Where the portfolio is

| | |
| --- | ---: |
| Mobile apps in the org | 42 |
| Flutter apps | **43 of 43** |
| Not ported to Flutter | 0 |
| Verified signed `.aab` | 43 of 43 |
| Verified signed `.apk` | 43 of 43 |
| Published to a GitHub Release | 42 (Kinnav skipped — outside the org) |
| Signature mismatches | 0 |
| Apps analysing clean | 43 |
| iOS artefacts built | **0** |

Android is done to the point of an uploadable, installable, signature-verified
artefact for every Flutter app. iOS has not been started — no distribution
certificate exists.

## What is blocking, and on whom

Everything genuinely blocked needs a human. In priority order, from
`docs/MANUAL_ACTIONS.md`:

1. **MA-001 (P0)** — a credentials workbook is still fetchable from a dangling
   commit. Needs credential rotation, then GitHub Support.
2. **MA-002** — `AGL_PACKAGES_TOKEN` is unset, so no CI job can resolve the
   private shared packages. Local builds are unaffected.
3. **MA-003** — no Play service account, so nothing can be uploaded.
4. **MA-005** — no iOS distribution certificate, so no `.ipa`.
5. **MA-006** — Firebase config files missing, so Crashlytics reports nothing.

## What is worth doing next, unblocked

- **Reduce the requested Gradle heap.** 27 apps ask for up to 12 GB; that will
  be uncomfortable on a 16 GB runner the moment CI can build.
- **Cover the biggest apps with real tests.** MyHealth is 44,887 lines behind 8
  test files. Startup, navigation, auth, primary flow — not coverage theatre.
- **Decide what the five scaffold apps are.** They pass every gate and are still
  not products; see `KNOWN_ISSUES.md`.
- **Resolve the `radiotune` / "Ratio Tune" name split** before a store record
  makes the `applicationId` permanent.

## Recently finished

- **The six non-Flutter apps are ported.** AGStudio, AeroSwift, ApexMarketWatch,
  BuddyPlay, MyCard and PlantPulse are Flutter apps under `mobile/`, each with a
  verified signed bundle and APK on a GitHub Release. Two of them were not ports
  at all: AeroSwift's mobile app was a 57-line placeholder and
  ApexMarketWatch's was a single web page, so both were built from the spec.
- Each port carries an honest offline mode rather than fabricated data — AGStudio
  burns "NOT AI GENERATED" into preview pixels, OmniControl states that nothing
  is transmitted, ApexMarketWatch marks sample quotes, AeroSwift distinguishes
  ADS-B observations from schedules.
- Generated launcher icons for all six; `flutter create` had left them as
  identical Flutter logos, which both stores reject.
- Fixed a manifest generator that emitted every newly ported app twice, which
  had inflated the status tables to "48 apps" for an org of 42.

- Every Flutter app now produces a signed, certificate-verified `.aab` and
  `.apk`, published to a GitHub Release in its own repo.
- Diagnosed why no Android build worked on this machine at all: the JVM's IPv6
  `connect()` is denied, and the JVM ignores the shell's proxy variables.
- Fixed eight apps that failed for their own reasons — misplaced Kotlin imports,
  undefined launcher resources, signing configs that rejected absolute paths.
- Caught CodeDeal signing release builds with the **debug** key while exiting 0.
- Generated the seven missing upload keystores.
- Corrected two metrics that were reporting the wrong thing: accessibility
  (ignored `tooltip`) and the iOS floor (matched a commented-out line).
