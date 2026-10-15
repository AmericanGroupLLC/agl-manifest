# Spec: iMaps, a driving app that remembers the road for you

- **Repo:** `/Users/spatchava/agl/iMaps` (Flutter app at the repo root, `lib/`)
- **base_sha:** `17916d5476d25eafe7d434a29239504cbe421768` (`git -C /Users/spatchava/agl/iMaps rev-parse HEAD`, 2026-10-12)
- **Branch:** `main` (`git branch --show-current`)
- **Author:** product-manager, AI Office. Written 2026-10-12. This is a spec only. I changed no app code, store file or fastlane file.
- **Store state:** Apple rejected it under 4.3 / 4.2.6 (the shared message, `/Users/spatchava/agl/.dist/rejections.json` key `iMaps`, version 1.0.2). The same thread also has a 2.1(a) crash on launch (iPhone 17 Pro Max, iOS 27.0), a 2.3.8 name mismatch ("iMaps: Navigate & Report" in the store vs "Maps Radar" on the device), and a 2.3.3 rejection because the 13-inch iPad screenshots showed only a splash screen. Google Play: LIVE_PRODUCTION.
- **Baseline on base_sha:** `flutter analyze` → "No issues found! (ran in 113.2s)". `flutter test` → "+510: All tests passed!". Both ran on 2026-10-12 in a working tree that includes other people's uncommitted edits, listed next.
- **Other people's uncommitted changes. Do not touch these files** (`git status --short`, 34 entries): `CLAUDE.md`, `android/app/build.gradle`, `android/app/src/main/AndroidManifest.xml`, `env/prod.json`, all of `fastlane/**`, `ios/Flutter/MapsRadar.xcconfig`, `ios/Runner.xcodeproj/project.pbxproj`, **`lib/services/admob_service.dart`**, **`lib/widgets/admob_banner_ad.dart`** and **`test/admob_ad_units_test.dart`**. Three consequences:
  - The ad widget and the ad service are reused exactly as they are.
  - `SubscriptionService` stays, because `admob_banner_ad.dart:73,136` reads it.
  - `CLAUDE.md` cannot be updated in this round, even though M5 contradicts its §3.2.7 tab rule. That is flagged to the chief-of-staff below.

---

## 1. Problem

### What the app is today (read from `lib/` at base_sha)

The shell is a custom four-slot bar, **Go · Alerts · Nearby · You**, in an `IndexedStack`. The ad banner sits directly above the bar (`lib/screens/home_screen.dart:29-34,58-62`). A first launch runs Splash, then a three-page onboarding, then Home (`splash_screen.dart:83`, `onboarding_screen.dart`).

| Screen | What really works | What is shallow, dead, false or a tell |
|---|---|---|
| **Go / map** (`screens/map_screen.dart`, 1,774 lines) | Nominatim place search (`routing_service.dart:458`). Route choice with OSRM alternatives (`route_choice_screen.dart:54-80`). Turn-by-turn HUD with localised steps. Speed versus posted limit from Overpass. An "ahead rail" of reports on the route within 5 km (`map_screen.dart:557-590`). A full-screen takeover for critical reports within 1.5 km on the route (`:596-650`). Reroute. Arrival at 60 m (`:274`). Saved Home and Work shortcuts with cached ETAs. One-tap report sheet with 5 s undo. Day, Night and Auto (sunrise/sunset) theme. | **Every report is the driver's own.** `IMAPS_BACKEND` is empty, so nothing is shared (`incident_service.dart:31-47`). The confirm/deny sheet asks the driver to confirm reports they made themselves (`:672-705`). The "AI Co-Pilot" banner (`widgets/ai_copilot_banner.dart:147`, label `'AI · SAFETY'`) is a rule-based ranker (`services/ai_suggestions_service.dart:68-80`), not AI. Dead demo and simulation code ships in the binary: `generateDemoIncidents()` (`models/incident_model.dart:632-750`), random demo descriptions and a 15 s timer (`incident_service.dart:146-170`), simulated San Francisco GPS (`location_service.dart:15-20,145-180`), and a `'🎮 SIMULATION MODE'` badge (`map_screen.dart:1154`). |
| **Alerts** (`screens/safety_feed_screen.dart`) | One feed combining the driver's own reports with USGS, NWS, GDACS, Open311 and OSM roadworks within about 2 miles (`realtime_data_service.dart:160-176`). Severity filter. Honest loading, error and no-fix states. | A permanent strip says "Reports from other drivers are not available yet…" (`:734-760`, `app_en.arb:157`). Open311 is unfiltered, so graffiti and similar requests appear as "alerts" (`realtime_data_service.dart:591`). Store screenshot 01 is exactly that list. |
| **Nearby** (`screens/nearby_services_screen.dart`) | Fuel, parking and transit from Overpass, and EV and alt-fuel from NREL (`navigation_data_service.dart:280-330`), with honest all-sources-failed copy. | NREL runs on the shared `DEMO_KEY` (`:702`), which throttles; CLAUDE.md "Keyless sources" says so too. Open Charge Map is off without a key. The POI colours are Tailwind defaults F59E0B, 10B981, 3B82F6 and 8B5CF6 (`widgets/poi_marker_widget.dart`, `nearby_services_screen.dart`). An interstitial ad fires on return to the map (`map_screen.dart:998`). |
| **You** (`screens/you_screen.dart`) | Two honest counters. Links to Notifications, Live events, Radio, Share, Language and Settings. | **The profile header always opens `LoginScreen`** (`:49-55`). `kAccountUiEnabled = false` hides the same sign-in in Settings ("Hidden for this release", `services/auth_service.dart:16-28`). That makes sign-in half-hidden, which is a 5.6 risk on an account Apple already warned. Sign-in unlocks nothing: grepping `lib/` for any sync code finds only the copy strings ("Cloud sync enabled", `settings_screen.dart:500`). The Google reversed client id is still the placeholder `REVERSED_CLIENT_ID_NOT_SET` (`ios/Flutter/MapsRadar.xcconfig`). Other copy: "Lifetime totals and an accuracy score arrive with account history" (`:78`). |
| **Radio** (`screens/radio_screen.dart`, `services/radio_service.dart`) | Lists OpenMHz, Radio Browser and LiveATC streams and opens them externally. | **MUST DROP.** It uses radiotune's source (overlap G7, `radio_service.dart:105-111`). It is also started on every map boot (`map_screen.dart:154,178-179`). |
| **Share this drive** (`screens/share_drive_screen.dart`) | An ETA snapshot by `sms:` or copy, built only from a real fix (`:24-41,167-191`). | The "IN AN EMERGENCY" dialler (`:132-141,223-250`) duplicates Kinnav (overlap G7). Its Japan entry is `110`, which is police only. Copy: "Continuous sharing needs an account and is not available yet" (`:91`). |
| **Login** (`screens/login_screen.dart`) | Supabase email, Apple, Google and anonymous sign-in. | The portfolio's sign-in family: 'Welcome back' (`:96`), 'Continue with Google' (`:280`), `supabase_config.dart`, `app_env.dart`. It also needs the shared demo account `qa@americangroup.ai` (store notes). |
| **Onboarding** | Three pages. Location is requested in context. | Page 2 promises "how many drivers confirmed it" (`onboarding_screen.dart:50`), which is false without a shared backend. It uses old mockup PNGs. The ARB still holds the paywall keys 'BEST VALUE' and 'Unlock the full experience' (12 `premium*` keys) and 'Get Started' (`app_en.arb:83,88,156`), plus the `settingsSimulation*` keys. |
| **Splash** | — | "Initializing AI navigation…" (`splash_screen.dart:230`) over a neon `NeonText` and `AiGradientMesh` layer (`theme/futuristic.dart`). It is a false AI claim. |
| **Settings** | Alert-family switches, units, appearance, privacy policy, UMP Privacy choices. | A hard-coded `'Version 1.0.2 • Navigate. Report. Connect.'` (`:133`) and 'Built with Flutter + OpenStreetMap' (`:455`). A navy gradient card `#0A1A4A→#0A0E27` (`:88-90`). A debug-only "Testing & Simulation" section (`:201-262`). |

**What is good and stays:** the OSRM route-choice and ahead-rail logic (`navigation_session_service.dart`), the localised turn instructions, the honest no-fix and all-sources-failed states, motion lock, alert families, and the posted-speed cluster. This is real navigation code, not a template.

### Why Apple called it a template (this app's tells)

1. **Name and job mirror Apple Maps.** It has the "i" prefix and a pin-on-blue-gradient icon (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png`, which I viewed). Its primary colour is a Google-Maps-like blue `#2C6BED` (`theme/app_palette.dart:151`). It was 4.3(b), "indistinguishable".
2. **The Supabase sign-in family**, with the shared demo account.
3. **Copy that says it does not do its job:** "not available yet" in four places.
4. **Paywall leftovers** in 15 ARB files, and a Poppins font that was named but never bundled (the dangling references were already removed; `app_theme.dart:94`). It has **no typeface of its own**.
5. **"AI" labels on deterministic code**, a neon "futuristic" layer, and the 'Navigate. Report. Connect.' slogan.
6. **The shared shell pattern:** the ad directly above the bottom bar. iOS shows stock Material.
7. **Overlap inside our own account:** radio (radiotune), the emergency dialler (Kinnav), and a generic Nearby directory (NearServe adjacency, overlap G11).
8. **Store packaging:** the subtitle 'Traffic, alerts & live radio'. Screenshot 01 is an Open311 graffiti list. The iPad screenshots were splash screens. The notes use the shared '2. DEVICES…' skeleton, and the 'Intended audience' line is the subtitle pasted in. The 09-29 reply claimed "incident reports from other drivers", "streaming public safety radio" and "Apple In-App Purchase", and none of those exists.

**Not tells (measured):** `LaunchScreen.storyboard` is the app's own (`shasum` = `1acdd51e…`, not the shared `3f6a9b27d8…`). iMaps is not in `generate_app_icons.py` (grep found nothing). `CFBundleDisplayName` is already "iMaps" (PlistBuddy), so the 2.3.8 name mismatch is fixed in source.

---

## 2. User

**People who drive the same roads every week**, such as commuters, school-run parents, delivery and trades drivers, and rural drivers. They know their roads have hazards no map shows: the pothole on the off-ramp, the dip that floods after rain, the school zone that matters only 7:30–8:30 on weekdays, the blind driveway, the speed trap that shows up on Fridays. Today that knowledge lives in their heads, and they get caught when they are tired, in the dark, or when someone else drives their car.

**Secondary:** someone planning a longer drive who wants official hazards on each route (NWS warnings, earthquakes, disaster alerts) before choosing one.

**Not the user:** people looking for a personal-safety or guardian app (Kinnav), a scanner or radio listener (radiotune), or a directory of service providers (NearServe). iMaps also does not claim to be a crowd-sourced traffic network. It has none, and it says that in one place, as a design choice rather than an apology.

---

## 3. Product

### Core job

**Get me there, and warn me about what's on this road: my own hazards and official ones, in the order I'll meet them.** Search, then Route check, then turn-by-turn, then arrival, with an ETA snapshot to share. Most of this exists today and works. It needs the false parts removed and its own identity.

### Signature feature: **Road Notes**, private hazard notes that speak up only when they apply

The driver taps **Mark** on a spot and chooses **Remember**. iMaps then warns them every time they approach that spot in the same direction of travel, on any future drive. A note can carry a **condition**, so it warns only when it is relevant:

- **Always**, for example a pothole or a blind exit.
- **Time window**: weekdays plus a start and end time, for example a school zone from 07:30 to 08:30. Evaluated on the device.
- **After rain**: at least X mm in the last N hours at that spot, for example "dip floods" with ≥ 5 mm in 6 h. It uses Open-Meteo `past_hours` precipitation for the note's coordinates. It is keyless, and I curl-verified it (section 5). If the rain data cannot be fetched, the note warns anyway and is labelled "rain data unavailable". It fails safe and never stays silent.

The data lives only on the phone. There is no account and nothing to sync. Notes can be exported and imported as GeoJSON, which also lets a household share its notes (M4).

**Why it is distinct (evidence, with honest limits).** I checked competitor listings through the keyless iTunes Search API on 2026-10-12 at 22:13Z. Web search was blocked in this session ("Internet mode is not enabled").
- **Waze** (waze, 3,194,610 ratings) describes hazard reports as *shared live with other drivers*.
- **Apple Maps** (Apple Inc.) says "Save places and add personal notes in Places Library". Those are place notes, and the description mentions no approach warnings and no conditions.
- **Google Maps** describes saved-place lists.
- None of the three descriptions mentions private, conditional notes that warn on approach. I did not test the apps themselves. **The claim that they lack this is not verified beyond their store descriptions** (founder question F7).
- I also checked whether *route weather* could be the signature. It cannot: **Weather on the Way** (19,929 ratings), **Drive Weather with Live Radar** (12,702) and **Highway Weather** (343) already sell forecast-at-arrival along a route, with route comparison and NWS alerts. Making that the headline would invite another 4.3(b). So the spec includes official alerts *in Route check* (M3) as depth, but not forecast-at-passage.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. The core drive works end to end on a fresh install, and every visible control does something real.**
- Search → **Route check** (M3) → Start → turn-by-turn HUD with the ahead rail → arrival screen, with no dead control on the way.
- In-drive controls: recenter, Mark (M2), Share ETA, stop.
- The confirm/deny sheet no longer asks the driver to "confirm" their own report. A tap on a note opens it for edit or archive. A tap on a one-tap report offers "Still there" (it refreshes the decay) or "Clear".
- The arrival screen's "confirms given" counter becomes "notes passed" plus "official alerts passed". Its "Was the report accurate?" question is asked only for a **note**, and the answer edits that note ("Keep warning me" or "Archive").
- **Share ETA** stays (`share_drive_screen.dart` `composeMessage`, `sms:` and copy). The emergency section and `emergencyNumberFor*` are removed (Kinnav owns that). The copy "Continuous sharing needs an account and is not available yet" is replaced with: "Sends a one-time snapshot: where you are and your arrival time."
- **Nearby becomes Stops.** It is reached from the Drive screen ("Stops" button) and shows only fuel, EV charging, parking and rest areas, as a sheet. During navigation it is ordered by distance *along the route*. Transit stays only as a parking-and-ride hint, or goes (developer's choice, recorded in the commit). The Nearby tab is removed.
- **Test:** a widget test drives search result → route check (faked `RoutingService` returning two fixture routes recorded from the real OSRM response) → Start → HUD visible → simulated position at the destination → arrival screen. That one test replaces nothing. Existing route, navigation-session and share tests keep passing.

**M2. Signature: Road Notes.**
- **Model.** A `RoadNote` in `lib/models/road_note.dart` (hand-written JSON, CLAUDE.md §3.2.2) with these fields: `id`, `kind` (pothole, flooding, school zone, sharp bend, blind exit, speed check, narrow or work zone, other), `lat`, `lng`, `bearingDeg` (the travel direction when marked, nullable), `label` (≤ 60 characters), `note` (optional), `condition` (`always` | `timeWindow{weekdays, start, end}` | `afterRain{mm, hours}`), `createdAt`, `lastWarnedAt`, `warnCount` and `archived`.
- **Service.** A `RoadNotesService extends ChangeNotifier` in `lib/services/road_notes_service.dart`, registered in `main.dart`'s `MultiProvider`. It persists to `SharedPreferences` key `imaps_road_notes_v1`, following the existing `saved_places_service.dart` pattern.
- **Creating a note.** The **Mark** button opens the existing one-tap report sheet with an added **"Remember this spot"** toggle, a kind picker, a label and a condition picker. A plain one-tap report still decays as it does today. A note does not decay.
- **Warning while navigating.** Active notes on the route within 1.5 km ahead join the ahead rail as amber diamonds and drive the `DriveAlertBanner` (reusing `metersAheadAlongRoute`).
- **Warning without navigation ("free drive").** If speed is above 15 km/h, a note within 400 m ahead with `|heading − bearingDeg| ≤ 45°` (or with no bearing stored) shows the banner, and if notifications are enabled, one local notification. Debounce: one warning per note per 10 minutes.
- **Condition evaluator.** `lib/services/note_condition.dart` is pure Dart and takes `now` and a rain lookup as inputs. Unit tests cover:
  - weekday and time edges, including windows that cross midnight;
  - a rain value above and below the threshold;
  - rain data unavailable, which must evaluate to *active* with the "rain data unavailable" flag.
- **Rain lookup.** One batched Open-Meteo call for all after-rain notes within 25 km of the driver, using `latitude=a,b,…&longitude=…&hourly=precipitation&past_hours=N` (multi-location verified, section 5). It times out after 10 s and is cached for 30 minutes.
- **Test:** service round-trip and persistence; direction filter (a note at 400 m behind the driver, or facing the opposite way, does not fire); debounce; the evaluator matrix above; a widget test that Mark → Remember → Save produces a note that appears on the map as an amber diamond.

**M3. Route check: what's on each route, before you commit.** This extends `route_choice_screen.dart`, which already counts reports per alternative.
- For each OSRM alternative (up to 3, real ones only, as now) the screen lists:
  - **your notes on this route that will be active when you pass them**. The pass time is the departure time plus the cumulative OSRM duration at that point, and the M2 evaluator runs at that time.
  - **official alerts along this route**: NWS `alerts/active?point=` at sample points every max(route length/20, 40 km), with at most 20 requests per route, deduplicated by alert id. USGS and GDACS events within 10 km of the polyline come from data `RealTimeDataService` already fetches. Only the alternative the driver selects is sampled, to respect NWS.
- **Partial failure is reported, never hidden.** In my probe 2 of 19 NWS points returned HTTP 500 (section 5). The screen then says "Official alerts checked at 17 of 19 points". It never shows "No alerts" unless every point answered.
- Outside the United States, the official-weather line reads "US weather alerts only; not available on this route". USGS and GDACS still apply.
- Network work goes in a service (`RouteCheckService`), not the screen (CLAUDE.md §3.1.2).
- **Test:** sampler spacing and the request cap; NWS deduplication; the "N of M points" wording when a fake client fails some points; the non-US wording; pass-time evaluation (a school-zone note reached at 08:10 counts, one reached at 09:00 does not).

**M4. A Notes tab with real depth.**
- **The list:** search over label and note; filter by kind and condition; sort by nearest, most warned or newest. Each row shows the condition in plain words ("Weekdays 07:30–08:30") and "warned 12 times, last 3 days ago" from `warnCount` and `lastWarnedAt`.
- **Actions:** edit (including moving the pin on a small map); archive with undo; delete with confirmation.
- **Export:** "Copy as GeoJSON" puts a `FeatureCollection` on the clipboard (`Clipboard.setData`, no new plugin). The properties are `kind`, `label`, `note`, `condition`, `bearingDeg` and `createdAt`.
- **Import:** "Paste notes" validates the GeoJSON. It rejects bad geometry, coordinates out of range, more than 500 features, or unknown kinds (which map to `other` and are counted). It shows "Added 7, skipped 2 (invalid)" and deduplicates on matching coordinates (≤ 10 m) plus label.
- **States.** Empty state: "No road notes yet. While driving, tap **Mark**, then **Remember this spot**." Offline banner on Drive: "Offline. Your notes still warn you; maps, search and routing need a connection." No-location state: the existing `LocationService.noFixMessage`.
- **Test:** search and filter logic; GeoJSON round-trip (export → import into an empty store gives equal notes); import rejection cases; deduplication; the empty-state widget.

**M5. Own identity: the "road sign" look (named concretely).**
- **Palette:** hand-built in `app_palette.dart`, replacing the Google-like blue.
  - **Day:** concrete `#ECEBE6` (bg), ink `#1B1E21` (text), **guide-sign green `#0C6B3B`** (primary, route line, Start), **warning amber `#F2B70F`** (Road Notes diamonds, with ink glyphs), cool grey `#8A8F93` (secondary text).
  - **Night:** asphalt `#15181B` (bg), retroreflective white `#F4F4EF` (text), green `#3FB97A` (primary), amber `#F2B70F`.
  - The six alert-family hues keep their meaning (CLAUDE.md §3.2.5) and are not re-mapped.
  - A grep of every Dart file under `/Users/spatchava/agl` found **0** uses of `15181B`, `ECEBE6`, `F2B70F`, `3FB97A`, `1B1E21`, `F4F4EF`, `8A8F93` and `0C6B3B`. (`0B6B3A` is used by GadgetNest, which is why the green is `0C6B3B`.)
- **Delete the neon layer:** `theme/futuristic.dart` (`AiGradientMesh`, `NeonText`, `AiPulseLoader`, `GlassCard`), the `neon*` constants (`app_theme.dart:84-87`), the Tailwind hexes in the POI widgets (use palette tokens), and the navy Settings gradient.
- **Typography:** **Overpass** for UI text and **Overpass Mono** for distances, ETAs, speeds and times.
  - Overpass is an interpretation of FHWA "Highway Gothic", the US road-sign letterforms. Google Fonts `DESCRIPTION.en_us.html` says so, and the font is licensed under SIL OFL 1.1 (`ofl/overpass/OFL.txt`, fetched 2026-10-12).
  - Files: `Overpass[wght].ttf` (318,700 B) and `OverpassMono[wght].ttf` (258,800 B) from `github.com/google/fonts/tree/main/ofl/overpass{,mono}`. Bundle them under `assets/fonts/` with `OFL.txt` and declare them in `pubspec.yaml` `fonts:`. Do not fetch them at runtime.
  - No other portfolio app uses Overpass as a font (grep of `pubspec.yaml` and `fontFamily`/`GoogleFonts` found none). The other apps' "overpass" hits are the Overpass *API*.
- **Shape language:** Road Notes are **amber diamonds**, like warning signs. Official alerts keep the existing `AlertDiamond` family colours. Cards use a 6 px radius (no 12 or 16) and a 2 px inset border on note cards, like a sign border. The Mark button is a 64 px amber diamond, bottom-right on Drive.
- **Home layout and tabs.** Tabs become **Drive · Notes · Alerts**, and Settings moves to a gear on the Drive search bar. This removes the four-slot shell and the You hub. Its rows are redistributed: Notifications merges into Alerts, Live events is the Alerts feed, Radio is dropped, Share goes to the Drive controls, and Language and Settings go behind the gear.
  - On iOS the bar uses `CupertinoTabBar` and `CupertinoIcons` (`cupertino_icons` is already a dependency, `pubspec.yaml`). Material stays on Android.
  - Keep the `IndexedStack`, so state survives tab changes.
  - **CLAUDE.md §3.2.7 forbids this tab change, and CLAUDE.md has someone else's uncommitted edits.** The developer must not edit it. The chief-of-staff must get CLAUDE.md updated by its owner, or accept the documented deviation.
- **Ads leave the shell.** Remove `const AdMobBannerAd()` from `home_screen.dart:62` and place the same widget, unmodified, as a list row after the 5th item in the **Notes** and **Alerts** lists. **No ad on the Drive screen** (a driver-distraction reason), on the onboarding or in Settings. UMP consent and Privacy choices stay. Interstitials: see F3. `admob_service.dart` and `admob_banner_ad.dart` are not edited.
- **App icon:** a new design, not in the generator. It is an amber `#F2B70F` warning diamond with an ink `#1B1E21` border. A guide-green `#0C6B3B` road curves through it, with a small white bookmark notch at the top right. Regenerate `assets/icons/app_icon.png` and `app_icon_foreground.png`, then run `dart run flutter_launcher_icons`. That writes `ios/Runner/Assets.xcassets/AppIcon.appiconset` and `android/app/src/main/res/mipmap-*`, which are not dirty. Update the adaptive and web background to `#15181B`.
- **Splash:** `flutter_native_splash` colour `#15181B` with the new mark (`pubspec.yaml` `flutter_native_splash:`). The Dart splash shows the wordmark in Overpass on asphalt, with no AI text and no neon. After regenerating, `LaunchScreen.storyboard` must still not hash to `3f6a9b27d8…`.
- **Test:** a theme test asserting primary `0xFF0C6B3B` (day) and `0xFF3FB97A` (night), font family `Overpass`, and card radius 6. A shell test asserting three tabs, no `AdMobBannerAd` in the shell or on Drive, and `CupertinoTabBar` on `TargetPlatform.iOS`. Rewrite `test/foldable_layout_test.dart` ("HomeScreen and its four tabs") for three tabs. Do not delete it.

**M6. Remove this app's template tells and dead surfaces (honesty, 5.6).**
- **Sign-in goes entirely.** It unlocks nothing and is half-hidden (section 1). Delete:
  - `screens/login_screen.dart`, `services/auth_service.dart`, `services/supabase_config.dart` and `app_env.dart`;
  - `Supabase.initialize` and `AppEnv.validate` in `main.dart`;
  - the You header, the Settings account card and the delete-account row;
  - the dependencies `supabase_flutter`, `google_sign_in`, `sign_in_with_apple` and `crypto` (only if nothing else imports it);
  - the `com.apple.developer.applesignin` key in `ios/Runner/Runner.entitlements` (tracked and clean).

  `ios/Podfile.lock` is tracked and clean, so `pod install` may rewrite it. If `pod install` changes `ios/Runner.xcodeproj/project.pbxproj` (dirty, someone else's), stop and report. Do not commit it. Leave `MapsRadar.xcconfig` alone: its unused `GOOGLE_REVERSED_CLIENT_ID` is harmless. *(F2 asks the founder to confirm that no iMaps accounts need keeping.)*
- **Radio goes:** `radio_screen.dart`, `radio_service.dart`, the `RadioService` provider, the map boot lines `map_screen.dart:154,178-179`, the You row, the `tabRadio` keys and the radio group in `test/store_claims_test.dart`.
- **Demo and simulation code goes from `lib/`:** `generateDemoIncidents`, the `IncidentService` simulation timer and random descriptions, the `LocationService` simulation and its San Francisco coordinates, the Settings debug section, the `SIMULATION MODE` badge and the `settingsSimulation*` ARB keys. If a test needs fixtures, they move to `test/support/`.
- **"AI" goes:** delete `ai_copilot_banner.dart` and `ai_suggestions_service.dart` (the ahead rail and the notes do this job honestly) and the splash "Initializing AI navigation…". No string in `lib/` contains "AI ".
- **The "not available yet" family goes:** `communityLocalOnly`/`communityUnavailable` (`app_en.arb:157-158` and all 15 ARBs), `safety_feed_screen.dart:734-760`, `report_incident_screen.dart:385-392`, the Settings "Community reports" row, and the You "Lifetime totals…" text. One line in Settings › About states the design: "iMaps keeps your notes and reports on this phone. Nothing you mark is uploaded."
- **Dead copy goes:** the 12 `premium*` keys, `onboardingGetStarted` and the stale `onboardingTitle/Desc*` keys, in all 15 ARBs. Then run `flutter gen-l10n`. Also remove the hard-coded 'Version 1.0.2 • Navigate. Report. Connect.' (take the version from no source rather than a stale constant, or drop it) and 'Built with Flutter + OpenStreetMap'. OSM and CARTO attribution stays on the map (`MapAttributionChip`).
- **Open311 is filtered** to road-relevant requests only: service names matching pothole, street light, traffic signal, sign, street or road defect, sinkhole, or obstruction. Graffiti and other non-road requests are dropped. Test it with real recorded `service_name` values.
- **The User-Agent contact is fixed.** `contact@imaps.app` appears 5 times (`routing_service.dart:120`, `navigation_data_service.dart:202`, `realtime_data_service.dart:219`, `weather_service.dart:196`, `radio_service.dart:127`). `imaps.app` has no A or MX record (Google DoH, 2026-10-12), so mail to it cannot arrive, and the OSM and Nominatim policies need a working contact. Use `iMaps/<version> (contact@americangroup.ai)`.
- **Test:** a guard test that `lib/**/*.dart` and `lib/l10n/app_en.arb` contain none of these strings:
  - "not available yet"
  - "this build"
  - "coming soon"
  - "SIMULATION"
  - "BEST VALUE"
  - "Unlock the full"
  - "Welcome back"
  - "Continue with Google"
  - "AI ·"
  - "Initializing AI"

  A second test asserts that `pubspec.yaml` has no `supabase_flutter`, `google_sign_in` or `sign_in_with_apple`.

**M7. Its own onboarding and settings copy (two screens, skippable, no account).**
- **Screen 1, "Your roads, remembered":** one sentence on Road Notes, plus the amber diamond shown live in Overpass. No stock mockup PNGs; the three `onboarding_*.png` files leave the asset list.
- **Screen 2, "What should iMaps warn you about?":** the alert-family switches from Settings, a miles/km choice, and then the in-context location request (existing `requestPermission`).
- No mention of other drivers, confirmations or AI. Stored as the existing `onboarding_complete` flag.
- Settings copy is rewritten in the app's own voice, keeping the two good existing captions (`settings_screen.dart:299-302,357-360`).
- No content depends on date, region or reviewer, and nothing is hidden behind a flag (5.6). The only build-time define affecting UI that remains is `SCREENSHOT` in the ad files, which belong to someone else. See store impact.
- **Test:** with fresh prefs onboarding is shown; completing it lands on Drive; a relaunch skips it.

**M8. Proven (plan criterion 6).**
- `flutter analyze` → "No issues found!". `flutter test` → all pass, with **at least 510 tests** (the base_sha baseline).
- Tests are deleted **only together with the code they test** (radio: `radio_service_test.dart`, 10 tests; sign-in: `account_deletion_test.dart`, 5; `app_env_test.dart`, 8; AI banner: `ai_suggestions_test.dart`, 12; the radio group in `store_claims_test.dart`). Each deleted file is named in its commit message. New tests make the total ≥ 510. No `skip:`.
- Commits are path-limited to: `lib/` except `lib/services/admob_service.dart` and `lib/widgets/admob_banner_ad.dart`; `test/` except `test/admob_ad_units_test.dart`; `assets/`; `pubspec.yaml`; `pubspec.lock`; `ios/Podfile.lock`; `ios/Runner/Runner.entitlements`; `ios/Runner/Assets.xcassets/`; `ios/Runner/Base.lproj/LaunchScreen.storyboard`; `android/app/src/main/res/`; `ARCHITECTURE.md`; `CHANGELOG.md`. Never `fastlane/**`, `env/`, `android/app/build.gradle`, `AndroidManifest.xml`, `project.pbxproj`, `MapsRadar.xcconfig` or `CLAUDE.md`.
- Do not run `dart format` (office rule for this run, which overrides CLAUDE.md §9.3).
- **Launch and look.** Run it on an iPhone simulator, and on the iOS 27 runtime if one is installed, because Apple's crash was on iOS 27.0. Use a real coordinate set through `simctl location`. Screenshot Drive, Mark → Remember, Notes, Route check and onboarding. Also run it on an iPad 13-inch simulator, since Apple rejected splash-only iPad screenshots under 2.3.3. A green test run is not enough. **The cause of Apple's 2.1(a) launch crash was not investigated for this spec.** QA must check the symbolicated log, or confirm the crash does not reproduce on the new build. A launch on a physical device is F6.

### SHOULD

- **S1. Forecast hints on Route check.** Add one line per alternative, such as "Gusts to 94 km/h near Rawlins at about 15:40", from the multi-point Open-Meteo call (verified). It stays a hint, not the headline, because of the route-weather competitors above.
- **S2. Spoken warnings** (`flutter_tts`) for notes and critical alerts. It adds a native plugin, so test it on iOS carefully.
- **S3. A share sheet** for the GeoJSON export (`share_plus`). Native; same caution.
- **S4. Rename internal "Maps Radar" identifiers** (`MapsRadarApp`, comments, `MapsRadar.xcconfig` once its owner has committed).
- **S5.** Replace NREL `DEMO_KEY` throttling with Overpass `amenity=charging_station` along the route. I verified this returns data: 22 charging stations and 17 fuel stations within 400 m of the SF to San José route.
- **S6.** Note statistics: "warned you 38 times this month".

---

## 5. Data source

All checks below were run by me on 2026-10-12 between 22:11 and 22:14 UTC, with the User-Agent `iMaps-spec-check/1.0 (contact@americangroup.ai)`.

| Data | Source | Verified |
|---|---|---|
| Routes and alternatives | `router.project-osrm.org/route/v1/driving/…&alternatives=2&steps=true` (keyless public demo server, already used) | **200**, 182,713 B, 1.26 s. SF to San José gave 2 routes: 77.5 km / 60 min and 83.4 km / 69 min. SLC to Cheyenne: 707 km, 7.4 h. |
| Place search | `nominatim.openstreetmap.org/search?format=jsonv2` (already used) | **200**, 3 results. |
| Official US weather alerts at a point | `api.weather.gov/alerts/active?point=lat,lng` | SF point: **200**, 2 alerts (Coastal Flood Advisory, Beach Hazards). Along SLC to Cheyenne, 19 sample points: 1 distinct alert (Flood Watch, Great Salt Lake Desert), and **2 points returned HTTP 500**, hence the "N of M points" rule. Only 6 of 113 national alerts carry polygons, so I query by point rather than by polygon. |
| Rain in the last N hours (after-rain notes) | `api.open-meteo.com/v1/forecast?…&hourly=precipitation&past_hours=6` | **200**, returns the hourly precipitation series for the past 6 h. Multi-location: 19 coordinates in one call → **200**, 19 locations. |
| Forecast along a route (S1 only) | same Open-Meteo, `hourly=wind_gusts_10m,visibility,…` | 19 points: max gust 94 km/h at 41.71,−106.43; min visibility 300 m at 40.96,−111.45 in the next 24 h. |
| Fuel and EV along a route (Stops, S5) | `overpass-api.de` `node(around:400,<polyline>)[amenity=fuel\|charging_station]` | **200**, 25,546 B, 6.1 s, 39 elements. |
| Earthquakes, disasters | USGS `earthquake.usgs.gov`, GDACS RSS (already used) | Not re-curled in this session. Both hosts are in use by the app today. |
| Road Notes, reports, saved places, settings | On the device (`SharedPreferences`) | — |
| Fonts | Google Fonts repo `ofl/overpass`, `ofl/overpassmono` (OFL 1.1) | GitHub API listing and `OFL.txt` fetched, **200**. |
| Competitor listings | `itunes.apple.com/search` (keyless) | Waze, Google Maps, Apple Maps, Weather on the Way, Drive Weather, Highway Weather listings read. Descriptions only; I did not test the apps. |

No Supabase, no account, no backend, no paid API, no new key. Nothing is invented: a note exists only because the driver made it, and an official alert exists only because a feed returned it.

---

## 6. Store impact (proposed; store-compliance applies it; this spec does not edit store files)

**Name:** the proposal is to drop the Apple-Maps echo (4.3(b)) and rename to **"Roadmark: Drive & Remember"**, with the device name "Roadmark", changing `CFBundleDisplayName`, the Android label and `appTitle` in the same release to avoid a repeat of 2.3.8. The iTunes Search API for "roadmark" returned no app with that name. Whether the name is free in App Store Connect is **not verified** (only a create/rename attempt proves it). This is a founder decision (F1). If "iMaps" is kept, every other change below still applies. **Category:** NAVIGATION (Kinnav moves off it, per overlap G7).

**Subtitle (≤ 30):** `Road notes that warn you` (24 characters). The radio wording goes.

**Promotional text:** "Mark the pothole, the flooding dip, the 7:30 school zone, and get warned every time you drive that way. Private to your phone."

**Description:** opens with the driver's problem, not the app name, and has no ALL-CAPS or '—— Heading ——' sections. Draft:

> You know the roads you drive every week: the pothole on the off-ramp, the dip that floods after a storm, the school zone that matters only on weekday mornings. Mark them once and get warned every time you're heading toward them, in the direction you marked them.
>
> A note can warn you always, only at certain times and days, or only after it has rained there. Rainfall comes from Open-Meteo for that exact spot.
>
> Before you set off, Route check shows each route's notes that will apply when you get to them, plus official alerts along the way: US National Weather Service warnings, USGS earthquakes and GDACS disaster alerts.
>
> Turn-by-turn directions come from OpenStreetMap data and the OSRM router, in 15 languages, with your speed against the posted limit and a dark night mode that switches at sunset. Find fuel, charging and parking along your route. Send someone a one-time message with where you are and when you'll arrive.
>
> Your notes stay on your phone. There's no account. You can copy them as GeoJSON to keep a backup or share them with your household.
>
> iMaps is free and shows ads from Google AdMob, never on the driving screen. Where consent is required you're asked first, and you can change it in Settings › Privacy choices.

The last paragraph replaces the shared "Google may use device identifiers…" ads paragraph. Legal confirms the wording (Charter §6). **Remove:** "public safety radio", "air traffic", LiveATC/OpenMHz/Radio Browser, "Companion browser extension" (F5), "incident reports from other drivers", "Initializing AI", and the "some screens are still in English" line if M6/M7 copy is translated. If it is not translated, keep that line honest.

**Keywords:** `road notes,hazard,pothole,school zone,flood,commute,route,navigation,weather alert,speed limit,gps,driving`

**Screenshots to retake.** iPhone 6.9-inch and iPad 13-inch, all real captures, none a splash or login screen (2.3.3). Notes and reports shown are ones the capturer made during the session. Official alerts are whatever the feeds returned at capture time, with the UTC capture time recorded in the commit.
1. Drive with the ahead rail showing an amber Road Note and its banner.
2. Mark → "Remember this spot" with the condition picker (Weekdays 07:30–08:30).
3. The Notes tab with search and filter chips.
4. Route check comparing two routes ("2 of your notes · 1 NWS alert · checked at 19 of 19 points", or whatever the live check says).
5. Onboarding, "Your roads, remembered".

Not the Open311 graffiti list. **Note on ads in screenshots:** the `SCREENSHOT` define in the ad files hides the banner. Since M5 removes ads from Drive, screenshots 1, 2 and 5 honestly show no ad. For 3 and 4, either capture without `SCREENSHOT`, or store-compliance accepts ad-free frames. That is their call.

**Feature graphic (Play):** the new diamond icon on asphalt `#15181B` with "Road notes that warn you" in Overpass.

**Review notes.** Rewrite them in this app's own words. Drop the '2. DEVICES…' skeleton, the simulator "never ships" line and the **demo account** (no sign-in exists, so set `demo_account_required: false` and remove `demo_account_name`). Draft core:

> iMaps is a driving app for people who drive the same roads often. On first launch choose which alerts you want and allow location while in use. To try the main feature, tap the amber Mark button on the Drive screen, turn on "Remember this spot", choose a condition and Save. The Notes tab lists it, with search and "Copy as GeoJSON". Search any destination to see Route check, then Start for turn-by-turn. There is no account, no sign-in and no in-app purchase. Data: OSRM (routing), Nominatim (search), CARTO/OSM tiles, api.weather.gov, Open-Meteo, USGS, GDACS, Overpass. Nothing is remote-configured, hidden or region-dependent. US weather alerts appear only on US routes, and the app says so.

State which physical devices were used **only if they really were** (F6). "Intended audience" becomes the section 2 user paragraph, not the subtitle.

**Differentiation answers (`store/apps/iMaps.json` → `differentiation` §3 GAP, currently TODO).** Proposed text: "Waze shares hazard reports publicly and they expire. Apple Maps keeps personal notes on places but does not warn you as you approach them. iMaps keeps private, permanent road notes that warn you on approach in your direction of travel, and only when their condition applies (time window or recent rain)." It must be approved under F7 before use. Also replace §6 (overlap with Kinnav) with: "Kinnav is on-foot personal safety. iMaps is driving and has no contacts, emergency or guardian features."

**Privacy label and Data safety.** Sign-in is removed, so there is no email or user ID. Location (precise) is used for app functionality, not linked to identity, and is sent to the routing, search, weather and alert services listed above. The advertising identifier comes from AdMob. This label must become iMaps-specific; today it is in the byte-identical 13-app group. **Privacy policy:** remove the account and sign-in sections (legal text, Charter §6).

**Correct the 2026-09-29 reply in any future reply** (founder, Charter §1): there are no reports from other drivers, no streaming radio, no In-App Purchase, and the app does not open on a sign-in screen.

---

## 7. Out of scope

- **Shared community reports** (a Waze-style network) through Supabase. It needs a migration (Charter §2) and user-generated-content moderation (Guideline 1.2: report, block, filter). See F4.
- Radio, scanners and ATC (radiotune). Emergency dialling, contacts and live location sharing (Kinnav). Service-provider directories (NearServe).
- Forecast-at-passage as a headline feature (it is S1 only). Live traffic speeds (no keyless source). Lane guidance. CarPlay and Android Auto.
- Paid or keyed data: Open Charge Map key, NASA FIRMS key, Mapbox or Google tiles.
- Fixing the AdMob unit or consent code (someone else's uncommitted edits).
- Editing `store/apps/*.json`, `fastlane/**`, `docs/**` or `CLAUDE.md`. Replying to Apple. Submitting.

---

## 8. Founder questions

- **F1 (product identity).** Rename "iMaps" to "Roadmark: Drive & Remember", on both stores? The "i" prefix plus a maps job reads as an Apple Maps variant (4.3(b)). Name availability in App Store Connect is not verified. Play is LIVE_PRODUCTION, so existing users would see the new name.
- **F2.** Remove the optional sign-in entirely (M6)? It unlocks nothing, it is half-hidden today (You tab vs `kAccountUiEnabled = false`), Google sign-in has a placeholder client id, and it forces a demo account in review. I could not verify whether any real users signed up through iMaps, or whether `delete_user` is applied (MA-044). If accounts exist, they need a deletion path on the support site after removal (legal and support).
- **F3 (money).** Move the banner out of the shell into the Notes and Alerts lists, with no ad on Drive. Also remove the two interstitials, which fire after Nearby (`map_screen.dart:998`) and **right after filing a report** (`report_incident_screen.dart:94`), both moments when the user may be driving. Revenue will probably drop. Approve?
- **F4.** Do we ever want shared reports (Supabase table + moderation + migration approval)? If not, the product stays private-by-design and the copy says so for good.
- **F5.** The repo's `extension/` (a Chrome, Edge and Firefox extension) mirrors live events and radio, and the listing advertises it. With radio dropped, should the extension be retired from the listing (Charter §8 adjacent)?
- **F6.** Apple's 2.1(a) crash happened on an iPhone 17 Pro Max with iOS 27.0, and Apple asks for testing on physical devices. The office cannot hold a phone. Who runs the build on a physical iPhone and an iPad before any resubmission?
- **F7.** Approve the competitive claim (section 3, section 6 differentiation) before it goes into store copy or an Apple reply. It rests on App Store descriptions read through the iTunes Search API, not on hands-on testing of Waze, Google Maps or Apple Maps.
- **F8 (legal, Charter §6).** The OSRM and Overpass public servers are volunteer-run demo or fair-use services. Is an ad-supported production app on `router.project-osrm.org` acceptable under its usage policy, or does it need self-hosting or a paid provider? This was not verified here. It affects iMaps whatever features ship.
