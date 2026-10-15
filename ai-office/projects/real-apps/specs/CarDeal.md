# Spec: CarDeal — check a used car before you buy it, and see how cars built like it have failed

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/CarDeal` (app in `mobile/`)
Base: `main` @ `ae13aa6b1bdbff74415e2c057a076191f2e9eebf` (`git rev-parse HEAD`, `git branch --show-current`, run 2026-10-12)
Baseline (run 2026-10-12 against that base): `flutter analyze` → "No issues found! (ran in 47.5s)". `flutter test` → "+516: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows changes under `mobile/fastlane/**` (descriptions, notes.txt, every screenshot, and 05.png deleted), plus `mobile/ios/Podfile.lock` and `mobile/ios/Runner.xcodeproj/project.pbxproj`. This spec changes none of those files. **One trap to watch:** adding a native plugin (`share_plus`, S1's `mobile_scanner`) makes CocoaPods rewrite `Podfile.lock`. Before you add one, run `git diff mobile/ios/Podfile.lock`. If someone else's edit is still there, do not commit `Podfile.lock`. Report it, and use the Clipboard fallback in M5 until that owner has committed.

---

## 1. Problem

**Apple's state.** Apple rejected the app under **5.6** on 2026-10-08T14:19:50Z (`/Users/spatchava/agl/.dist/rejections.json` → "CarDeal"): "the app contains features that appear to have been intentionally hidden during the review process." Google Play: PRODUCTION_DRAFT_STAGED.

**What in this binary reads as "hidden" (evidence, read 2026-10-12):**
- **Build-time define switches.** Three `String.fromEnvironment` defines (`CARDEAL_API_BASE_URL`, `CARDEAL_API_KEY`, `CARDEAL_DEFAULT_POSTAL_CODE`, at `lib/core/config/app_config.dart:21,25,30`) decide the app's shape. `lib/app/router.dart:21,27` define two tab sets: `liveFeedTabs = ['/', '/search', '/saved', '/budget', '/settings']` and `noFeedTabs = ['/budget', '/settings']`. `MainShell` picks one at run time (`router.dart:74-77`).
- **Screens that cannot be reached.** The default (submitted) build has no define, so Browse, Search, Saved, car detail and Compare are compiled into the binary but cannot be reached. `store/apps/CarDeal.json` → `differentiation` §1 says so outright: "The code also contains browse, search, saved, compare and detail screens, but they only appear in a build with a live inventory feed". That describes 5.6 exactly.
- **A dealer feed that has never worked.** It has never answered a request. `lib/services/http_listing_data_source.dart:15-16`: "It has never been run against a live gateway — there are no credentials in this repository". The old default host "no longer answers" (`app_config.dart:17-20`).

**Why it reads as a template, or as a duplicate (4.3 portfolio context):**
- **Its one working job duplicates other apps.** That job is a car-loan calculator ("standard amortisation", `lib/models/finance.dart:3-7`). The first screen is "What can I afford?" (`lib/l10n/cardeal_strings.dart:128`, `features/budget/budget_screen.dart`), which is CalcMaster's EMI with a car label. Its affordability ceiling repeats HomeWise's "Affordability" screenshot (`overlap.md` G4).
- **Its main content is a "not connected" notice.** "No live inventory is connected in this build. Search real listings on AutoTrader or CarMax." (`cardeal_strings.dart:154`, `widgets/no_live_feed_notice.dart:24-26`). The store screenshot carries that banner, and screenshot 3 is Settings.
- **Shared affiliate-family copy:** "Where prices come from" (`cardeal_strings.dart:156`), "Your data" (`:171`), "Nothing saved yet" (`features/saved/saved_screen.dart:40`).
- **Shared shell.** A Material `NavigationBar` with `AglAdBanner` above it, hidden on Settings (`router.dart:117`), plus an interstitial on every tab switch (`router.dart:128`).
- **Skin:**
  - The icon comes from the generator: `scripts/generate_app_icons.py:66` `"CarDeal": ("directions_car", "#263238", "#546E7A")`.
  - The splash is shared: `ios/Runner/Base.lproj/LaunchScreen.storyboard` has shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same as 37 of 43 apps.
  - The font is Inter (`core/theme/app_theme.dart:156` `GoogleFonts.interTextTheme`), on a seeded stock-Material scheme (`app_theme.dart:142-148`, brand red `#B71C1C`).
  - Corners are 16/12/20.
- **Name mismatch.** The store name is "iCarDeal" and the home-screen name is "CarDeal" (`Info.plist` `CFBundleDisplayName`). The pubspec still reads "Find the best car deals", but the app has no deals.

**What is real and worth keeping:**
- `finance.dart` `quote()`. It is tested, and it becomes one line of M4's per-car cost, not a screen.
- `PreferencesStore`, the theme-mode setting, the honest delete-everything flow (`settings_screen.dart:266-312`), the `PrivacyChoicesRow`-style UMP row, and the guarded startup in `main.dart`.
- The rest of the app depends on a feed that does not exist, so it goes.

## 2. User and core job

**User:** a person in the US buying a **used** car, usually private-party or from a small lot, with two to four candidates on the go. They have each car's VIN, or at least its year, make and model, plus an asking price. They want to know, before they drive across town or hand over a deposit:

> "Has this model been recalled, and for what? What actually goes wrong with cars built like this one? What should I ask the seller to prove? And what will it really cost me each month, fuel included?"

**Core job: Check a car.** The user types a VIN, or picks the year, make and model. Within seconds they get a car report built from three federal sources:
- the decoded build (NHTSA vPIC),
- every safety recall issued for that model-year, with the remedy, and with "park outside" / "do not drive" warnings shown first (NHTSA Recalls),
- owner complaints to NHTSA, summarised by component (NHTSA Complaints),
- EPA fuel economy for the exact engine/transmission variant (fueleconomy.gov).

They save the car to a **shortlist**, enter the asking price, and the report gains a **cost-to-own** line. They then compare shortlisted cars side by side.

**Signature feature: "Built like yours."**
- **What it matches.** A VIN's characters 1–8 encode the maker and the build: body, engine, restraint system, line. Characters 10–11 encode the model year and the assembly plant. Character 9 is a check digit. NHTSA complaint records carry an 11-character partial VIN. CarDeal matches complaints whose partial VIN shares positions 1–8 and 10–11 with the user's VIN (the check digit is skipped).
- **What it shows.** The complaint pattern for **cars built like this exact one**, next to the pattern for the whole model-year.
- **The seller checklist.** It turns the top trouble spots, and every recall with a remedy, into a concrete **"Ask the seller / check at inspection"** list. The user ticks the list off, it persists, and they can share it.

*Measured on real data (2026-10-12, a Python prototype over the curl responses in §3):*
- VIN `1HGCM82633A004352` (2003 Honda Accord EX-V6 coupe) has 2,013 model-year complaints. Of those, 212 come from VINs built like it.
- Among those 212, **POWER TRAIN accounts for 151 (71%)**. Across all 2003 Accords the figure is 926 of 2,013 (46%). The next components in the built-like group are AIR BAGS 12, ELECTRICAL SYSTEM 11 and VEHICLE SPEED CONTROL 11.
- The same model-year has 24 recalls, including `19V182000` (driver air-bag inflator).
- These figures check the method. **They are not copy.** The app shows whatever it computes at run time.

**Honesty limits the feature must state on screen:**
1. Complaint counts are reports filed by owners, **not failure rates**. NHTSA publishes no count of cars on the road, so there is no denominator.
2. Partial VINs are missing on some complaints: 359 of the 2,013 above had an empty `vin`. The app shows "N of M complaints carry a VIN".
3. The keyless API cannot say whether **this** car's recall was repaired. `api.nhtsa.gov/recalls/recallsByVin` returned **HTTP 403** to curl. So the app lists recalls *for the model-year* and tells the user to confirm repair status with the seller's records, a dealer of that make, or NHTSA's VIN lookup.

**Competitor check.** WebSearch is disabled here ("Internet mode is not enabled"). I used Apple's keyless iTunes Search/Lookup API on 2026-10-12. I read store descriptions only; I did not run any of these apps.
- **VINDecoded "VIN Check Report, Plate Lookup"** (id1191483515, 3,118 ratings). Its description claims "Open recalls, safety ratings, complaints and service bulletins" and "Compare cars side by side, with notes, tags and inspection checklists", and it sells auto-renewing subscriptions. **This is the closest competitor, and it already covers much of the shortlist and compare idea.**
- **"VIN Report for Used Cars"** (Omnisee, id1181052583, 1,803 ratings). It sells a market-value and history-report subscription.
- **Bumper** (id1543977359). Paid history reports.
- **SaferCar** (NHTSA, id1526869558, 117 ratings). The official per-VIN recall check. It does not mention complaints, fuel cost or comparison.
- **CARFAX** (id479267592). Listings plus paid history.

So the **claimed gap** is narrow, and I state it plainly:
- (a) "Built like yours". No description above mentions grouping complaints by VIN build pattern, or setting a sub-population against the whole model-year.
- (b) A seller checklist **generated from that car's own recalls and complaint pattern**, rather than a generic inspection list.
- (c) Free with no account, no plate lookup, no paid report upsell and no subscription. Every figure links to its federal source.

**Competitor behaviour beyond their descriptions is not verified.** "VIN check" is a crowded category, so the 4.3 "already widely available" risk is real. That is why the signature, not the decoder, has to lead the screenshots (§5) and the founder question Q1.

## 3. Data sources (real, keyless; verified 2026-10-12)

Hosts resolved with the repo's own DoH check (`python3 -c "import verify_api_hosts as v; v.doh(h)"` from `agl-manifest/scripts`): `vpic.nhtsa.dot.gov ok`, `api.nhtsa.gov ok`, `www.fueleconomy.gov ok`, `static.nhtsa.gov ok`, `www.nhtsa.gov ok`. These hosts are not yet in the app's code. After the build, re-run `python3 scripts/verify_api_hosts.py --print` and confirm all four show `ok` for CarDeal.

| Data | Endpoint | curl proof (2026-10-12) |
|---|---|---|
| VIN decode | `https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{VIN}?format=json` | HTTP 200, 3,921 B. HONDA / Accord / 2003 / EX-V6 / Coupe / 6 cyl / Gasoline. `ErrorCode "0"`, "VIN decoded clean. Check Digit (9th position) is correct" |
| Recalls by model-year | `https://api.nhtsa.gov/recalls/recallsByVehicle?make=&model=&modelYear=` | HTTP 200, 36,156 B, Count 24 (2003 Honda Accord). Fields include `NHTSACampaignNumber, Component, Summary, Consequence, Remedy, parkIt, parkOutSide, overTheAirUpdate, ReportReceivedDate`. 2015 Ford `F-150` → 14 |
| Complaints by model-year | `https://api.nhtsa.gov/complaints/complaintsByVehicle?make=&model=&modelYear=` | HTTP 200, **1,991,850 B**, count 2,013. Fields `odiNumber, crash, fire, numberOfInjuries, numberOfDeaths, dateOfIncident, dateComplaintFiled, vin (11 chars), components (comma-joined), summary` |
| Model lists for the no-VIN path | `https://api.nhtsa.gov/products/vehicle/makes?modelYear=&issueType=r` and `.../models?modelYear=&make=&issueType=c` | HTTP 200: 341 makes for 2015; 69 Ford models |
| Crash-test stars (SHOULD S2) | `https://api.nhtsa.gov/SafetyRatings/modelyear/{y}/make/{m}/model/{model}` → `.../SafetyRatings/VehicleId/{id}` | HTTP 200. 2019 Honda Accord → VehicleId 14004 → `OverallRating "5"` |
| Fuel economy variants | `https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year=&make=`, `.../menu/options?year=&make=&model=` (send `Accept: application/json`) | HTTP 200. 2003 Accord: 4 options, e.g. "Auto 5-spd, 6 cyl, 3.0 L" = 18657 |
| Fuel economy record | `https://www.fueleconomy.gov/ws/rest/vehicle/{id}` | id 18657 → `city08 19, highway08 27, comb08 22, fuelType "Regular", fuelCost08 3050`. EV id 46204 (2023 Model 3 LR AWD) → `combE 25.8238` kWh/100 mi, `range 358` |
| National average fuel prices | `https://www.fueleconomy.gov/ws/rest/fuelprices` | `{"regular":"4.47","midgrade":"5.07","premium":"5.48","diesel":"6.38","electric":"0.15","e85":"3.31","cng":"3.08","lpg":"3.59"}`. No date field in the response |
| Shortlist, notes, checklist ticks, cached reports | on-device (`shared_preferences` through the existing `PreferencesStore`, plus one JSON file per cached report in app documents) | — |

**Gotchas found while verifying (the developer must handle each one):**
- **Model names differ across the three systems.** vPIC gives "F-150", recalls need "F-150" (`model=F150` → HTTP **400** with Count 0), and fueleconomy.gov calls it "F150 Pickup 2WD / 4WD / FFV". Rules:
  - Query recalls and complaints only with a model string that appears (case-insensitively) in NHTSA's `products/vehicle/models` list for that year and make. Then "0 recalls" means NHTSA lists none, not that the name failed to match.
  - If the vPIC model is not in that list, show the list and let the user pick.
  - For fuel economy, normalise both names (lowercase, strip non-alphanumerics) and offer the fueleconomy.gov models whose normalised name starts with the vPIC model. The user confirms the variant (drive, engine, transmission). Never auto-pick silently when more than one matches.
- **fueleconomy.gov returns `menuItem` as an object, not a list, when there is one option** (Model 3 LR AWD 2023 → `{"menuItem":{"text":"Auto (A1)","value":"46204"}}`). Accept both shapes.
- **Complaints can be about 2 MB for a popular model-year.** Parse in a background isolate (`compute`) and store only the derived summary plus at most 200 summaries, not the raw body. Dates are `MM/DD/YYYY` strings, so parse them before sorting (comparing the strings gave nonsense ranges).
- **`fuelCost08` assumes 15,000 miles a year at current prices.** 15,000 / 22 × $4.47 = $3,048 against the API's 3,050. So the app's default is **1,250 miles a month, labelled "fueleconomy.gov's assumption — change it"**. EVs: `combE/100 × miles × electric price`.
- **The fuel-price response carries no date.** Label it "U.S. average, from fueleconomy.gov" and show the date the app fetched it. Do not claim a week.
- **VIN rules.** Validate on the device before any network call: 17 characters, none of I/O/Q, and the 49 CFR 565 check digit (weights 8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2; transliteration A=1…Z=9). Pre-1981 VINs and non-North-American VINs that fail the check digit get "This VIN's check digit doesn't match. Check for a mistyped character." They can still continue with year/make/model.

No API keys, no paid feed, no Supabase, no sign-in, no backend.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. One build, nothing hidden (5.6).**

Delete:
- the dealer-inventory feature and every switch: `core/config/app_config.dart` `apiBaseUrl/apiKey/defaultPostalCode/hasLiveInventory/isLiveInventoryConfigured` (keep the three policy URLs);
- the services: `services/http_listing_data_source.dart`, `services/listing_data_source.dart`;
- the widgets: `widgets/no_live_feed_notice.dart`, `widgets/car_card.dart`, `widgets/price_history_chart.dart`;
- the models: `models/listing.dart`, `models/deal_rating.dart`, `models/price_snapshot.dart`, `models/saved_search.dart`, `models/search.dart`;
- the features: `features/home`, `features/search`, `features/saved`, `features/detail`, the listing `features/compare`, and the standalone `features/budget`;
- `noFeedSearchLinks`, and the affiliate builders unless Q3 says to keep them;
- `liveFeedTabs`/`noFeedTabs`/`defaultInitialLocation`;
- in providers: inventory, filter, sort, saved-car and saved-search providers, the postal code, and `noLiveFeedProvider`;
- the `dio` dependency, if M2 uses `package:http` or keeps `dio` for the new client (pick one, not both).

The new features in M2–M5 replace all of this. They are not gated.

Acceptance:
- (a) `grep -rn "fromEnvironment" mobile/lib` → 0 hits. The AdMob ids inside `agl_ads` are out of scope. `main.dart`'s `AglAdIds.fromEnvironment(...)` call stays only because it is the shared ads package's API. Note this in the commit.
- (b) `grep -rniE "in this build|this build|not connected|no live|inventory|coming soon|unavailable in|gateway|CARDEAL_API|sample|placeholder|Simulator" mobile/lib` → 0 hits. Any remaining match needs a one-line justification in the commit message.
- (c) Release iOS build: `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "this build|live inventory|CARDEAL_API|gateway|AutoTrader"` → 0. This checks the binary Apple inspects, not just the source.
- (d) Every feature is reachable from the first screen on a fresh install, in every region and locale, with no account.

**M2. Core job: Check a car → Car report.**

*Entry, on the home screen:*
- a VIN field (17-character counter, uppercase, I/O/Q rejected as typed, check digit validated on the device),
- **or** "No VIN? Pick year, make, model": year list, then NHTSA `products` makes, then models.

*Car report (one scrolling page), top to bottom:*
1. **Header.** Year Make Model Trim, body, engine (cylinders/litres), fuel, drive, plant country, all from vPIC. Show only the fields vPIC filled; never print "Unknown" or "0". Add the line "Decoded by NHTSA vPIC · <fetch date>".
2. **Safety recalls (N).** Any recall with `parkIt` or `parkOutSide` true comes first, under a red **"Do not drive" / "Park outside"** label quoting NHTSA's flag. Each row shows campaign number, component, report date, a 3-line summary that expands to Summary, Consequence and Remedy, and an "Over the air" chip when `overTheAirUpdate`. A permanent line reads: "These are recalls for every <year make model>. Whether this car's repair was done isn't public through this service — ask for the dealer repair record, or check the VIN at nhtsa.gov/recalls." Include a button that copies the VIN and opens `https://www.nhtsa.gov/recalls` in the browser. Zero recalls → "NHTSA lists no safety recalls for the <year make model>." Never "No issues".
3. **Owner complaints.** Total M, the share that carry a VIN, the top 5 components as a bar row, and crash, fire, injury and death totals. Tapping opens the complaint list (M5 filter and search).
4. **Fuel economy.** After the user confirms the variant (sheet listing fueleconomy.gov options): city/highway/combined MPG (or kWh/100 mi and range for EVs), and **annual fuel cost at the user's miles**.
5. **Built like yours** (M3), shown only when the entry was a VIN.
6. **Cost to own** (M4), once an asking price is entered.

*Acceptance:*
- On a fresh install, typing `1HGCM82633A004352` shows a report whose header reads 2003 HONDA Accord EX-V6 Coupe, with 24 recalls (or whatever NHTSA returns that day), and complaints summarised.
- A widget test with recorded fixtures (`test/fixtures/`, cut from **real** 2026-10-12 responses) asserts the order: park-outside recall first, then the rest by date.
- The model-name rule from §3 is unit-tested with the real "F-150"/"F150"/"F150 Pickup 4WD" strings.

**M3. Signature: "Built like yours" + seller checklist.**
- **Pure module** `lib/services/build_pattern.dart`.
  - Input: the user's VIN and the parsed complaints.
  - Output: `{matchedCount, withVinCount, totalCount, componentsMatched: [(component, count, share, crash, fire, injuries)], componentsAll: [...]}`.
  - Matching: positions 1–8 and 10–11 equal, case-insensitive; complaints with fewer than 11 VIN characters are excluded from "matched" but counted in "total".
  - `components` is split on commas and trimmed.
- **Card.** "Cars built like yours: 212 owner complaints (of 1,654 that carry a VIN)". Then the top 5 components, each with **two bars: built-like share and whole-model-year share**. A component is called out ("Most reported for cars built like this one") only when its built-like share is at least 10 percentage points above the model-year share **and** it has at least 10 matched complaints. Fewer than 10 matched complaints in total → "Too few complaints from cars built like this one to show a pattern (N). Showing the whole model-year." Never extrapolate.
- **Permanent caption.** "Counts are complaints filed with NHTSA by owners, not failure rates — NHTSA doesn't publish how many of these cars are on the road." Plus a "How matching works" link that explains VIN positions 1–8 and 10–11 in two sentences.
- **Seller checklist**, generated per saved car:
  - one item per recall: "Ask for proof recall <campaign> (<component>) was repaired";
  - one item per called-out component: "Ask about <component> repairs; on the test drive, check <hint>". The hints are a **fixed table in code** for NHTSA's top-level component names (POWER TRAIN → "shifts at low and highway speed, no slipping or flare"; AIR BAGS → "airbag light goes out after start"; SERVICE BRAKES → "straight, quiet stops, no pulsing"; ELECTRICAL SYSTEM → "every window, light and gauge works"; ENGINE AND ENGINE COOLING → "temperature stays mid-gauge, no coolant smell"; STEERING → "no clunk or pull at full lock"; SUSPENSION → "no knocks over bumps"; FUEL SYSTEM → "no fuel smell"). Any other component gets "Ask about <component> repairs" with no invented hint.
  - The user can add their own items. Ticks and notes persist per car.
- **Acceptance:**
  - A unit test over the real 2003 Accord fixture asserts matched = 212 and POWER TRAIN = 151 for `1HGCM82633A004352`, and that the check digit is ignored. If the fixture is trimmed for size, assert against the trimmed fixture's own recomputed counts and record the trim in the test.
  - Tests cover the fewer-than-10 fallback, the call-out threshold, and checklist generation (recall items plus component items).

**M4. Cost to own, per car (not a standalone calculator).**
- **Inputs on the saved car:**
  - asking price (required for this section),
  - down payment,
  - APR,
  - term (`loanTermOptions`),
  - sales tax %,
  - miles per month (default 1,250, labelled with its source),
  - fuel grade (preset from fueleconomy.gov `fuelType`, editable),
  - optional insurance per month and registration per year, both **empty by default** (no invented figures).
- **Output:** monthly loan payment (existing `quote()`), monthly fuel (EPA combined × miles × fueleconomy.gov national price for that grade), the optional lines, and a **monthly total**. The line "Fuel at $<price>/gal U.S. average (fueleconomy.gov, fetched <date>)" stays visible.
- **Removed:** the "What can I afford?" screen, its affordability ceiling (`affordablePrice`) and its "term gap" sentence. Delete `affordablePrice` unless a test of something kept needs it.
- **Acceptance:** a unit test checks fuel cost: 22 mpg, 1,250 mi/month, $4.47 → $253.98/month (1,250 / 22 × 4.47). The EV path is tested with `combE` 25.8238, 1,250 mi, $0.15/kWh → $48.42. A widget test checks that the section is hidden until an asking price exists.

**M5. Depth: shortlist, compare, search/filter, share, offline.**
- **Shortlist (home).** Every checked car can be saved, and saving keeps it with its inputs, notes, ticks and cached report.
  - Card: year make model, the last 6 VIN characters, recall count (red if any park flags), the top built-like trouble spot, monthly total (or "Add asking price").
  - Sort by monthly total, recalls or date added. Text filter by make, model or note.
  - Swipe to delete with Undo. Rename ("Blue one on Elm St").
  - Persisted through `PreferencesStore`. Survives relaunch.
- **Compare.** Pick 2–4 shortlisted cars to get columns: recalls (and park flags), complaints total, top built-like trouble spot, combined MPG, monthly fuel, monthly total, checklist progress. The best value in each row is marked, ties stay unmarked, and rows with missing data say "—" with a reason.
- **Complaint list.** Filter chips by component and by crash/fire/injury, text search in summaries, newest first (parsed dates). Each row shows ODI number, date, component and summary.
- **Share / export.** "Share report" sends plain text through the system share sheet: header, recalls with campaign numbers, the built-like summary with its caption, fuel and cost lines, the checklist with ticks, and sources with fetch dates. Use `share_plus` **only after** the Podfile.lock check in the header. Until then, or if blocked, a "Copy report" action (Flutter `Clipboard`) meets this criterion.
- **Offline and errors.**
  - Each saved car's report is cached with its fetch date, and opens offline with "Saved <date> · offline". Pull to refresh re-fetches.
  - A new check with no network → "Checking a car needs a connection to NHTSA and fueleconomy.gov." with Retry; the VIN check digit is still validated.
  - Per-source failure: when one source fails, the others still render. That section shows "NHTSA complaints didn't answer. Try again." Never a blank page and never a spinner forever (15 s timeout).
  - Use `connectivity_plus`. It is already in `pubspec.yaml` and unused (`grep -rn Connectivity mobile/lib` → 0).
- **Acceptance:** an integration-style widget test covers: save two cars → relaunch (a fresh `ProviderScope` on the same mock prefs) → both present with ticks → compare shows 2 columns. An offline test serves a cached report with the label. The share text is unit-tested.

**M6. Own identity: home, onboarding, colour, type, shape, icon, splash, name.**
- **Home layout: no tab bar.**
  - One home screen, **"Shortlist"**: a large "Check a car" VIN field with the YMM link at the top, the shortlist cards below, and a Compare button once 2 or more cars are saved.
  - Settings opens from an app-bar icon. The car report and Compare are pushed pages.
  - This replaces the shared `NavigationBar` shell.
- **Ads.**
  - `AglAdBanner` is **not** in any shell. One inline banner sits at the end of the car report, below Sources. None on Shortlist, Compare, onboarding or Settings.
  - The tab-switch interstitial is removed, because there are no tabs; any interstitial is founder question Q2.
  - Acceptance: `grep -rn "AglAdBanner" mobile/lib` → exactly 1 hit, in the report screen. `grep -rn "onTransition" mobile/lib` → 0 (unless Q2 says otherwise).
- **Onboarding: "Where's the VIN?"** Shown once and re-openable from Settings, as two cards:
  1. **Where to find the 17-character VIN.** Base of the windshield on the driver's side, the driver's door-jamb sticker, and the title, registration or insurance card. Use simple drawings in `CustomPainter`, no stock art.
  2. **What CarDeal checks.** Recalls, owner complaints, cars built like yours, fuel cost. One line each, naming NHTSA and fueleconomy.gov.

  No sign-in, no "Get started" / "Welcome" boilerplate. The final button reads "Check a car".
  - Acceptance: tests that it is shown once and that Skip works.
- **Palette "Guide sign"** (cool, not the warm paper family other specs chose). `ThemeMode.system`, with a hand-built `ColorScheme`, not `fromSeed` with a brand red.
  - Light: surface concrete `#E9ECEA`, cards `#FFFFFF`, text asphalt `#1A1E21`, **primary guide-sign green `#00563F`** (on-primary white), secondary signal amber `#D99A00` (checklist and "called out"), danger `#A4262C` (park-it/park-outside, fire/crash), muted `#5E676D`.
  - Dark: surface asphalt `#141719`, cards `#1E2326`, text `#E6E9E7`, primary lifted to `#3FA37E`, amber `#F0B83A`, danger `#E0676C`.
  - Acceptance: `grep -rhoiE "B71C1C|7F0000|F59E0B|10B981|EF4444|3B82F6|1A1A2E|F8F9FA" mobile/lib` → 0. The palette's contrast pairs (text on surface, on-primary on primary, both modes) must be ≥ 4.5:1, asserted in a test using `computeLuminance`.
- **Typography.**
  - **Barlow** (Regular, Medium, SemiBold) for UI. **Barlow Semi Condensed** (SemiBold, Bold) for headings and the big numbers. Barlow takes its cue from California highway signage, which fits the domain.
  - Use `FontFeature.tabularFigures()` on every price, count, MPG and VIN.
  - Show VINs in 4-4-4-5 groups.
  - Bundle the TTFs under `assets/fonts/` with `OFL.txt`, declare them in `pubspec.yaml`, and **remove `google_fonts`** (no runtime fetch).
  - Sources resolve: curl `github.com/google/fonts/raw/main/ofl/barlow/Barlow-Regular.ttf` 200 (104,068 B), `-Medium` 200 (103,536 B), `-SemiBold` 200 (108,348 B), `OFL.txt` 200 (4,377 B), and `ofl/barlowsemicondensed/BarlowSemiCondensed-SemiBold.ttf` 200 (109,772 B), `-Bold` 200 (111,772 B).
  - `grep -rli barlow` across `/Users/spatchava/agl` (excluding the Flutter SDK and pub cache) found no app using it, and no other spec in `specs/` names it.
- **Shape.**
  - 6 px corners on cards and buttons. A guide-sign treatment on the report header and the recall-count badge: a green field with a 2 px inset white border.
  - Flat surfaces. No 16 px glass cards. Chips are 6 px, not pills.
  - Acceptance: `grep -rn "circular(16)\|circular(20)" mobile/lib` → 0.
- **Icon.**
  - Hand-built art: a guide-sign-green rounded square with a 2 px inset white border, holding a white VIN-plate strip with a check mark through it, flat with no gradient. **It must not come from `generate_app_icons.py`.**
  - Ask store-compliance to delete line 66 (`"CarDeal": ("directions_car", ...)`) so a rerun cannot overwrite the new icon. That file is in `agl-manifest`, not this repo.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- **Splash.**
  - A new `LaunchScreen.storyboard` with background `#00563F` and the white mark. Android `launch_background.xml` uses the same.
  - Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Names.**
  - `CFBundleDisplayName`, the Android `android:label`, `MaterialApp.title` and the pubspec description ("Check a used car before you buy") must match the store name the founder picks (Q1). Until then they stay "CarDeal".
  - Acceptance: a test reads `Info.plist` and asserts the display name equals a single `kAppName` constant.

**M7. Honest, app-specific copy; shared furniture trimmed.**
- **Remove** "Where prices come from", "Your data", "Nothing saved yet", "What can I afford?", "You can afford about", "Live inventory", "No live inventory…", "Search AutoTrader/CarMax", and the affiliate disclosure (unless Q3 keeps links).
- **Settings becomes one short page:**
  - **Sources**: NHTSA vPIC, NHTSA Recalls & Complaints, fueleconomy.gov, each with what it provides, the "counts are not failure rates" caption, and the VIN-repair-status limit.
  - **Units & defaults**: miles per month, default fuel grade.
  - **Appearance**.
  - **Language**: `AglLanguageScreen` may stay (shared infrastructure).
  - **Privacy choices**: keep the UMP row and its behaviour (legal).
  - **Privacy policy, Terms, Support.**
  - **Delete everything**: keep the existing flow. The copy becomes "Delete your shortlist, notes and saved reports from this phone".
  - **Version**: read from the build, not the hard-coded `'1.0.0 (1)'` at `settings_screen.dart:212`.
- **Crash reporting row.** Remove the "Crash reporting: Not configured" row (`settings_screen.dart:219`). It is an internal state, not a user control.
- **Empty shortlist:** "No cars yet. Check a VIN, or pick a year, make and model." No generic "Nothing saved yet".
- **Banned in the UI:** "coming soon", "not connected", "in this build", "unavailable", "simulator", "sample", "demo".

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes.
- **New tests cover:**
  - the VIN validator (good VIN, I/O/Q, wrong check digit, short);
  - the model-name rule;
  - each API parser against **real** recorded fixtures under `test/fixtures/`: vPIC 2003 Accord, recalls 2003 Accord, complaints trimmed with the trim recorded, fueleconomy options with both list and single-object `menuItem`, vehicle 18657 and 46204, fuelprices;
  - `build_pattern` (M3);
  - checklist generation;
  - the fuel-cost and EV maths (M4);
  - shortlist persistence and relaunch;
  - compare;
  - complaint filter and search;
  - share text;
  - the offline cached report;
  - per-source failure rendering;
  - onboarding shown once;
  - "no tab bar / one AglAdBanner";
  - identity (fonts declared and on disk, no `google_fonts` in pubspec, palette contrast, storyboard shasum, display name);
  - an extended `release_sanity_test` that greps `lib/` for the M1(b) strings.
- **Tests that go:** remove tests for the deleted listing, feed, budget and affiliate code **only together with the code they test**:
  - `test/services/listing_data_source_test.dart`
  - `test/models/price_snapshot_test.dart`
  - `test/models/search_test.dart`
  - `test/models/unreported_fields_test.dart`
  - `test/widgets/browse_screen_test.dart`
  - `test/widgets/budget_screen_test.dart`
  - `test/widgets/compare_screen_test.dart`
  - `test/widgets/detail_screen_test.dart`
  - `test/widgets/saved_screen_test.dart`
  - `test/widgets/search_screen_test.dart`
  - `test/support/sample_catalog.dart`
  - the listing parts of `test/models/domain_test.dart`, `test/app/providers_test.dart`, `test/services/preferences_store_test.dart`, `test/services/affiliate_test.dart`, `test/foldable_layout_test.dart`, `test/app_boot_test.dart`, `test/harness.dart`, `test/i18n_test.dart` and `test/widgets/settings_screen_test.dart`

  The commit message lists every removed test by name. Keep and adapt the `finance.dart` `quote()` tests. No other test is deleted or skipped. `foldable_layout_test` and `i18n_test` must be **rewritten** for the new screens, not dropped.
- **Look at it.** Launch on the iOS simulator. Check `1HGCM82633A004352` live, save it, enter an asking price, and look at screenshots of the report (header + recalls), Built like yours, the checklist, Shortlist with 2 cars, Compare, and onboarding card 1. No white screen, no overflow. Commit path-limited (never `fastlane/`, `Podfile.lock` or `project.pbxproj` while they carry others' edits) and push to `main`.

### SHOULD (if time allows, in this order)

- **S1. Scan the VIN** with the camera (`mobile_scanner`, Code 39 / Data Matrix on door-jamb stickers). This needs `NSCameraUsageDescription` ("Scan the VIN barcode on the door jamb or windshield") and adds a pod. Same Podfile.lock rule as M5. Typed entry remains the main path.
- **S2. NHTSA crash-test stars** in the report and in Compare (`SafetyRatings` endpoints in §3). The user picks the matching `VehicleDescription` when there is more than one. "Not rated by NHTSA" when absent.
- **S3. Recall watch on launch.** For saved cars, re-query recalls once a day on app open and badge "New recall since you saved this car (<campaign>, <date>)". On-device only; no push, no background fetch.
- **S4. iOS-native feel.** On iOS, `CupertinoIcons`, Cupertino page transitions and a `CupertinoSliverNavigationBar` large title on Shortlist. Material stays on Android.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/` or `fastlane/`)

**Name.** Founder decision, Q1. "iCarDeal" carries the portfolio's mechanical "i" prefix, and "Deal" now misdescribes the app. Candidates (availability **not checked**): "CarDeal: Used Car Check", "Built Like Yours: VIN Check", "Lemon Lens". The bundle id is permanent either way.

**Category.** Keep `SHOPPING` (the closest competitors, VINDecoded, Omnisee and Bumper, list under Shopping per the iTunes API). Secondary: `REFERENCE` (SaferCar's genre).

**Subtitle (≤30):** `Used car check before you buy` (29)

**Play short description (≤80):** `Recalls, owner complaints and real monthly cost for the used car you're eyeing.` (79)

**Promotional text (≤170):** `Type a VIN and see every recall, what owners of cars built like it complain about, and what it will really cost you each month — free, from NHTSA and EPA data.` (159)

**Description (draft; drops the shared ALL-CAPS skeleton, the opening "<AppName> helps you…" line, and the house ads paragraph's wording):**
> Looking at a used car? Type its 17-character VIN — or pick the year, make and model — and get a report built from U.S. government data: the car's decoded build from NHTSA, every safety recall for that model-year with the fix the maker offers (and NHTSA's "park outside" warnings first), owner complaints filed with NHTSA grouped by part, and EPA fuel economy for the exact engine.
>
> Built like yours: a VIN encodes the body, engine, model year and assembly plant. CarDeal finds the complaints filed about cars that share those characters and shows how their trouble spots differ from the model-year as a whole — then turns them, with the recalls, into a list of things to ask the seller and check on the test drive. Complaint counts are reports from owners, not failure rates, and the app says so.
>
> Add the asking price and your loan terms to see the real monthly cost, fuel included at the U.S. average price. Save the cars you're considering, add notes, tick off your checklist, compare up to four side by side, and share a report. Saved reports open offline.
>
> No account, no plate lookup, no paid reports. Recall repair status for an individual car isn't available from NHTSA's public data; CarDeal tells you how to confirm it.
>
> Free with ads from Google AdMob, shown at the end of a report. Where the law requires it you choose about ad personalisation first, and can change it later in Settings.

**Keywords:** `vin check,vin decoder,recall,used car,car complaints,nhtsa,mpg,fuel cost,car buying,inspection checklist`

**Screenshots to retake.** All live, from real VINs checked at capture time; no seeded cars, no Settings frame. iPhone 6.9", iPad 13", Play phone/tablet.
1. Built like yours card, with the two-bar comparison and the caption.
2. Car report top: guide-sign header, recalls with a park-outside item if the chosen car has one (do not hunt for a dramatic car to stage fear; use a real car the capturer chose).
3. Seller checklist with some items ticked.
4. Compare, two cars.
5. Shortlist home.

The current fastlane screenshots carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic.** Rebuild it from the new icon and a Barlow wordmark on `#00563F`. The current one shows the Flutter logo (diagnosis: identical icon-region hash in 14 apps).

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton and the simulator / "a build that cannot start never ships" paragraph):
- "This build has no hidden or switchable features. Earlier builds contained car-listing screens that only appeared with a build-time dealer-feed key; those screens and the switch have been deleted. Every feature is reachable from the first screen, without an account, identically in every region."
- Path: "Type the VIN 1HGCM82633A004352 (a 2003 Honda Accord) on the first screen → the report opens → scroll to 'Built like yours' → tap 'Save to shortlist', enter an asking price → 'Cost to own'." A VIN is public vehicle data, not a demo login.
- External services: NHTSA vPIC and api.nhtsa.gov (recalls, complaints), fueleconomy.gov (EPA fuel economy and U.S. average fuel prices), Google AdMob, Firebase Crashlytics. No sign-in, no backend of our own.
- Audience, in place of the pasted subtitle: "People buying a used car, often private-party, who want to check recalls and known trouble spots for a specific car and compare true monthly costs before committing."
- Test devices: state only what was actually used. A physical-device run is a human step and is **not verified** here.
- Translation: state honestly that new screens are English-first and that other locales show shared labels translated.

**Privacy label.** No change: device ID, advertising data and crash data, all not linked. VINs and notes stay on the phone. API calls send the VIN or year/make/model to NHTSA and fueleconomy.gov to fetch public data, which Apple does not treat as collection by the developer. `share_plus` and `mobile_scanner` collect nothing. If S1 ships, add the camera purpose string; camera frames are processed on the device. Sharing the 4-app label is correct here, because the practices are identical.

**differentiation (store json):**
- §1: rewrite to the new screens.
- §3: use §2's competitor paragraph, keeping its "descriptions only" caveat and naming VINDecoded as the closest.
- §6: "Not a feature of CalcMaster or HomeWise: no general loan or home-affordability calculator; the loan line exists only inside a specific car's cost to own. Not CodeDeal/GadgetNest: no listings, prices or deals."
- §4 (beta testing) and §9 remain founder items.

**`_blocker` in store json.** It can be cleared once this ships, because the app no longer depends on `CARDEAL_API_*`. That is store-compliance's edit, not mine.

## 6. Out of scope

- Car listings, dealer inventory, prices, "deal ratings", market value or trade-in estimates. There is no keyless real source, and inventing them is banned.
- Vehicle history: accidents, title brands, odometer. NMVTIS and similar are paid or keyed.
- Per-VIN open-recall status. `recallsByVin` returned 403. Do not scrape nhtsa.gov.
- Plate lookup.
- Technical service bulletins. No keyless endpoint was verified.
- A general loan or affordability calculator (CalcMaster and HomeWise own those).
- Mileage or fuel logging for a car you own (MileMaster owns drive logs).
- Accounts, Supabase, sync, push notifications, background fetch, AI chat.
- Localising the new copy into the 11 other languages (English first; keys go through `CarDealL10n` so translators can follow).
- A home-screen widget.

## 7. Not verified

- `https://www.nhtsa.gov/recalls` (the page the report links to) answered **HTTP 403** to curl with a browser user-agent. DNS resolves (`www.nhtsa.gov ok`). Whether it opens in Safari on a phone is not verified; the developer must open it in the simulator and screenshot it. If it fails, the button opens SaferCar's App Store page (`apps.apple.com/app/id1526869558`) instead.
- Competitor behaviour beyond App Store descriptions. WebSearch is disabled in this environment.
- Whether NHTSA or fueleconomy.gov rate-limit a phone that checks many cars quickly. Nothing was observed in about 15 requests.
- The date of fueleconomy.gov's fuel prices; the response has no date field.
- How often vPIC's model string is missing from NHTSA's `products` model list. I tested only Accord and F-150. The pick-from-list fallback covers the rest.
- Store-name availability for any Q1 candidate.
- Physical-device behaviour, and whether Apple accepts a resubmission.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. Name, and whether the product is worth keeping.** VIN-check apps are a crowded App Store category (VINDecoded, Omnisee, Bumper, SaferCar and more). This spec bets on "Built like yours" plus the generated seller checklist as the distinct angle. If the founder judges that not distinct enough under 4.3, the alternative the plan names is **retiring CarDeal** (Charter §8). If kept: keep "iCarDeal" or rename (candidates in §5, availability not checked)?
- **Q2. Interstitial ads.** The tab-switch interstitial (`router.dart:128`) disappears with the tab bar. Add an interstitial anywhere else (for example, after closing a report), or run one inline banner only? Money decision (Charter §3).
- **Q3. Affiliate links.** The code carries `affId=americangroupllc` / `ref=americangroupllc` partner links (`services/affiliate.dart`). Do real AutoTrader, CarMax or Tesla affiliate accounts exist under that id? Not verified. If yes, should the report offer "Find a <year make model> for sale on AutoTrader"? This spec removes them by default; keeping them brings back the "affiliate family" tell and a disclosure obligation.
- **Q4. Resubmission.** Replying to Apple and resubmitting stay frozen under the 5.6 hold (MA-043, Charter §1).
- **Q5. Beta testing statement.** differentiation §4 needs a true account of TestFlight testing, which only the founder can give.
