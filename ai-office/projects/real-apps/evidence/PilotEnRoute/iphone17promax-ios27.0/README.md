# PilotEnRoute — M8 launch on Apple's 2.1(a) device class, 2026-10-14

Simulator: `agl-qa-iphone-4` = **iPhone 17 Pro Max, iOS 27.0** (runtime 24A434), created for this
run with `xcrun simctl create agl-qa-iphone-4 iPhone-17-Pro-Max iOS-27-0`. App at pushed head
**ee701b8** (no code change). Debug build, `--dart-define=SCREENSHOT=true`.

## Drive from a fresh install (`integration_test/store_screenshots_test.dart`)
`flutter drive ... -d 14C540F3-…` → `flutter: 01:55 +2: All tests passed!` (log: `drive.log`;
re-run with `--keep-app-running`: `01:15 +2: All tests passed!`). Frames 1320×2868, looked at:

| File | What it shows |
| --- | --- |
| 01_onboarding_airport.png | "Am I legal, and inside my minimums?", home airport KPAO typed, ASEL selected, no account |
| 02_onboarding_minimums.png | Step 3 of 3: day minimums 2000 ft / 5 sm / 20 kt / 25 kt gust / 10 kt crosswind typed; night left blank; "never suggests values" |
| 03_go_card.png | Today / Go Card at 14 Oct 2026 16:45 for KPAO: **INSIDE & LEGAL**, legal rows with 14 CFR cites |
| 04_entry_form.png | Log a flight: 3 day take-offs / 3 day landings, night, instrument, checks, remarks |
| 05_logbook_search.png | Logbook search "KPAO": 1 of 1 flights, 14 Oct, C172S · N35AB · ASEL, 1.2 h, 3 ldg, "Pattern work" |
| 06_weather.png | Live METAR `KPAO 142247Z 33009KT 10SM SKC 23/14 A3007`, VFR, "No TAF is issued for KPAO", source aviationweather.gov |
| 07_kit.png | Kit: E6B, W&B, Fuel, Flight planner, Checklists ("Representative only"), Documents, Airport, Charts & plates |

## Cold relaunches (the "Checking…" freeze)
Normal app build (`flutter build ios --simulator --debug`), installed over the drive's data so the
QA profile (KPAO, ASEL, third-class medical + flight review dated today, day minimums, one flight)
stays. Each launch: `simctl terminate` → `simctl launch` (new PID each time) → screenshot ~15 s later.

| File | Result |
| --- | --- |
| relaunch-qa-profile-1..4, 6 | Today opens and the Go Card auto-checks to **INSIDE & LEGAL** ("Checked 17:10/17:11/17:12/17:16 local"); Passengers valid through 12 Jan 2027 |
| relaunch-qa-profile-5 | **CHECK INCOMPLETE**: "Legal for this flight. The latest METAR is 6 h 25 min old, so it is not treated as current." Not a freeze; the next launch was INSIDE & LEGAL again. At 17:12 PDT the METAR the app had shown (22:47Z) was ~1 h 25 min old, so this one response looked 5 h older. **Cause not verified** (a stale AWC response or an age calculation issue). Worth a follow-up |
| relaunch-fresh-1..5 | Five cold launches before the profile existed: onboarding drawn each time, no hang |

11 cold launches on iOS 27.0 iPhone 17 Pro Max, none stuck on "Checking…".

Not verified: a physical device; a release (AOT) build (Flutter refuses release on simulators);
the in-list banner placement (no AdMob unit defines in a debug build). The drive log shows
`Winds aloft (json) fetch error: FormatException … 000`. The Weather tab's winds-aloft source
answered with non-JSON at that moment. Not investigated.
