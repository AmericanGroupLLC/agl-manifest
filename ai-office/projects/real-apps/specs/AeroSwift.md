# Spec — AeroSwift: what is landing at your airport right now, and a log of what you saw

- **Repo:** `/Users/spatchava/agl/AeroSwift` (Flutter app in `mobile/`)
- **base_sha:** `3fb4606ffd974ef7514e20869d28a6544b45f92d` (`git -C /Users/spatchava/agl/AeroSwift rev-parse HEAD`, 2026-10-12)
- **Branch:** `master` (`git branch --show-current`)
- **Author:** product-manager, AI Office. Written 2026-10-12. This is a spec only: no app code, store file or fastlane file was changed.
- **Store state:** Apple rejected it under 4.3 / 4.2.6 on 2026-10-05 (`/Users/spatchava/agl/.dist/rejections.json` key `AeroSwift`). Google Play: PRODUCTION_DRAFT_STAGED.
- **Baseline measured on base_sha:** `flutter analyze` gave "No issues found! (ran in 108.8s)". `flutter test` gave "+327: All tests passed!".
- **Uncommitted changes by other people in this repo (do not touch):** 16 files under `mobile/fastlane/` (metadata text and screenshots), plus `mobile/ios/Podfile.lock`, whose only change is `COCOAPODS: 1.16.2 -> 1.17.0`. Source: `git status --short` / `git diff mobile/ios/Podfile.lock`. This is the reason the spec adds **no new native plugin** to MUST: a native plugin rewrites Podfile.lock on the next `pod install`.

---

## 1. Problem

### What the app is today (read from `lib/` at base_sha)

The shell is four tabs in an `IndexedStack`: Search, Airports, Watchlist and Settings (`lib/app/app.dart:49-66`). There is no onboarding.

| Screen | What actually works | What is shallow, dead or a template tell |
|---|---|---|
| **Search** (`features/search/search_screen.dart`) | Flight-number, airline and free-text search filter a live `/states/all` world snapshot (`services/opensky_data_source.dart:116-125`). Browse lists traffic in a ±3° box round the home airport (`:219-233`). | **Route search is broken.** It asks for a 24 h departures window (`opensky_data_source.dart:256-261`, `maxLookback = Duration(hours: 24)` at `:59`). I ran the same endpoint anonymously on 2026-10-12 at about 21:45Z. `flights/departure?airport=KSFO` with a 86400 s window returned **HTTP 403**, and a 72000 s window returned 200. So the "SFO–LHR" and "JFK–LAX" example chips (`search_screen.dart:31-37`) lead to an error screen. That last step is inferred from the code: I did not run it in the app. The home tab is a generic search box with chips. |
| **Airport board** (`features/airports/airport_board_screen.dart`) | Departures work: KSFO returned 110 rows for 8 h and 126 for 20 h. | **The Arrivals tab is close to empty.** Over the same windows the arrival endpoint returned 5 rows for 8 h, 10 for 20 h, and a 404 with nothing for 2 h. Settings offers a **24h** window chip (`settings_screen.dart:29`), which hits the same 403. |
| **Flight detail** (`features/detail/flight_detail_screen.dart`) | Live altitude, speed, track, vertical rate, position, ICAO24 and callsign. A great-circle route drawn offline (`widgets/route_diagram.dart`). `/tracks/all` ground track. | Nine rows can never hold a value with OpenSky: Scheduled out/in, delays, gates, terminals, type and registration (`:380-420`, `:463-490`, `:511-524`). Each one prints **"Not published by OpenSky Network"** (`models/data_source_info.dart:59-60`). That is the text in store screenshot 01. |
| **Watchlist** (`features/saved/saved_flights_screen.dart`) | Saved on the device (`SharedPreferences`). Refresh-all. Swipe to remove. Readable offline. | No search, no filter, no export. A leftover "Removed N sample flights" notice for upgrades from the sample-data era (`:97-137`). |
| **Settings** (`features/settings/settings_screen.dart`) | Home airport picker over 3,238 bundled OurAirports rows (`assets/data/airports.psv`). Board window. Privacy choices (UMP). | **The "DATA SOURCE" radio group has exactly one option** (`:59-66`; `providers.dart:55-59` lists only OpenSky), so tapping it does nothing. The about line reads "Real-time flight tracking and aviation data." |
| **Every data screen** | — | A full-width `DataSourceBanner`: "Live data from OpenSky Network. Positions are ADS-B observations, not airline schedules." (`widgets/data_source_banner.dart:33-35`). It appears in every screenshot. Tapping it opens the dead source radio. |
| **Dead code** | — | `services/sample_data_source.dart` (649 lines of invented schedules, gates and registrations) is in `lib/` but cannot be reached from the app (`providers.dart:85-96`). Only tests use it. `DataFidelity.sample`, `FidelityBadge` and the capability flags exist only to serve it. The repo-root `README.md` and `apps/` describe a retired React Native/Expo monorepo. |

### Why Apple called it a template (this app's tells, measured)

1. **Icon** comes from the generator script: a white Material `flight` glyph on a #0B3D91→#1E88E5 diagonal gradient (`agl-manifest/scripts/generate_app_icons.py:60`). 19 other apps use the same formula.
2. **Launch screen** is the shared white storyboard. `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` gives `3f6a9b27d8…`, the same hash as 36 other apps.
3. **Shell:** Material 3 `NavigationBar` with `if (_index != _settingsIndex) const AglAdBanner()` directly above it (`app/app.dart:145,161-162`). This is the portfolio's shared shell.
4. **Theme:** `ColorScheme.fromSeed(0xFF0B6FB8)` with stock Material, radii 14 and 16 (`app/theme.dart:13-50`). No font of its own: `grep fontFamily|GoogleFonts lib` finds nothing and there is no `fonts:` block in `pubspec.yaml`.
5. **Copy that says the app does not do its job:** nine "Not published by…" rows, plus a banner on every screen.
6. **Store packaging:** feature graphic is the old "AS" monogram. The privacy label is byte-identical to 19 other apps. Notes are the shared '2. DEVICES…' skeleton. "Intended audience: Flight and airport board" is the subtitle pasted in. Listing is still marked `_drafted … NOT YET APPROVED`. `differentiation` has four TODOs (`store/apps/AeroSwift.json`).
7. **Contradictory reply (2026-09-29):** it promised "where an aircraft is and when it is going to land" and "HTTPS requests to the app's own endpoints". The notes say "AeroSwift has no backend of its own" and that it shows no arrival estimates.
8. **Code twins:** `widgets/responsive.dart` is ~0.50 Jaccard with AGStudio `responsive_body.dart`. `widgets/state_views.dart` is 0.49 with RideZap.

**What is not a tell:** the OpenSky data layer, the query parser, the offline great-circle painter and the watchlist merge logic are this app's own code, and they are good. Keep them.

---

## 2. User

**Plane spotters and aviation hobbyists who watch from one airport.** They stand at the fence or a spotting hill, or sit at home under an approach path. One question comes up again and again: *"What is on final right now, what is coming next, and what was that one?"* They know callsigns, ICAO24 hex codes and squawks. They do not need fares, gates or schedules. They keep a personal record of what they have seen.

**Secondary user:** someone under a flight path who wants to know what just flew over the house. The same screen answers that.

**Not the user:** travellers who need schedules, gates, delays or bookings. Those belong to TripNest; AeroSwift links out and adds nothing of the kind. Also not student pilots: PilotEnRoute does training and a pilot logbook. AeroSwift's log records aircraft **seen**, not hours **flown**.

---

## 3. Product

### Core job (one job, done end to end)

**Pick your airport and see, live, every aircraft around it. Each one is sorted into what it is doing (approaching, departing, overflying or on the ground), nearest first. Tap one for the full live picture and its flown track.**

The data is anonymous OpenSky `/states/all` with a bounding box. That is one small request per refresh, which I curl-verified (section 5). AeroSwift already parses this data for "browse". Today it shows the result as an unsorted list under a search box.

### Signature feature: **Approach Scope**, a live phase-sorted radar view of one airport, plus the **Spotter Log**

1. **Approach Scope (home screen).** A circular, range-ringed plan view centred on the chosen airport, painted offline in the same way as `route_diagram.dart` (no map SDK, no key). Each aircraft is a heading-oriented blip, coloured by phase, with its callsign and altitude. Range options are 10, 25 and 50 nm.
   - **Below the scope, the "Inbound now" list.** It shows aircraft classified as *approaching*, ordered by distance. Each row shows distance, altitude, ground speed and **"≈ N min out at current speed"**. N is `distance / groundSpeed`, computed on the device. It is labelled as a straight-line estimate, not an airline ETA.
   - **Phase classifier** (pure Dart, unit-tested), using the state vector plus the bundled airport position:
     - *Approaching*: airborne; baro altitude < 3,000 m; vertical rate ≤ −1.0 m/s; distance ≤ range; track within ±35° of the bearing to the airport.
     - *Departing*: airborne; vertical rate ≥ +1.0 m/s; distance ≤ 40 km; track within ±45° of the bearing *away from* the airport.
     - *On ground*: `on_ground == true` and distance ≤ 5 km.
     - *Overflying*: everything else that is airborne.
   - **Disclosure, written once on the scope's info sheet:** "Phase is inferred from position, heading and climb rate. An aircraft descending toward SFO may be landing at a nearby field."
   - **Evidence this produces real content.** In the 2026-10-12 21:44:35Z KSFO snapshot (161 states, 101 airborne), 17 aircraft within 60 km were descending below 4,000 m. They included UAL195 at 23.0 km, 1,105 m and −4.2 m/s, and UAL1074 at 16.4 km. I ran that simple filter offline against the saved response. The full classifier has not been run yet.
   - This replaces the near-empty Arrivals tab as the main way to answer "what is landing". The observed-arrivals records stay as a second section with an honest count.
   - **Competitors.** I could not run a web search in this session, so the obvious candidates (Flightradar24, FlightAware, Plane Finder) are **competitor not verified**. The claimed angle has to be checked before it goes into store copy or a reply to Apple. It is: no account, no subscription, an airport-centred list of approaching traffic sorted by phase, and an exportable personal sighting log. The PM's assumption that this is weaker in those apps is not verified.
2. **Spotter Log.** A "Log sighting" button on every blip, row and detail screen. It saves a record on the device with: ICAO24, callsign, operator (from the 94-entry `airline_directory.dart`), altitude, ground speed, phase, airport, lat/lon, UTC time, and an optional note. Every value comes from the live state at the moment of the tap.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. Approach Scope is the home tab and it works on a fresh install.**
- First launch shows onboarding (M6). After that, tab 1 is the Scope for the home airport, filled from one bbox `/states/all` call. It auto-refreshes every 20 s while visible and pauses when the app is in the background or the tab is hidden. The 20 s respects OpenSky's anonymous budget: the 2026-10-12 response header showed `x-rate-limit-remaining: 396`.
- The phase classifier lives in `lib/core/phase.dart` (or similar). It has unit tests for each phase, for the boundary angles and for null fields (no altitude, no speed or no track means *unknown*, never a guess).
- "Inbound now" list as described above, with the ≈ minutes label. The minutes are hidden when ground speed is below 30 m/s or missing.
- Tapping a blip or row opens the existing detail screen.
- **Test:** widget test with a fake `FlightDataSource` built from a fixture of real recorded state vectors. It asserts the blip count and the inbound ordering, and that an aircraft with no ground speed shows no minutes. Use the fixture, not `SampleFlightDataSource`.

**M2. Fix the broken lookback, and make Boards honest and full.**
- `maxLookback` drops to **20 h**. That is the largest window measured to return 200; 24 h returned 403 for both endpoints. Remove the 24h chip. Allowed board windows are 2, 4, 8, 12 and 20 h.
- Route search uses ≤ 20 h. Keep the SFO–LHR and JFK–LAX chips only if a test shows the route path no longer requests a window over the limit. Otherwise replace them with flight-number examples.
- The Arrivals tab opens with an **"Inbound now"** section (the M1 list for that airport), then **"Observed arrivals (last N h)"** from `/flights/arrival` with its real count. When that count is 0, the copy says what is true: "OpenSky has recorded no completed arrivals here in the last N h. Inbound traffic is above."
- **Test:** a unit test that the departure, arrival and route requests never ask for a `begin` older than 20 h. A widget test for the empty-arrivals-with-inbound state.

**M3. Spotter Log replaces the generic Watchlist (depth).**
- Persisted on the device: `SharedPreferences` JSON, following the existing `saved_flights_store.dart` pattern, or a file under app documents if it grows past a few hundred rows. Ships with migration tests.
- Search by callsign, operator or ICAO24. Filter by airport and by date range. Group by day. Swipe to delete with undo. Edit the note.
- **Export:** "Copy as CSV" to the clipboard (`Clipboard.setData`, no plugin). Columns: `utc_time,icao24,callsign,operator,phase,altitude_m,ground_speed_mps,lat,lon,airport,note`. A share sheet is SHOULD S2 because it needs a native plugin.
- Followed flights (the current watchlist entries) become a "Following" segment inside this tab. Existing saved flights migrate untouched, with a test.
- Empty state: "Nothing logged yet. Tap *Log sighting* on any aircraft in the Scope."
- **Test:** store round-trip, search and filter logic, CSV escaping (commas and quotes in notes), and migration of the existing `saved_flights` key.

**M4. Own identity: the "aeronautical chart" look (named concretely).**
- **Palette:** a hand-built `ColorScheme`, not `fromSeed`. Light uses chart paper `#F3EFE4` (surface), ink `#16233A` (onSurface), **sectional-chart magenta `#A3195B` (primary, also used for approaching)**, chart blue `#24527A` (secondary, overflying), terrain green `#4E6B3A` (tertiary, departing) and ground grey `#77736A`. Dark uses night ink `#111A29` (surface), paper text `#E9E4D6` and magenta `#E0679A`. It deliberately avoids the portfolio's near-black-plus-neon look. A grep of every Dart file under `/Users/spatchava/agl` found none of these 9 hex values in use.
- **Typography:** **B612** for UI text and **B612 Mono** for callsigns, ICAO24, altitudes, speeds and times. B612 was designed by Airbus and Intactile for cockpit displays. The fonts are bundled under `assets/fonts/` and declared in `pubspec.yaml`, not fetched at runtime. No other app in the portfolio uses B612 (grep found none); PilotEnRoute uses Orbitron and Inter. *Not verified in this session:* that the TTFs download from the official source (github.com/polarsys/b612 or Google Fonts) and that the licence is SIL OFL 1.1. The developer checks both and commits the licence file next to the fonts. If B612 cannot be obtained, **stop and report**; do not fall back to Inter or the system font.
- **Shape language:** 4 px corner radius everywhere (instrument and chart style, not 12 or 16). Hairline 1 px rules between rows. Phase colours always come with a text label or shape (blip triangle vs ground square), never colour alone.
- **Home layout:** Scope on top, inbound list below. Tabs become **Scope · Boards · Find · Log**. Settings moves to a gear icon in the Scope app bar, which removes the shared four-tab-with-Settings shell. On iOS the tab bar uses `CupertinoTabBar` styling and `CupertinoIcons` where a glyph exists (`cupertino_icons` is already a dependency). Material stays on Android.
- **Ad placement leaves the shared shell.** `AglAdBanner` is no longer in the shell `Column` above the nav bar (`app.dart:145,161`). One banner goes in the Find results and one in the Boards lists, as a list row after the 5th item. There is none on the Scope, Log or Settings. UMP consent and the Privacy choices tile stay. *(Founder question F2.)*
- **App icon:** a new hand-specified design that is not in the generator. It is a top-down aircraft silhouette crossing two range rings, in magenta `#A3195B` and ink on paper `#F3EFE4`. Remove the `"AeroSwift"` row from `scripts/generate_app_icons.py` `DESIGN` so a re-run cannot overwrite it. Regenerate every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset` and the Android mipmaps.
- **Launch screen:** the storyboard background becomes paper `#F3EFE4` with the new mark, and the Android `launch_background` matches. After the change, `shasum` of `LaunchScreen.storyboard` must no longer be `3f6a9b27d8…`.
- **Test:** a theme test asserting the primary colour, the font family and the 4 px radius. A test that the shell has no `AglAdBanner` on the Scope tab.

**M5. Remove this app's template tells and dead surfaces (honesty).**
- Delete the nine never-available detail rows (scheduled times, delays, gates, terminals, type, registration) and the `unavailableReason` "Not published by …" mechanism. The detail screen shows only what the app has. One sentence in Settings › About the data says what OpenSky does not provide.
- Replace the per-screen `DataSourceBanner` with a small **freshness line** under each list: "ADS-B via OpenSky · updated 14 s ago". It has no tap target. Attribution stays on the detail screen and in About, as OpenSky's terms require.
- Remove the single-option "DATA SOURCE" radio group from Settings.
- Move `services/sample_data_source.dart` from `lib/` to `test/support/`, and remove `DataFidelity.sample`, `FidelityBadge` and the sample-only code paths. Keep the one-time migration that drops sample flights saved by old installs, with its test, but the notice copy no longer appears for fresh installs.
- Rewrite or delete the stale root `README.md` and the `apps/` tree. Deleting `apps/`, `packages/` and `tests_suite/` (the retired React Native monorepo) needs confirmation that they are not used. *(Founder question F5.)*
- Rewrite the Settings about text ("Real-time flight tracking and aviation data.") in the app's own voice: "AeroSwift watches the sky around one airport using open ADS-B receivers. No account; your log stays on this phone."
- **Test:** a grep-style test (or CI check) that `lib/` contains none of "Not published by", "this build", "coming soon", "not connected" or "SAMPLE".

**M6. Own onboarding (two screens, skippable, no account).**
- Screen 1, **"Where do you watch from?"**: search the 3,238 bundled airports, with two or three nearby suggestions if a location fix exists (SHOULD S1 only; otherwise plain search). The choice is saved as the home airport.
- Screen 2, **"What you'll see"**: one honest card. Live ADS-B positions within about 50 nm, phase inferred from flight data, the last 20 h of observed boards. No schedules, gates or fares; those are TripNest's job, with a link out (M7).
- Stored as `onboarding_done` in prefs. Settings has "Change airport". There is no hidden or delayed content, and nothing depends on date, region or reviewer (5.6).
- **Test:** a fresh-prefs widget test shows onboarding, picking KJFK lands on a Scope titled JFK, and a relaunch skips onboarding.

**M7. Link out instead of duplicating TripNest.**
- On flight detail, a "Plan a trip on this route" text button opens TripNest's App Store/Play URL. This is the only travel-planning surface. No fares, no booking, no schedules. If the TripNest store URL is not live, leave the button out rather than linking to nothing.

**M8. Proven (plan criterion 6).**
- `flutter analyze` is clean and `flutter test` passes. The test count must not fall below the base_sha baseline of 327 passing.
- Tests that asserted removed UI (`test/widgets/flight_detail_screen_test.dart` and `test/foldable_layout_test.dart` mention the banner, Settings tab or unavailable rows) are **rewritten** to assert the new behaviour, not deleted or skipped. Each rewrite is named in the commit message.
- Commits are path-limited to `mobile/lib`, `mobile/test`, `mobile/assets`, `mobile/pubspec.*`, `mobile/ios/Runner/Assets.xcassets`, `mobile/ios/Runner/Base.lproj/LaunchScreen.storyboard`, `mobile/android/app/src/main/res` and, if confirmed, the root README. Never `mobile/fastlane/**` or `mobile/ios/Podfile.lock`.
- The app is launched on an iPhone simulator, and Scope, Boards, Find, Log and the onboarding are screenshotted on live data. A green test run is not enough.

### SHOULD

- **S1. "Use my location"** as an anchor (a "what's overhead me" scope). It needs `geolocator` (or similar) plus `NSLocationWhenInUseUsageDescription` and a new privacy-label entry. That rewrites `ios/Podfile.lock`, which has someone else's uncommitted edit, so it waits until that edit is committed by its owner. The bbox sent to OpenSky would reveal approximate location: founder question F3.
- **S2. Share sheet export** (CSV file through `share_plus`). Blocked for the same Podfile.lock reason.
- **S3. Emergency squawk highlight:** state-vector index 14 = 7500, 7600 or 7700 gets a red ring on the blip and a pinned row. This is real data; the app currently drops the field.
- **S4. Airport elevation:** regenerate `airports.psv` from OurAirports (public domain) with `elevation_ft`, so the approach threshold is above field level. This matters for high airports such as KDEN.
- **S5.** Log statistics on the device: distinct airframes seen, top operators, sightings per airport.
- **S6.** Retire the code twins: `responsive.dart` and `state_views.dart` get rewritten in this app's visual language rather than kept near-identical to AGStudio and RideZap.

---

## 5. Data source

| Data | Source | Verified |
|---|---|---|
| Live states round an airport | `GET https://opensky-network.org/api/states/all?lamin&lamax&lomin&lomax`, anonymous | `curl` 2026-10-12: **200**, 21,296 bytes, 161 states round KSFO. `x-rate-limit-remaining: 396`. |
| Observed departures | `GET /flights/departure?airport=ICAO&begin&end` | 2 h → 200 (70 rows). 8 h → 200 (110). 12 h → 200 (110). 20 h → 200 (126). **24 h → 403**. |
| Observed arrivals | `GET /flights/arrival?…` | 2 h → 404 (empty). 8 h → 200 (5). 12 h → 200 (8). 20 h → 200 (10). **24 h → 403**. Sparse, hence M2. |
| Flown track | `GET /tracks/all?icao24=&time=0` | **Not verified in this session.** My second curl batch was stopped by the office's command judge, which says external API calls belong in committed `scripts/`. The app already uses this endpoint, and `docs/api-hosts.json` lists `opensky-network.org: ok` (DNS only). |
| Airports (3,238) | Bundled `assets/data/airports.psv`, OurAirports, public domain | Read from the file header. |
| Airlines (94) | Bundled `services/airline_directory.dart` | Counted `Airline(`. |
| Spotter Log, settings | On the device (`SharedPreferences`) | — |

No Supabase, no account, no backend, no key. Nothing is invented: when a field is null, the row is hidden or says "not reported".

---

## 6. Store impact (proposed; store-compliance applies it, and this spec does not edit store files)

**Name:** keep "AeroSwift". **Category:** TRAVEL. Plane spotting has no better App Store category; Reference is an alternative (F4).

**Subtitle (30 max):** `Live approaches, spotter log` (28 characters).

**Promotional text:** "See what's on approach to your airport right now, nearest first, and keep a log of every aircraft you spot. No account."

**Description:** starts with the user's problem, not the app name, and uses no ALL-CAPS headings. Proposed draft:

> Standing at the fence and wondering what's next on final? Pick your airport and AeroSwift shows every aircraft around it on a live scope, sorted into approaching, departing, overflying and on the ground, nearest first.
>
> Each inbound aircraft shows its distance, altitude, ground speed and roughly how many minutes out it is at its current speed. That figure is a straight-line estimate worked out on your phone, not an airline arrival time. Tap any aircraft for its live position, climb rate, operator, ICAO 24-bit address and the track it has flown.
>
> Log the aircraft you see. Each sighting keeps the callsign, operator, altitude, phase, place and time. You can search and filter your log and copy it as CSV.
>
> Departure and arrival boards show what the receiver network observed at any airport since 00:00 UTC today.

*Correction (software-developer, 2026-10-13, repair round):* the line above used to say "over the last 20 hours". That is false for most of the day: OpenSky's anonymous limit is a cutoff at 00:00 UTC of the current day (curl KSFO 14:01Z: begin = midnight - 60 s and midnight exactly → 403, midnight + 1 s → 200; QA at 12:04Z: 16/19/20 h → 403). The app now says "since 00:00 UTC" (AeroSwift commit 7529c07). Any store description or review note that promises "20 hours" should use this wording instead.
>
> Data comes from the OpenSky Network's open ADS-B receivers. It shows where aircraft actually are; it has no airline schedules, gates or fares. For trip planning, AeroSwift links you to TripNest. There's no account, and your log stays on your phone.
>
> AeroSwift is free and shows ads from Google AdMob. Where consent is required you are asked first, and you can change it in Settings › Privacy choices.

The last paragraph is the shared ads paragraph made shorter. Legal must confirm the wording (F1, F6).

**Keywords:** `plane spotting,ads-b,approach,aircraft,airport,callsign,squawk,spotter log,arrivals,opensky`

**Screenshots to retake** (all from real live captures, with the UTC capture time recorded in the commit):
1. Scope at a busy airport (KSFO or KJFK) with the inbound list.
2. The Arrivals board's "Inbound now" section.
3. Flight detail with the flown track and no "Not published" rows.
4. Spotter Log with sightings the capturer actually logged from live traffic during the session. Never seeded or invented.
5. Onboarding, "Where do you watch from?".

**Feature graphic:** replace the "AS" monogram with the new icon on paper `#F3EFE4`, showing a range-ring motif.

**Review notes:** rewrite them in this app's own words. Drop the '2. DEVICES…' skeleton and the simulator/"never ships" boilerplate. Proposed core text:

> AeroSwift is for plane spotters watching one airport. On first launch, pick an airport (e.g. SFO). The home screen is a live scope of aircraft within 25 nm, sorted by phase. Tap any aircraft, then 'Log sighting'. The Log tab shows it, with search and 'Copy as CSV'. All data is anonymous OpenSky Network ADS-B. AeroSwift has no backend, no account and no sign-in. Nothing is hidden, remote-configured or region-dependent.

State honestly which physical devices were used, and only if they really were. "Intended audience" becomes the user paragraph in section 2, not the subtitle.

**Privacy label:** unchanged in substance for MUST (no new data collected). It is still byte-identical to 19 other apps. Whether a matching label is a problem is for store-compliance and F1. If S1 (location) ships, the label changes (F3).

**Correct the 2026-09-29 reply's errors in any future reply** (founder decision, Charter §1): there is no "own endpoints", and only the labelled on-device estimate replaces "when it will land".

---

## 7. Out of scope

- Trip planning, fares, bookings, hotel or ride links, airline schedules, gates, delays. These belong to TripNest and AeroSwift links out (M7).
- Pilot training, E6B, a logbook of hours flown (PilotEnRoute).
- Paid or keyed data (FlightAware AeroAPI, ADS-B Exchange paid feeds, map tile SDKs).
- An OpenSky account or authenticated access (which would extend the lookback). That needs credentials: Charter §4.
- Push notifications for watched flights. It would need a backend poller, and the app has none.
- Editing `store/apps/*.json`, `fastlane/**` or `docs/**`, or replying to or submitting to Apple.

---

## 8. Founder questions

- **F1 (legal, Charter §6).** OpenSky's terms are quoted in the app as "free for non-commercial use" (`opensky_data_source.dart` attribution). AeroSwift shows AdMob ads. Is an ad-supported app allowed under OpenSky's terms, or does it need written permission from OpenSky or a licence? This blocks resubmission no matter which features ship.
- **F2 (money).** Moving the banner out of the shell into list rows, and removing it from the home Scope, will probably lower impressions. Approve?
- **F3 (privacy / legal).** If "Use my location" (S1) ships, a bounding box near the user's position goes to OpenSky in each request. Approve, and approve the privacy-label and privacy-policy change?
- **F4.** Keep the category as TRAVEL or move it to Reference?
- **F5 (removing products, Charter §8 adjacent).** May the retired React Native/Expo trees at the repo root (`apps/`, `packages/`, `tests_suite/`, `package.json`) be deleted from the AeroSwift repo?
- **F6.** Approve the claimed competitive angle before it is used in store copy or an Apple reply. Competitors were **not verified**: web search was unavailable in this session.
