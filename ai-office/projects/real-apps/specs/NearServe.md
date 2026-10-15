# Spec: NearServe. Call around for a local pro, and keep track of what each one said

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/NearServe` (Flutter app in `mobile/`; the repo root also holds old React Native / server folders that are not in the shipped app)
Base: `main` @ `4cd2a0dd146c0bdcb0658c2decbf86e0b7376fac` (`git rev-parse HEAD`, `git branch --show-current`, run 2026-10-12)
Baseline (run 2026-10-12 against that base, with `--no-pub` so `pubspec.lock` was not touched):
- `flutter analyze --no-pub` → "No issues found! (ran in 9.8s)"
- `flutter test --no-pub` → "+410: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.**
- `git status --short` shows changes under `mobile/fastlane/**`: both descriptions, `keywords.txt`, `notes.txt`, every Play phone and tablet screenshot, and `tenInchScreenshots/05.png` deleted. It also shows `mobile/ios/Podfile.lock` and `mobile/ios/Runner.xcodeproj/project.pbxproj` modified.
- This spec changes none of those files.
- **Rule 1: add no native plugins.** No `share_plus`, no notifications plugin and no calendar plugin until the owner of `Podfile.lock` has committed, because CocoaPods would rewrite that file. Everything below works with plugins the app already has: `url_launcher`, `shared_preferences`, `connectivity_plus` and `Clipboard`.
- **Rule 2: `AppIcon.appiconset`, `LaunchImage.imageset`, `Base.lproj/LaunchScreen.storyboard`, `Info.plist` and `android/app/src/main/res/**` are clean today**, so they may be edited. Edit them in place. Do not add new files to the Xcode project, because that would touch `project.pbxproj`.

---

## 1. Problem

**Store state.**
- Apple rejected NearServe under **5.6** on 2026-10-08T14:19:59Z (`/Users/spatchava/agl/.dist/rejections.json` → "NearServe"): "the app contains features that appear to have been intentionally hidden during the review process."
- Google Play: PRODUCTION_DRAFT_STAGED.

**What in this code reads as "hidden" or as not doing its job (read 2026-10-12):**

1. **A build-time switch decides which product you get.**
   - `lib/core/config/app_config.dart:22-30` reads `String.fromEnvironment('NEARSERVE_API_BASE_URL')` and `NEARSERVE_API_TOKEN`.
   - `lib/core/state/app_providers.dart:53-65` picks `HttpDirectorySource` when the define is set, and `OsmDirectorySource` when it is not.
   - The HTTP path shows prices, ratings, "Verified", lead times and "Available today" (`services/http_directory_source.dart:120-178`). That code ships in every binary but can never run in the store build, because the documented host `api.nearserve.app` exists only in comments (`docs/api-hosts.json` → NearServe `comment_only: ["api.nearserve.app", …]`). That is the 5.6 pattern.
2. **The build Apple reviewed is older than today's code.** Git history: the OpenStreetMap directory arrived in `033a1f2` on 2026-10-11. The invented "Sampleton" directory and its fake reviews were removed in `dc1f805` on 2026-10-09, and the rejection is dated 2026-10-08. So the reviewed binary most likely showed either sample listings or "No directory is connected yet" (`services/service_directory_source.dart:66-67`). I did not verify which binary was reviewed.
3. **Dead sample scaffolding is still in `lib/`.**
   - `widgets/sample_notice.dart:57-59` still says "Every listing is an example in a town called Sampleton."
   - `isSample` flags run through every model (`models/service_provider.dart`, `models/booking.dart:113`, `services/booking_repository.dart:155`).
4. **Bookings that nobody receives.**
   - "Book a slot" (`features/provider/provider_detail_screen.dart`, bottom button) generates 60-minute appointment slots from a business's opening hours (`models/availability.dart:52-84`, `slotMinutes = 60` default at `models/service_provider.dart`).
   - The live screenshot `fastlane/screenshots/en-US/iphone69-02.png`, which I viewed, shows "Appointments are 60 minutes." under a real Austin salon. **OpenStreetMap never published that.** The app invented it.
   - After the slot time passes, the booking settles to "Completed" by itself (`models/booking.dart` `settled()`). The user may then "review" an appointment that may never have happened (`features/bookings/review_screen.dart`).
   - The flow does say "NearServe does not contact {provider}" (`features/booking/booking_flow_screen.dart:163-166`). Even so, a booking calendar the provider never sees is the dishonest kernel of the app.
5. **Every row says what the app lacks.**
   - `ServiceProvider.rateLabel` returns "Contact the provider for pricing" for every OSM listing (`models/service_provider.dart`, `rateLabel`; OSM `rateUsd: 0` at `services/osm_directory_source.dart` `providerFromOsmElement`).
   - `leadTimeLabel` returns "Availability not published" or "Opening hours published (not bookable)" (`widgets/provider_card.dart:51-58`).
   - Screenshot 01 is a column of those two phrases. A price estimator (`models/estimate.dart`) and price, rating and verified filters (`features/search/search_screen.dart:400-433`) exist only for data the store build never has.

**Why it reads as a template:**
- **Shared shell.** Browse / Search / Bookings / Saved / Settings on a Material `NavigationBar`, with `AglAdBanner` above it and hidden on Settings (`app/router.dart:15-21, 88-140`), plus a tab-switch interstitial (`router.dart:106`). These are the same tabs as CarDeal, and the `main.dart` shingle score is 0.77 with HomeWise (orchestrator diagnosis).
- **Skin.**
  - Inter (`core/theme/app_theme.dart:63` `GoogleFonts.interTextTheme`).
  - `fromSeed` orange `#E65100` (`app_theme.dart:12`).
  - Tailwind and zinc hexes: `F59E0B`, `DC2626`, `16A34A`, `E5E7EB`, `6B7280`, `FFF7ED`, `FDBA74`, `9A3412`, `A1A1AA`, `3F3F46`, `27272A`. I counted 17 hex-literal hits in `lib/`.
  - Corners of 12, 14 and 16 (21 `BorderRadius.circular` uses).
  - Emoji category glyphs (`models/service_category.dart:11-22`).
- **Generated icon.** `agl-manifest/scripts/generate_app_icons.py:74` `"NearServe": ("handyman", "#E65100", "#FFA726")`.
- **Shared splash.** `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` → `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (white background, centred icon; the same file as 37 apps).
- **Play feature graphic.** I viewed `mobile/fastlane/metadata/android/en-US/images/featureGraphic.png`. It shows the **default Flutter logo**, "NearServe", and the tagline "UrbanNeeds — local services consumer app".
- **Shared copy.** "Your data" heading (`features/settings/settings_screen.dart:95`). "Nothing saved yet" (`features/saved/saved_screen.dart:58`). The store description opens with the app name, uses ALL-CAPS headings (FIND / PLAN / AFTER / SAVED / ADS), and ends with the house ads paragraph. The review notes start at "2. DEVICES AND OS VERSIONS TESTED", claim simulator testing, and give the audience as "Local services directory", which is the subtitle pasted in (`store/apps/NearServe.json`).
- **Portfolio overlap.** `overlap.md` G11: NearServe owns service providers. Its `health` category (doctors, dentists, clinics, physiotherapists, `osm_directory_source.dart` `osmTagsByCategory`) touches MyHealth's doctor finder (MyHealth spec line 23, NPPES). Its `fitness` category (gyms) belongs to no service job.

**What is real and worth keeping:**
- `OsmDirectorySource`: one category per request, a 15-minute cache, the Overpass "remark" busy detection, and `fetchByIds` for saved listings.
- `AreaGeocoder`: Nominatim, one request per submitted search.
- The `providerFromOsmElement` mapping (name, address, phone, website, hours).
- `parseOsmOpeningHours`.
- `milesBetween`, `websiteUri`, the ledger-failure handling pattern, and the honest "delete my data" flow.
- `PreferencesStore`, the theme mode, and the UMP "Privacy choices" row.
- `osm_directory_source_test.dart` and `opening_hours_test.dart`.

## 2. User, core job and signature

**User.** A renter or homeowner with something specific that needs doing: a leaking tap, a dead socket, a lock-out, a cracked phone screen, trousers to take up, a car that needs a service, a maths tutor for a child. They do not want an auction where their phone number goes to a dozen businesses. They want to **call two to five local businesses themselves, remember what each one said, and pick one**. Today they do this with Maps and a scrap of paper.

**Core job: "Get it sorted": job → call list → calls → quotes → hire → done.**
1. **Start a job.** "What needs doing?" The user types "leaking kitchen tap" or picks a trade. `categoriesForQuery` already maps free text onto categories.
2. **Get a call list.** Real businesses in that trade around the user's area, from OpenStreetMap. The list is ordered so the ones that can answer the phone right now come first (§M4). Each row shows only facts: distance, open state, whether a phone number is published, and how recently the listing was edited on OpenStreetMap.
3. **Call.** Tap the number and the phone dials. When the user comes back to NearServe, it asks "How did the call to *X* go?" The choices are No answer, Left a message, Call back (with a time), Gave a quote (amount, basis, earliest start), Can't do it, or Booked a visit (the date and time the user agreed). If the phone can't place calls (iPad), or the user called from another phone, "Log a call" records the same thing.
4. **Compare and hire.** The quote board lines up what each business said. The user marks one **Hired** and enters the date they agreed.
5. **Done.** After that date the job asks "Was it done?" The user can record the price paid and a private "Would use again?" note. The next time that business appears in any list, NearServe shows "You hired them in Mar 2026 · would use again".

The user can also **add someone who isn't listed**: name, phone and trade, for the plumber a neighbour recommended. This matters because OpenStreetMap coverage of home trades is thin in the US (§3).

**Signature feature: the call-around board.** A job-centred call sheet and quote board. Three parts work together:
- **(a) Call-now ordering.** Candidates are sorted by whether they are open now according to their published hours, with a time-zone guard. Then come listings with no published hours, then closed ones labelled "Opens Tue 8:00".
- **(b) The return-from-call logger.** It turns each phone call into a structured record: outcome, quote, basis, earliest date, and note.
- **(c) Like-for-like comparison.** Fixed prices are compared with fixed prices, hourly rates with hourly rates, and "needs a visit to quote" is never ranked against a number. The board also shows per-listing **freshness** ("Last edited on OpenStreetMap: Jun 2019 — call to check they're still trading"). When OSM has no number, it offers **"Find their number in Maps"**, which opens Apple Maps / Google Maps search for that name at that location.

Everything the board shows is either OpenStreetMap data or something the user typed after a real call. NearServe contacts no one.

**Competitor check.** WebSearch is disabled in this session ("Internet mode is not enabled"). I used Apple's keyless iTunes Search/Lookup API on 2026-10-12, read the store descriptions only, and ran none of these apps.
- **Thumbtack: Home Service Pros** (id852703300, 474,234 ratings, Lifestyle): "Spending hours researching businesses and calling around for estimates? Thumbtack does that hard work for you… See cost estimates… compare prices… book the pro". Its pros are platform members.
- **Angi: Find Local Home Services** (id432633172, 116,305 ratings, Lifestyle): "we match you to local professionals". The pro-side app **Angi for Pros** (id437003175) says "formerly Angi Leads… Target the leads you want… your preferred tasks, locations, and budget". So the matched pros are paying lead buyers.
- **Taskrabbit** (id374165361, 45,683 ratings, Lifestyle): "Tell us what you need… Get instant…" taskers on its platform.
- **Yelp** (id284910350) and **Nextdoor** (id640360962): reviews and neighbour recommendations, no call log or quote comparison in their descriptions.
- Quote-tracking apps exist, but **for contractors**, not customers: **QuoteIQ** (id1635217093, "CRM built by contractors"), **Joist** (id592163563), **QuotePulse** (id6759159987, "quote tracker built for contractors").

**Claimed gap, stated narrowly:**
- (1) A **customer-side** call log and quote board that works with **any** business: OSM-listed, found elsewhere, or recommended by a neighbour. The platforms compare only their own members' quotes, and the tracking apps are for the contractor.
- (2) **No lead hand-off.** NearServe sends the user's details to nobody. The user calls the business directly.
- (3) Open-now call ordering, plus a listing-freshness warning drawn from OSM edit history. None of the descriptions above mention freshness.

Competitor behaviour beyond these descriptions is **not verified**. Thumbtack's "calling around… does that hard work for you" shows the category is crowded, so the screenshots must lead with the board, not the directory (§5).

## 3. Data sources (real, keyless; checked 2026-10-12)

| Data | Endpoint | Proof (curl, 2026-10-12) |
|---|---|---|
| Listings by trade, with edit date | `POST https://overpass-api.de/api/interpreter`, query `[out:json][timeout:25][bbox:…];(nw["craft"="plumber"]["name"];…);out center tags meta N;` (adds `meta` to today's `out center tags`) | Austin bbox, plumbers: **HTTP 200, 2,164 B, 6.2 s, 3 elements**, each with `timestamp` (2025-09, 2026-02, 2026-08) and tags `phone`, `website`, `opening_hours` (`Mo-Fr 07:30-17:00`, `Mo-Sa 07:00-18:00`, `24/7`). London bbox, 4 trades: **HTTP 200, 150,294 B, 24.6 s, 300 elements**. The same endpoint also returned **HTTP 504** three times today (9.5 s, 12.1 s and one Columbus OH count query), so "busy" is a normal state, not an edge case. |
| Fallback Overpass instance | **Replace** `https://overpass.private.coffee/api/interpreter` (configured at `osm_directory_source.dart` `overpassEndpoints`) with `https://maps.mail.ru/osm/tools/overpass/api/interpreter` | private.coffee: **HTTP 000** (no answer) at 60.7 s and 40.0 s, so today's fallback is dead. `overpass.kumi.systems`: HTTP 000 at 40 s. maps.mail.ru: **HTTP 200, 16.7 s**, `"generator": "Overpass API 0.7.62.4"`, same `timestamp_osm_base` as the main instance. |
| Area search | `GET https://nominatim.openstreetmap.org/search?q=&format=jsonv2&limit=5` (unchanged) | `q=Austin, TX` → HTTP 200, relation 113314, lat 30.2649 lon -97.7474 |
| "Find their number in Maps" (a link, not an API) | iOS: `https://maps.apple.com/?q=<name>&sll=<lat>,<lon>`; Android: `https://www.google.com/maps/search/?api=1&query=<name> <lat>,<lon>` | Apple: HTTP 301 (redirect, which is expected for a universal link that opens Maps). Google: HTTP 200 |
| "Fix this listing" (a link) | `https://www.openstreetmap.org/edit?node=<id>` (or `way=`) opened in the browser. The user edits on OSM; the app posts nothing. | not curl-checked (it is a page link) |
| Jobs, candidates, calls, quotes, verdicts, starred businesses, cached call lists | on-device (`shared_preferences` JSON through the existing store pattern) | — |

**Coverage measured today** (Overpass `out count`, named features, 10-mile box around the city centre):

| Tag | Austin TX | London UK | Berlin DE |
|---|---|---|---|
| craft=plumber | 3 | 51 | 85 |
| craft=electrician | 5 | 20 | 65 |
| craft=hvac | 14 | 3 | 54 |
| shop=locksmith / craft=locksmith / craft=key_cutter | 1 / 1 / 0 | 92 / 20 / 47 | 93 / 16 / 30 |
| craft=roofer / painter / carpenter / gardener | 10 / 3 / 3 / 4 | 12 / 5 / 21 / 8 | 36 / 48 / 32 / 26 |
| craft=glaziery / craft=cleaning | 1 / 3 | 51 / 11 | 56 / 40 |
| shop=car_repair | 110 | 662 | 531 |
| craft=electronics_repair | 11 | 103 | 61 |
| shop=shoe_repair / craft=shoemaker | 2 / 1 | 57 / 35 | 14 / 52 |
| craft=tailor / shop=tailor | 4 / 3 | 23 / 160 | 91 / 231 |
| service:bicycle:repair=yes | 11 | 133 | 205 |
| shop=dry_cleaning | 18 | 889 | 127 |
| amenity=prep_school / music_school | 8 / 5 | 63 / 30 | 49 / 130 |
| amenity=veterinary / shop=pet_grooming | 42 / 6 | 221 / 98 | 188 / 47 |
| office=lawyer / office=moving_company / craft=caterer | 41 / 3 / 7 | 514 / 6 / 72 | 324 / 58 / 79 |
| craft=handyman / craft=pest_control / craft=tiler | 0 / 0 / 0 | 0 / 0 / 4 | 0 / 2 / 7 |

Columbus OH timed out (504) and is not in the table.

**What this means for the product, and why the user-added candidate is a MUST:**
- In a US city, home trades on OSM number in single digits. Car repair, vets, dry cleaners, bike repair and electronics repair are better covered.
- Fields in the London sample of 300 (plumber, locksmith, electronics repair, shoe repair):
  - phone: 88 (29%), and 212 have no `phone`, `contact:phone`, `mobile` or `contact:mobile`;
  - website: 82; `opening_hours`: 63 (21%); `check_date`: 93;
  - no multi-range days (lunch breaks) among the 63 hours strings;
  - **97 (32%) were last edited before 2023-10-12.**
- So "Find their number in Maps", the freshness line and "Add someone not listed" are not decoration. They are how the job still works where OSM is thin. The app must say plainly how many it found ("3 plumbers listed within 10 mi on OpenStreetMap") and never pad the list.
- Do not add `craft=handyman`, `craft=pest_control` or `shop=appliance` (an appliance *shop*, not a repairer). They returned 0–2 listings, or are the wrong kind of business.

**Rules the developer must keep:**
- One category per Overpass request. The existing comment measured 30–40 s for all categories at once.
- Identify with the existing User-Agent. Geocode only on submit.
- Treat a 200 response with an error `remark`, an HTML body, a 429 or a 5xx as "busy": try the fallback once, then show the busy state with Retry.
- `meta` adds `timestamp`, `version`, `user` and `uid`. **Store and show only `timestamp`** (and `check_date` if tagged). Drop `user` and `uid`, because there is no reason to put mappers' names on screen.
- **Open-now time-zone guard.** "Open now" uses the phone's clock. Show an open or closed state only when `|round(area.longitude / 15) − DateTime.now().timeZoneOffset.inHours| ≤ 1`. Otherwise show the weekly hours with no "now" state and the caption "Hours are local to {area}". This is a deliberate approximation. Test it with Austin from a London clock and London from a London clock.

No API keys, no paid feed, no Supabase, no sign-in, no backend.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. One build, nothing hidden, nothing invented (5.6).**

*Delete:*
- `core/config/app_config.dart` defines `apiBaseUrl`, `apiToken` and `hasLiveDirectory`, and the `bookingHorizonDays` constant. Keep `searchDebounce`, or move it.
- `services/http_directory_source.dart` and `NoDirectorySource`, `noDirectoryMessage` and `label` in `service_directory_source.dart`. The `ServiceDirectorySource` interface may stay with one implementation, or go.
- `widgets/sample_notice.dart`, and every `isSample` field and branch.
- `models/estimate.dart`.
- `models/availability.dart`, the slot generator.
- `LeadTime`, `RateType`, `rating`, `reviewCount`, `rateUsd`, `calloutFeeUsd`, `verified`, `available`, `yearsInBusiness` and `slotMinutes` from `ServiceProvider`.
- `models/booking.dart` and `models/user_review.dart`.
- `services/booking_repository.dart` and `services/booking_store.dart`. They are replaced by the job store in M3.
- `features/booking/`, `features/bookings/`, `features/saved/` (folded into M5's "Your pros"), and the rating, price, verified and "Available today" filters and sorts in `models/search.dart` and `features/search/`.
- `dio` stays (the Overpass client uses it).

*Acceptance:*
- (a) `grep -rn "fromEnvironment" mobile/lib` → exactly 1 hit, `main.dart`'s `AglAdIds.fromEnvironment(...)`. That is the shared ads package's API; note it in the commit.
- (b) `grep -rniE "sampleton|sample|isSample|this build|not connected|no directory|coming soon|contact the provider for pricing|availability not published|not bookable|book a slot|appointments are|NEARSERVE_API|api\.nearserve" mobile/lib` → 0 hits.
- (c) Release iOS build: `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "sampleton|NEARSERVE_API|api.nearserve|contact the provider for pricing|book a slot"` → 0. This checks the binary Apple inspects, not just the source.
- (d) On a fresh install, every feature is reachable from the first screen, in every region and locale, with no account.

**M2. A service directory scoped to NearServe's job (overlap G11).**
- **Rewrite `ServiceCategory` into three groups, with plain-word labels and no emoji.** Each gets a drawn icon (M6). OSM tags per category:
  - **Home repairs**
    - Plumber: `craft=plumber`
    - Electrician: `craft=electrician`
    - Heating & cooling: `craft=hvac`
    - Locksmith & keys: `shop=locksmith`, `craft=locksmith`, `craft=key_cutter`
    - Roofer: `craft=roofer`
    - Painter & decorator: `craft=painter`
    - Carpenter: `craft=carpenter`
    - Glazier: `craft=glaziery`
    - Gardener: `craft=gardener`
    - Cleaner: `craft=cleaning`
  - **Fix it**
    - Phone & electronics repair: `craft=electronics_repair`
    - Shoe repair: `shop=shoe_repair`, `craft=shoemaker`
    - Tailor & alterations: `craft=tailor`, `shop=tailor`
    - Bike repair: `service:bicycle:repair=yes`
    - Car repair: `shop=car_repair`
    - Dry cleaning & laundry: `shop=dry_cleaning`, `shop=laundry`
  - **Lessons, pets & more**
    - Tutoring & lessons: `amenity=prep_school`, `language_school`, `music_school`, `driving_school`
    - Pet care: `amenity=veterinary`, `shop=pet_grooming`, `amenity=animal_boarding`
    - Lawyer & notary: `office=lawyer`, `office=notary`
    - Movers: `office=moving_company`
    - Caterer: `craft=caterer`
    - Hair & beauty: `shop=hairdresser`, `shop=beauty`
- **Removed:** `health` (doctors, dentists, clinics, physiotherapists belong to MyHealth), `fitness` (gyms), and `shop=massage`.
- **Not touched:** fuel, parking or EV charging (iMaps), material or DIY shops (RoomCraft), and supermarkets (GroceryMatch). Acceptance: `grep -rnE "doctors|dentist|clinic|physiotherapist|fitness_centre|massage|fuel|parking|charging_station|supermarket|doityourself|hardware" mobile/lib` → 0.
- **Overpass client:** switch to `out center tags meta`, and keep only `timestamp` and `check_date` (`ListingFreshness`). Replace the fallback endpoint as §3 says. Keep the busy/remark handling and one category per request.
- **Listing row** (directory and call list):
  - name and trade label;
  - distance;
  - open state: "Open now · closes 17:30", "Closed · opens Tue 08:00", "Hours on file" when the time-zone guard fails, or nothing when no hours are published;
  - a phone glyph only when a number exists;
  - a freshness chip only when the listing was last edited more than 3 years ago ("Not updated since 2019");
  - "You hired them · would use again" when the user's own history says so.
- **Never shown:** price, rating, "not published", "unavailable".
- **Count line:** "3 plumbers within 10 mi on OpenStreetMap". When the count is under 5, add "OpenStreetMap is missing many businesses here. Add one you know →", which opens "Add someone not listed".
- **Acceptance:** unit tests map real recorded Overpass elements (fixtures cut from today's Austin and London responses, with `user`/`uid` removed) to categories. They check that `meta.timestamp` becomes freshness, and that a health or gym element maps to null.

**M3. Core job: Jobs, end to end.**
- **Model** (pure Dart, `lib/jobs/`):
  - `Job{id, title, category?, areaLabel, createdAt, status: open|hired|done|dropped, candidates, hiredCandidateId?, agreedAt?, pricePaid?, currencyCode, verdict?}`.
  - `Candidate{id, source: osm(osmId)|added, snapshot{name, trade, phone?, website?, address?, lat?, lon?, hoursText?, lastEdited?}, addedAt, calls[]}`. The snapshot keeps the job readable offline and after OSM changes.
  - `CallRecord{at, outcome: noAnswer|leftMessage|callBack(at)|quoted|cantDoIt|bookedVisit(at), quote?{amount, basis: fixed|hourly|callOutPlusHourly|visitToQuote, callOutFee?}, earliestStart?, note}`.
  - `Verdict{wouldUseAgain: bool?, note}`.
- **Status rules, enforced in a repository (the pattern `booking_repository.dart` uses today):**
  - Only a candidate with at least one call can be hired.
  - `done` needs `hired`.
  - `dropped` can come from `open` or `hired`.
  - Nothing moves by itself. The app may *ask* "Was it done?" once `agreedAt` has passed, but it never sets `done` without the user tapping.
- **Store:** `shared_preferences` JSON, versioned envelope `{v: 1, jobs: [...], starred: [...], pendingCall?}`, written through one class with a failure type, as `LedgerWriteException` works today.
- **Migration of old keys:**
  - Saved provider ids become starred.
  - Each old booking becomes a `dropped` job titled with its `serviceName` and holding one candidate, with the note "Planned in an earlier version of NearServe; the business was not contacted by the app".
  - Old reviews are discarded. Old keys are deleted after a successful write.
  - Corrupt data never crashes the app; it is ignored with a one-line notice.
- **Screens:**
  - **New job sheet:** the "What needs doing?" text field suggests categories through `categoriesForQuery`; the user picks or confirms the area.
  - **Job page:** a header ticket, the call list (M4), and then candidates.
  - **Outcome sheet.**
  - **Hire sheet:** the agreed date and time, entered by the user.
  - **Close sheet:** price paid (optional) and "Would use again?" Yes / No / skip, plus a note.
  - **Add someone not listed:** name required; phone, trade and note optional.
- **Honest wording:**
  - Use "You noted", "You agreed", "Hired by you".
  - Banned in UI strings: "booked with", "confirmed", "appointment request sent", "request", "review" (as public content), "verified".
  - Acceptance: `grep -rniE "\b(confirmed|request sent|booking|bookings|review)\b" mobile/lib --include=*.dart` → 0 in user-facing strings. The commit lists any code identifiers that remain.
- **Acceptance (journey widget test, fake clock, recorded Overpass fixture):**
  - Fresh install, pick area "Austin, TX" (Nominatim fixture), New job "leaking kitchen tap", suggested category Plumber, call list shows the 3 fixture plumbers.
  - Log call 1 as no answer, call 2 as quoted 180 fixed with earliest Thursday, and call 3 as can't do it.
  - Hire candidate 2 for Thursday 10:00, advance the clock, "Was it done?", Done, paid 180, would use again.
  - Restart (new `ProviderScope`, same prefs). The job is in Done, and the plumber's listing row shows "You hired them · would use again".

**M4. Signature: the call-around board.**
- **Call-now ordering** (pure function `rankForCalling(candidates, now, area)`):
  1. open now (time-zone guard true), nearest first;
  2. no published hours, nearest first;
  3. closed, ordered by next opening, labelled "Opens Tue 08:00";
  4. no phone, at the bottom, with "Find their number in Maps".
  - A candidate already marked "Can't do it" drops below the rest, greyed. "Call back" candidates rise to the top once their call-back time has passed.
  - Unit-tested across a weekday, a Sunday, `24/7`, `PH off`, and the guard failing.
- **Return-from-call logger:**
  - Before launching `tel:`, write `pendingCall{jobId, candidateId, startedAt}`.
  - On `AppLifecycleState.resumed` with a `pendingCall` younger than 2 hours, open the outcome sheet. Clear `pendingCall` after the user logs or dismisses.
  - If `canLaunchUrl(tel:)` is false (iPad, or no SIM), show the number in Space Mono with **Copy** and **Log a call** instead. Never a dead button.
  - "Log a call" exists on every candidate, so a call from another phone can be recorded.
  - Widget-tested with a fake launcher and lifecycle.
- **Quote board** (job page, "Compare" segment, shown once ≥ 2 candidates have a quote):
  - Rows group by basis: **Fixed price**, **Hourly** (call-out shown separately), **Needs a visit to quote**.
  - Within a group, sort by amount and mark the lowest "Lowest you've been quoted". **No comparison across groups.** A pure function, unit-tested so that a £60/h quote is never ranked against a £180 fixed price.
  - Columns: amount, basis, earliest start, last contact ("Called 2 h ago"), your note.
  - Money is formatted with `intl` `NumberFormat.simpleCurrency(locale)`, and the job's currency is fixed at creation.
- **Freshness and fallbacks on every candidate:**
  - "Last edited on OpenStreetMap: Jun 2019" (plus "checked 2024-05" if `check_date`), with "call to check they're still trading" when older than 3 years.
  - "Find their number in Maps" when no phone.
  - "Fix this listing on OpenStreetMap" (browser link, §3).
- **Acceptance:**
  - The pure functions have unit tests.
  - A widget test shows the board with 3 quoted candidates in 2 bases and asserts the group headers and the single "Lowest" mark per group.
  - A golden-free assertion checks that no row renders a price unless the user entered one.

**M5. Depth: directory, history, search/filter, share, offline, empty and error states.**
- **Directory** (from the home app bar):
  - a search field (trade words);
  - a category grid in the three M2 groups;
  - results with filters **Open now**, **Has phone** and **Updated in the last 3 years**, and sort **Open first / Nearest**;
  - **"Your pros"**: starred businesses and businesses you hired, at the top.
- **Listing page:**
  - name, trade and distance;
  - address (copyable);
  - open state and weekly hours, or the raw hours text when the parser can't represent it;
  - phone (Call / Copy), website;
  - freshness, and "Your history with them" (jobs, calls, verdict);
  - **Add to a job** (pick an open job or start one), Star;
  - OSM attribution.
- **Job history:** a Done/Dropped section on the home screen with a search field (title, business name) and a status filter.
- **Share/export without a new plugin:** **Copy job summary** to the clipboard as plain text, and **Email summary** through `mailto:?subject=&body=` with `url_launcher`. Add `mailto` to `LSApplicationQueriesSchemes`, since `Info.plist` is clean. The summary has the title, area, each candidate's name, phone, outcomes, quotes and basis, the hired business and agreed date, and "Listing data © OpenStreetMap contributors". Unit-test the text. A `share_plus` sheet is S3, after `Podfile.lock` is clean.
- **Offline:**
  - Jobs and candidates render entirely from the snapshot with no network.
  - The last call list per (area, category) is persisted with its fetch time and shown offline as "Saved list from 12 Oct, 14:05 — you're offline".
  - `connectivity_plus` drives an offline banner on the directory only.
- **Empty and error states (each written for this app; no generic "Nothing saved yet"):**
  - no area: "Where should we look? Type a town or postcode.";
  - no jobs: "Nothing on the go. What needs doing?" with the field inline;
  - zero results: "OpenStreetMap lists no {trade} within 10 mi of {area}." with **Add someone you know** and **Try a nearby town**;
  - busy: "OpenStreetMap's servers are busy. Try again in a minute." with **Retry**, after the fallback was tried;
  - offline with no saved list;
  - place search with no match;
  - a write failure, as a snackbar via the existing failure pattern.
- **Acceptance:** widget tests for each state above, and persistence across restart for jobs, stars, `pendingCall` and the cached list.

**M6. Own identity: home, onboarding, colour, type, shape, icon, splash.**
- **Home: the Jobs board, with no tab bar.**
  - Top: the area line ("Around Hackney, London · Change").
  - Then the "What needs doing?" field.
  - Then open job tickets, each showing progress: "3 called · 2 quotes · hired: —".
  - Then a collapsed "Done" section.
  - App-bar actions: **Directory** and **Settings**.
  - This replaces the shared `NavigationBar` shell (`router.dart` `MainShell`, `tabPaths`).
- **Ads:**
  - One `AglAdBanner`, in the Directory results screen, in layout flow at the end of the results column. None on the Jobs board, job page, outcome sheets, onboarding or Settings.
  - Remove the tab-switch interstitial. Any interstitial is founder question Q2.
  - Acceptance: `grep -rn "AglAdBanner" mobile/lib` → 1 hit. `grep -rn "onTransition" mobile/lib` → 0 unless Q2 says otherwise.
- **Onboarding** (shown once, re-openable from Settings):
  1. **"Where do you need help?"**: the area search. Skip is allowed and leads to "Add later".
  2. **"How NearServe works"**: three numbered lines. "Start a job. Call businesses from your list. Note what each one said, then pick one." Then the sentence "NearServe never contacts anyone for you, and has no account."
  - Final button: **"Start a job"**. No "Get started", "Welcome" or "Continue as guest".
  - Test: it is shown once, and Skip works.
- **Palette "Work-order pad".** A hand-built `ColorScheme`, not `fromSeed(orange)`. `ThemeMode.system` stays. Seed reference `#1C2B4A`.
  - **Light:**
    - desk background `#EEF0F3`, ticket paper `#FFFFFF`;
    - **duplicate-sheet pink `#FBE3DF`** (ticket stubs, quoted rows);
    - text ink `#16213A`, **primary ink navy `#1C2B4A`** (on-primary `#FFFFFF`);
    - **stamp green `#2E7D4F`** ("Open now", HIRED stamp), danger `#9E2F2A` ("Can't do it"), muted `#5C6577`, rule `#D5D9E0`.
  - **Dark:** desk `#0F1522`, ticket `#18202F`, pink sheet `#4A3034`, text `#E7EAF0`, primary `#A9BCE6` (on-primary `#0F1522`), green `#5CC28A`, danger `#E57373`, muted `#9AA3B2`.
  - Acceptance:
    - `grep -rhoiE "E65100|BF360C|FFA726|F59E0B|DC2626|16A34A|E5E7EB|6B7280|F8F9FA|1A1A2E|FFF7ED|FDBA74|9A3412|0E7490|A1A1AA|3F3F46|27272A" mobile/lib` → 0.
    - Contrast pairs (text on desk/paper/pink, on-primary on primary, green and danger on paper, both modes) are ≥ 4.5:1, asserted in a test with `computeLuminance`.
    - None of the ten palette hexes appears in any sibling spec (grep of `specs/*.md`, 2026-10-12; danger was moved off `#A8322D`, which EventSpark uses). Note: iMaps already uses amber `#F2B70F` with ink, so NearServe must not use amber or yellow.
- **Typography:**
  - **Work Sans** (variable `wght`) for all UI.
  - **Space Mono** (Regular, Bold) for phone numbers, quote amounts and dates on tickets, the carbon-copy work-order voice.
  - Use `FontFeature.tabularFigures()` on counts.
  - Bundle the TTFs under `assets/fonts/` with both `OFL.txt` files, declare them in `pubspec.yaml`, and **remove `google_fonts`** and Inter (no runtime fetch).
  - Sources resolve: `github.com/google/fonts/raw/main/ofl/worksans/WorkSans%5Bwght%5D.ttf` 200 (361,072 B), `…/worksans/OFL.txt` 200 (4,396 B), `…/spacemono/SpaceMono-Regular.ttf` 200 (99,356 B), `SpaceMono-Bold.ttf` 200 (98,232 B), `…/spacemono/OFL.txt` 200 (4,392 B).
  - A grep across `/Users/spatchava/agl` (Dart, pubspec and Markdown, excluding SDK, pub-cache and build) found **no app or spec using Work Sans or Space Mono**. Archivo was my first choice, but `portfolio-board.md:128` already claims it.
- **Shape:**
  - 4 px corners on tickets, buttons and chips (no pills).
  - Each job and candidate card is a **ticket**: a header strip, then a perforated tear line (a dashed rule with two half-circle notches, drawn with `CustomPainter`), then the body.
  - HIRED and DONE appear as a rubber-stamp label: outlined, uppercase Work Sans 700, rotated −4°, in stamp green.
  - Category icons are simple line drawings in `CustomPainter` (a wrench, plug, flame/snowflake, key, roof, roller, saw, pane, leaf, spray, phone, shoe, needle, bike, car, hanger, book, paw, scales, box, whisk, comb). No emoji, and no Material glyph as the brand mark.
  - Acceptance: `grep -rn "circular(1[0-9])\|circular(20)" mobile/lib` → 0, and `grep -rn "emoji" mobile/lib` → 0.
- **Icon:**
  - Hand-built art: an ink-navy `#1C2B4A` square holding a pink duplicate-sheet ticket with a perforated edge, and a green tick stamped across it. Flat, no gradient. It **must not come from `generate_app_icons.py`**.
  - Ask store-compliance to delete line 74 (`"NearServe": ("handyman", …)`) so a rerun cannot overwrite it. That file is in `agl-manifest`, not this repo.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- **Splash:**
  - A new `LaunchScreen.storyboard` with background `#1C2B4A` and the ticket mark. Android `launch_background.xml` uses the same colour.
  - Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, and `grep -c 'red="1" green="1" blue="1"'` on it → 0.
- **iOS feel:** on iOS use `CupertinoIcons` for app-bar, call and share actions and Cupertino page transitions. Material stays on Android.
- **Names:** `CFBundleDisplayName` is already "NearServe". Set the pubspec description to "Call around for a local pro" (it is "Local services, instantly" today). The About subtitle "Discover, book and review local services" (`settings_screen.dart:144`) goes. Version is read from the build, not the hard-coded `'1.0.0'` at `settings_screen.dart:145`.

**M7. Proven.**
- `flutter analyze` is clean and `flutter test` passes.
- **New tests cover:**
  - M2 category mapping and freshness, on real fixtures;
  - the fallback endpoint order;
  - the time-zone guard;
  - `rankForCalling`, the quote grouping and "lowest";
  - job status rules and migration from the old booking and saved keys (with a recorded old-format prefs blob);
  - the return-from-call logger with a fake launcher and lifecycle, and the `canLaunchUrl == false` path;
  - the M3 journey;
  - each M5 empty and error state, offline cached lists, and the summary text;
  - onboarding shown once;
  - identity: fonts declared and on disk, no `google_fonts`, palette contrast, storyboard shasum, one `AglAdBanner`, no `NavigationBar` (`find.byType(NavigationBar)` → nothing);
  - an extended `test/release_sanity_test.dart` that greps `lib/` for the M1(b) and M3 banned strings.
- **Tests that go, only together with the code they test, each listed by name in the commit:**
  - `test/models/availability_test.dart`
  - `test/models/booking_test.dart`
  - `test/models/estimate_test.dart`
  - `test/models/review_rule_test.dart`
  - `test/services/booking_repository_test.dart`
  - `test/services/http_directory_source_test.dart`
  - `test/widgets/booking_flow_test.dart`
  - `test/widgets/bookings_screen_test.dart`
  - `test/widgets/review_screen_test.dart`
  - `test/widgets/saved_screen_test.dart`
- **Tests that are rewritten, not dropped:** `browse_screen_test`, `search_screen_test`, `provider_detail_test`, `journey_test`, `write_failure_test`, `settings_screen_test`, `layout_test`, `foldable_layout_test`, `i18n_test`, `area_flow_test`, the rating/price parts of `test/models/search_test.dart`, and `osm_directory_source_test`. No test is skipped.
- **Look at it.**
  - Launch on the iOS simulator.
  - Pick a real area live. Use one where OSM has data; London or Berlin is honest, and so is Austin with its 3 plumbers.
  - Start a job, log calls with "Log a call", hire, close.
  - Look at screenshots of the Jobs board, the call list, the outcome sheet, the quote board, a listing page with freshness, onboarding card 2, and dark mode. No white screen, no overflow at 320 pt or with 1.6× text.
- Commit path-limited (never `fastlane/`, `Podfile.lock` or `project.pbxproj` while they carry others' edits) and push to `main`.

### SHOULD (if time allows, in this order)
- **S1. Fuller opening-hours parser.** Multiple ranges per day ("Mo-Fr 08:00-12:00,13:00-17:00"), `Sa-Su`, and overnight ranges. `DayHours` becomes a list of ranges. Today's London sample had 0 multi-range strings, so this is lower priority.
- **S2. Call-back nudges without a plugin.** On app open, a "Due to call back" strip at the top of the Jobs board for any `callBack(at)` that has passed. No push and no background work.
- **S3. Share sheet and calendar.** Once `Podfile.lock` carries no one else's edits: `share_plus` for the job summary, and an `.ics` "Add to calendar" for the agreed visit.
- **S4. Translations.** New strings in the 12 shipped locales through the app's own delegate. Until then the review notes must say new screens are English-first.
- **S5. iPad two-pane:** the job list on the left, the job page on the right.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/`, `fastlane/` or `docs/` by design; see §7 for one accidental docs write)

- **Name.** Keep "NearServe". Founder decision Q5 if a rename is wanted; availability not checked.
- **Category.** Keep `LIFESTYLE`. Thumbtack, Angi and Taskrabbit all list under Lifestyle (iTunes API `primaryGenreName`). Secondary: `UTILITIES`.
- **Subtitle (≤30):** `Call around for local pros` (26)
- **Play short description (≤80):** `Find local tradespeople and repairers, call around, and compare what they quote.` (80)
- **Promotional text (≤170):** `Something broken? Find nearby plumbers, electricians and repairers, call them from one list, note what each one quoted, and pick who to hire. No account.` (153)

**Description** (draft). It does not open with the app name, drops the ALL-CAPS skeleton, and rewords the ads paragraph:
> Got a leak, a lock-out or a phone with a cracked screen? Start a job, and NearServe lists the local businesses that do that kind of work around the town or postcode you choose — plumbers, electricians, locksmiths, heating engineers, roofers, glaziers, phone and shoe repairers, tailors, bike and car repairers, tutors, vets and more — with the ones that are open right now at the top.
>
> Call straight from the list. When you hang up, NearServe asks how it went: no answer, call back, a quote and when they can start, or a visit you agreed. Your quotes line up side by side — fixed prices with fixed prices, hourly rates with hourly rates — so you can pick one, mark them hired, and keep a record of what you paid and whether you'd use them again.
>
> Listings come from OpenStreetMap, the map anyone can edit. NearServe shows when each listing was last updated, points you to Maps when a business has no phone number on file, and lets you add someone a neighbour recommended. Coverage varies by town; the app tells you how many it found and never pads the list.
>
> NearServe never contacts a business for you and hands your details to no one. There's no account; your jobs, call notes and quotes stay on your phone, and you can copy or email a job summary.
>
> Free, with one ad at the bottom of directory results from Google AdMob. Where the law requires it you choose about ad personalisation first, and can change it later in Settings.
>
> Listing data © OpenStreetMap contributors.

**Keywords (≤100):** `plumber,electrician,locksmith,repair,tradesperson,quotes,compare quotes,call list,home repair,tailor` (100)

**Screenshots to retake** (iPhone 6.9", iPad 13", Play phone and tablet), all from the real app with live OSM data:
1. **Quote board.** Two groups with real quotes. Founder question Q3: the quotes must come from a real call-around for a real job. Our script must **not** type invented prices next to real business names. Without real quotes, frame 1 is the call list instead, and the board appears without amounts.
2. Call list for a trade, with "Open now" first and a freshness chip visible.
3. The after-call outcome sheet.
4. A listing page with hours, "Last edited on OpenStreetMap" and "Find their number in Maps".
5. The Jobs board with one hired ticket and its stamp.

No Settings frame, and no frame containing "not published", "pricing" or "unavailable". The current fastlane screenshots carry someone else's uncommitted edits, so coordinate with their owner.

**Play feature graphic.** Rebuild it from the new ticket mark and a Work Sans wordmark on `#1C2B4A`, tagline "Call around for local pros". Remove the Flutter logo and "UrbanNeeds — local services consumer app".

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton, the simulator paragraph and "a build that cannot start never ships"):
- "This version has no hidden or switchable features. Earlier builds contained a second listings source that only appeared with a build-time server address, and a sample directory; both have been deleted, along with the in-app appointment calendar. Every feature is reachable from the first screen, without an account, identically in every region."
- Path: "Launch → type any town or postcode (e.g. 'Hackney, London' or 'Austin, TX') → 'What needs doing?' type 'locksmith' → the call list loads from OpenStreetMap → on any listing tap 'Log a call' (no need to phone a real business) → choose 'Gave a quote', enter an amount → do the same on a second listing → open 'Compare' → 'Hire' one → back on the Jobs board the ticket shows HIRED."
- External services:
  - OpenStreetMap Overpass API (overpass-api.de, fallback maps.mail.ru) for listings;
  - Nominatim for the place search;
  - Google AdMob (one banner in directory results, UMP consent);
  - Firebase Crashlytics and Analytics through our shared observability package.
  - No sign-in, no backend of ours.
- Audience, in place of the pasted subtitle: "People who need a local tradesperson or repairer for a specific job and prefer to call a few businesses themselves and compare what they say, rather than post a request to a lead marketplace."
- Test devices: state only what was actually used. A physical-device run is a human step and is **not verified** here.
- Translation: new screens are English-first. Shared labels are translated in 12 locales (until S4).

**Privacy label.** No change proposed: Device ID and Advertising data (third-party advertising), Crash data and Performance data (app functionality), Product interaction (analytics), all "not linked". `store/privacy/NearServe.json` is derived from the SDK flags (`_derived_from`: ads, crash, analytics). It matches 19 other apps because their SDK set is identical. Making it different without a different practice would be dishonest. The typed area and its coordinates go to the OpenStreetMap Foundation's services only to answer the request. Jobs, call notes and quotes never leave the phone. store-compliance should confirm the Nominatim and Overpass handling against Apple's definition of "collect".

**differentiation (store json):**
- §1: rewrite to the new screens: Jobs board, call list, outcome logger, quote board, directory, listing.
- §3: use §2's competitor paragraph, with its "descriptions only" caveat.
- §6: "Not a feature of RoomCraft (material shops), iMaps (driving POIs), GroceryMatch (supermarkets) or MyHealth (doctors): NearServe lists service businesses only, and its job — calling around and comparing quotes — exists in none of them."
- §4 (beta testing) and §9 remain founder items.

## 6. Out of scope
- Contacting businesses from the app (SMS, email or in-app requests), lead forms, payments, or any booking a business receives.
- Ratings, reviews or prices from any source other than the user's own call notes. No public reviews; the user's verdict is private and on-device.
- Posting edits or notes to OpenStreetMap from inside the app. Only the browser link "Fix this listing on OpenStreetMap" is in scope.
- Device location. The user types the area, as today; no location permission.
- Supabase, accounts, sync across devices.
- Health, fitness, fuel/parking/EV, material or DIY shops, supermarkets.
- Store submission, Resolution Center replies, edits to `store/apps/*.json`, `fastlane/`, `docs/` (other workstreams; Charter §1).

## 7. Not verified, and one accidental write
- **Which binary Apple reviewed** (build number and whether it had Sampleton or the empty directory). I inferred it from commit dates only.
- **Competitor behaviour** beyond their App Store descriptions. WebSearch was unavailable.
- **The time-zone guard** is an approximation by longitude. It is not tested against real tz boundaries; for example, Spain sits on CET at about 0° longitude, so a guard tolerance of ±1 h is required.
- **Overpass availability.** It is measured flaky today (three 504s). The fallback `maps.mail.ru` answered once in 16.7 s. I did not measure its long-run reliability.
- The `tel:` and Maps hand-offs on a physical iPhone. I made no physical-device run.
- **Accidental write under `docs/`.** I ran `python3 scripts/verify_api_hosts.py --print` from `agl-manifest` to check NearServe's hosts. It reported `NearServe: hosts 5, dead {}, unverified {}`. I learned afterwards that the script **rewrites `docs/api-hosts.json`** (mtime 2026-10-12 15:32 after my run). `git status` shows that file modified. The diff against HEAD changes entries for other apps' hosts, for example removing `api.aviationapi.com: NODATA`, marking `api.nal.usda.gov` "unverified", and adding `www.fts.tsa.dhs.gov`. I did **not** revert it. I cannot tell whether it already carried someone else's uncommitted run, and the regenerated content reflects the current code and DNS. The `docs/` owner should decide whether to keep it or check it out.

## 8. Founder questions (Charter decisions; the office does not take them)
- **Q1. US coverage.** OSM lists 3 plumbers and 5 electricians within 10 mi of central Austin today, against 51 and 20 in London and 85 and 65 in Berlin. The spec handles this honestly ("Add someone not listed", the count line, Maps fallback). Do you still want the US as the lead market in screenshots and copy, or should the listing lead with a city where OSM coverage is strong, such as London? Territory availability is your call.
- **Q2. Interstitial ads.** With no tabs, the tab-switch interstitial (`router.dart:106`) goes. Should NearServe run banner-only (one banner in directory results), or do you want a capped interstitial somewhere, for example after closing a job? This affects revenue (Charter §3).
- **Q3. Real quotes for screenshot 1.** Will you, or someone you choose, do a real call-around for a real job so the quote board can be shown with genuine quotes? Otherwise the board is shown without amounts. We will not type invented prices next to real business names.
- **Q4. Privacy policy wording.** If the policy needs a sentence that the typed area is sent to the OpenStreetMap Foundation's Nominatim and Overpass services, and that call notes stay on the device, that is legal text (Charter §6) for your approval.
- **Q5. Name.** Keep "NearServe" (the spec assumes so), or rename to match the new job (for example "Callaround")? Availability is not checked, and the bundle id stays.
- **Q6. Review contact and test devices** (applies portfolio-wide). The review notes must name a real contact rather than "App Reviewer", and list only devices actually used. Physical-device testing is a human step.

## 9. Implementation notes (software-developer, 2026-10-13)

Written by the developer who built this spec. Store items below are **proposals** for store-compliance; nothing was written to `store/`, `fastlane/` or `docs/`.

**Deviations from the spec, with reasons**
- **Time-zone guard formula.** The spec's `|round(lon/15) − offset.inHours| ≤ 1` rejects Austin on CDT (round(−97.75/15) = −7 against −5) and Madrid on CEST (0 against +2), so Austin and Spain would never show "Open now" during summer time. Implemented instead: `−1.0 ≤ offsetHours − lon/15 ≤ 2.5` (`lib/models/open_state.dart`). It still rejects both cases the spec names (Austin from a London clock, which is 7.5 h out, and London from an Austin clock, 5 h out) and accepts Austin on CDT/CST, London, Madrid and Berlin. Unit-tested in `test/models/open_state_test.dart`. Known limit, shared with the spec's formula: a US Pacific phone viewing a Central-time area in summer passes the guard, yet the hours shown are 2 h off. Longitude alone cannot tell these apart.
- **Lowest mark.** It appears only in a group with two or more priced quotes. A single quote is not "lowest" of anything (`lib/jobs/quote_board.dart`).
- **Work Sans.** The variable TTF was cut into static 400/500/600/700 instances with fontTools, so Flutter's `FontWeight` maps to real glyph weights. Licence: `assets/fonts/WorkSans-OFL.txt`.
- **`flutter_secure_storage` and `cached_network_image`** stay in `pubspec.yaml` although unused. Removing them would change the CocoaPods set and rewrite `Podfile.lock`, which carries someone else's edits.

**Proposed store changes (in addition to §5)**
- **Screenshot 5** ("Jobs board with one hired ticket and its stamp") cannot be produced from live data without marking a real business as hired that nobody hired. `integration_test/store_screenshots_test.dart` now captures: 01 the call list, 02 the after-call sheet (opened, nothing chosen), 03 a listing page, 04 the Jobs board with the open job, 05 the directory, and 06 "How NearServe works". It never logs a call, types a quote or hires. The quote-board and HIRED-stamp frames still wait on founder question Q3.
- **Icon.** The new launcher icon is hand-drawn (ink-navy square, pink perforated ticket, green tick). Please delete `scripts/generate_app_icons.py:74` (`"NearServe": ("handyman", …)`) so a rerun cannot overwrite it.
- **Review notes.** "Hours are local to {area}" appears when the phone's clock cannot be trusted for the area, and Open now is then not shown.
