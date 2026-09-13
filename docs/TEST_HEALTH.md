# Test health across the 43 Flutter apps

Source data: the portfolio sweep in `/Users/spatchava/agl/.sweep/`, finished
**2026-09-12 23:24 local** (`results.psv` mtime). The sweep ran
`flutter pub get` → `flutter analyze --no-pub` → `flutter test --no-pub --reporter compact`
in every app, four apps at a time (`xargs -P 4` in `.sweep/sweep.sh`).

Four apps were re-run single-file on **2026-09-13** to check whether the sweep was
still true. Three of them had already changed. Read the staleness note below before
quoting any number here.

## How to read the numbers

* **Test files** — count of `*_test.dart` under the app's `test/` tree, counted today.
* **Passed / failed / skipped** — the compact reporter's final `+p -f ~s` line.
* **Suite time** — the compact reporter's own elapsed clock (`mm:ss`) on its last line.
  This **excludes** kernel compilation, and it was measured with four apps competing
  for the machine, so treat it as an upper bound on relative cost, not as a clean
  single-app wall clock.
* **Product LOC** — Dart lines under `lib/`, **excluding** generated localisation
  (`**/generated/**`, `app_localizations*.dart`) and `*.g.dart`. This differs
  deliberately from the `loc` field in `.sweep/assignments.json`, which counts the
  generated files. For NexusTransferPay that is the difference between 15 755 and
  6 091 lines — 61% of that app is generated ARB output, and judging its test count
  against the raw figure would be unfair. The raw figure is kept in its own column.
* **T/KLOC** — total tests ÷ product KLOC. A crude density measure, useful only for
  spotting the two ends of the distribution.

## Staleness warning

This table is a snapshot, and the portfolio moved underneath it. Verified today:

| App | Sweep said | Re-run 2026-09-13 said |
| --- | --- | --- |
| yourtube | `30:09 +178 -5`, exit 1 | `00:12 +204`, **exit 0**, 14 s wall |
| MyHealth | `00:23 +305 -2`, exit 1 | `00:14 +320`, **exit 0**, 17 s wall |
| iMeasure | `00:08 +122 -7`, exit 1 | `00:10 +132`, **exit 0**, 12 s wall |
| FashionFactory | `00:26 +869 -1`, exit 1 | `00:19 +869 -1`, **exit 1**, 21 s wall |

Three of the four red suites were fixed by other agents between the sweep and this
report. `yourtube` commit `13f3e73` ("Unhang the layout suite and give the app a
semantics tree", 2026-09-13 01:04) landed 100 minutes after the sweep captured the
30-minute hang. Only FashionFactory is still red, and its failure is not a test bug —
see below.

## Per-app table

Numbers are from the 2026-09-12 sweep unless the row is marked †, in which case they
are today's re-run.

| App | Raw LOC | Product LOC | Test files | Passed | Failed | Skipped | Suite time | T/KLOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AeroSwift | 6039 | 6505 | 11 | 133 | 0 | 0 | 00:10 | 20.4 |
| AGCleaner | 1727 | 870 | 5 | 31 | 0 | 0 | 00:10 | 35.6 |
| AGrammarly | 2365 | 2620 | 7 | 76 | 0 | 0 | 00:10 | 29.0 |
| AGRecorder | 1096 | 558 | 6 | 33 | 0 | 0 | 00:10 | 59.1 |
| AGStudio | 8785 | 4537 | 12 | 88 | 0 | 0 | 00:16 | 19.4 |
| ApexMarketWatch | 7846 | 7991 | 11 | 232 | 0 | 0 | 00:12 | 29.0 |
| BodyQuest | 8050 | 8437 | 12 | 130 | 0 | 0 | 00:09 | 15.4 |
| BuddyPlay | 15621 | 15801 | 11 | 213 | 0 | 0 | 00:12 | 13.5 |
| CalcMaster | 17748 | 12586 | 23 | 242 | 0 | 1 | 00:19 | 19.3 |
| CarDeal | 7073 | 7390 | 17 | 316 | 0 | 0 | 00:20 | 42.8 |
| ChefCount | 1635 | 1924 | 6 | 44 | 0 | 0 | 00:12 | 22.9 |
| CodeDeal | 4390 | 2822 | 10 | 86 | 0 | 0 | 00:06 | 30.5 |
| daily-pulse | 19750 | 13712 | 15 | 165 | 0 | 0 | 00:17 | 12.0 |
| DriftDate | 16512 | 16589 | 19 | 198 | 0 | 0 | 00:28 | 11.9 |
| EventSpark | 19499 | 19585 | 13 | 367 | 0 | 0 | 00:21 | 18.7 |
| FashionFactory † | 11558 | 11558 | 42 | 869 | **1** | 0 | 00:19 | 75.3 |
| GadgetNest | 5122 | 5459 | 10 | 145 | 0 | 0 | 00:17 | 26.6 |
| GroceryMatch | 33589 | 33592 | 47 | 1289 | 0 | 0 | 00:29 | 38.4 |
| HerJourney | 10241 | 10402 | 8 | 62 | 0 | 0 | 00:07 | **6.0** |
| HomeWise | 5155 | 5582 | 9 | 155 | 0 | 0 | 00:12 | 27.8 |
| iMaps | 32907 | 25782 | 28 | 338 | 0 | 0 | 00:12 | 13.1 |
| iMeasure † | 15398 | 15448 | 12 | 132 | 0 | 0 | 00:10 | 8.5 |
| Kinnav | 11890 | 8214 | 24 | 258 | 0 | 0 | 00:19 | 31.4 |
| MileMaster | 1359 | 610 | 4 | 12 | 0 | 0 | 00:11 | 19.7 |
| MyCard | 4622 | 4815 | 10 | 107 | 0 | 0 | 00:07 | 22.2 |
| MyFinance | 3332 | 3482 | 5 | 56 | 0 | 0 | 00:09 | 16.1 |
| MyHealth † | 45100 | 45370 | 22 | 320 | 0 | 0 | 00:14 | **7.1** |
| NearServe | 6257 | 6408 | 21 | 257 | 0 | 0 | 00:17 | 40.1 |
| NewsBoard | 5067 | 5499 | 8 | 86 | 0 | 0 | 00:13 | 15.6 |
| NexusTransferPay | 15755 | 6091 | 9 | 64 | 0 | 0 | 00:04 | 10.5 |
| Photriya | 36307 | 36576 | 25 | 948 | 0 | 0 | 00:23 | 25.9 |
| PilotEnRoute | 39652 | 40100 | 26 | 364 | 0 | 1 | 00:29 | **9.1** |
| PlantPulse | 7952 | 7962 | 12 | 139 | 0 | 0 | 00:09 | 17.5 |
| portfolio-board | 5270 | 5522 | 9 | 124 | 0 | 0 | 00:14 | 22.5 |
| radiotune | 10323 | 10325 | 12 | 82 | 0 | 0 | 00:21 | **7.9** |
| RideZap | 6044 | 6255 | 16 | 173 | 0 | 0 | 00:17 | 27.7 |
| RoomCraft | 930 | 1059 | 6 | 29 | 0 | 0 | 00:12 | 27.4 |
| TripNest | 11386 | 11518 | 15 | 194 | 0 | 0 | 00:18 | 16.8 |
| Uscis-Case | 12123 | 12346 | 11 | 73 | 0 | 0 | 00:15 | **5.9** |
| Verba | 17652 | 17661 | 32 | 582 | 0 | 0 | 00:27 | 33.0 |
| VirtuBand | 7850 | 8038 | 8 | 44 | 0 | 0 | 00:10 | **5.5** |
| WiFiTrail | 3079 | 1387 | 7 | 41 | 0 | 0 | 00:09 | 29.6 |
| yourtube † | 11712 | 11938 | 16 | 204 | 0 | 0 | 00:12 | 17.1 |

Portfolio totals on these numbers: **43 suites, 1 failing test in 1 app**, 9 501
passing tests and 2 skipped, across 632 test files.

## 1. Suites that are too slow for CI

**There is exactly one, and it is already fixed.** Every other suite in the portfolio
finishes in 29 seconds or less on the reporter clock. The claim that a group of apps
sit above two minutes is not supported by the logs: the second-slowest suites are
GroceryMatch and PilotEnRoute at 00:29, then DriftDate at 00:28 and Verba at 00:27.

### yourtube — was 30:09, now 00:12

The 30 minutes were not slow tests. They were **three ten-minute runner timeouts**,
all in `test/layout_phone_test.dart`:

```
10:08 +170 -2: ... at iPhone SE 375x667 the login screen lays out with no overflow [E]
  TimeoutException after 0:10:00.000000: Test timed out after 10 minutes.
20:09 +177 -4: ... at iPhone 14 390x844 the login screen lays out with no overflow [E]
  TimeoutException after 0:10:00.000000: Test timed out after 10 minutes.
30:09 +178 -5: ... accessibility text scale the login screen survives a 1.3x text scale [E]
  TimeoutException after 0:10:00.000000: Test timed out after 10 minutes.
```

Three hangs × 10 min = 30:09. Each hanging test needed the signed-out state, which
went through `AuthService.signOut()`
(`yourtube/lib/data/services/auth_service.dart:300`) — `_client.auth.signOut()` then
`GoogleSignIn().signOut()`, both unmocked. Inside a `testWidgets` fake-async zone the
platform-channel reply never arrives and the `await` never returns.

Commit `13f3e73` moved that reset into `setUp`, which runs outside the fake-async
zone. Verified today: the whole yourtube suite is `00:12 +204: All tests passed!`,
exit 0, 14 s wall clock.

**This is the pattern to watch for portfolio-wide, not the runtime.** A ten-minute
runner timeout is indistinguishable from a slow suite in a CI dashboard, and Flutter's
default per-test timeout means one unmocked platform channel costs ten minutes of
build time every run.

### What is actually slow in the remaining suites

Scanned every `test/` tree for `await Future.delayed(`, `Timer(`, unmocked
`http.Client()` / `HttpClient()`, `pumpAndSettle(Duration…)`, `sleep(` and
`Process.run/start`. Complete list of hits:

| App | Finding | Cost | Verdict |
| --- | --- | --- | --- |
| Photriya | 10 × real `await Future.delayed(300–500 ms)` in `test/auth/auth_comprehensive_test.dart` (lines 283, 293, 317, 329, 340, 351, 361, 599, 850, 891) | ~3.2 s of pure sleeping | Real waste, but 3 s of a 23 s suite carrying 948 tests. Low priority. |
| Verba | `Process.runSync(<c++ compiler>)` in `test/llm/llama_bindings_abi_test.dart:32`, compiling `native/verba_llama` in `setUpAll` | one compile per run | Legitimate — it is the FFI ABI contract test — but it makes the suite depend on a C++ toolchain being on `PATH`. Note it in CI setup; do not delete it. |
| daily-pulse | `news.client = http.Client()` at `test/support/harness.dart:78` | none observed | It is in `addTearDown`, restoring the real client after a `MockClient`. It constructs a client but never issues a request. Harmless today; it is the kind of line that becomes a live network call the moment a later test forgets to install the mock. |
| Kinnav, EventSpark | `Process.runSync('git', ['ls-files', …])` (`Kinnav/test/regression/fixed_defects_test.dart:123`, `EventSpark/mobile/test/production_test.dart:329`) | negligible | Fine. |
| CalcMaster (6), EventSpark (5), FashionFactory, Kinnav, MyHealth, TripNest (1 each) | `pumpAndSettle(Duration…)` | bounded | Bounded pumps, not real waits. Fine. |

No app uses `sleep()`, and the grep found no test that issues a real HTTP request.
That grep only catches `http.Client()` / `HttpClient()` / `IOClient()`, so it would
**not** have caught yourtube's hang, which came through an unmocked Supabase auth call
and an unmocked `GoogleSignIn` platform channel. Treat "no network in tests" as
unproven for any app whose tests touch an auth service.

## 2. Test counts that cannot be defended

Ranked by tests per thousand lines of hand-written product code. The portfolio median
is 19.7 (MileMaster). These seven sit at or below 10 — half the median or worse —
while carrying some of the largest codebases in the portfolio.

| Rank | App | Product LOC | Tests | T/KLOC | Product LOC never imported by any test | Why it is indefensible |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | **VirtuBand** | 8 038 | 44 | 5.5 | 6 483 (81%) | 8 test files. No test imports `main.dart` or `app.dart`, so **no screen is rendered at all** — the audio engine and all six screens are pure dead weight in CI. |
| 2 | **Uscis-Case** | 12 346 | 73 | 5.9 | 8 481 (69%) | An immigration-status app. `civics_test_screen.dart` (719 lines) and `civics_data.dart` (643 lines) — the actual product — are untouched. |
| 3 | **HerJourney** | 10 402 | 62 | 6.0 | 8 981 (86%) | The worst coverage ratio in the portfolio. 8 test files, none importing the app root. Every screen, including the health dashboard and the report-analysis scan flow, is untested. |
| 4 | **MyHealth** | 45 370 | 320 | 7.1 | 35 881 (79%) | **The largest app in the portfolio** and the fourth-thinnest. 172 lib files are never imported by a test. A medication app where the dose-logging store only just stopped failing (two red tests in yesterday's sweep). |
| 5 | **radiotune** | 10 325 | 82 | 7.9 | 5 243 (51%) | `audio_player_service.dart` (436 lines) — the entire reason the app exists — has no test that imports it. So does `auth_service.dart`. |
| 6 | **iMeasure** | 15 448 | 132 | 8.5 | 4 752 (31%) | Five of the five shipped instruments (`noise_meter`, `pedometer`, `barometer`, `protractor`, `converter`) are never imported. Yesterday's 7 failures were all layout/tab-mounting in `app_boot_test.dart` — i.e. the only file that does cover them. |
| 7 | **PilotEnRoute** | 40 100 | 364 | 9.1 | 14 340 (36%) | Second-largest app. `weight_balance_screen.dart` is 1 147 untested lines, and weight-and-balance is the one computation in an aviation app that has a safety consequence. |

Two apps look bad on raw LOC but are fine once generated code is excluded:

* **NexusTransferPay** — 15 755 raw → 6 091 product LOC (61% generated ARB).
  64 tests = 10.5 T/KLOC, and only 268 lines (4%) go unimported. Not a priority.
* **MileMaster** — 12 tests looks alarming, but the app is 610 product lines and
  **0%** of it is unimported. Adequately covered.

At the other end, FashionFactory (75.3), AGRecorder (59.1), CarDeal (42.8) and
NearServe (40.1) are the only apps where the test suite is plausibly a safety net
rather than a smoke check.

## 3. The one real failure

**FashionFactory — `test/security/release_config_test.dart:197`**, reproduced today
(`flutter test`, exit 1, `+869 -1`):

```
Expected: empty
  Actual: ['android/key.properties']
signing material must never be in the repo
```

`android/key.properties` exists in the working tree (176 bytes, created 2026-09-11
18:17). It is gitignored (`android/.gitignore:12`) and untracked, but the test scans
the **working tree**, not the index, and FashionFactory's own policy forbids signing
material on disk at all.

This is not a broken test. It is a genuine collision between the release-signing work
and FashionFactory's stated policy, and it must be resolved by whoever owns the
signing rollout — **not** by loosening the assertion to check `git ls-files` instead.
Either FashionFactory is exempted from the on-disk keystore convention, or the policy
is relaxed deliberately and documented. Deleting the check silently would remove the
only automated guard the portfolio has against committing a keystore.

Two skipped tests also remain: one in CalcMaster and
`PilotEnRoute/test/services/weather_service_fetch_test.dart` — "live traffic short or
null rows are skipped rather than throwing". Both should be given a `skip:` reason or
be made to run.

## 4. Ranked remediation

Ordered by (safety consequence × untested surface), not by how easy the work is.

1. **PilotEnRoute — `lib/screens/weight_balance_screen.dart` (1 147 lines, no test
   imports it).** Weight-and-balance is the one calculation in this portfolio that can
   hurt somebody. Extract the arithmetic out of the screen and unit-test the envelope
   maths: CG within limits, CG out of limits fore and aft, max ramp/takeoff/landing
   weight, fuel burn shifting CG in flight. Screen-level golden tests are secondary;
   the numbers are the product.

2. **MyHealth — `lib/data/train_data.dart` (1 429 lines) and the dose-logging path.**
   Yesterday's two failures were `MedicineStore a logged dose survives a relaunch` and
   `logging a dose is idempotent for the day` — exactly the two invariants a
   medication app cannot get wrong. They pass now, but 172 lib files still have no
   test importing them in a 45 K-line app. Start with `data/` (train, care, profile —
   2 871 lines of behaviour), then `screens/profile/profile_screen.dart` (1 050
   lines).

3. **radiotune — `lib/services/audio_player_service.dart` (436 lines).** The playback
   engine has zero tests. Cover: stream URL resolution, play/pause/stop state machine,
   what happens when a station 404s or the stream drops mid-play, and background
   audio-session handover. A radio app that silently fails to play is a one-star
   review, and nothing in CI would notice.

4. **VirtuBand — everything, starting with `lib/services/audio_engine.dart` (601
   lines).** 81% of the app is invisible to CI and no test renders a single screen.
   Minimum viable fix: one boot test that pumps the app root (as AGCleaner, ChefCount
   and MileMaster already do — they are the three apps at 0% unimported), then unit
   tests on the audio engine's note/instrument mapping. The boot test alone would move
   this from "untested" to "at least it starts".

5. **HerJourney — `lib/screens/home/home_screen.dart` (1 028 lines) and
   `lib/services/llm_service.dart` (516 lines).** 86% unimported, the worst in the
   portfolio, in a health app handling scan-report analysis. The LLM service is the
   right first target: it is pure logic, it is where prompt/response parsing can fail
   silently, and `screens/scan/report_analysis_screen.dart` (533 lines) depends on it.

6. **iMeasure — the five instrument screens under `lib/screens/tools/`
   (2 193 lines).** Noise meter, pedometer, barometer, protractor and converter are
   the entire product. `converter_screen.dart` in particular is pure unit conversion
   with no platform dependency — there is no excuse for it to be untested. The other
   four need their sensor streams behind an injectable interface first.

7. **Uscis-Case — `lib/services/civics_data.dart` (643 lines) and
   `lib/screens/civics_test_screen.dart` (719 lines).** The civics question bank is
   static data with a right answer; assert its shape, that every question has exactly
   one correct option, and that the scoring in the test screen matches USCIS rules.
   Wrong answers here mislead people about a naturalisation exam.

8. **Verba — the six feature screens (5 341 lines, 61% of the app unimported).**
   Verba has 582 tests, so it is not neglected — they are concentrated in the LLM
   layer. `features/paywall/screens/paywall_screen.dart` (635 lines) is the one to do
   first: a paywall that renders wrong is direct lost revenue, and it is the only
   untested screen with a money path.

9. **EventSpark — `features/live/live_screen.dart` (811 lines) and
   `features/tickets/tier_picker_screen.dart` (578 lines).** 367 tests but 63% of lib
   unimported. The tier picker is a purchase flow; test tier selection, quantity
   limits and price recalculation.

10. **Photriya — delete the 10 real `Future.delayed` sleeps in
    `test/auth/auth_comprehensive_test.dart`.** Three seconds per run, and they are
    the seed of the exact flake class that cost yourtube 30 minutes. Replace with
    `fakeAsync` or an explicit pump. Cheap, and it removes a bad pattern from the
    highest-test-count app people will copy from.

11. **Portfolio-wide: add a per-test timeout to CI.** yourtube burned 30 minutes on
    Flutter's default 10-minute-per-test timeout. `flutter test --timeout 60s` would
    have surfaced the same three failures in under a minute. Nothing in the portfolio
    legitimately needs a single test to run longer than a minute — the slowest healthy
    *suite* is 29 s.

12. **Portfolio-wide: a boot test in the 19 apps whose tests never import the app
    root.** AGCleaner, ChefCount and MileMaster are at 0% unimported precisely because
    they pump the real app. The 19 that never do — AeroSwift, AGrammarly, AGStudio,
    ApexMarketWatch, BuddyPlay, CalcMaster, CarDeal, GadgetNest, HerJourney, HomeWise,
    NearServe, NewsBoard, PlantPulse, portfolio-board, radiotune, RideZap, TripNest,
    Verba, VirtuBand — cannot catch a startup crash, a missing provider or a broken
    route in CI at all, however many unit tests they carry.

## Reproducing this

```bash
FL=/Users/spatchava/agl/.flutter-sdk/bin/flutter
cd /Users/spatchava/agl/<app>[/<subdir>]   # subdir per .sweep/appdirs.txt
"$FL" pub get
"$FL" test --no-pub --reporter compact
```

Raw logs: `.sweep/<App>.log` (analyze) and `.sweep/<App>.test.log` (test). The compact
reporter writes with carriage returns, so pipe through `tr '\r' '\n'` before grepping.

## What this report does not cover

* Line/branch coverage. No `--coverage` run was made; "untested" here means **no test
  file anywhere in the app imports that library**, computed from `package:` imports
  across each `test/` tree. A file imported transitively through a pumped app root
  counts as reached by this measure even if nothing asserts on it, so the real
  coverage gap is wider than the percentages above, never narrower.
* The 39 apps not re-run on 2026-09-13. Their rows are the 2026-09-12 sweep, and three
  of the four rows that were re-checked had already changed.
* `flutter analyze`. Eleven apps exited 1 on info-level diagnostics only (0 errors,
  0 warnings across all 43) — that belongs in the readiness audit, not here.
