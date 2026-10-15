# Spec: TripNest — every leg of a trip in one place, with gaps found before you leave

Author: product-manager (AI office) · Date: 2026-10-12 · Project: `real-apps` (plan.md, criteria 1–7)
Repo: `/Users/spatchava/agl/TripNest` (app in `mobile/`) · Branch: `main` · Base SHA: `054282613b6d378552fd2129a97a52677c0acda3`
Store record: App Store "TripNest: Trip Planner", **rejected under 5.6** on 2026-10-08T14:19:50Z (`.dist/rejections.json` key `TripNest`; hold in `docs/store-holds.json:202`). Google Play: `LIVE_PRODUCTION`, versionCode 1 (`docs/play-production-blockers.json`).

This spec is written for the software-developer, who changes the code. This document changes nothing.

---

## 0. What I read and what the evidence shows (baseline at 0542826)

Commands I ran:
- `git -C /Users/spatchava/agl/TripNest rev-parse HEAD` returned `054282613b6d378552fd2129a97a52677c0acda3`, and `git branch --show-current` returned `main`.
- `flutter analyze` in `mobile/` returned `No issues found! (ran in 16.7s)`.
- `flutter test` returned `00:14 +463: All tests passed!`.
- `wc -l mobile/lib/**/*.dart` counted 39 files and 12,626 lines. `core/engine/travel_engine.dart` alone is 1,504 lines.

**I read the code. I did not run the app on a device or a simulator.**

### What works today (real, on-device)
- **Trips.** You can create a trip with origin, destination, dates and number of travellers (`features/trips/trips_screen.dart`, `NewTripSheet`). Trips are stored in SharedPreferences under `tripnest.trips` (`core/state/app_state.dart:197`). They split into Upcoming and Past by end date (`trips_screen.dart` `_isPast`).
- **Add a booking you made elsewhere** (`trip_detail_screen.dart`, `AddBookingSheet`). You enter a category, a title, an optional provider, a confirmation code, a date and a booked toggle. Mark as booked, Remove, and Delete trip (with a confirmation dialog) all work.
- **Partner hand-off** (`core/engine/partner_links.dart:63-151`). It builds prefilled public URLs for Google Flights, Booking.com, Airbnb and Google Maps (directions and search). It does not claim affiliation (`core/widgets/partner_handoff.dart:27-30`). On 2026-10-12 I curled each format with an iPhone user-agent:
  - Booking.com `searchresults.html?ss=…&checkin=…` returned 200.
  - Airbnb `/s/<place>/homes?…` returned 200.
  - Google Maps `/maps/dir/?api=1…` and `/maps/search/?api=1…` returned 200.
  - Google Flights `?q=Flights to …` returned 302 and landed on `/travel/flights/unsupported?q=…` for curl. **How it behaves in phone Safari is not verified.**
- **Itinerary ideas** (`features/trips/planner_screen.dart`). Five destinations (Goa, Paris, Tokyo, Bali, New York) have hand-written highlights and tips (`travel_engine.dart:1257-1322`). Any other destination gets an honest "No ideas for X yet" state. "Save as a trip" creates an empty trip.
- **Home city** prefill (`home_screen.dart` `editHomeCity`), the theme mode setting, and "Delete local data" (`settings_screen.dart:154-218`).

### What is shallow, dead, hidden or invented
1. **Most of the binary is a product that release builds never show (the likely 5.6 trigger; this is my inference).** The app ships a full search-results marketplace that release builds switch off with compile-time flags:
   - The flags: `TRIPNEST_INVENTORY` (default `sample`), `TRIPNEST_ALLOW_SAMPLE_DATA`, `TRIPNEST_SUPPLIER_CONFIGURED` and `TRIPNEST_API_BASE_URL` (`core/config/app_config.dart:26-61`).
   - `AppConfig.resultsAvailable` is false in release (`app_config.dart:78-79`).
   - Code that is compiled in but cannot be reached in release:
     - `features/results/results_screen.dart` (with `'BEST VALUE'` at `:378`)
     - `features/details/details_screen.dart` (933 lines)
     - `features/saved/saved_screen.dart`, plus the **Saved tab**, which is hidden when `showSaved` is false (`core/router/app_router.dart:31-35, 186-190`)
     - `core/widgets/result_cards.dart` (958 lines)
     - `core/engine/supplier_client.dart`, `inventory_source.dart` and `affiliate.dart`
   - The **invented inventory** that feeds them: airlines, fares, hotels, buses, cars and transfers at `travel_engine.dart:649-1040`, e.g. `_FlightBase('United Airlines', … 1.0, 0, 670, '8:40 AM' …)` at `:680`, with fares from a formula (`_flightBaseFare` `:695`).
   - **The current iPhone screenshot `fastlane/screenshots/en-US/iphone69-01.png` shows a "Saved" tab** in the bottom bar. A release build hides that tab. So the store listing showed a feature the reviewed build does not have. I looked at the image myself. That file is someone else's uncommitted change (§10).
2. **"Coming soon" scaffolding shared with EventSpark.**
   - `AppConfig.comingSoonTitle = 'Coming Soon'`, `comingSoonMessage` "Live prices and booking are coming soon…" and `comingSoonShort = 'Prices coming soon'` (`app_config.dart:94-102`).
   - `core/widgets/coming_soon.dart` (used by `booking_widgets.dart:49`, `details_screen.dart:199,525` and `saved_screen.dart:70`).
   - `inventory_source.dart:52` says "This build is not connected to live travel inventory".
   - Shown in release:
     - `monetisation_screen.dart:82` "Live prices and booking are not switched on yet"
     - `search_screen.dart:237` "TripNest does not … show live prices yet"
     - `partner_handoff.dart:43` "TripNest does not show live prices yet"
3. **Dead controls.**
   - The cabin class picker (Economy / Premium economy / Business / First) is stored in `_cabin` (`search_screen.dart:41, 217`) but never reaches a query or a link.
   - The **"Canceled"** trip filter always returns an empty list (`trips_screen.dart` `_visible`: `TripFilter.canceled => const <Trip>[]`).
4. **Shallow core record.**
   - A booking you add has only a date. It has no time, no from/to place and no time zone.
   - Date and reference are flattened into a display string (`trip_detail_screen.dart` `AddBookingSheet` save: `subtitle: details` with `'Ref …'` joined by `' · '`).
   - Legs are kept in insertion order, not time order.
   - Nothing checks whether the legs actually connect. "Missing categories" (`travel_engine.dart` `Trip.missingCategories`) only counts categories.
5. **Itinerary ideas call the invented engine.** `generateAITripPlan` (`travel_engine.dart:1330-1398`) runs `searchFlights` / `searchHotels` / `searchAirportTransfers` with a hard-coded `origin: 'New York'` and puts `bestHotel.name` into every `ItineraryDay.stay`. The screen hides those fields, but the invented data is still computed and shipped.
6. **Dead link host.**
   - `AppConfig.linkHost` defaults to `tripnest.americangroupllc.com` (`app_config.dart:155-158`).
   - It is declared in `ios/Runner/Runner.entitlements:11` (`applinks:`) and in `android/app/src/main/AndroidManifest.xml:35-40` (`autoVerify="true"`).
   - The repo's own checker, `agl-manifest/scripts/verify_api_hosts.py` `doh()`, reports it as **`NXDOMAIN`**.
   - `details_screen.dart:229` builds share links to that host.
7. **Generic home.** A wordmark, "Where do you want to go?", a pill search field, four category tiles, a "deals" carousel of 12 destinations with generated art (`tool/generate_destination_art.py`, whose own docstring says "Swap them for licensed photography before launch"), "Beach escapes" / "City breaks" collections (`travel_engine.dart:1416-1438`), and an `AdBanner` at the foot (`home_screen.dart:125`).

### Template tells in this app (from the brief; the ones I checked myself are marked ✔)
- ✔ **Twin of EventSpark.** `comm` of the two `lib/` trees gives **22 shared paths**:
  - `main.dart`
  - under `core/`: `config/app_config`, `engine/{affiliate,inventory_source,search_failure,supplier_client}`, `router/app_router`, `state/{app_state,serialisation}`, `telemetry/telemetry`, `theme/{app_colors,app_theme}`, `widgets/{coming_soon,common_widgets,error_view,skeletons}`
  - under `features/`: `about/monetisation_screen`, `menu/menu_screen`, `profile/profile_screen`, `saved/saved_screen`, `search/search_screen`, `settings/settings_screen`

  10 test paths are shared as well. `app_theme.dart:24` carries the header "TripNest theme — AmericanGroupLLC Design System v2.0".
- ✔ **Inter everywhere.** `pubspec.yaml` `fonts:` lists only Inter, and `app_theme.dart:10` has `fontFamily = 'Inter'`.
- ✔ `useMaterial3: true` (`app_theme.dart:70`). Material `NavigationBar` with 5 tabs (`app_router.dart:178-201`). There are no Cupertino widgets.
- ✔ The `LaunchScreen.storyboard` shasum is `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the shared one. Android `launch_background.xml` is plain `@android:color/white`.
- ✔ **Icon:** a white pin over an arc on an `#FF6B35`→`#D9501C` diagonal gradient (`tool/generate_icon.py:22-23`; I viewed `assets/icon/icon.png`). TripNest is **not** in `agl-manifest/scripts/generate_app_icons.py` (grep: no match), but it follows the same formula.
- ✔ The same "Your data" settings section (`settings_screen.dart:145`) and "How TripNest makes money" screen as the affiliate family.
- ✔ `'BEST VALUE'` (`results_screen.dart:378`) and "Coming Soon" (`app_config.dart:94-102`).
- ✔ **Privacy label** `store/privacy/TripNest.json`: DEVICE_ID, ADVERTISING_DATA, CRASH_DATA, PRODUCT_INTERACTION, PERFORMANCE_DATA. The brief says this is the 20-app shared label. I did not re-hash the other apps.
- ✔ **Review notes** use the shared skeleton. They open with "2. DEVICES AND OS VERSIONS TESTED", claim simulator and emulator testing, give "Intended audience: Plan trips, search every leg" (which is the subtitle), and name the contact "App Reviewer" (`store/apps/TripNest.json` `review_information`).
- ✔ **Remote Config.** `AglInsights.init` (`main.dart:30`) initialises Firebase Remote Config and runs `fetchAndActivate()` at launch (`agl_observability/lib/src/insights.dart:104-125`). TripNest reads no Remote Config value (grep for `remoteConfig` in `TripNest/mobile/lib` found nothing), but the SDK is in the binary and fetches on every launch.
- Overlaps from the brief: RideZap (ride hand-off), and AeroSwift (aviation; **not** duplicated here).

### Competitors (from the keyless iTunes Search/Lookup API, run 2026-10-12)
Web search is disabled in this session, so I used `itunes.apple.com/search` and `/lookup`. I read listing text only. **I have not verified how any of these apps actually behaves.**

| App (id) | Rating / count | What its listing says | What its listing does not say |
|---|---|---|---|
| TripIt: Travel Planner (311035142) | 4.84 / 311,802 | Forward confirmation emails to plans@tripit.com, offline access, maps. Pro at $48.99/yr adds flight alerts, fare-drop refunds and "keep you informed when a potential disruption may impact your trip". | Nothing about nights with no place to stay, legs that don't connect, or wrong-airport hand-offs. It needs an account and email forwarding. |
| Wanderlog (1476732439) | 4.90 / 35,828 | Itinerary, map, budget, collaboration, Gmail import, offline. Pro adds Google Maps export. | Nothing about checking that bookings chain together. It is built around an account and sync. |
| Tripsy (1429967544) | 4.66 / 5,636 | Day plan with "arrival buffers… see when your schedule leaves too little travel time", time zones, 10-day weather, CSV export. Smart Import is Pro. | Nothing about night-by-night stay coverage or wrong-airport chaining. It syncs to the cloud. |

**TripNest's honest angle:** no account, no inbox access, everything on the phone and working offline. It checks the whole trip as a chain: every night has a bed, every arrival connects to the next departure in real local time, and every airport has a way into town. Each gap comes with one tap to fill it on a real site. The listings above do not claim this. I have **not verified** that the apps lack it in practice.

---

## 1. Problem

People who book a multi-leg trip themselves (a flight here, a bus there, a stay from one site and a transfer from another) find the mistakes too late. A night with nowhere to sleep. A train that leaves before the flight lands, because one time was entered in the wrong zone. A connection from GOX while the flight lands at GOI. An airport an hour from the hotel with nothing booked in between. Inbox-based planners need an account and access to your email, and they mostly show what you booked rather than what you forgot.

TripNest today stores trips, but each booking is a date and a label. Around that sits an invented-price marketplace that release builds hide, and Apple rejected the app for hidden features (5.6).

## 2. User

- **Primary user:** an independent traveller planning a 3–14 day trip with two or more legs, booked across several sites. Examples: a couple doing Mumbai → Goa by flight, then a stay, then an overnight bus to Bangalore; a student doing Lisbon → Porto → Madrid by train with hostels. They plan on the phone, travel with patchy data, and do not want to hand an app their inbox.
- **Not the user:**
  - People who want to buy travel inside the app (TripNest sells nothing).
  - Corporate travellers on managed tools.
  - Aviation fans tracking aircraft: that is AeroSwift. TripNest shows no live flight positions, gates or delays.
  - Riders keeping a fare history for repeated local trips: that is RideZap's "if kept" scope.

## 3. Product

**Core job:** put every leg of one trip into a single time-ordered itinerary, shown in each place's local time, and keep it on the phone.

**Signature feature: Gap Check.** A live check of the whole trip that finds what is missing or impossible before you leave. It runs entirely on the device, against a bundled offline place and airport dataset with IANA time zones, and offers a prefilled hand-off to fill each gap.

**Kept and made honest:**
- Multi-category search (`travel_engine.dart:26-33`) becomes **"Fill this gap"**: the gap supplies the category, place and dates.
- Partner hand-off (`partner_links.dart:98-151`).
- Itinerary ideas (`planner_screen.dart:12`) become **Day ideas** inside a trip.

---

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app). Each item is testable.

**M1. Remove the hidden product and the invented data (plan criteria 1 and 5; the 5.6 fix)**
- **Delete these files:**
  - `features/results/`, `features/details/`, `features/saved/`
  - `features/menu/`, `features/profile/`, `features/about/monetisation_screen.dart` (their useful rows move into Settings, M8)
  - `core/engine/supplier_client.dart`, `inventory_source.dart`, `affiliate.dart`, `search_failure.dart`
  - `core/widgets/coming_soon.dart`, `result_cards.dart`, `skeletons.dart`, and any `booking_widgets.dart` code that only served results
- **Remove from `travel_engine.dart`:**
  - every `*Result` class
  - every `_*Base` table and `search*()` function
  - `sortResults`, `filterNonstop` and `SortOrder`
  - `dealCollections`
  - `generateAITripPlan`'s calls to the search functions, and its hard-coded `'New York'`
- **Remove from `AppConfig`:**
  - every `TRIPNEST_*` `--dart-define`, `InventoryMode`, `sampleDataBlocked`, `liveBookingAvailable` and `resultsAvailable`
  - `comingSoon*`, `affiliateMarker` and `linkHost` / `deepLink`
  - `buildDescription` (it prints "sample inventory")
- **Remove the dead link host:** the `applinks:tripnest.americangroupllc.com` entry in `ios/Runner/Runner.entitlements`, and the `autoVerify` intent-filter for that host in `AndroidManifest.xml` (NXDOMAIN, §0.6). Do **not** touch `project.pbxproj`.
- **Remove the dead controls:** the cabin class picker and the "Canceled" filter.
- **No build-time or remote switch may change what the app shows.** TripNest code reads no Remote Config value; the founder decides on the SDK itself (§9 Q4).
- **Done when:**
  - `grep -rniE "coming soon|this build|not connected|not available yet|not switched on|sample|BEST VALUE|LOWEST PRICE|QUICKEST|fromEnvironment|remoteConfig|americangroupllc\.com" mobile/lib` returns nothing, except the two AdMob unit-id defines in `lib/core/ads/ad_config.dart` (`String.fromEnvironment('ADMOB_BANNER_ANDROID')` and `('ADMOB_BANNER_IOS')`). Amended 2026-10-14 under the founder's delegation (decision log, 2026-10-14): this bullet targets the `TRIPNEST_*` feature switches removed above. The two unit-id defines supply the production banner ids at release build time, gate no feature and no content, and follow the portfolio convention (`scripts/agl_paths.py` `admob_defines`; the same exception as RoomCraft M7 and Uscis-Case M1(a)). `test/release_shape_test.dart` pins them as the only defines, in that one file, and `test/ads_test.dart` keeps production unit ids out of `lib/`.
  - `grep -rn "United Airlines\|Priceline\|_flightBaseFare" mobile/lib` returns nothing.
  - `grep -rn "tripnest.americangroupllc.com" mobile/ios/Runner mobile/android/app/src` returns nothing.
  - The router has no `/results`, `/details` or `/saved` route.

**M2. Structured legs and a time-ordered itinerary (plan criterion 1, core job)**
- **Replace `TripItem` with a `Leg` model.** Fields:
  - `kind`: flight, train, bus, ferry, car rental, stay, transfer/ride, other
  - `from` and `to` as `Place` (for a stay, one `Place`)
  - `start` and `end` as **local wall-clock date-time plus the place's IANA zone** (departure zone for start, arrival zone for end)
  - `provider` (free text), `confirmationCode`, `notes`, `status` (planned / booked)
  - Optional `number` (flight or train number, free text)
- **Leg editor:**
  - Add, edit, duplicate and delete legs.
  - Pickers for date and time.
  - The kind decides the labels: Depart/Arrive, Check-in/Check-out, Pick-up/Drop-off.
  - The editor validates that end is not before start **in absolute time**, and shows both local times plus the duration (e.g. "Dep 23:40 BOM, arr 01:05 GOI next day, 1 h 25 m").
- **Trip page = timeline:**
  - Legs sorted by absolute start instant and grouped under day headers in the local time of the leg's start place.
  - A day header shows the place's local date. When the zone changes inside a day, the header says so ("Clocks: now UTC+1").
  - Each leg row shows its local times in DM Mono, the place codes, provider, confirmation code (tap to copy, with a haptic and a snackbar), and its status.
- **Migration of existing Play users' data.** TripNest is live on Play, so data in `tripnest.trips` must survive the update:
  - Each old item becomes a `Leg` with the same title, provider, status and category→kind.
  - The date and `Ref …` are parsed back out of the subtitle where the `' · '` pattern matches. Anything else goes into `notes`.
  - `tripnest.saved` is dropped. It cannot have held anything in a release build.
  - The stored format gets a version key, `tripnest.schema = 2`.
- **Done when:**
  - Unit tests cover ordering across zones: a JFK 22:00 departure arriving LHR 10:00 next day sorts before a LHR 12:00 train.
  - A unit test covers the migration of a recorded v1 JSON blob, including the `'Oct 25 · Ref K7QX2M'` form.
  - A widget test covers add → edit → delete of a leg, and copy of a code.

**M3. Offline place and airport search with time zones (plan criteria 3 and 5)**
- **Bundle a trimmed dataset in `assets/data/`, built by a committed script `mobile/tool/build_places.py`** (run with `python3 -I`). The script also writes the attribution file.
  - **GeoNames `cities5000`.** Licence CC BY 4.0 (readme lines 6-7: "This work is licensed under a Creative Commons Attribution 4.0 License"). `https://download.geonames.org/export/dump/cities5000.zip` returned 200, 69,793 rows. Keep name, asciiname, a few Latin-script alternate names, country code, admin1 name, lat/lon (5 dp), IANA timezone and population. Admin1 names come from `admin1CodesASCII.txt` (200).
  - **OurAirports `airports.csv`.** `https://davidmegginson.github.io/ourairports-data/airports.csv` returned 200. Keep rows with an IATA code and `scheduled_service=yes` (4,133 rows today): IATA, name, municipality, country, lat/lon. Each airport's time zone is taken from the nearest GeoNames place. The script asserts every airport got a zone.
  - **Licence: not verified.** I could not read OurAirports' public-domain statement from the site with curl (the page is script-rendered, and the GitHub README had no licence line). The AeroSwift spec already relies on OurAirports as public domain (`specs/AeroSwift.md:157`). The developer must confirm the licence text before shipping and record it in the attribution file.
  - **Size budget:** at most 3 MB compressed in the bundle. The developer measures and reports the real size.
- **Place picker:**
  - Type-ahead over name, ascii name, alternate names and IATA code. Results are ranked by exact IATA match, then prefix match, then population.
  - Each row shows "Name, Region, Country" plus the IATA code for airports, e.g. "Goa Dabolim Intl (GOI) · Vasco da Gama, IN" and "Manohar Intl (GOX) · Mopa, IN".
  - The picker **never auto-picks**. The user taps a row. (Why: the Open-Meteo geocoder returned **Genoa, Italy** as the first hit for "Goa". A fuzzy first hit cannot be trusted, and the offline list has the same risk.)
  - A "Use '…' as typed" fallback lets the user name a place the dataset doesn't have. The user must then pick its time zone from a list, and Gap Check treats it as having no coordinates (no distance checks).
  - It works in airplane mode, with no network call at all.
- **Attribution:** Settings › About shows "Places: GeoNames (CC BY 4.0)" and "Airports: OurAirports".
- **Done when:**
  - Tests: "goi" ranks GOI first; "Candolim" resolves to IN / `Asia/Kolkata`; "Lisbon" offers Portugal before Lisbon, Ohio (population ordering); a typed place requires a zone.
  - The asset loads in under 500 ms on the test host (measured and logged).

**M4. Gap Check, the signature feature (plan criterion 2)**
- A **Gap Check** panel sits at the top of every trip with legs, and a count badge appears on the trip card. The rules are pure Dart functions in `lib/core/gaps/gap_check.dart` with no Flutter imports.
  1. **Nights with no bed.**
     - Every night from the trip start date to the day before the end date (destination local) is a cell in a **nights strip**.
     - A night is covered by a stay where check-in date ≤ night < check-out date, or by an overnight transport leg that departs that evening and arrives the next local day.
     - An uncovered night produces a **Gap**: "Night of Tue 27 Oct — nowhere to stay yet". The cell is outlined in gap red.
  2. **Legs that don't connect.** For time-ordered moves A then B:
     - If A's arrival place and B's departure place are more than 50 km apart (haversine on coordinates), that is a **Gap**: "You arrive in Goa (GOI) but your next leg leaves from Mumbai (BOM)".
     - If they are two different airports or stations 5–50 km apart, that is a **Check**: "Different airport: you land at GOI and leave from GOX, about 40 km apart in a straight line." Always say "straight line".
  3. **Time conflicts.**
     - B starting before A ends, compared in absolute time, is a **Gap**: "Overlap: the bus leaves 1 h 10 m before the flight lands. Check the times and time zones".
     - B starting less than 60 min after a flight lands (flight to flight), or less than 30 min after any other arrival, is a **Check**: "Tight: 40 min between landing at GOI and the next departure".
     - These thresholds are product defaults. The panel states them, e.g. "We flag connections under 60 min after a flight".
  4. **No way into town.** An arrival at an airport or station followed by a stay more than 15 km away, with no transfer, ride or car leg between them, is a **Gap**: "No way yet from GOI to your stay in Candolim (about 29 km)".
  5. **Double-booked night.** Two stays covering the same night is a **Check**: "Two stays booked for the night of 28 Oct". This one can save real money.
  6. **No way home** (only when a home city is set, M8). If the last move does not end within 50 km of home, that is **Info**: "No way home yet". It stays Info, never a Gap, because many trips are one-way.
- **Each finding has:**
  - a severity: Gap, Check or Info, each with its own colour and icon
  - one plain sentence that names the real places and local times
  - actions: **Fill this gap** (M5), **Edit leg**, and **It's fine** (dismiss)
- **Dismissals** persist per finding id (rule + leg ids). They come back if the legs involved change.
- **All clear:** with no findings, the panel says "Every night has a bed and every leg connects." It does not say this for an empty trip; an empty trip shows the M6 empty state.
- **Done when:** a unit test exists for every rule, covering both a positive and a negative case, including:
  - an overnight bus covering a night
  - a JFK→LHR overnight flight where local dates differ
  - a stay checked out on the trip end date, which must not flag the last night
  - GOI/GOX
  - a typed place with no coordinates, which skips the distance rules and says "Can't check distance for 'X'"

  A widget test renders the panel with one finding of each severity, and the "It's fine" dismissal survives an app restart (SharedPreferences round trip).

**M5. Fill this gap, then record it (plan criteria 1 and 3)**
- **"Fill this gap"** opens a sheet with the existing `partner_links.dart` formats, prefilled **from the gap** rather than from a blank search form:
  - A night gap gives Booking.com and Airbnb for that place and those nights.
  - A disconnected leg gives Google Flights (when both ends have an airport) and Google Maps transit directions.
  - "No way into town" gives Google Maps driving directions from the airport to the stay. If the founder approves D1, it also gives Uber and Lyft (S2).
- **Keep the honest line** from `partner_handoff.dart:27-30`: these sites are not affiliates, and TripNest earns nothing from these links. Keep opening links in the **external** browser.
- **Remove these lines:** "TripNest does not show live prices yet" and similar. The sheet simply describes what each site will show.
- **After returning to the app**, a "Booked it? Add the details" button opens the M2 editor prefilled with the kind, places and dates from the gap.
- **Google Flights:** QA must open the link on a physical iPhone. If it lands on Google's "unsupported" page there, as it did for curl, drop Google Flights and offer only the other sites.
- **Done when:** unit tests check the exact URL built for each gap type (place names, dates, party size), and a widget test checks that "Add the details" opens the editor prefilled.

**M6. Depth: search, filter, share, offline, empty and error states (plan criterion 3)**
- **Trips list:** Upcoming / Past segments; a search field matching trip name, places, provider and confirmation code; sort by start date.
- **Share a trip as plain text** through the share sheet (`share_plus` 13.x; pub.dev latest 13.3.1). The text is the day-by-day itinerary in local times with codes, plus the open Gap Check findings. Also offer **Copy itinerary**. No link to any TripNest host.
- **Offline:** every screen except the partner sites works in airplane mode. Opening a partner link with no connection shows "You're offline. The link will work once you're connected" instead of a silent failure.
- **Empty states:**
  - No trips: "Start a trip: where are you going and when?", with a button.
  - Trip with no legs: "Add the first leg: a flight, train, bus or stay."
  - Search with no match: "No trip matches 'x'."
  - Past with nothing in it: honest copy, no illustration filler.
- **Corrupt storage:** if a saved blob fails to parse, keep the raw blob under a backup key, show "Some trip data couldn't be read. It's been kept so nothing is lost", and carry on.
- **Done when:** widget tests cover each empty state, search across code and provider, the share text (golden string), and the corrupt-blob path.

**M7. Its own identity (plan criterion 4)**
- **Palette, "Lagoon and route".** Hand-built `ColorScheme`, not `fromSeed`, with `ThemeMode.system`. Replace every value in `app_colors.dart` and `app_theme.dart`; `FF6B35` and the category tints go.

  | Role | Light | Dark |
  |---|---|---|
  | Background (cloud) | `#F2F5F6` | `#0D1A1D` |
  | Surface | `#FFFFFF` | `#152629` |
  | Ink | `#102A30` | `#E6F0F1` |
  | Muted | `#5E7176` | — |
  | Primary (lagoon) | `#0B7A83` | `#4FC3CC` |
  | Gap red | `#C93A2E` | — |
  | Check amber | `#985A00` | — |
  | Clear green | `#2F7D4F` | — |

  - I grepped every portfolio `lib/` and every real-apps spec for these 12 hexes on 2026-10-12. None is used.
  - The orange of the old EventSpark/TripNest twin is gone. EventSpark moves to plum/amber (`specs/EventSpark.md:205-206`), so the two no longer share a hue.
  - Contrast I computed (WCAG formula): white on lagoon 5.09:1; ink on cloud 13.73:1; lagoon on cloud 4.65:1; muted on cloud 4.68:1; gap red on white 5.09:1; amber on white 5.53:1; green on white 5.04:1; dark ink on dark background 15.3:1; dark lagoon on dark background 8.46:1. (I dropped `#B26B00` at 4.2:1 and `#9A5C00`, which GroceryMatch uses.)
  - A test asserts at least 4.5:1 for every text pair the theme uses, in both modes.
- **Typography (bundled; no `google_fonts`, no runtime fetch):**
  - **Rethink Sans** (`ofl/rethinksans/RethinkSans[wght].ttf`, 200, 120,588 B) for UI and headings.
  - **DM Mono** (`ofl/dmmono/DMMono-Regular.ttf` 200, 49,744 B; `DMMono-Medium.ttf` 200, 50,360 B) for every time, date, duration, IATA code and confirmation code, with tabular figures.
  - Add both `OFL.txt` files (200) and register them in `LicenseRegistry`. Remove Inter and its assets.
  - `grep -rli` for "rethink" and "dm mono|dmmono" across specs, every app `lib/` and every `pubspec.yaml` found **0 files**. (Chivo, Hanken Grotesk and Schibsted Grotesk were rejected: iMeasure, CodeDeal and RideZap claim them.)
- **Shape language: "route rail".** The trip page is a vertical rail:
  - filled lagoon dots for departures and arrivals
  - a thick rail segment for time in transit
  - a bracket for each stay that spans its nights

  Cards use 6 px corners and hairline borders. The nights strip is a row of square cells, one per night. Do **not** use a ticket-stub notch (EventSpark's shape) or the 12 px `AppCard`.
- **Home layout: "Next trip".** There is no bottom tab bar. Top to bottom:
  1. The next or current trip as a hero card: destination, local dates, a countdown ("in 12 days" / "Day 3 of 7"), its **nights strip**, and the Gap Check count ("2 gaps · 1 check" or "All clear").
  2. Other upcoming trips.
  3. Past trips, collapsed.
  4. A floating **New trip** button.

  Settings is a gear in the app bar. Remove the wordmark headline "Where do you want to go?", the category tiles, the deals carousel, the destination art and `tool/generate_destination_art.py`'s assets, unless an asset is used by M4/M8, which none is.
- **Platform feel:** on iOS use `CupertinoIcons`, Cupertino page transitions, `.adaptive` switches and dialogs, and a Cupertino date-time picker in the leg editor. Android keeps Material icons with the same palette and fonts.
- **Ads:** exactly one `AdBanner`, inline at the end of the Home list. No ads on the trip timeline, leg editor, Gap Check, hand-off sheet or Settings. Remove `AdService.instance.onTransition()` from the planner pop (`planner_screen.dart:137`) and the details pop. This is a founder decision (§9 Q2). If the founder declines, keep one interstitial on leaving Day ideas only. The UMP consent flow and the `Privacy choices` tile stay, because they are legally required.
- **Icon** (new, flat, no gradient, no Material glyph):
  - Three lagoon dots joined by a route line that bends into a shallow bowl (the "nest"), with the middle dot sitting in it. Cloud `#F2F5F6` background, lagoon `#0B7A83` line and dots.
  - Rewrite `tool/generate_icon.py` to draw it. Regenerate every `AppIcon.appiconset` size (the 1024 has no alpha) and every Android mipmap and adaptive layer.
  - Update `adaptive_icon_background` and the web colours in `pubspec.yaml`.
- **Launch screen:**
  - `LaunchScreen.storyboard` background becomes cloud `#F2F5F6` (red 0.949, green 0.961, blue 0.965) with the new mark. Regenerate `LaunchImage`.
  - The storyboard shasum must no longer be `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, and `grep -c 'red="1" green="1" blue="1"'` must return 0.
  - Android `launch_background.xml` uses the same colour and mark.
- **Repo docs:** remove the "AmericanGroupLLC Design System v2.0" header. Update `TripNest/CLAUDE.md` and `ARCHITECTURE.md` so they no longer describe modelled inventory, affiliate rules, `TRIPNEST_*` defines or five tabs.
- **Done when:**
  - Tests assert `colorScheme.primary == Color(0xFF0B7A83)` in light and `bodyMedium.fontFamily == 'RethinkSans'`.
  - `grep -rn "Inter\b\|FF6B35\|NavigationBar(" mobile/lib` returns nothing.
  - The storyboard check above passes.
  - QA attaches screenshots of Home, a trip with gaps, and Settings, in light and dark, from a real run.

**M8. Onboarding, Day ideas and Settings copy of its own (plan criteria 1 and 4)**
- **First launch, two short skippable screens.** No account, no permission prompts:
  1. "Where's home?" uses the M3 picker. It sets the home city and zone used for "No way home" and for prefilling a new trip's origin.
  2. "Your first trip": destination and dates, then the user lands on the trip with the empty "Add the first leg" state.

  Do not use "Get started", "Welcome back" or any generic marketing copy.
- **Day ideas** (replaces "Itinerary ideas"):
  - Shown inside a trip whose destination matches one of the five curated places, as "Ideas for Goa" with the hand-written highlights and tips.
  - Reached from the trip page, not from a promo card.
  - Built from the curated lookup only, with no engine search.
  - Other destinations show nothing; no empty promo.
- **Settings sections:**
  - **Home**: home city.
  - **Appearance**: System / Light / Dark.
  - **Your trips, on this phone**: share all trips as text; delete all data, with confirmation.
  - **Privacy**: privacy policy link; `Privacy choices` (kept); one plain sentence on what leaves the phone (ad requests after consent, crash reports, and analytics if the founder keeps them, §9 Q4).
  - **About**: one paragraph, "TripNest is free and shows one ad on the Home screen. It sells no travel and earns nothing from the sites it opens", plus data attribution (M3), contact support, licences and version.
- **Remove:** Menu, Profile (with its "Traveler details" name field, which nothing needs), "How TripNest makes money" as a separate screen, and the "Your data" heading.
- **Done when:** widget tests cover onboarding completion and skip, Day ideas shown only for curated destinations, and the Settings rows.

**M9. Proven (plan criterion 6)**
- `flutter analyze` is clean and `flutter test` passes, with output quoted in the QA report.
- New tests cover M2–M8 as listed above.
- **Tests for deleted code may be deleted only with that code.** This applies to tests whose subject M1 removes: `supplier_client_test.dart`, `parity_test.dart`, `coming_soon_test.dart`, `search_failure_regression_test.dart`, the sample-guard parts of `production_test.dart`, `deep_link_test.dart`, and the result/pricing groups of `travel_engine_test.dart`. List every deleted test file in the commit message. QA checks that each deleted test's subject no longer exists in `lib/`. No test of surviving code may be deleted or skipped.
- `accessibility_test.dart`, `layout_resilience_test.dart` and `foldable_layout_test.dart` keep running against the new screens.
- Commits are path-limited to `mobile/lib`, `mobile/test`, `mobile/assets`, `mobile/tool`, `mobile/pubspec.yaml`, `mobile/pubspec.lock`, `mobile/ios/Runner/{Assets.xcassets,Base.lproj/LaunchScreen.storyboard,Runner.entitlements,Info.plist}`, `mobile/android/app/src/main/{AndroidManifest.xml,res}`, and `CLAUDE.md` / `ARCHITECTURE.md`. Push to `main`.
- **Never stage** `mobile/fastlane/**` or `mobile/ios/Podfile.lock` (§10).
- Launch the app on the iOS simulator and take screenshots. A green test suite has missed a white screen before.

### SHOULD (build after the MUSTs, in this order)
- **S1. Public holidays on your dates.**
  - For each country the trip touches, fetch `https://date.nager.at/api/v3/PublicHolidays/{year}/{CC}` once per country-year and cache it on the device. Show Info findings such as "Mon 1 Jun: public holiday in Portugal (Dia de Portugal). Banks and many shops may be closed."
  - Verified 2026-10-12: FR, PT and JP return 200 with JSON. **IN returns 204 (no data)**, so India shows "No public-holiday data for India", never silence. `AvailableCountries` lists 204 countries. The host resolves (`verify_api_hosts.doh`: ok).
  - **Blocker:** I could not find Nager.Date's terms for commercial or ad-supported use. Their terms pages returned 404 to curl, and the README says only that the REST API is public. Build this only after the chief-of-staff confirms the terms (§9 Q5).
- **S2. Ride hand-off for "No way into town"** (only if D1 is approved). Reuse RideZap's verified formats (`specs/RideZap.md` §3): `m.uber.com/ul/?action=setPickup&pickup[latitude]…&dropoff[…]` and `www.lyft.com/ride?id=lyft&pickup[latitude]…&destination[…]`. Coordinates come from the M3 dataset. Say "Fine-tune the pickup pin in Uber or Lyft." No fare history; that stays RideZap's scope if it is kept.
- **S3. Export to Calendar (.ics).** One `VEVENT` per leg with the correct `TZID`, shared through `share_plus`. Unit-test the output against RFC 5545 line folding.
- **S4. Day ideas into the timeline.** "Add to day 2" turns an idea into a note leg.

### MUST NOT
- No invented prices, fares, hotels, flights, ratings, users or "popular" counts, not even in debug builds, tests' production code paths, or screenshots.
- No account, no demo login, no remote config reads, no build flags that hide screens, no reviewer, region or date detection, no hidden gestures. Every feature is reachable on one device from the first screen after onboarding.
- No live aircraft positions, gates, delays or flight status. That is AeroSwift's domain. AeroSwift is not live on either store (`docs/play-production-blockers.json`: `PRODUCTION_DRAFT_STAGED`; Apple: rejected), so **no link to it** until it is live.
- No Open-Meteo. Its terms say "Operating websites or apps that have subscriptions or display advertisements" is commercial use (`open-meteo.com/en/terms`, read 2026-10-12), and TripNest shows ads.
- No in-app web view for partner sites.

---

## 5. Data source
| Data | Source | Proof (2026-10-12) |
|---|---|---|
| Trips, legs, dismissals, home city, settings | On-device SharedPreferences (`tripnest.*`, `tripnest.schema = 2`) | Existing keys at `app_state.dart:193-197` |
| Places with time zones | GeoNames `cities5000` (CC BY 4.0), bundled | `download.geonames.org/export/dump/cities5000.zip` 200, 69,793 rows. Licence lines 6-7 of `readme.txt`. "Candolim IN Asia/Kolkata 9197" present (it is not in `cities15000`) |
| Airports (IATA) | OurAirports `airports.csv`, bundled | 200, 12.7 MB; 4,133 IATA rows with scheduled service; `GOI`, `GOX`, `BOM` present with coordinates. **Licence statement not verified** (M3) |
| Time-zone maths | `timezone` package (pub.dev, publisher labs.dart.dev, latest 0.11.2), bundled IANA database | pub.dev API read |
| Partner hand-off | Booking.com, Airbnb, Google Maps (200); Google Flights (302 → "unsupported" for curl, phone behaviour not verified) | curl results in §0 |
| Holidays (S1 only) | `date.nager.at` v3 | 200 for FR, PT and JP; 204 for IN; terms not found |
| Ride hand-off (S2 only) | Uber and Lyft universal links | Verified in `specs/RideZap.md` §3, not re-run by me |

No Supabase, no sign-in, no key, no paid API. The app makes no network call for its own data. Network goes to partner sites (when the user taps), AdMob, Firebase Crashlytics, and Analytics and Remote Config unless dropped (§9 Q4).

## 6. Store impact (proposals for store-compliance to apply after the build. I did not edit `store/apps/TripNest.json`, `store/privacy/` or `fastlane/`.)

**Name:** keep "TripNest: Trip Planner" (it is live on Play, and Apple has not objected to the name).

**Subtitle (28 chars):** "Every leg and night, checked"
**Play short description:** "Keep every leg of a trip in order and catch missing nights and bad connections."
**Promotional text:** "Add your flights, trains, buses and stays. TripNest shows the trip in local time and flags any night with no bed and any leg that doesn't connect."
**Keywords:** `itinerary,trip organizer,travel planner,layover,connection,offline itinerary,multi city,overnight,hostel,rail` (store-compliance should check length and duplicates).

**Description (proposed). It does not open with the app name, and it has no shared ads boilerplate paragraph:**
> A night with nowhere to sleep. A bus that leaves before your flight lands. A flight into GOI with an onward ticket from GOX. These are the mistakes you find at midnight in arrivals. TripNest finds them while you're still planning.
>
> Add each leg you've booked: flights, trains, buses, ferries, car hire, transfers and stays. TripNest puts them in order in each place's own local time, and Gap Check reads the whole trip:
> • every night from arrival to departure has a bed, or an overnight journey
> • each arrival connects to the next departure, in the same place
> • connections aren't too tight once time zones are taken into account
> • you have a way from the airport or station to where you're staying
> • you haven't booked two places for the same night
>
> When something's missing, tap Fill this gap. Booking.com, Airbnb or Google Maps opens with the place and dates already filled in. Book there, then add the details back to your trip.
>
> Everything stays on your phone and works offline: places and airports are built in. There's no account and no email forwarding. Share the itinerary as text with anyone travelling with you.
>
> TripNest is free and shows one ad on the Home screen. It sells no travel and earns nothing from the sites it opens. Place data: GeoNames (CC BY 4.0). Airport data: OurAirports.

**Screenshots (retake all; currently 3 iPhone and 3 iPad):** at least 5 iPhone 6.9" and 5 iPad 13", captured from a release build on a device or simulator. The trip shown must be one the capturer entered through the app's own UI; nothing seeded in code:
1. Home, "Next trip" hero with its nights strip and "2 gaps · 1 check".
2. Trip timeline across a time-zone change, with the route rail and local times in DM Mono.
3. Gap Check: "Night of … nowhere to stay yet", plus a wrong-airport Check.
4. The Fill-this-gap sheet with Booking.com and Airbnb prefilled.
5. The leg editor showing two local times and the duration.
6. Day ideas for one curated city (optional).

None may show a tab or screen the build doesn't have. The current `iphone69-01.png` shows a Saved tab the release hides (§0.1).

**Play feature graphic:** a new design from the new icon on cloud `#F2F5F6` with a route-rail motif and Rethink Sans. It replaces the generated layout.

**Review notes (rewrite; drop the "2. DEVICES…" skeleton):**
> TripNest organises a trip someone has already booked across several sites, and checks that it holds together. There is no account, no login and no server. Everything is on the device.
> To see the main feature: onboarding asks for a home city (you can skip it) and a first trip. On the trip, tap Add leg to add a flight and a stay that leaves a night uncovered. Gap Check, at the top of the trip, shows "Night of … nowhere to stay yet". Tap Fill this gap to open Booking.com with that place and those dates.
> All features are visible to every user at all times. Nothing is enabled remotely or by region.
> External services: Google AdMob (one banner on Home, after consent where required), Firebase Crashlytics [and Analytics if kept]. Partner sites open in Safari only when the user taps them. TripNest has no affiliation with them.
> Place data GeoNames CC BY 4.0; airport data OurAirports. Fonts SIL OFL.

The devices line must state only what QA actually did. If a physical-iPhone run happened, name the model and iOS version. If not, say nothing about devices. **Do not reuse the simulator/emulator sentence.** The contact name must be a real person (§9 Q3).

**`differentiation` field:** fill §3 "Gap it fills" with the competitor table in §0, marked as listing-text comparisons. In §6, answer "not a feature of AeroSwift (aircraft tracking) or RideZap (repeated local ride fares)".

**Privacy label:** if the founder drops Analytics and Performance (§9 Q4), TripNest's label becomes DEVICE_ID + ADVERTISING_DATA (third-party advertising) + CRASH_DATA (app functionality). That is a label of its own and is accurate. If they stay, the current label is still accurate. No location is collected: the place picker is offline and never reads GPS. S1, if built, sends a country code and a year to `date.nager.at`, with no user data.

**Category:** Travel (unchanged).

## 7. Out of scope
- Buying travel, live prices, fare alerts, flight status and gate data.
- Email or PDF import, accounts, cloud sync and collaboration.
- Maps with pins: no map SDK, no key.
- Weather (Open-Meteo is excluded on its terms).
- The `web/` portal and the `extension/` in this repo. Neither ships to the stores. Their engine still holds invented prices, which is a separate cleanup to raise with the chief-of-staff. The mobile parity test is removed with the mobile engine (M9).
- Retiring RideZap (founder decision D1).

## 8. Files the developer will touch (expected)
- **Delete** (M1): `features/{results,details,saved,menu,profile}/`, `features/about/monetisation_screen.dart`, and `core/engine/{supplier_client,inventory_source,affiliate,search_failure}.dart`, `core/widgets/{coming_soon,result_cards,skeletons}.dart`.
- **Rewrite:**
  - `core/engine/travel_engine.dart`, which becomes the trip, leg and curated-ideas model
  - `core/config/app_config.dart`, `core/router/app_router.dart`, `core/state/app_state.dart`, `core/state/serialisation.dart`
  - `core/theme/*`
  - `features/home/home_screen.dart`, `features/trips/*`, `features/search/search_screen.dart` (replaced by the Fill-this-gap sheet), `features/settings/settings_screen.dart`
- **New:** `core/gaps/gap_check.dart`, `core/places/` (loader and search), `features/onboarding/`, `features/legs/leg_editor.dart`, `tool/build_places.py`, `assets/data/*`, `assets/fonts/*` (with the OFL files).
- **Platform:** `ios/Runner/Runner.entitlements`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets/*`, `android/app/src/main/AndroidManifest.xml`, `android/app/src/main/res/*`, `tool/generate_icon.py`, `pubspec.yaml`.

## 9. Founder decisions (not taken by the office)
1. **D1:** absorb RideZap's Uber/Lyft hand-off into TripNest's "No way into town" gap (S2), and retire RideZap (Charter §8). This spec works either way.
2. **Ads (Charter §3, money):** one inline Home banner, no interstitials. Revenue may change.
3. The App Review contact name, to replace "App Reviewer", and whether a human will record a physical-iPhone run of the M4 flow for any future Resolution Center reply. Only a human can make that recording, and replying is a Charter §1 decision under the 5.6 freeze (MA-043).
4. Whether TripNest stops calling `AglInsights.init`. That drops Firebase Analytics, Performance **and Remote Config**, keeps crash reports, gives TripNest its own privacy label, and removes a remote-config SDK fetch from an app under a 5.6 hold. **The office recommends yes.**
5. Nager.Date's terms for an ad-supported app (S1). Someone needs to confirm them or write to the maintainer. That is external contact, Charter §5.
6. Confirm that the in-app marketplace (results, prices, affiliate bookings) is removed for good, not parked for a future supplier deal. The spec assumes removal; keeping it hidden is what 5.6 objects to.

## 10. Other people's uncommitted work in this repo (do not touch)
`git status --short` at base `0542826`:
- Modified:
  - `mobile/fastlane/metadata/android/en-US/{changelogs/default.txt, full_description.txt, short_description.txt}`
  - `.../images/phoneScreenshots/0{1,2,3}.png`
  - `.../images/tenInchScreenshots/0{1,2,3}.png`
  - `mobile/fastlane/metadata/en-US/{description,keywords,promotional_text,release_notes,subtitle}.txt`
  - `mobile/fastlane/metadata/review_information/notes.txt`
  - `mobile/fastlane/screenshots/en-US/{ipadpro13,iphone69}-0{1,2,3}.png`
  - `mobile/ios/Podfile.lock`
- Deleted: `phoneScreenshots/0{4,5}.png`, `tenInchScreenshots/0{4,5}.png`, `screenshots/en-US/{ipadpro13,iphone69}-0{4,5}.png`.
- None of these is a file this spec asks the developer to change.
- `git status --short -- mobile/lib mobile/test mobile/pubspec.yaml mobile/ios/Runner mobile/android mobile/assets` was **empty**, so the files in §8 have no one else's edits.
- Note: `TripNest/CLAUDE.md` rule 10 says "Do not commit or push unless explicitly asked". The plan (criterion 6) and Charter authorise pushing to main after tests pass. The chief-of-staff should confirm which applies to this repo before the developer pushes.

## 11. Not verified
- How the app behaves on a device. I read the code only.
- Google Flights links in phone Safari (curl got the "unsupported" page).
- The OurAirports licence statement, and Nager.Date's commercial terms.
- Whether TripIt, Wanderlog and Tripsy actually lack gap detection. I compared listing text only.
- That the hidden marketplace caused the 5.6 rejection. Apple did not say which feature it meant. This is my inference from §0.1.
- The final bundle size of the place dataset (budget 3 MB; the developer measures it).
