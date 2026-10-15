# Spec: RideZap — know your usual Uber and Lyft fare for the trips you take, and spot a high quote before you book

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7). Overlap: `../overlap.md` row G1.
Repo: `/Users/spatchava/agl/RideZap` (app in `mobile/`)
Base: `main` @ `3c6ce3785710b7388e40a4ec0ed348d3b4130e16` (`git -C /Users/spatchava/agl/RideZap rev-parse HEAD` and `git branch --show-current` → `main`, run 2026-10-12)
Baseline (run 2026-10-12 on that base, `--no-pub` so `pubspec.lock` was not touched): `flutter analyze --no-pub` → "No issues found! (ran in 10.6s)". `flutter test --no-pub` → "+349: All tests passed!"

> **Read this first: this spec is the "if kept" path.** Portfolio-director recommends **retiring RideZap** and moving its ride hand-off into TripNest (`overlap.md` G1, founder decision **D1**). Retiring an app is a founder decision (Charter §8). This spec does not take that decision. It describes the only honest product RideZap can be with what we have today, so the founder can compare the two options. My recommendation as PM is in §8 Q1.

**Other people have uncommitted work in this repo. Leave it alone.** `git status --short` (2026-10-12) shows modified `mobile/fastlane/**` (both descriptions, `notes.txt`, every phone/tablet/iPhone/iPad screenshot, plus 4 untracked screenshots), `mobile/ios/Podfile.lock` (the only change is `COCOAPODS: 1.16.2` → `1.17.0`) and `mobile/ios/Runner.xcodeproj/project.pbxproj` (12 lines). This spec changes none of those files.
**Plugin trap:** adding any plugin with native code (`share_plus`, `geolocator`, `flutter_local_notifications`) makes CocoaPods rewrite `Podfile.lock`. So **the MUST items add no native plugin.** They use only what `pubspec.yaml` already has (`url_launcher`, `shared_preferences`, `dio`, `intl`, `go_router`, `flutter_riverpod`, `agl_*`), plus pure Dart, bundled fonts and image assets. The SHOULD items that need a plugin first require `git diff mobile/ios/Podfile.lock` to show no one else's edit.

---

## 1. Problem

**Apple's state.** Apple rejected the app under **5.6 Developer Code of Conduct** on 2026-10-08T14:19:40Z (`/Users/spatchava/agl/.dist/rejections.json` → "RideZap", 1 thread): "the app contains features that appear to have been intentionally hidden during the review process." Google Play: PRODUCTION_DRAFT_STAGED.

**What in this binary reads as "hidden" (evidence, read 2026-10-12):**
- **Build-time switches decide what the app is.** `lib/core/env.dart:21,28,35` define `RIDEZAP_API_BASE_URL`, `RIDEZAP_API_COMPARE_PATH` and `RIDEZAP_API_KEY` through `String.fromEnvironment`. `Env.hasLiveEndpoint` (`env.dart:37`) then branches the UI in `providers.dart:61-67,75-83,91-96`, `ride_search_form.dart:143,151`, `results_screen.dart:98,115` and `settings_screen.dart:105,134`.
- **A tab the reviewer cannot see.** `router.dart:138-141` `visibleBranches(hasLivePrices:)` drops the "Watch list" tab when there is no gateway. The test `responsive_layout_test.dart` ("the watch list is a destination only with live prices") locks this in.
- **Screens compiled in but unreachable.** Without a gateway, the results list, verdict cards, quote detail (`features/detail/quote_detail_screen.dart`), price breakdown and the watch list (`features/saved/saved_trips_screen.dart`) are all in the binary and can never be opened.
- **The store record says so.** `store/apps/RideZap.json` → `differentiation` §1: "The watch list and quote detail screens exist in the code but are only reachable when a live fare source is configured, which this build does not have." That sentence is Guideline 5.6.
- **A gateway that does not exist.** `env.dart:9-12`: the two documented gateway hosts "have no DNS record; the org runs no API server". The `_blocker` in the store JSON says the same.

**Why it reads as a template or a duplicate (4.3 portfolio context):**
- **It does not do its job and says so on every screen.** `widgets/data_source_banner.dart:9-11`: "No live prices — RideZap is not connected to Uber, Lyft, Bolt, Expedia or Booking.com yet, so it shows no fares." That banner is in store screenshot 01. Other examples: `no_live_price_source.dart:51-56` ("can't get live fares … yet", "aren't available in RideZap yet") and `ride_search_form.dart:155-157`.
- **Overlap.** Its flight and hotel hand-off (`models/travel_mode.dart:3-6`, `models/travel_provider.dart:5-6`) is a subset of TripNest's (`overlap.md` G1).
- **Already widely available.** Live Uber/Lyft price comparison exists. Obi "compares every taxi, rideshare and black car price … Live prices across Uber, Lyft, Waymo…" (§2). We have no fare API, so RideZap cannot compete there.
- **Shared shell.** A Material `NavigationBar` with `AglAdBanner` above it, hidden on Settings (`router.dart:201,214`), and an interstitial on every tab switch (`router.dart:167`).
- **Shared affiliate-family copy.** "Where prices come from" (`settings_screen.dart:38`) and "Booking links" (`:160`). A referral tag `affId=americangroupllc` is added to Uber's link (`services/affiliate_links.dart:41-44`). Uber's universal link has no such parameter, and no agreement is confirmed (the file's own comment says so).
- **Skin.**
  - The icon comes from the generator: `scripts/generate_app_icons.py:77` `"RideZap": ("electric_bolt", "#F57F17", "#FFCA28")`.
  - The splash is shared: `ios/Runner/Base.lproj/LaunchScreen.storyboard` has shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (the 37-app storyboard).
  - The font is Inter through `google_fonts` (`core/theme/app_theme.dart:24,30`), on `ColorScheme.fromSeed(0xFF1B5E20)` with Tailwind greys `#F8F9FA/#6B7280/#E5E7EB/#1A1A2E` (`app_theme.dart:4-12`).
  - Diagnosis measured the theme as a clone of portfolio-board's (Jaccard 0.83).
- **Internal jargon shown to users.** The Settings footer prints `source "none" · gateway id "gateway"` (`settings_screen.dart:258-262`). It also has an unreachable "NOT REAL PRICES" tag (`:74`).
- **Store packaging.** The privacy label is byte-identical to 19 other apps (`store/privacy/*.json` md5 grouping, 20 apps including RideZap). Per diagnosis, the Play feature graphic shows the default Flutter logo (I did not re-check this image myself).

**What is real and worth keeping:**
- `LinkLauncher`/`RecordingLinkLauncher` (`services/link_launcher.dart`). It can be tested and opens apps externally.
- The Uber universal-link builder idea (`affiliate_links.dart:89-101`), minus the fake tag.
- The shared-preferences store pattern with tolerant `fromJson` (`saved_trips_store.dart`, `search_history_store.dart`).
- The guarded `main.dart` start-up.
- `PrivacyChoicesTile` (legal UMP row).
- `ContentWidth`/layout helpers.
- The "Copy trip details" idea.

Everything priced through the gateway goes.

## 2. User, core job, signature

**User:** someone in a US city who takes **the same few Uber or Lyft trips again and again**: home ↔ work on bad-weather days, home ↔ airport, a late shift, a weekly appointment. They have both apps installed. They already know the trick: the same trip can cost different amounts on the two apps, and from one hour to the next. What no app tells them is the thing they actually want to know on the kerb:

> "Uber says $34 right now. Is that normal for this trip, or should I check Lyft, or wait 20 minutes?"

**Core job: Check a trip.**
1. The user saves a trip once (pickup and drop-off as real places).
2. To check it, they tap **Check fares**. RideZap shows the real driving distance and no-traffic drive time, then opens **Uber** and **Lyft** with both ends already filled in (one tap each, coordinates carried).
3. When the user comes back to RideZap, a keypad asks **"What did Uber show?"**. They type the number they saw, which takes about two seconds. Same for Lyft.
4. RideZap answers at once: which service is cheaper **right now**, and whether each quote is **high, typical or low against the user's own history** for this trip at this time of day.
5. If they ride, one tap turns the quote into a **ride in the log**. They can add the final paid amount and tip later.

**Signature feature: "Your usual" fare check.** It is a personal fare baseline per trip, per service and per time-of-day band, built only from quotes and receipts the user entered. It gives a clear verdict on the quote in front of them:
- "**High.** Uber $34.20 is 41% above your usual $24.25 for Home → Work on weekday evenings (7 earlier quotes, usual range $22–27)."
- Next to it: "**Lyft is $6.10 less right now.**"
- The **hour pattern** for the trip: the user's own quotes plotted by hour of day, per service. Over a few weeks this shows when the trip is reliably cheap.

Users can **backfill** past rides from their Uber/Lyft receipts (date, time, amount), so the baseline works from the first week rather than the second month.

*Every amount in this spec's examples ($34.20, $24.25, $6.10, $1.62/mi and so on) is an illustration of the copy format, not app data. The app shows only what it computes from the user's entries.*

**Why this and not live prices:** RideZap has no Uber, Lyft or Bolt fare API and no partner credentials (`no_live_price_source.dart:9-14`). Inventing fares is banned. The only honest fare data is what the user saw and paid, so the product is built around that, and it is useful exactly where live-comparison apps are silent.

**Competitor check.** WebSearch is disabled here ("Internet mode is not enabled", hook error, 2026-10-12). I used Apple's keyless iTunes Search/Lookup API on 2026-10-12 and read store descriptions only. I did not run any of these apps.
- **Obi – Get the cheapest ride** (Bellhop Technologies, id1081008679, 2,182 ratings, 4.7). "Live prices across Uber, Lyft, Waymo, Tesla, Curb, Bolt, Via…", "Book in seconds, straight from Obi". This is the strongest live comparison. Its description says nothing about a personal fare history or a baseline per trip.
- **FairFare – Compare Uber & Lyft** (id6761694835, 4 ratings). "See estimated prices and travel times", "Open your selected ride directly in the provider app". No history mentioned.
- **FareWise: Rideshare Compare** (id6804430468, 0 ratings, released 2026-10-09). Compares prices and wait times. It puts "price drop alerts, full ride history" behind **FareWise Pro $4.99/month**.
- **All Taxis: compare ride prices** (id1332439993, 166 ratings, last updated 2023-02-26).
- **Uber** (id368677368) and **Lyft** each show only their own price, and only the current one.

**The gap I claim, stated narrowly:**
- (a) A verdict on a quote **against your own history for this exact trip at this time of day**. No description above mentions one. Obi and FairFare show *today's* prices, not whether today is unusual for you.
- (b) Free: no account, no subscription. FareWise charges for history.
- (c) Everything stays on the phone, and the receipt backfill makes it useful from day one.

**What I do not claim:**
- RideZap does not show live prices, and live comparison is Obi's ground. The app must never imply otherwise.
- Competitor behaviour beyond these descriptions is **not verified**.

**Category risk, stated plainly:** "compare Uber & Lyft" is a crowded search term. RideZap's distinct value needs a few logged quotes before it shows. A reviewer with an empty phone sees the side-by-side and the "log N more" state unless they backfill. That is why the review notes in §5 give an exact backfill path, and why Q1 exists.

## 3. Data sources (real, keyless; checked 2026-10-12)

The hosts resolve through the repo's own DoH check (`python3 -c "import verify_api_hosts as v; v.doh(h)"` from `agl-manifest/scripts`): `photon.komoot.io ok`, `routing.openstreetmap.de ok`, `router.project-osrm.org ok`, `m.uber.com ok`, `lyft.com ok`, `ride.lyft.com ok`. After the build, run `python3 scripts/verify_api_hosts.py --print` and confirm RideZap's hosts show `ok`.

| Data | Endpoint | curl proof (2026-10-12) |
|---|---|---|
| Place search (pickup/drop-off) | `https://photon.komoot.io/api/?q=<text>&limit=6&lang=en[&lat=&lon=]` | HTTP 200, 1,349 B for "San Francisco International Airport". The first hit is that airport at `[-122.3839894, 37.622452]`, followed by Oakland International. GeoJSON `features[].properties{name, housenumber, street, city, state, postcode, countrycode, osm_key, osm_value}` and `geometry.coordinates [lon, lat]`. Location bias `&lat=37.77&lon=-122.42` → 200 |
| Driving distance and no-traffic time | `https://routing.openstreetmap.de/routed-car/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false` (FOSSGIS-run OSRM) | HTTP 200, 616 B. Downtown SF → SFO: `distance 21433.4` m (13.3 mi), `duration 1213.5` s (20 min). `router.project-osrm.org` gives the identical answer, but its policy page now points to the FOSSGIS server, so use FOSSGIS |
| Hand-off to Uber, both ends filled in | `https://m.uber.com/ul/?action=setPickup&pickup[latitude]=&pickup[longitude]=&pickup[nickname]=&pickup[formatted_address]=&dropoff[latitude]=&dropoff[longitude]=&dropoff[nickname]=&dropoff[formatted_address]=` | curl → 302 to `get.uber.com/open_app/?action=setPickup&pickup[latitude]=…` (parameters kept). `m.uber.com/.well-known/apple-app-site-association` lists path `/ul`, so iOS opens the Uber app when it is installed |
| Hand-off to Lyft, both ends filled in | `https://www.lyft.com/ride?id=lyft&pickup[latitude]=&pickup[longitude]=&destination[latitude]=&destination[longitude]=` | curl `lyft.com/ride?...` → 301 → `www.lyft.com/ride?...` (parameters kept). `www.lyft.com/.well-known/apple-app-site-association` lists path `/ride`, so iOS opens the Lyft app when it is installed. **Without the app**, curl lands on `ride.lyft.com/not-supported?destination=37.6213,-122.3839&origin=37.7749,-122.4194` (curl user-agent; phone Safari behaviour **not verified**) |
| Quotes, rides, places, trips, settings | on-device (`shared_preferences`, versioned JSON keys) | — |

**Usage rules the build must follow (from the providers' own policy pages, read 2026-10-12):**
- **Photon (komoot)**, from its terms: "You can use the API for your project, but please be fair - extensive usage will be throttled."
  - Debounce typing by 400 ms, require at least 3 characters, cancel in-flight requests and cache results in memory for the session.
  - Never geocode in a loop. Saved places store their coordinates, so checking a saved trip makes **no** geocoding request.
- **FOSSGIS routing** (`routing.openstreetmap.de/about.html`, `fossgis.de/…/nutzungsbedingungen`):
  - send a valid User-Agent naming the app, its version and a contact, e.g. `RideZap/<version> (contact@americangroup.ai)` (library user-agents are not enough);
  - at most 1 request per second;
  - no scraping;
  - show the attribution "© OpenStreetMap contributors (ODbL)" with a link to `https://www.openstreetmap.org/fixthemap`;
  - an operator e-mail must be easy to find in the store listing.
  - Route distance is fetched **once per saved trip** and cached; a "Recalculate" action re-fetches it.
- **Their policy also "explicitly recommends" not hard-coding the service URLs.** We have no server to serve a config, and a remote config would raise a 5.6 question. So the URL is a constant in `lib/core/sources.dart`, and the app keeps working (minus distance) if FOSSGIS withdraws access. This is recorded under Q4.
- **Excluded after checking: Transitous (public-transit routing).** It answered (HTTP 200, 3 SF→SFO itineraries), but its policy says "Due to data source licences … commercial use is not allowed". RideZap carries ads. Do not use it.
- **Gotcha: Photon is weak on US house numbers.** "1 Market St San Francisco" returned transit stops on Market Street, not number 1. Mitigations:
  - show the full label (name, street, number, city, state) for every hit;
  - let the user rename a saved place ("Home");
  - send Uber the coordinates **and** `formatted_address` + `nickname`. Both apps let the rider adjust the pin before booking.
  - Say on the place-search screen: "Pick the closest match. You can fine-tune the pickup pin in Uber or Lyft."
- **Gotcha: OSRM time has no traffic.** Always label it "drive time without traffic (OpenStreetMap/OSRM)". Never present it as an ETA.
- **Coordinates:** Photon and OSRM use `[lon, lat]`, while Uber and Lyft parameters use lat/long. Unit-test the order.
- **Currency:** each quote stores the currency the user's device locale formats (`NumberFormat.simpleCurrency`). A trip's baseline compares only quotes in the same currency.

No API key, no paid feed, no Supabase, no sign-in, no backend of ours.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. One build, nothing hidden; flights, hotels and the gateway deleted (5.6, G1).**

*Delete:*
- `core/env.dart` and every `Env.` reference;
- the services: `services/http_price_source.dart`, `services/no_live_price_source.dart`, `services/travel_price_source.dart`, `services/saved_trips_store.dart` (replaced in M4);
- the models: `models/comparison_result.dart`, `models/price_quote.dart`, `models/data_source_info.dart`, `models/saved_trip.dart`, and the flight/hotel parts of `travel_mode.dart`, `travel_provider.dart` and `travel_query.dart` (Expedia, Booking.com, Bolt, `CabinClass`, `FlightQuery`, `HotelQuery`);
- the features: `features/search/flight_search_form.dart`, `features/search/hotel_search_form.dart`, `features/results`, `features/detail`, `features/saved`;
- the widgets: `widgets/data_source_banner.dart`, `widgets/price_breakdown.dart`, `widgets/price_change_chip.dart`, `widgets/quote_tile.dart`;
- in providers: `availableDataSourcesProvider`, `DataSourceController`, `priceSourceProvider`, `comparisonProvider`, `SavedTripsController`;
- in the router: `visibleBranches` and the watch-list branch;
- the `affId` referral tag (unless Q3 says to keep it).

Bolt is dropped because it does not operate rides in the US market this spec targets, and it has no documented deep link that carries the trip (`affiliate_links.dart:27-29`).

*Acceptance:*
- (a) `grep -rn "fromEnvironment" mobile/lib` → exactly 1 hit, `main.dart`'s `AglAdIds.fromEnvironment(...)` (the shared ads package's API; note it in the commit).
- (b) `grep -rniE "in this build|not connected|no live|live prices|coming soon|yet\.|unavailable|gateway|RIDEZAP_API|sample|placeholder|simulator|expedia|booking\.com|flight|hotel|watch list" mobile/lib` → 0 hits. Any remaining hit needs a one-line justification in the commit message.
- (c) Release iOS build: `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "RIDEZAP_API|gateway|No live prices|Expedia|Booking.com|watch list"` → 0. This checks the binary Apple inspects.
- (d) Every feature is reachable from the first screen on a fresh install, with no account, in every region and locale. Nothing is gated by build define, region, date, account or remote value.
- (e) `grep -rniE "RemoteConfig|remoteConfig" mobile/lib` → 0. `agl_observability` initialises Firebase Remote Config (`packages/agl_observability/lib/src/insights.dart:104-115`), and this app must never read a value from it.

**M2. Core job: saved trips → Check fares → hand-off → log the quote.**
- **Places.** "Add a place" uses a Photon search field (rules in §3). The user picks a hit, can rename it ("Home", "Work", "Mum's") and it is saved with lat/lon and the full label. Places are reusable across trips.
- **Trips.** A trip is pickup place + drop-off place, with a "Reverse" action that creates or opens the return trip. On save, the app fetches the OSRM distance and duration once and caches them with the fetch date. If routing fails, the trip still saves and shows "Distance unavailable — Recalculate".
- **Check fares** (a pushed page per trip):
  - Header: From → To, "13.3 mi · 20 min drive without traffic", attribution line with the fix-the-map link.
  - Two large buttons: **Open Uber** and **Open Lyft**. Each builds the §3 link with coordinates and opens it through `LinkLauncher` (`LaunchMode.externalApplication`). If `open` returns false: "Couldn't open Lyft on this phone. Trip copied — paste it in the app." The trip (labels + coordinates) is copied with `Clipboard`.
  - **Return capture.** RideZap records which service it handed off to. On the next `AppLifecycleState.resumed` within 15 minutes, it opens the **quote keypad** for that service:
    - an amount, with a big numeric pad and currency from the locale;
    - optional product label, with suggestions taken only from the user's earlier labels for that service (no hard-coded product list);
    - optional "pickup in N min";
    - Save / Skip.
    - The keypad is also reachable from a visible "Log a quote" button, so nothing relies on lifecycle timing.
  - Every saved quote stores: trip id, service (`uber`/`lyft`/`other` with a free name), amount in minor units, currency, product label, timestamp (now, editable), and source `quote`.
- **Acceptance:**
  - Unit tests build the Uber and Lyft URLs from fixed coordinates and labels, checking parameter names, lat/lon order and URL encoding of `formatted_address` with commas and `&`.
  - A widget test with `RecordingLinkLauncher`: tap Open Uber → the URL recorded is `https://m.uber.com/ul/?action=setPickup&pickup[latitude]=37.7749…`. A simulated `resumed` → the keypad for Uber appears → typing 2 4 2 5 → saved quote 2425 minor units.
  - Photon and OSRM parsers are tested against **real recorded fixtures** under `test/fixtures/`, cut from the 2026-10-12 responses in §3: the SFO search, the "1 Market St" search (transit-stop hits) and the SF→SFO route.
  - Network calls go through an injectable client with a fake in tests. No test calls the real servers.

**M3. Signature: "Your usual" verdict, right-now comparison, hour pattern.**
- **Pure module** `lib/domain/usual_fare.dart`, with no Flutter imports:
  - `baseline(quotes, tripId, service, at, currency)` → `{median, p25, p75, n, band}`, or `null`.
  - **Band rules:**
    - first, the same day type (Mon–Fri vs Sat–Sun) **and** ±90 minutes of `at`'s time of day: if there are 3 or more quotes, `band = sameTime`;
    - otherwise all the trip's quotes for that service in that currency: if there are 3 or more, `band = anyTime`;
    - otherwise `null`.
  - Rides logged from receipts count, using their paid amount without the tip. Each quote counts once (a quote turned into a ride is not double-counted).
  - `verdict(quote, baseline)` → `high` if at least +20%, `low` if at most −10%, otherwise `typical`, with the signed percentage.
  - `p25`/`p75` are shown only when `n` is 5 or more.
  - The thresholds are constants, shown verbatim on a "How 'your usual' works" sheet.
- **Verdict card** (on Check fares, after each logged quote):
  - Example: "High · Uber $34.20 is 41% above your usual $24.25 for this trip on weekday evenings · 7 quotes · usual range $22–27".
  - Colours: vermilion for high, teal for low, ink for typical. The verdict word is always written, never colour alone.
  - With `null`: "Log 2 more Uber quotes on this trip to see your usual. Add past rides from your receipts to get there faster." The second sentence links to backfill (M4).
- **Right now.** When both services have a quote for this trip within the last 10 minutes: "Lyft is $6.10 less than Uber right now (both logged 6:42 pm)". If they are equal: "Same price on both". Only the user's own numbers are compared.
- **Hour pattern** (trip page, once there are 5 or more quotes):
  - a `CustomPainter` strip: x = hour of day 0–23, y = amount; one dot per quote, coloured by service; the median line for each service;
  - filter chips: Weekdays / Weekends / All;
  - one sentence computed from the data, only when each compared hour band has at least 3 quotes: "Your cheapest weekday hours for this trip: 10 am–noon (median $19.40, 4 quotes)". Otherwise no sentence.
  - No prediction and no "best time to ride" claim beyond the user's own counts.
- **Caption shown under every verdict:** "Based only on fares you entered. RideZap doesn't see Uber's or Lyft's prices."
- **Acceptance:**
  - Unit tests over hand-built quote lists (test data, not app data) cover: the sameTime vs anyTime fallback, the ±90-minute window wrapping midnight (11:30 pm vs 00:45), the day-type split, the 3-quote minimum, the p25/p75 only from 5 quotes, the +20%/−10% boundaries (exactly +20.0% → high; +19.9% → typical), the currency mismatch excluded, no double count of a quote that became a ride, and the right-now 10-minute window.
  - A widget test: three backfilled weekday-evening rides of $22, $24, $26, then a logged Uber quote of $34 → the card reads "High" and "42% above your usual $24.00". (34/24 = 1.4167; format the percentage with `round()` and assert it.)

**M4. Depth: rides log, backfill, search/filter, monthly totals, export, offline.**
- **Took this ride.** From a quote: "I took this" turns it into a ride (service, quoted amount, time). Later the user can add the paid amount, tip, a tag (**Work** / **Personal**, editable list) and a note.
- **Add a past ride (backfill).** Pick a trip (or create one), service, date and time, and amount paid. Copy on the form: "From your Uber or Lyft receipt". Backfilled rides feed M3.
- **Rides log** (pushed page from the home app bar):
  - newest first, grouped by month;
  - text search across place names, product label and note;
  - filter chips by service, tag and month;
  - swipe to delete with Undo;
  - per month, totals per service and per tag ("October: Uber $142.80 · Lyft $96.10 · Work $180.40").
  - It is a ride log only. No budgets, no non-ride expenses (MyFinance owns those, `specs/MyFinance.md`).
- **Export.** "Copy as CSV" for the current filter, through Flutter `Clipboard`. Columns: `date,time,from,to,service,product,quoted,paid,tip,currency,tag,note`, RFC 4180 quoting. Also "Copy summary" (plain text, month totals). `share_plus` is SHOULD S2 because of the Podfile.lock rule.
- **Persistence.** `shared_preferences` JSON under versioned keys (`ridezap.places.v1`, `ridezap.trips.v1`, `ridezap.quotes.v1`, `ridezap.rides.v1`). Loading tolerates unreadable entries (drop the entry, keep the rest), following the existing `fromJson` pattern. Cap at 5,000 quotes, dropping the oldest *quotes* first, never rides.
- **Old data.** Remove the old `ridezap.data_source.v1`, saved-trip and history keys on first launch of the new version. Old history entries carry no coordinates and cannot become trips; do not attempt to convert them.
- **Offline and errors:**
  - Saved trips, Check fares hand-off, quote logging, verdicts, the rides log and export all work with no network. Only place search and distance need it.
  - Place search offline: "Searching places needs a connection. Your saved places still work." with Retry.
  - Routing failure or timeout (10 s): the trip still works without distance.
  - Photon or OSRM HTTP 429/5xx: "OpenStreetMap search is busy — try again in a minute." Never a spinner forever, never a blank page.
- **Acceptance:**
  - A relaunch test: add 2 places + 1 trip + 3 quotes + 1 ride, rebuild with a fresh `ProviderScope` on the same mock prefs, and check all are present and the verdict is the same.
  - Rides log search and filter widget tests.
  - CSV unit test with commas, quotes and a newline in a note.
  - Month totals unit test.
  - Offline place search state test.
  - Routing-failure trip save test.

**M5. Own identity: home, onboarding, colour, type, shape, icon, splash.**
- **Home: no tab bar.**
  - One screen, **"Your trips"**: a board of trip cards. Each card shows From → To, distance, the usual per service (e.g. "Uber usual $24 · Lyft usual $21"), or "No fares yet", the last check time, and a **Check fares** button.
  - The app bar has Rides log and Settings icons. A large "New trip" button sits at the end of the list.
  - Check fares, the trip page, the rides log, place search and Settings are pushed pages.
  - This replaces `HomeShell`/`NavigationBar`/`NavigationRail`.
  - On wide windows, the board becomes a two-column grid, still with no navigation rail.
- **Ads.**
  - Exactly **one** `AglAdBanner`, inline at the bottom of the trip page (below the hour pattern).
  - None on Your trips, Check fares, the keypad, onboarding, the rides log or Settings. The keypad must never sit next to an ad.
  - No interstitial (`AglAds.onTransition` removed; any interstitial is Q2).
  - Acceptance: `grep -rn "AglAdBanner" mobile/lib` → 1 hit, in the trip page. `grep -rn "onTransition" mobile/lib` → 0.
- **Onboarding** (shown once, re-openable from Settings), as two cards:
  1. **"Save the trips you actually take."** Add a place now (opens place search), or skip.
  2. **"Check both apps, tell RideZap what you saw."** A simple `CustomPainter` diagram: Uber quote and Lyft quote arrive as two receipt slips, then the verdict. Text: "Your fares stay on this phone. After three, RideZap tells you when a price is high for you."

  The final button reads "Add your first trip". No sign-in, no "Get started", no "Welcome".
  - Acceptance: tests that it is shown once and that Skip works.
- **Palette "Kerbside receipt"** (hand-built `ColorScheme`, not `fromSeed`; `ThemeMode.system`):
  - Light:
    - surface receipt `#F4F5F2`, cards `#FFFFFF`, text `#1B1F27`, muted `#5B6270`;
    - **primary ink `#22304F`** (on-primary white);
    - **fare-high vermilion `#B23A1A`**;
    - **fare-low teal `#1E7268`**.
  - Dark:
    - surface `#12151C`, cards `#1B2029`, text `#E8EAEE`, muted `#A3A9B5`;
    - primary `#8FA3D1` (on-primary `#12151C`);
    - vermilion `#FF7A57`;
    - teal `#5CC2B5`.
  - Contrast measured with the WCAG formula (2026-10-12):
    - light: text/surface 15.09, white on ink 13.09, ink/surface 11.97, vermilion/white 5.98, vermilion/surface 5.46, teal/white 5.73, teal/surface 5.24, muted/surface 5.6;
    - dark: text/surface 15.16, primary/surface 7.24, teal/surface 8.56, vermilion/surface 7.11, muted/card 6.92.
  - Avoid Uber black-and-white and Lyft pink, so the app is never mistaken for either.
  - No other spec in `specs/` and no app `lib/` uses `22304F`, `B23A1A`, `1E7268`, `F4F5F2`, `12151C`, `8FA3D1`, `5CC2B5` or `FF7A57` (grep, 2026-10-12).
  - Acceptance: `grep -rhoiE "1B5E20|2E7D32|F8F9FA|1A1A2E|6B7280|E5E7EB|DC2626|16A34A|F57F17|FFCA28" mobile/lib` → 0. A test asserts every pair above is at least 4.5:1, using `computeLuminance`.
- **Typography.**
  - **Big Shoulders** (variable `opsz,wght`) for fares, verdict words and screen titles. It is a condensed face drawn from Chicago street signage, and it reads like a meter or a kerb sign.
  - **Schibsted Grotesk** (variable `wght`) for UI text.
  - `FontFeature.tabularFigures()` on every amount, distance and time.
  - Bundle `assets/fonts/BigShoulders[opsz,wght].ttf`, `SchibstedGrotesk[wght].ttf` and both `OFL.txt` files. Register the licences with `LicenseRegistry`, declare the fonts in `pubspec.yaml`, and **remove `google_fonts`** (no runtime fetch).
  - **Gotcha:** the Big Shoulders file's default instance is Thin (`post_script_name: "BigShoulders-Thin"` in `METADATA.pb`). Set weights with `fontVariations: [FontVariation('wght', 700)]` (and `opsz`), not only `fontWeight`, and check it on screen.
  - Sources resolve: `github.com/google/fonts/raw/main/ofl/bigshoulders/BigShoulders%5Bopsz,wght%5D.ttf` 200 (320,800 B), `…/bigshoulders/OFL.txt` 200 (4,397 B), `…/schibstedgrotesk/SchibstedGrotesk%5Bwght%5D.ttf` 200 (176,068 B), `…/schibstedgrotesk/OFL.txt` 200 (4,406 B).
  - `grep -rli` for "big shoulders" and "schibsted" across `specs/`, every app `lib/` and every `pubspec.yaml` → 0 files.
- **Shape: receipt and ticket.**
  - Cards have 4 px corners and a **perforated top edge** (a `CustomPainter` row of half-circle notches) on quote slips and the verdict card. Buttons have 4 px corners. No 12/16/20 px rounded cards, no pill chips (chips at 4 px).
  - Acceptance: `grep -rn "circular(12)\|circular(16)\|circular(20)" mobile/lib` → 0.
- **Icon.** Hand-made art: an ink `#22304F` square holding a white receipt slip with a perforated top edge and a vermilion upward tick, meaning "higher than usual". Flat, no gradient, no Material glyph.
  - It **must not come from `generate_app_icons.py`**. Ask store-compliance to delete line 77 (`"RideZap": ("electric_bolt", …)`), which lives in `agl-manifest`, so a rerun cannot overwrite the art.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- **Splash.**
  - A new `LaunchScreen.storyboard` with background `#22304F` and the white receipt mark. Android `launch_background.xml` uses the same.
  - The storyboard is not `project.pbxproj`. Edit it only if it has no one else's uncommitted change (none on 2026-10-12).
  - Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Name.**
  - "RideZap" stays unless the founder renames it (Q1). `CFBundleDisplayName` and `android:label` are already "RideZap".
  - The pubspec description changes from "Compare rides in seconds" to "Know your usual ride fare".
  - Acceptance: a test asserts that `Info.plist`'s display name equals a single `kAppName` constant used by `MaterialApp.title`.

**M6. Honest, app-specific copy; shared furniture trimmed.**
- **Remove:** "No live prices…", "can't get live fares … yet", "Where prices come from", "Who RideZap compares", "Providers RideZap links to", "Booking links", "NOT REAL PRICES", "CHEAPEST TOTAL", "Watch list", "Comparing providers…", the source/gateway footer (`settings_screen.dart:258-262`), "Trip history" and "No provider priced this trip".
- **Settings: one short page.**
  - **How RideZap works**: one paragraph. It includes "RideZap doesn't see Uber's or Lyft's prices. It remembers the fares you enter and tells you when one is unusual for you", and the M3 thresholds.
  - **Map data**: "Places and distances: © OpenStreetMap contributors (ODbL), search by Photon (komoot), routes by OSRM on FOSSGIS servers", with a "Report a map error" link to `openstreetmap.org/fixthemap`.
  - **Trip defaults**: the day-type split on or off (default on). Currency follows the device and is shown, not editable.
  - **Appearance.**
  - **Language**: `AglLanguageScreen` may stay (shared infrastructure).
  - **Ads & privacy choices**: keep `PrivacyChoicesTile` (legal). Replace the house paragraph "Google may use device identifiers…" with this app's sentence: "One ad appears at the bottom of a trip's page. Where the law requires it, you choose about ad personalisation first."
  - **Privacy policy, Terms, Support**: the existing URLs, if present; if not, add the portfolio's documented URLs for RideZap. Do not invent pages.
  - **Delete everything**: "Delete your places, trips, fares and rides from this phone", with a confirm step.
  - **Version**: read from `package_info_plus` (already in the pod list through `agl_observability`). Never hard-code it.
- **Empty states, in this app's voice:**
  - Your trips: "No trips yet. Add the one you take most — home to work is a good start."
  - Rides log: "No rides logged. Tap 'I took this' after a quote, or add past rides from your receipts."
  - Hour pattern below 5 quotes: "Your hour pattern appears after 5 fares on this trip (N so far)."
- **Banned in the UI:** "coming soon", "not connected", "in this build", "yet" as an apology, "unavailable" as a product state, "simulator", "sample", "demo", "cheapest" (RideZap compares only the user's numbers, so it says "less than", not "cheapest").

**M7. Proven.**
- `flutter analyze` is clean and `flutter test` passes.
- **New tests cover:**
  - the Uber and Lyft link builders;
  - the Photon and OSRM parsers on real fixtures;
  - debounce and cancellation of place search (fake async);
  - `usual_fare` (all M3 cases);
  - the verdict card and right-now widget tests;
  - the hour-pattern minimum;
  - return capture on resume;
  - backfill feeding the baseline;
  - rides log search and filter;
  - CSV and month totals;
  - persistence and relaunch;
  - offline and routing-failure states;
  - onboarding shown once;
  - "no tab bar and exactly one AglAdBanner";
  - identity (fonts declared and on disk, `google_fonts` absent from pubspec, palette contrast, storyboard shasum, display name);
  - `release_sanity_test` extended to grep `lib/` for the M1(b) strings.
- **Tests that go**, only together with the code they test, each listed by name in the commit message:
  - `test/services/http_price_source_test.dart`
  - `test/services/no_live_price_source_test.dart`
  - `test/models/price_math_test.dart`
  - `test/models/saved_trip_test.dart`
  - `test/widgets/quote_detail_screen_test.dart`
  - `test/widgets/results_screen_test.dart`
  - `test/widgets/saved_trips_screen_test.dart`
  - `test/support/fixtures.dart` (quote fixtures for the deleted gateway)
  - the flight/hotel/watch-list cases in `test/models/travel_query_test.dart`, `test/widgets/search_screen_test.dart`, `test/widgets/history_screen_test.dart`, `test/widgets/responsive_layout_test.dart` and `test/services/stores_test.dart`
- **Rewritten, not dropped:**
  - `test/services/affiliate_links_test.dart`, for the new Uber/Lyft link builders;
  - `test/foldable_layout_test.dart` and `test/widgets/responsive_layout_test.dart`, for the new screens at the same window sizes;
  - `test/i18n_test.dart`;
  - `test/widget_test.dart`.
  - Keep `privacy_choices_tile_test.dart` and `release_sanity_test.dart`. No other test is deleted or skipped.
- **Look at it.** Launch on the iOS simulator with real network:
  - add two real places through Photon, save the trip, and confirm the distance shows;
  - tap Open Uber (the simulator has no Uber app, so the web link opens; screenshot it) and return; log a quote;
  - backfill three rides;
  - see the verdict;
  - open the rides log and copy CSV.

  Screenshot Your trips, Check fares with a verdict, the hour pattern, the rides log and onboarding card 2. Check for no white screen and no overflow at the largest text size.
- **Commit and push.** Commit path-limited (`mobile/lib`, `mobile/test`, `mobile/assets`, `mobile/pubspec.yaml`, `mobile/pubspec.lock`, `LaunchScreen.storyboard`, `AppIcon.appiconset`, Android res). Never commit `fastlane/`, `Podfile.lock` or `project.pbxproj` while they carry others' edits. Push to `main`.

### SHOULD (if time allows, in this order)

- **S1. "Rough guide" for a new trip from your $/mile.** Once the user has 8 or more fares with known distance across any trips, a trip with no history shows "From your other trips (median $1.62/mi, 14 fares), about $21 for 13.3 mi". The label is permanent: "a guide from your own fares, not a quote". No guide below 8 fares. This needs a unit test, and a check that the guide never appears on the store screenshots as if it were a price.
- **S2. Share sheet** (`share_plus`) for CSV and summary, **only** once `git diff mobile/ios/Podfile.lock` shows no one else's edit. Clipboard stays as the fallback.
- **S3. "Use my location" as pickup** (`geolocator` + Photon `/reverse`, verified 200 on 2026-10-12). It needs `NSLocationWhenInUseUsageDescription` ("Use where you are as a pickup point") and the same Podfile.lock rule.
- **S4. Re-check reminder.** "Remind me in 15 min" through `flutter_local_notifications` (same Podfile.lock rule). The notification reopens Check fares for that trip. On-device only, no push server.
- **S5. iOS-native feel.** On iOS: `CupertinoIcons`, Cupertino page transitions, a `CupertinoSliverNavigationBar` large title on Your trips, and the keypad as a Cupertino-style bottom sheet. Material stays on Android.

## 5. Store impact (proposed; store-compliance applies it later; nothing was written to `store/` or `fastlane/`)

**Name.** Keep "RideZap" unless the founder renames it (Q1). It does not carry the "i"/"AG"/"My" prefixes.

**Category.** Primary `TRAVEL` (Obi, FairFare and FareWise all list under Travel, per the iTunes API). Change the secondary from `SHOPPING` (RideZap no longer has anything to buy) to `UTILITIES`.

**Trademarks.** Do not put "Uber" or "Lyft" in the name, subtitle or keywords. Guideline 2.3.7 bars other apps' names in keywords; the subtitle is a judgement call left out on purpose. The description may say factually that RideZap opens Uber and Lyft.

**Subtitle (≤30):** `Know your usual ride fare` (25)

**Play short description (≤80):** `Save your regular trips, log the fares you see, and spot a price that's high.` (77)

**Promotional text (≤170):** `Open both ride apps with your trip filled in, type in the fares you see, and RideZap tells you whether today's price is high for you. Your fares stay on your phone.` (163)

**Description (draft; drops the ALL-CAPS skeleton, the opening "RideZap is…" line and the house ads paragraph):**
> Take the same rides often? Save the trip once — home to work, home to the airport — and checking it becomes two taps: RideZap opens Uber and Lyft with both ends already filled in.
>
> Back in RideZap, type in the fares you saw. RideZap remembers them and tells you, for that trip at that time of day, whether the price in front of you is high, typical or low compared with what you usually see — and which app is lower right now. Add a few past rides from your receipts and it works from the first week.
>
> Over time each trip shows your own hour pattern: the fares you've logged, by hour, for each app, so you can see when that trip tends to cost less.
>
> Keep a log of the rides you take, with what you paid, tips and a Work or Personal tag. Search it, filter it, see monthly totals per app, and copy it as CSV for an expense report.
>
> RideZap doesn't see Uber's or Lyft's prices and never shows a price you didn't enter. No account; your trips and fares stay on this phone. Places and distances come from OpenStreetMap.
>
> One ad appears at the bottom of a trip's page, from Google AdMob. Where the law requires it you choose about ad personalisation first, and can change it in Settings.

**Keywords:** `ride fare,rideshare,taxi,commute,fare log,ride log,airport ride,surge,receipt,trip cost`. No competitor trademarks.

**Screenshots to retake** (all from the real app):
- Fares must be the **capturer's own real past receipts**. Record which receipts in the capture log. No made-up numbers. If no real receipts are available, capture the honest empty and "Log 2 more" states rather than invent.
- No Settings frame. Sizes: iPhone 6.9", iPad 13", Play phone and tablet.
- Order:
  1. Check fares with a verdict card ("High · …% above your usual") and the right-now line.
  2. Trip page hour pattern.
  3. Your trips board.
  4. The quote keypad after returning from a ride app.
  5. Rides log with month totals.
- The current fastlane screenshots carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic.** Rebuild it from the new receipt icon and a Big Shoulders wordmark on `#22304F`. Per diagnosis, the current one shows the Flutter logo.

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton, the simulator paragraph and "a build that cannot start never ships"):
- "This version removes every switchable or hidden feature. Earlier builds contained price-comparison, watch-list and quote screens that only appeared when a build-time gateway key was set; those screens, the key and the flight and hotel searches have been deleted. Every feature is reachable from the first screen, with no account, identically in every region."
- "RideZap does not show Uber or Lyft prices; it never had access to them. It remembers fares the user types in and compares new quotes with that history."
- **Path:**
  1. On the first screen, tap 'Add your first trip'.
  2. Search 'San Francisco International Airport' and pick it, then search 'Ferry Building' and pick it. Save the trip.
  3. Tap 'Check fares' → 'Open Uber'. The Uber app or uber.com opens with both ends filled in. Return to RideZap and the fare keypad appears.
  4. To see a verdict without days of history, open the trip, tap 'Add a past ride' three times with any amounts from a receipt, then log a new quote that is higher.

  These are values the reviewer types, not a demo account.
- **External services:** Photon (komoot) place search; OSRM on FOSSGIS servers for distance; links to uber.com and lyft.com; Google AdMob; Firebase Crashlytics. No sign-in, no backend of ours.
- **Audience** (in place of the pasted subtitle): "People in US cities who take the same ride-hail trips repeatedly — commutes, airport runs, late shifts — and want to know whether today's quote is unusually high for them before booking."
- **Test devices:** state only what was actually used. A physical-device run is a human step and is **not verified** here.
- **Translation:** state honestly that new screens are English-first and that shared labels are translated.

**Privacy label.**
- **No collection change:** device ID, advertising data and crash data, all not linked.
- **Data stays on the phone:** places, trips, fares and rides.
- **Network requests:** place search sends the typed text, and routing sends coordinates, to Photon and FOSSGIS to fetch public map data. Neither is collection by the developer, but **disclose them in the privacy policy** (legal text, founder §6, Q5).
- Sharing the 20-app label is acceptable only if the practices really are identical. Store-compliance should confirm `PRODUCT_INTERACTION` is still true (Firebase Analytics through `agl_observability`).
- If S3 ships, add the location purpose string. Location is used on the device and sent only as coordinates to Photon reverse.

**differentiation (store JSON):**
- §1: rewrite to the new screens.
- §2: the audience line above.
- §3: §2's competitor paragraph, naming Obi as the live-price leader and stating the narrow claimed gap.
- §6: "Not a TripNest feature: TripNest plans trips and books flights, hotels and cars; RideZap has no booking, no flights, no hotels — it keeps a per-trip personal fare history for repeated local rides. Not MileMaster (drive logs for your own car) and not MyFinance (no budgets or general expenses)."
- §4 (beta testing) and §9 remain founder items.

**`_blocker` in store JSON.** It can be cleared once this ships, because the app no longer depends on `RIDEZAP_API_*`. That is store-compliance's edit.

## 6. Out of scope

- Live or estimated Uber, Lyft, Bolt, Waymo or taxi prices, ETAs or surge figures from any provider. There is no keyless source, and inventing them is banned.
- Booking or paying for rides inside RideZap. Uber's and Lyft's ride-request APIs need partner credentials.
- Flights, hotels, cars, buses and airport-transfer search (TripNest owns them, `overlap.md` G1).
- Public-transit alternatives. Transitous forbids commercial use. No other keyless transit API was verified.
- Turn-by-turn maps and navigation (iMaps).
- General expenses, budgets and mileage for your own car (MyFinance, MileMaster).
- Accounts, Supabase, sync, push servers, background fetch, AI chat, home-screen widgets.
- Reading Uber/Lyft receipts from e-mail. That needs mail access and is a privacy and legal question.
- Localising the new copy into the 11 other languages. English comes first; keep strings in one file so translators can follow.

## 7. Not verified

- Whether Lyft's `www.lyft.com/ride?…` link opens the Lyft app with both ends filled in on a real iPhone. The AASA lists `/ride` and curl kept the parameters, but on-device behaviour is untested. Without the app, curl lands on `ride.lyft.com/not-supported?…`. Phone Safari is untested.
- Whether Uber's `/ul` link pre-fills both ends from coordinates in today's Uber app. Uber's deep-link doc URL that `affiliate_links.dart:90` cites returned **HTTP 404** to curl on 2026-10-12. The redirect keeps the parameters and the AASA lists `/ul`.
- Competitor behaviour beyond App Store descriptions. WebSearch is disabled in this environment.
- Whether Photon or FOSSGIS would throttle the app at real user volume.
- Whether FOSSGIS objects to use by an ad-supported app. Their terms set technical rules, attribution and 1 request/s; I found no explicit commercial ban, but I read a machine-extracted copy of the German page.
- The Play feature graphic content (taken from diagnosis, not re-opened by me).
- Physical-device behaviour, and whether Apple accepts a resubmission.
- Store-name availability, if the founder renames the app.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. Keep RideZap, or retire it (D1)?** Portfolio-director recommends retiring it and moving the ride hand-off into TripNest (`overlap.md` G1).
  - **My PM view.** The product in this spec is honest and buildable in a session. But its distinct value (your usual fare) needs the user's own entries before it shows, and it competes for the crowded "compare Uber & Lyft" search against Obi, which has live prices.
  - If the founder wants fewer, stronger apps on an account Apple is judging as a whole, **retiring RideZap is the lower-risk choice**. If the founder wants to keep the listing, build this spec.
  - Rename? "RideZap" can stay.
- **Q2. Interstitial ads.** The tab-switch interstitial (`router.dart:167`) disappears with the tab bar. Should there be one anywhere else, or just the single inline banner? This is a money decision (Charter §3).
- **Q3. Referral tag.** The code appends `affId=americangroupllc` to Uber links. No Uber or Lyft referral agreement is confirmed (`affiliate_links.dart:17-25`). This spec removes the tag. Keep it only if a real agreement exists, which would also need a disclosure.
- **Q4. Volunteer-run map servers.** Photon (komoot) and FOSSGIS OSRM are free and keyless, with fair-use terms, attribution and 1 request/s. Is the founder comfortable with an ad-supported app depending on them, accepting that access can be withdrawn? The alternative is paying for or self-hosting geocoding and routing later (Charter §3). The app degrades gracefully: without them, saved trips and fare logging still work.
- **Q5. Privacy policy text.** It must mention that typed place names and coordinates go to Photon and FOSSGIS for map lookups. That is legal text (Charter §6).
- **Q6. Resubmission.** Replying to Apple and resubmitting stay frozen under the 5.6 hold (MA-043, Charter §1).
- **Q7. Beta testing statement.** differentiation §4 needs a true account of TestFlight testing, which only the founder can give.
