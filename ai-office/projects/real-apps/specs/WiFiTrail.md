# Spec: WiFiTrail becomes a room-by-room Wi-Fi survey you can repeat

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/WiFiTrail`, branch `main`, base_sha `e537f9b83e8a889cd5bc9c0d247cdf99e5c9164f` (`git rev-parse HEAD`, `git branch --show-current`, run today)
- Apple: rejected under **4.3 / 4.2.6** (the identical 26-app message, `/Users/spatchava/agl/.dist/rejections.json` key `WiFiTrail`, message 0). The same thread also holds Apple's automated **VPN** question; our 2026-09-29 reply was the 23-app template and does not mention VPN (message 2). The proper answer, `store/replies/WiFiTrail-vpn.md`, is still a draft. Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:69`. WiFiTrail owns connection facts and the HTTPS speed test. A grep of every repo under `/Users/spatchava/agl` for `speed.cloudflare` / `__down?bytes` / `speedtest` in `*.dart` finds hits only in WiFiTrail, so no sibling does this job.
- Baseline, measured today: `flutter analyze` → "No issues found! (ran in 12.5s)". `flutter test` → "+140: All tests passed!".

**Other people's uncommitted work is in this repo. Do not touch it:** `fastlane/**` (12 modified screenshots, 2 untracked, `fastlane/metadata/review_information/notes.txt`) and `ios/Podfile.lock` (`git status --short`, today). `git status --short lib test pubspec.yaml ios/Runner android/app/src/main` printed nothing, so no file this spec asks you to change has uncommitted edits right now. If that changes before you start, stop and report it.

---

## 1. Problem

### What the app is today (read in full: the 1382-line `lib/main.dart`, `lib/domain/*`, `lib/core/*`, `lib/l10n/app_en.arb`)

| Area | State | Evidence |
|---|---|---|
| Connection tab | **Real and careful.** It shows the transport the OS reports (it can show more than one, e.g. VPN + Wi-Fi), the SSID/BSSID when the OS releases them, a location prompt only on tap, a precise reason when the SSID is withheld, and the device's IPv4/IPv6 addresses. It re-reads on change and on resume. | `lib/main.dart:581-807`, `lib/domain/connection_info.dart`, `lib/core/network/os_connection_info.dart` |
| Speed Test tab | **Real.** Streamed HTTPS against `speed.cloudflare.com`: 5 latency samples (median, jitter), a 25 MB download and a 10 MB upload, each capped at 10 s. The bytes and seconds are shown under each figure. Six localized failure kinds, cancel, and an offline guard. | `lib/domain/speed_test.dart:216-266`, `lib/main.dart:823-1105` |
| Security tab | **Static filler.** Five generic tips, one of which is "Use a VPN on networks you do not control". The copy itself says "Advice, not a scan". It does nothing with the user's network, and it is one of the two places "VPN" appears in the binary's text (the VPN draft reply says so). | `lib/domain/security_guidance.dart:1-13`, `app_en.arb` `guidance*` |
| Persistence | **None.** A speed result disappears when you leave the tab or relaunch. No history. | no storage code in `lib/`, no storage package in `pubspec.yaml` |
| Search / filter / export | **None.** | — |
| Onboarding / settings | None. The language button and a region-conditional Privacy choices button sit in the header (`lib/main.dart:421-425`). | |
| Negation-heavy copy | A whole card on the main screen says what the app cannot do (`noNearbyScan`, `lib/main.dart:656-660`). About 47% of the store description's sentences are negations (task brief), and the description has a "WHAT IT CANNOT DO" section. | `store/apps/WiFiTrail.json` |
| Identity | Template. A `class C` palette monolith copied "verbatim from the RN app" (`lib/main.dart:57-71`), 7 of whose 12 hexes are Tailwind defaults (`0EA5E9 22D3EE 10B981 EF4444 F59E0B 7DD3FC 1E40AF`). The theme is dark-only `ColorScheme.fromSeed(C.sky)` (`:168-176`). System font. Emoji used as icons (`📡 ⚡ 🔐 ⬇️ ⬆️ 🏓`, `:114-118`, `:942-953`). Three pill tabs. Generated glyph icon (`scripts/generate_app_icons.py:79` `wifi_find`, `#01579B→#4FC3F7`). Shared splash: `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` = `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, and `LaunchImage@3x` is 540 px, both measured today. Android `launch_background.xml` is stock white. Home-screen name `Wifitrail` (`ios/Runner/Info.plist:32`), `CFBundleName` `wifitrail` (`:40`), Android label `wifitrail` (`AndroidManifest.xml:34`). pubspec description is "A new Flutter project." | as cited |
| Ads | `AglAdBanner` at the bottom of the shell column (`lib/main.dart:375`), removed during a test. Interstitial hook on every tab change (`:344-349`). | |

### Why Apple sees a template / an opportunistic variant
1. **4.3(b): "a speed test" is the most crowded utility category there is.** Today's app is a correct speed test plus connection facts, but nothing it does is beyond what any speed-test app already shows. Apple's question 3 ("What need or gap… that existing apps do not address") has no answer today. In `store/apps/WiFiTrail.json`, `differentiation` §3 still reads "TODO".
2. **4.2.6: it looks like the scaffold.** It has the generated icon, the byte-identical splash, a `class C` monolith shared with AGCleaner/ChefCount/MyFinance, the Tailwind palette with a near-black + neon-cyan dark look, the flutter-create home-screen name, and a Play feature graphic with the Flutter logo (task brief).
3. **The VPN question is still open in substance.** Apple's automated analysis flagged VPN functionality. The "use a VPN" tip in the Security tab adds to that impression, for no product value.

## 2. User and product decision

**User:** a person in a home or small office whose Wi-Fi is fine in one room and bad in another: calls drop at the desk upstairs, or the TV buffers in the bedroom. They are deciding something concrete: where to put the desk, whether moving the router helped, or whether the mesh point or extender they just bought was worth it. They want numbers for *each place*, kept, and comparable before and after a change. A one-off figure on a single screen does not answer that.

**Core job (one, done well):** walk the place, measure Wi-Fi **at each named spot** with a real HTTPS test, and get a **ranked trail of spots**, saved on the phone, that shows where the connection holds up and where it does not.

**Signature feature: "Rounds" (before-and-after comparison of the same spots).**
A trail has rounds. Round 1 is the first walk. The user changes something (moves the router, adds a mesh point, switches the band) and starts Round 2, labelled in their own words, e.g. "Router on the shelf". They walk the **same spots**, and the app shows, spot by spot, the measured change in download, upload and ping, with the evidence for each number: the readings it used, the bytes and seconds behind them, and the Cloudflare server each reading went through. If the two rounds were measured through different Cloudflare locations, or a spot has only one reading, the comparison says so next to the number and does not hide it.
- Why it fits WiFiTrail: the name finally means something. The product is a trail of spots through your home.
- Competitors: **competitor not verified.** WebSearch was blocked in this session ("Internet mode is not enabled"), so I verified no claim about Ookla Speedtest, NetSpot, Wi-Fi SweetSpots or anyone else. No competitor comparison may appear in the store copy or review notes until someone verifies it.
- Buildable now by one developer: yes. It reuses the existing `SpeedTest` engine and adds local persistence, two screens and arithmetic. No backend, no key, no paid API.

**What goes:** the Security tab (static advice, and the source of the VPN text), the main-screen "what we cannot do" card (moved into an explanation page), the three-pill tab shell, and the dark-only neon look.
**What stays and gets better:** the Connection facts (now a detail screen) and the one-off "Quick test" (which now saves to History).

---

## 3. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app). Each item is testable.

**M1. Core job end to end (plan criterion 1).** On a fresh install:
onboarding ("Where are you measuring?" → user types a place name, e.g. "Home") → Home shows the empty trail → **Measure here** → spot sheet (pick an existing spot or type a new name; suggestion chips Living room / Kitchen / Bedroom / Office / Hallway are labels only, never data) → a **spot check** runs live with the bytes counting → the reading is saved → the spot appears in the ranked trail → the user walks to the next spot and repeats.
- Add a spot-check profile to `SpeedTestConfig`: `SpeedTestConfig.spotCheck()` = 5 latency samples, `downloadBytes: 10000000`, `uploadBytes: 4000000`, `maxPhaseDuration: 6 s`. A walk of 6 rooms then takes minutes, not a quarter of an hour. The existing 25 MB/10 MB profile stays as **Full test** (Home → "Quick test", no spot, saved to History).
- Ranking per spot in the selected round: the median download of that spot's **Wi-Fi** readings. Each row shows a bar scaled to the best spot in the trail ("41% of Office"), median ping, the reading count and the time measured. The weakest spot gets a one-line callout ("Bedroom: 18% of Office's download"). All of this is arithmetic on stored readings, with no thresholds or quality labels from outside (see M6).
- Every visible control does something real. The Security tab is removed. The tests that assert it (`test/widget_test.dart:505-530`, `test/accessibility_test.dart:74-100,228-246`, `test/foldable_layout_test.dart:86`, `test/responsive_test.dart:23`, `test/wifitrail_test.dart:493-500`, the `guidanceNote` claim in `test/l10n_test.dart:158-181`) are **replaced** by tests of the new screens, plus one test asserting that no `guidance*` key and no Security screen remain. Say in the commit message that this is an intended behaviour change. No test is deleted to go green: each replaced assertion gets a successor.

**M2. Signature feature: Rounds (criterion 2).**
- Model: `Place {id, name}`, `Spot {id, placeId, name}`, `Round {id, placeId, label, startedAt}`, and `Reading {id, placeId, spotId?, roundId?, takenAt, mode (spot|full), transportAtStart, transportAtEnd, downBytes, downMs, upBytes, upMs, pingMedianMs, jitterMs, latencySamples, colo?}`. Mbps is **always derived** from bytes/ms with `megabitsPerSecond` and never stored as a free number. Only completed runs are saved. Failed and cancelled runs are not saved and keep today's failure card.
- "New round" asks for a label (default "Round 2"). The round selector on Home is a segmented control. **Compare** (Home toolbar, enabled once 2 rounds exist) picks Round A and Round B and lists every spot measured in both: download A → B with the change in Mbps and %, the same for upload, and ping in ms. Spots measured in only one round are listed underneath as "Measured only in Round 1". They are never given a delta.
- Evidence on every number: tap a spot row → the readings used, each with "10.0 MB in 2.4 s", time, transport, and "via Cloudflare SJC".
- Server location: before the latency phase, `GET https://speed.cloudflare.com/cdn-cgi/trace` and parse `colo=`. I curled it today: HTTP 200, keyless, the body includes `colo=LAX` and `loc=US`. Store `colo` only. **Do not store the `ip=` line.** If the trace fails, `colo` is null, the reading still runs, and the UI says "Server location not reported". When Round A and Round B readings went through different colos, Compare shows a note on that pair: "Measured through different Cloudflare locations (LAX / SJC), so part of this difference may be the route." Do **not** use `speed.cloudflare.com/meta`: today it returned 403 `{}` to a plain client and answered only when browser `Origin`/`Referer` headers were added, which an app should not spoof.
- Not-on-Wi-Fi guard: if `transportAtStart` or `transportAtEnd` is not Wi-Fi (the phone fell back to cellular, or the user was on ethernet), the reading is saved, flagged "Not on Wi-Fi", shown greyed, and **excluded from the ranking and from Compare**. The row explains why.

**M3. Depth (criterion 3).**
- **Persistence:** one JSON document, `trail_v1.json`, in `getApplicationSupportDirectory()` (`path_provider`, already in the pub cache, keyless). Write it atomically (temp file + rename). If the file is unreadable, rename it to `trail_v1.corrupt-<ts>.json`, start empty, and show a one-time banner saying the earlier data could not be read. Several places are supported (Home, Office, Parents'), switched by tapping the large title.
- **Search and filter:** a History screen lists every reading, newest first, with search over spot and round names. Filter chips: Place · Round · Wi-Fi only / Not on Wi-Fi · Spot checks / Full tests.
- **Share/export (keyless `share_plus`):** (a) **Export CSV** of a place (`taken_at, place, round, spot, mode, transport_start, transport_end, down_mbps, down_bytes, down_ms, up_mbps, up_bytes, up_ms, ping_ms, jitter_ms, samples, colo`), written to the temp dir and handed to the system share sheet. (b) **Share comparison** as plain text: "Home: Router on the shelf vs Round 1. Office 212 → 305 Mbps (+44%) …". Useful for a landlord, a partner, or an ISP ticket. Neither contains an SSID, BSSID, IP address or location.
- **Editing:** rename or delete a spot, a round or a place, and delete a single reading. Destructive actions confirm (iOS `CupertinoActionSheet`, Android dialog). Settings → "Delete all measurements".
- **States, each with its own copy:** first run (onboarding), a place with no spots ("Stand where you use your phone and tap Measure here"), a round with no readings yet, a spot not measured in this round, Compare with fewer than 2 rounds (button disabled, with the reason), offline (Measure disabled, with today's `speedErrorOffline` reason), a run failure (today's six localized kinds), cancelled, not on Wi-Fi, colo unknown, and storage read/write failure.

**M4. Own identity, not the shared scaffold (criterion 4).** Name these in code exactly:
- **Palette "survey map", light by default, following the system setting.** Light: background paper `#F3F1E7`, surface `#FFFFFF`, ink `#22262B`, primary spruce `#1D5C63` (Measure here, the selected round), marker amber `#D9822B` (the spot being measured, the live ring), strong `#3D7A52` (the best spot), weak berry `#A23B4C` (the weakest-spot callout), hairline `#D8D4C4`. Dark: background `#101A1C`, surface `#182528`, text `#E6ECE8`, primary `#5FB3B3`, marker `#F0A35A`, strong `#7CC08F`, weak `#E07A8A`. Build the `ColorScheme` from these explicit values, not `fromSeed`. I grepped `*.dart`, `*.md` and `*.xml` across `/Users/spatchava/agl` today (excluding dot-dirs, build and Pods), and none of these 15 hexes appears anywhere.
- **Typography:** bundle **Geologica** (variable, `Geologica[CRSV,SHRP,slnt,wght].ttf`, 348,640 B) for all UI text and headings, and **Sometype Mono** (`SometypeMono[wght].ttf`, 64,308 B) for every measured figure: Mbps, ms, MB, seconds, addresses, colo codes. Sources resolve: `curl -L github.com/google/fonts/raw/main/ofl/geologica/…` → 200 (348,640 B), `…/ofl/geologica/OFL.txt` → 200, `…/ofl/sometypemono/SometypeMono%5Bwght%5D.ttf` → 200 (64,308 B), `…/ofl/sometypemono/OFL.txt` → 200. Ship both `OFL.txt` files under `assets/fonts/` and register them with `LicenseRegistry`. They are variable fonts, so set `fontVariations: [FontVariation('wght', n)]` alongside `fontWeight` in the text theme. The weight must be checked on screen, not assumed. No repo or sibling spec under `/Users/spatchava/agl` mentions Geologica or Sometype (grep today).
- **Shape language:** no filled 12/14 px cards. The trail is drawn as a **route**: a 2 px vertical line down the leading edge joining a circular marker per spot, filled in proportion to the spot's share of the best download. Rows are separated by hairlines. Bars are 6 px tracks with square ends. Buttons have an 8 px radius. Measured figures are always set in Sometype Mono, with the unit in a lighter weight.
- **Home layout (domain-specific, not tabs):** a large title with the place name (tap to switch places) and a toolbar of History (clock) and Settings (gear). Under the title is a one-line connection strip ("Wi-Fi · <SSID>", or "Wi-Fi · name hidden" with a link to why). Tapping it opens the **Connection** detail screen, which is the current Connection tab content moved there with the location flow unchanged. Below that come the round selector and the ranked trail route. Pinned at the bottom: a full-width **Measure here** button, plus a secondary "Quick test". While measuring, a sheet shows the spot name, a live ring in marker amber driven by `SpeedTestProgress.fraction`, the phase, the bytes so far and Cancel. On iOS use `CupertinoSliverNavigationBar`, `CupertinoIcons`, `CupertinoSlidingSegmentedControl` (round selector), `CupertinoActionSheet` and `showAdaptiveDialog`. On Android use Material 3 equivalents with the same palette. No emoji anywhere in the UI.
- **Code structure:** split `lib/main.dart` into `lib/app/` (theme, fonts, routes), `lib/data/trail_store.dart`, `lib/domain/trail.dart` (model, ranking, round comparison: pure and unit-tested) and `lib/features/{onboarding,trail,measure,compare,history,connection,settings}/`. **No `class C`.** `lib/domain/speed_test.dart` and `connection_info.dart` keep their existing tested logic.
- **Onboarding (one screen, this app's words only):** title "Where are you measuring?", a name field, then three lines: "Stand where you use your phone and tap Measure here." / "Name the spot, then walk to the next one." / "After you change something, start a new round and walk the same spots." Button: "Start the trail". No "Get started", no "Welcome".
- **Settings (its own screen, its own copy):** Places · Delete all measurements · **How WiFiTrail measures** (the Cloudflare method, what the bytes/seconds mean, why the OS gates the network name, and that phones cannot list nearby networks; `noNearbyScan` moves here from the main screen) · Language (`AglLanguageScreen` is allowed as infrastructure and is opened from this row, no longer from a header icon) · Privacy choices · Privacy policy · About (version, font licences).

**M5. Remove this app's template tells (criterion 4).**
- **Icon:** a new icon **not** from `scripts/generate_app_icons.py`. It shows a dashed trail in paper `#F3F1E7` linking three spot dots on a flat spruce `#1D5C63` square, and the last dot carries two signal arcs in amber `#D9822B`. Draw it as vector geometry, with no Material glyph and no diagonal gradient. Regenerate every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset` and every `android/app/src/main/res/mipmap-*` (plus an adaptive foreground/background under `mipmap-anydpi-v26`). Remove the `"WiFiTrail"` row from the DESIGN table (`scripts/generate_app_icons.py:79`, agl-manifest, not on the do-not-edit list) so a re-run cannot overwrite it.
- **Splash:** `LaunchScreen.storyboard` gets background `#F3F1E7` with the trail mark centred, and a new `LaunchImage` set. Android `drawable/launch_background.xml` and `drawable-v21` get the same colour and mark, with a dark variant (`#101A1C`) in `values-night`. Acceptance: the storyboard's sha1 ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, and `grep -c 'red="1" green="1" blue="1"'` on it → 0.
- **Names:** `CFBundleDisplayName` → `WiFiTrail`, `CFBundleName` → `WiFiTrail`, `android:label` → `WiFiTrail`, and pubspec `description:` → "Room-by-room Wi-Fi survey with before-and-after rounds."
- **Palette:** none of the old `C` hexes (`050A14 0A1628 0F1F3D 1E3A5F 0EA5E9 22D3EE 10B981 EF4444 F59E0B F0F9FF 7DD3FC 1E40AF`) left in `lib/`. No dark-only theme.
- **Header furniture:** the header language and Privacy choices buttons are gone (moved to Settings).
- **Ads:** keep `AglAdBanner`, but as the last item **inside** the Home trail list and the History list (in flow, zero height until filled), not as a pinned shell strip. It is never shown on the measuring sheet or Compare, and never while a test runs. That last rule is today's rule, so keep its test. There are no tabs any more, so the tab-change interstitial hook goes. Whether an interstitial returns elsewhere is founder question 2 (money). Until the founder answers, call `AglAds.onTransition()` only when History or Compare is opened, never during or straight after a measurement.

**M6. Honest, and nothing that could read as hidden (criterion 5, Apple 5.6).**
- Real data only. Every number on screen comes from bytes moved on this device. No sample trails, no seeded readings, no "typical speed" figures, no quality verdicts ("Great for 4K") unless a cited published requirement backs them, and none is in scope. Relative statements ("41% of Office") are arithmetic and allowed. Keep `kNoReading` and the never-invent rule in `speed_test.dart`.
- **No SSID, BSSID, IP address or location is stored or exported.** Places and spots are names the user types. This keeps the VPN answer true ("not stored, logged or sent anywhere"). Add a test that serialises a store holding readings and asserts that the JSON and the CSV contain none of the SSID/BSSID/IP values a fake connection source supplied.
- **No region-conditional UI:** the Settings → Privacy choices row is **always visible**. Where UMP says the form applies, it opens `AglConsent.showPrivacyOptions()`. Elsewhere it opens a short sheet saying Google's consent form does not apply in this region. Check that sheet's wording against `packages/agl_ads` before finalising it.
- **No remote switches:** keep `AglInsights.init` out (the `release_sanity_test.dart` assertion stays). Add a test that greps `lib/` for `AglInsights.flag(`, `AglInsights.setting(` and `FirebaseRemoteConfig` and fails on any hit.
- No hidden gestures, no long-press-only actions (every long-press action is also in a visible menu), no debug menus, no demo login, no date/region/reviewer checks. Everything is reachable from Home in at most 2 taps.
- Copy states what the app does in positive terms. Limits are explained once, on the "How WiFiTrail measures" page and next to the value they affect (e.g. the SSID reason), not as a disclaimer card on the main screen.

**M7. Proven (criterion 6).** `flutter analyze` clean. All tests pass. No test deleted or skipped (the replaced assertions are listed in M1). New tests, at least:
- `test/trail_ranking_test.dart`: median per spot. Not-on-Wi-Fi readings are excluded. The bar fraction equals spot/best. The weakest-spot callout is correct. A spot with no reading in the round gives "not measured", never 0.
- `test/round_compare_test.dart`: the deltas in Mbps and % for spots measured in both rounds. Spots measured in only one round get no delta. The different-colo note appears exactly when the colos differ. Single-reading spots are marked.
- `test/trail_store_test.dart`: the round trip survives a reload. A corrupt file is renamed and the store starts empty with the flag set. Rename and delete cascade correctly. The privacy assertion from M6 (no SSID/BSSID/IP in JSON or CSV).
- `test/cloudflare_trace_test.dart` (with `MockClient`): `colo=` is parsed, the `ip=` line is never kept, and a trace failure leaves colo null while the run proceeds.
- `test/csv_export_test.dart`: the header and the row values, and that Mbps is derived from bytes/ms.
- Widget tests: onboarding shows once. A measurement on the fake server adds the spot to the trail, and the trail survives a re-pump with the same store. A new round plus re-measuring enables Compare and shows the delta. History search and each filter chip narrow the list. The Privacy choices row is present in both consent states. The banner is absent while a test runs.
- `test/identity_test.dart`: no `class C`, none of the old hexes, the Geologica and Sometype Mono files declared in pubspec and present on disk, light and dark themes both defined, the LaunchScreen sha differs from the shared one, `CFBundleDisplayName` == `WiFiTrail`, and no emoji code points in `lib/**/*.dart` string literals.
- **Translations:** `test/l10n_test.dart` requires every `app_en.arb` key in all 11 other locales and not left in English (`l10n_test.dart:95-150`). Every new string must be translated into ar, de, es, fr, hi, it, ja, ko, pt, ru and zh, then regenerated with `flutter gen-l10n`. Do not weaken the test to pass.
- Update `integration_test/store_screenshots_test.dart` to the new flow (it currently opens Security and the language picker).
- Commit path-limited (`git add lib test integration_test assets pubspec.yaml pubspec.lock ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main`, plus the one-line change in agl-manifest `scripts/generate_app_icons.py` committed in that repo). Never stage `fastlane/` or `ios/Podfile.lock`. Push to `main`.
- **Launch it and look at it:** build for the iOS simulator and screenshot onboarding, Home with a trail, the measuring sheet, Compare and History, in light and in dark. Green tests are not proof the screens render.

**M8. Store impact written down (criterion 7).** See section 5. store-compliance applies it. The office submits nothing (5.6 freeze, MA-043).

### SHOULD (valuable, not required for the resubmission)
- **S1. Loaded latency ("ping while busy"):** sample latency on a second connection during the download and upload phases, and show it beside idle ping. This is the figure that predicts call stutter (bufferbloat). It is real measurement, but the engine needs care to avoid self-interference, so it is not a MUST.
- **S2. Wi-Fi vs internet split:** time a TCP connect to the gateway (`NetworkInfo().getWifiGatewayIP()`, implemented on iOS in `network_info_plus-8.2.1/ios/.../FPPNetworkInfoPlusPlugin.m:58`) against the Cloudflare round-trip, to show whether a weak spot is the radio link or the line. This needs `NSLocalNetworkUsageDescription` and triggers iOS's Local Network prompt, so it needs its own primer and denial state.
- **S3. Measure twice per spot:** an option to take 2 spot checks back to back and use the median, to steady single-reading noise.
- **S4.** The PDF one-pager of a comparison (CSV + text cover the MUST).

---

## 4. Data source
- **Throughput and latency:** `https://speed.cloudflare.com/__down?bytes=N` and `/__up`, which the app already uses. Curled today: `__down?bytes=100000` → 200 with 100,000 bytes, and `POST /__up` → 200. Keyless.
- **Server location:** `https://speed.cloudflare.com/cdn-cgi/trace`. Curled today: 200, keyless, plain-text `key=value` lines including `colo=LAX` and `loc=US`. Only `colo` is kept.
- **Connection facts:** the OS, through `connectivity_plus`, `network_info_plus` and `dart:io` (unchanged).
- **Trails, rounds, readings:** the local JSON file in Application Support. It is never uploaded, and it is removed with the app or by Settings → Delete all measurements.
- No Supabase, no account, no other API, no keys. No new third party receives anything: the trace request goes to the same Cloudflare host the speed test already uses. Crashlytics and AdMob are unchanged and already disclosed.

## 5. Store impact (proposals only. I edited nothing under `store/apps/`, `fastlane/`, `docs/` or `store/replies/`)

**Name:** keep **WiFiTrail**. With trails of spots, the name now describes the product. The device name must match it (M5).
**Subtitle (≤30):** "Find your Wi-Fi weak spots" (26 characters).
**Play short description (≤80):** "Measure each room, compare runs before and after you move the router" (68).
**Promotional text:** "Changed something? Start a new round, walk the same rooms, and see what got faster, room by room, with the bytes and seconds behind every number."
**Keywords (≤100):** `wifi dead spots,room by room,wifi survey,router placement,mesh,speed test,ping,before after,home` (96 characters, counted with python `len`).

**Description (proposed, replaces the current one. Do not open with the app name, do not use the shared ALL-CAPS skeleton or the shared ads paragraph word for word):**
> Your Wi-Fi is fast in one room and useless in another. Walk your home with your phone, stop wherever you actually use it — the desk, the sofa, the bedroom — and tap Measure here. Each spot gets a real download, upload and ping measurement, and the spots line up as a trail from strongest to weakest.
>
> Then change something: move the router, add a mesh point, switch the band. Start a new round, walk the same spots, and see room by room what improved and by how much.
>
> Every figure shows its evidence: the megabytes moved, the seconds they took, and the Cloudflare location the test ran through. If two rounds went through different locations, the comparison tells you. Readings taken after your phone switched to mobile data are marked and kept out of the ranking.
>
> Keep several places (home, office, a parent's flat), search your history, and export any place as a CSV or share a comparison as text.
>
> The connection screen shows what your phone is joined to: Wi-Fi, mobile data or ethernet, the network name when you allow it, and your device's addresses.
>
> Measurements stay on your phone. There's no account. WiFiTrail is free with Google AdMob ads; where the law requires consent, Google asks first, and Settings → Privacy choices is always available. Crash reports go to Google Firebase. The network name is read on the device only when you tap Show network name, and it is never stored or sent.

(store-compliance: check the ads and crash sentences against `agl_ads`/`agl_observability` before use. Target: under 10% of sentences are negations, against 47% today.)

**Screenshots (retake all from a release-configured build on a physical iPhone, in a real home or office, by a QA person who actually walked it):**
1. Home: a trail of 5 or more real spots, ranked, with the weakest-spot callout.
2. The measuring sheet mid-run (live ring, bytes counting).
3. Compare: Round 1 vs a labelled Round 2 with per-spot deltas.
4. Spot detail: readings with "MB in s" and "via Cloudflare XXX".
5. History with search and a filter chip active.
6. (iPad/tablet) Home + Compare side by side if the layout supports it, otherwise the same set.
Remove the Settings/language screenshot and the Security screenshot. **Spot names must name where each reading was really taken.** Taking every reading at one desk and labelling them "Kitchen", "Bedroom" would be fabricated framing. The simulator cannot produce a real trail, so this needs a person and a device (founder question 5).

**Play feature graphic:** rebuild from the new icon on paper `#F3F1E7`, with the tagline "Find your Wi-Fi weak spots". The current one shows the Flutter logo and "Mobile app Wi-Fi security auditor", which is a security-scanner claim we must not make.

**Review notes (proposed, bespoke. Not the shared "2. DEVICES…" skeleton):**
> WiFiTrail measures Wi-Fi speed at named spots around a home or office, ranks the spots, and compares the same spots before and after a change (rounds).
> To try it: launch → type a place name → Start the trail → Measure here → name the spot (e.g. "Desk") → wait about 15 seconds. Move to another spot and repeat. Then tap the round selector → New round → measure the same spots → Compare. History (clock icon) lists every reading. Export CSV is in the place menu. The connection strip at the top opens connection details. Location is requested only if you tap Show network name there, and denying it changes nothing else.
> Test traffic goes to speed.cloudflare.com over HTTPS (download, upload, and `/cdn-cgi/trace` for the server location code). No account. Every feature is on the home screen. Nothing is region-, date- or server-controlled. The only regional difference is Google's ads consent form (EEA/UK/CH). Settings → Privacy choices is visible everywhere.
> VPN: WiFiTrail has no VPN functionality and no Network Extension. NetworkExtension.framework is linked by the network_info_plus plugin for `NEHotspotNetwork.fetchCurrent` (current SSID). "VPN" appears in the app only as a connection-type label when Android reports a VPN transport. The earlier "use a VPN" tip has been removed with the Security screen.
> Tested on: [QA fills in the actual physical iPhone/iPad models and iOS versions used. No simulators listed as devices.]
> Contact: [a real named person; founder question 4].

**VPN reply draft (`store/replies/WiFiTrail-vpn.md`):** I did not edit it, because replying to Apple is founder-gated (Charter §1). Before anyone sends it, it needs two corrections. (a) "VPN also appears in the app's text in two places": after this spec only the connection-type label remains. (b) "The app makes only two kinds of network traffic" is already wrong today: `store/apps/WiFiTrail.json` `notes_extra` lists three (speed test, Crashlytics, AdMob). After this spec the speed-test traffic also includes `/cdn-cgi/trace` on the same host. The "not stored, logged or sent anywhere" sentence stays true **only if** M6's no-SSID/BSSID storage rule is kept.

**Privacy label:** collection does not change (readings stay on the device, and on-device storage is not collection). store-compliance should still answer WiFiTrail's label on its own rather than reuse the 20-app identical label. Any privacy-policy wording change is a founder decision (Charter §6).

**`differentiation` §3 (gap):** proposed text for whoever answers Apple: "Per-spot measurements saved as a trail, and round-over-round comparison of the same spots, so a user can see whether a change to their network helped, room by room, with the bytes and timings behind each figure." Do not name a competitor (none was verified).

## 6. Out of scope
- Listing or scanning nearby networks, signal strength (RSSI) of other networks, channels: not available to apps on iOS, throttled and location-gated on Android.
- Floor-plan heatmaps drawn over an image (the spot list carries the job, and a heatmap would imply positions we do not measure).
- Any security scoring, router inspection, port scanning, VPN, DNS or "protection" feature or claim.
- Accounts, cloud sync, Supabase, a paid tier.
- Editing `store/apps/WiFiTrail.json`, fastlane metadata, docs or `store/replies/`. Uploading, submitting or replying to Apple.

## 7. Founder questions
1. **Removing the Security tab:** it is static advice, and it is the source of the VPN text Apple's analysis tripped on. This spec removes it rather than rewriting it. Agree?
2. **Interstitial ads (Charter §3, money):** the tab-change interstitial disappears with the tabs. Should one show when History/Compare is opened (the spec's interim default, capped by agl_ads), after a completed round, or not at all?
3. **Reply to Apple (Charter §1, MA-043):** the 4.3 thread and the open VPN question are on one thread. Who sends the corrected VPN answer and the 4.3 answers, and when, given the account-wide 5.6 freeze?
4. **App Review contact:** replace "App Reviewer" (`store/defaults.json`) with a real person's name for this app?
5. **Screenshots need a real walk:** a person with a physical iPhone has to measure 5 or more real spots in a real home or office, plus a second round after an actual change, for honest screenshots. Who does it?
6. **Access WiFi Information capability:** `store/apps/WiFiTrail.json` `_was_blocked_resolved.note` says nobody has verified that it is enabled on App ID `com.americangroupllc.wifitrail` (Apple Developer account, Charter §4). If it is not enabled, iOS never releases the SSID. Can someone with portal access confirm it?
