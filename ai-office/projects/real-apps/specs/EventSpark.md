# Spec: EventSpark — the door list for hosts who take money their own way

Author: product-manager (AI office) · Date: 2026-10-12 · Project: `real-apps` (plan.md, criteria 1–7)
Repo: `/Users/spatchava/agl/EventSpark` (app in `mobile/`) · Branch: `main` · Base SHA: `cb272a33d802b0c306f37c4fd2692bdab089c186`
Store record: App Store "iEventSpark" (rejected 4.3 / 4.2.6, `.dist/rejections.json` key `EventSpark`) · Google Play: PRODUCTION_DRAFT_STAGED

This spec is for the software-developer. The developer changes code. This document does not.

---

## 0. What I read, and what the evidence shows (baseline at cb272a3)

Commands run:
- `git -C /Users/spatchava/agl/EventSpark rev-parse HEAD` gave `cb272a33d802b0c306f37c4fd2692bdab089c186`. `git branch --show-current` gave `main`.
- `flutter analyze` (in `mobile/`) gave `No issues found! (ran in 63.9s)`.
- `flutter test` gave `00:16 +536: All tests passed!` (16 test files plus `test/screenshot_tool.dart`).
- `wc -l` over `lib/**/*.dart`: 59 files, 19,890 lines.

**I read the code. I did not run the app on a device or simulator.**

### What works today (the host half: real, on-device)
- **Create / edit an event**: `features/host/create_event_screen.dart`. It validates every field at once (`validateEventDraft`, `core/engine/event_engine.dart:1154`) and persists to SharedPreferences under `eventspark.hosted` (`core/state/app_state.dart:91`, `HostedEventsNotifier` `:340-520`).
- **Guest list**: `features/host/attendees_screen.dart`. You can add, remove and search by name, email or ticket type. The list refuses to oversell (`addAttendee`, `app_state.dart` "Refuses once the event is full").
- **Door check-in**: `features/host/check_in_screen.dart`. You type the code or tap a name. Check-in is idempotent. A second use of a code is reported with its time (`:205-216`). Undo exists. Haptics fire.
- **Door codes**: `confirmationCode()` (`event_engine.dart:776`) is an FNV hash of `eventId#sequence`, using an alphabet with no I/O/0/1.
- **Host numbers**: `features/host/host_analytics_screen.dart` and `analyseEvents` (`event_engine.dart:1225`) show booked, arrived, taken, fill rate and check-in rate.
- **Copy event details** puts plain text on the clipboard (`manage_event_screen.dart:205-212`).
- **Delete all my data** in Settings works (`resetLocalData`, `app_state.dart` end).

### What is shallow, misleading, dead or invented
1. **The first screen says the app does not do its job.** Release builds default to `EVENTSPARK_INVENTORY=sample` with sample data blocked (`core/config/app_config.dart:55-66, 121-137`). So Discover, the home tab, renders `SearchFailure.title` **"Live events coming soon"** with a rocket icon (`core/engine/search_failure.dart:44-45`, `core/widgets/error_view.dart:113-118`). The body text is **"This build is not connected to a live ticketing partner…"** (`core/engine/inventory_source.dart:59`).
2. **Three of the five tabs are hollow in release.**
   - Tickets: "Booking tickets in EventSpark is not available yet." (`features/tickets/tickets_screen.dart:78-80`).
   - Saved: "Public event listings are not available in EventSpark yet." (`features/saved/saved_screen.dart:21-23`).
   - Discover: item 1 above.
   - Nearby, Search, organiser profiles, the live room, the agenda and the tier-picker checkout all read from the same blocked catalogue.
3. **"Coming soon" is built into the code.**
   - `AppConfig.comingSoonTitle/Message/Short/Tight` (`app_config.dart:97-111`), with the message "Live prices and ticket checkout are coming soon".
   - `core/widgets/coming_soon.dart` (`ComingSoonNote`, `showComingSoon`, `SampleDataBanner` "Sample catalogue — these events and prices are examples").
   - The host's own event screen offers **"Sell tickets online — coming soon"** (`features/host/manage_event_screen.dart:166`).
   - The Hosting list footer says "Publishing them to the public catalogue arrives with the ticketing partners" (`features/host/host_screen.dart:88-89`).
   - `payments.dart:71` says "Card payment is not enabled in this build yet", and `conferencing.dart:139` says "Live video is not enabled in this build".
4. **Invented catalogue.** `core/engine/sample_catalogue.dart` (543 lines) and `sample_extras.dart` (486 lines) contain invented events, prices, ratings and attendee counts, plus invented organisers such as "Gershwin Presents … 780400 attendees, 4.9" (`sample_extras.dart:18-30`), and invented agendas, tiers and promo codes. They are blocked in release, but they ship in the binary and run in debug. The `_blocker` in `store/apps/EventSpark.json` says the default build shows sample content.
5. **Tiers exist in the engine but not in the product.** `HostedEvent` has `tiers`, `promoCodes` and `agenda` (`event_engine.dart:867-930`). The create screen has no UI for any of them (grep of `create_event_screen.dart` finds only emoji, city and date fields). `HostedEventJson.toJson` does **not serialise** tiers, promo codes or agenda (`core/state/serialisation.dart:225-247`), so they would be lost on restart anyway. A guest's "ticket type" is free text (`Attendee.ticketType`).
6. **Money is a single number with no method.** `Attendee.paidCents` defaults to the event price (`app_state.dart` `addAttendee`). Nothing records whether someone paid, owes, or was comped, or how they paid. "Taken" on the dashboard is the sum of `paidCents`, so it counts unpaid guests as revenue.
7. **The host's city must be one of 15 hard-coded US places**, including Yosemite, Napa and Key West (`knownCities`, `event_engine.dart:123-139`, picked via `features/search/city_picker.dart`). A host in Portland cannot set their city.
8. **Dead controls.** "Event reminders" and "Price alerts" toggles (`features/settings/settings_screen.dart:91-101`, `features/profile/profile_screen.dart:165-177`) persist a boolean that nothing reads. There is no notification plugin in `pubspec.yaml`. "Published / Draft" (`manage_event_screen.dart:146-156`) publishes to nothing: hosted events are on-device only.
9. **Door codes collide across phones.** Event ids are `hosted-0, hosted-1…` per device (`app_state.dart` `create`), and the code is a pure function of id and sequence. So the first guest of the first event on every phone gets the same code. Anyone who reads the algorithm can derive codes.
10. **Live room, networking and conferencing are single-device simulations of multi-user features.** Examples: Q&A upvotes with `kLocalVoterId = 'local-voter'` (`core/state/live_state.dart:27`); booths and leads (`core/engine/networking.dart`); a removed video SDK (`app_config.dart:158-166` "Always false").

### Template tells in this app (from the brief; the bracketed ones I checked myself)
- **Twin of TripNest.** `comm` of `lib/**/*.dart` relative paths gives 21 shared paths [ran]:
  - `core/config/app_config.dart`, `core/router/app_router.dart`, `core/state/{app_state,serialisation}.dart`, `core/telemetry/telemetry.dart`, `core/theme/{app_colors,app_theme}.dart`;
  - `core/engine/{affiliate,inventory_source,search_failure,supplier_client}.dart`;
  - `core/widgets/{coming_soon,common_widgets,error_view,skeletons}.dart`;
  - `features/{about/monetisation_screen,menu/menu_screen,profile/profile_screen,saved/saved_screen,search/search_screen,settings/settings_screen}.dart`, `main.dart`.
  `app_theme.dart:24` reads "EventSpark theme — AmericanGroupLLC Design System v2.0" [read]. The brand is `0xFFF57F17` (`app_theme.dart:32`) [read].
- **Generated glyph icon**: `agl-manifest/scripts/generate_app_icons.py:68` `"EventSpark": ("celebration", "#6A1B9A", "#EC407A")` [read].
- **Shared splash**: `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` = `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` [ran].
- **Shared shell**: a Material `NavigationBar` with `AglAdBanner` above it (`core/router/app_router.dart:237`), and an interstitial on tab change (`:248`) [read]. No Cupertino.
- **Typography**: bundled Inter (`pubspec.yaml` `fonts:`), one of 13 Inter apps [read].
- **Affiliate furniture**: `core/engine/affiliate.dart`, `features/about/monetisation_screen.dart` ("How we make money"), "Your data" heading (`settings_screen.dart:146`), and "Nothing saved yet" (`saved_screen.dart:58, 70`) [grep].
- **Store packaging**: the Play feature graphic is the default Flutter logo on grey with "Event hosting & ticketing" [viewed `fastlane/metadata/android/en-US/images/featureGraphic.png`, 1024x500]. The store name has the "i" prefix ("iEventSpark") while the home-screen name is "EventSpark" (`Info.plist` `CFBundleDisplayName`, `AndroidManifest.xml:16`) [read]. The privacy label is the shared 20-app body (`store/privacy/EventSpark.json`, md5 `44be1e09…`) [ran].
- **Reply contradiction (brief)**: the 2026-09-29 reply said the app "calls no external service", while the notes list AdMob and Firebase. Not re-checked line by line.

### Competitors (keyless iTunes Search/Lookup API, `itunes.apple.com/search` and `/lookup`, run 2026-10-12. Web search is disabled in this session. I read only the listing text. I have not verified how any of these apps behave.)

| App (seller, App Store id) | Ratings | What the listing says about money and the door |
|---|---|---|
| Eventbrite Organizer (Eventbrite, 368260521) | 32,593 | Ticket scanning, live attendance, multi-device sync, on-site card payments. "Standard credit card processing fee (2.9%) and an Eventbrite Service Fee are charged." |
| Partiful (Partiful Co., 1662982304) | 267,329 | Paid tiers with capacity and promo codes, paid by Apple Pay or card; QR check-in. For off-platform money: "Drop your Venmo or CashApp for guests to chip in." |
| Posh (Posh Group Inc., 1556928106) | 54,324 | Tiers; "Take payments at the door and cash out… with Instant Payouts" (its own rail). |
| Luma (Luma Labs, 1546150895) | 18,882 | QR check-in, cohosts. Ticket sales require connecting a bank account. |
| Guest List Organizer (Olha Ievenko, 474032896) | 526 | On-device/iCloud guest lists, door arrival marking, 11 PDF reports. No money tracking described. |
| Guest Manager Check In (Guest Manager LLC, 1460267612) | 203 | Offline door app tied to a web account; check-in/check-out, head counts. No cash tracking described. |
| Guestlist (Pixable s.r.o., 1168724694) | 414 | Synced guest lists, Excel import, scanning, offline mode. No money tracking described. |

**The gap EventSpark fills.** The ticketing platforms (Eventbrite, Partiful, Posh, Luma) handle tiers and the door, but only for money that goes through their own payment rail and fees. The guest-list apps (Guest List Organizer, Guest Manager, Guestlist) handle the door but describe no money tracking at all.

None of the seven listings describes the job of a host who takes payment their own way, in cash at the door or by Venmo, Zelle or Cash App: knowing who has paid, who still owes and how much, per tier, collecting at the door in one tap, and **balancing the cash box at the end of the night**. EventSpark already has the hard half (guest list, codes, door). It should own that job.

I do **not** claim that door check-in, tiers, capacity limits or offline use are new. The listings above already describe those.

---

## 1. Problem

People who run small in-person events often take money outside any ticketing platform. Examples: a monthly supper club, a community-hall fundraiser, a DIY gig, a dance class social, a school or church event, a run club's paid social. They want no 3%-plus fees, no attendee accounts, no bank onboarding. So they juggle a spreadsheet of names, a Venmo feed, a notes app of "owes $20" and a cash box that never quite matches.

EventSpark has the hard part (a reliable guest list and door). But it ships as a half-built event marketplace whose first screen says "Live events coming soon", with three empty tabs, an invented catalogue and a theme cloned from TripNest. That is exactly what Apple called "indistinguishable" and template-made.

## 2. User

**Primary:** an independent host running in-person events of about 15–300 people, two or more times a year, who collects money themselves: cash at the door, Venmo, Zelle, Cash App, PayPal, or a card reader they already own. They run the door from their own phone, often with patchy venue signal.

**Not the user:**
- people looking for events to attend (guest discovery is removed);
- large ticketed venues;
- anyone who needs online card checkout;
- travel planning (TripNest owns travel search and booking hand-offs; nothing here touches it).

**Core job:** set up an event with its ticket tiers, build the guest list (typed, or pasted from wherever RSVPs came in), run the door (codes, names, walk-ins, collecting what is owed), and finish the night knowing exactly who came, who paid, how, and whether the cash box balances.

**Signature feature: the Door Ledger.** Every guest carries a payment record: tier, party size, Paid / Owes / Comp, method, amount. Door mode does three jobs in one tap: it checks a guest in, collects what they still owe, and sells walk-in places against each tier's remaining capacity. **Close-out** then reconciles the cash box (starting float + cash taken vs counted), gives totals per method and per tier, lists no-shows and anyone still owing, and copies the whole report or a CSV. It is all on-device: no fees, no account, no guest app, no network.

---

## 3. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app). Each item is testable.

**M1. One product: hosting. Remove the guest marketplace and the TripNest scaffold (plan criteria 1, 4, 5)**
- **Delete these routes and screens:**
  - `features/discover/*`, `features/search/*` (including `city_picker.dart`, `filter_sheet.dart`), `features/nearby/*`, `features/saved/*`;
  - `features/organiser/*`, `features/live/*`, `features/agenda/*`, `features/about/monetisation_screen.dart`;
  - the guest side of `features/tickets/*` (`tickets_screen.dart`, the checkout behaviour of `tier_picker_screen.dart`);
  - `features/details/event_details_screen.dart` (the "Preview as a guest" view);
  - `features/menu/*` and `features/profile/*`, whose content folds into Settings (M7).
- **Delete these engine and state files:**
  - `core/engine/{sample_catalogue,sample_extras,affiliate,supplier_client,inventory_source,search_failure,payments,conferencing,networking,live_interaction,agenda}.dart`;
  - `core/services/conference_service.dart`, `core/state/{discovery_state,live_state}.dart`;
  - `core/widgets/{coming_soon,skeletons,error_view}.dart` (replace `AppErrorWidget` with a new, app-specific crash fallback widget);
  - `core/engine/organiser.dart` keeps only `initialsOf`, moved to a small util file.
- Remove the guest `Ticket` model, `TicketsNotifier` and `SavedNotifier`. On first launch after upgrade, delete their SharedPreferences keys (`eventspark.tickets`, `eventspark.saved`, `eventspark.sort`, plus the live, agenda and networking keys). The app has no store users: App Store rejected, Play draft only, TestFlight records 1 install per `store/apps/EventSpark.json` `differentiation` §4.
- **Remove from `AppConfig`:** `InventoryMode`, `apiBaseUrl`/gateway, `affiliateMarker`, `allowSampleDataInRelease`, `supplierApiKeyConfigured`, every `comingSoon*` string, `liveBookingAvailable`, `hostSellingAvailable`, the video/conference flags, and `linkHost`/`deepLink` (nothing resolves there). **No `--dart-define` may switch any user-visible feature on or off** (5.6).
- Remove pure-Dart dependencies that become unused (`dio`, `shimmer`, `go_router` only if replaced). **Do not remove or add any plugin with native iOS code** (`url_launcher` and `shared_preferences` stay). Either change would rewrite `ios/Podfile.lock`, which has someone else's uncommitted edits (§9).
- Tests whose subject code is deleted are deleted **in the same commit as that code**: `supplier_client_test.dart`, `discovery_state_test.dart`, `live_test.dart`, and the guest-side cases in the other files. The commit message lists every removed test file or case and the deleted code it covered. qa-reviewer checks that each one maps to deleted code. No test of kept behaviour may be removed.
- **Check:** after the change, the `comm` command in §0 against TripNest lists none of the engine, widget, about, saved or search paths above. `grep -r "AmericanGroupLLC Design System" lib` is empty.

**M2. Core job end to end: events with real tiers and a real guest list (plan criteria 1 and 3)**
- **Create / edit an event:**
  - Fields: title, kind, date and time, duration, venue name, free-text address, overall capacity, and **one or more tiers**.
  - Kinds replace the travel-flavoured `EventCategory` (Outdoor, Vacation, …): Supper club, Party, Meetup, Class or workshop, Show or gig, Fundraiser, Watch party or sport, Other.
  - The address is free text with no city list, no geocoding and no location permission. Delete `knownCities`.
  - Currency defaults to the device locale (`NumberFormat.simpleCurrency()`), is stored per event, and stays in whole minor units.
- **Tier editor:**
  - Each tier has a name, a price (0 = free), an optional quantity, optional sales start and end, and a "hidden" flag (for comps or crew).
  - Reuse `TicketTier` (`core/engine/ticketing.dart`) and drop its `sold` field: the sold count comes from the guest list.
  - Overall capacity and per-tier quantities are both enforced, counting **party size** (a guest +2 uses 3 places).
  - A new event starts with one tier, "General", at the price the host types.
  - Remove `PromoCode` and basket code unless the host can create and apply codes in the UI. Default: remove.
- **Persist everything**: fix `serialisation.dart` so tiers, attendee tier id, party size, payment record and the event's door/close-out state round-trip. Add a schema version field. Events saved at the base SHA load with one "General" tier built from their `priceCents`, and each guest's `paidCents` becomes `Paid · Other · amount` (or `Comp` when 0). No guest is dropped.
- **Guest list:**
  - Add or edit a guest: name, optional phone or email, tier, party size (1–10), payment (M3), and a note.
  - Remove a guest, with confirmation.
  - **Search** by name, email, phone or code.
  - **Filter chips**: tier · Paid / Owes / Comp · Arrived / Not yet.
  - Sort: name, or arrival time.
  - A summary row: guests, heads, owed total.
- **Paste a guest list:**
  - "Add from clipboard" reads `Clipboard.getData`. It accepts one name per line, or CSV/TSV with a header containing any of `name`, `email`, `phone`, `tier`, `party`, `paid`.
  - A preview marks duplicates (same name and email, or same phone), rows over capacity, and unknown tier names (mapped to the default tier, with a warning).
  - Nothing is saved until the host confirms.
- **Guest pass text:** "Copy pass" puts on the clipboard: event, date and time, venue, address, guest name, tier, party size, door code and amount owed if any. The host pastes it into their own message.
- **Door codes no longer collide:**
  - Each new event gets a 64-bit random salt from `Random.secure()`, stored with the event. Codes are derived from salt + attendee sequence with the existing alphabet.
  - Events without a salt (saved at the base SHA) keep the legacy derivation, so codes already handed out still work.
  - Codes are unique within an event; regenerate on a collision.
- Remove the "Published / Draft" toggle and the Live/Draft pills. Event status is computed: Upcoming · Today · Door open · Closed · Past.
- Remove the dead "Event reminders" and "Price alerts" toggles and their `Profile` fields.

**M3. The Door Ledger (signature feature; plan criteria 2 and 3)**
- **Payment record per guest:**
  - Status: `paid` / `owes` / `comp`. Method: one of the host's enabled methods (Cash, Venmo, Zelle, Cash App, PayPal, Card reader, Other). Amount in minor units. Timestamp.
  - The default amount is tier price × party size. A free tier defaults to `comp` with amount 0.
  - A partial payment leaves the remainder as `owes`.
  - "Taken" everywhere means the sum of `paid` amounts only. This fixes defect 6.
- **Door mode** (`/host/:id/door`, replacing `check_in_screen.dart`'s layout):
  - Full-screen. On iPhone, a dark high-contrast surface regardless of theme.
  - Big live header: **heads in / capacity**, **taken tonight** split by method, **still owed**.
  - A code field (autofocus, Kode Mono, uppercase formatter kept) and name search below it.
- **One tap at the door.** A matched guest shows tier, party size and payment status:
  - Paid or Comp: **Check in**.
  - Owes: **Collect $X & check in**, with one button per enabled method. The payment and the check-in are recorded together.
  - Already in: a red banner with their arrival time, as today.
  - Party arrivals can be partial ("2 of 3 here"). The rest can be checked in later.
- **Walk-ins:**
  - "Sell at the door" lists only the tiers that are on sale now and have places left. It takes party size and method, and the name is optional (default "Walk-in N").
  - It creates a guest who is already checked in and paid.
  - It is disabled with a reason when the event is full ("Full: 120 of 120 heads").
- **Undo** the last door action from a snackbar for 10 seconds. This covers check-in, collection and walk-in.
- **Close-out** (`/host/:id/close-out`):
  - The host enters a **starting float** (before the door opens, editable) and the **counted cash** (at close).
  - The screen shows: expected cash = float + cash collected; difference **Over / Short / Balanced**; totals per method; per tier sold, arrived and taken; walk-ins; **no-shows** (with names); **still owing** (names and amounts).
  - "Close the door" stores the close-out on the event, and door mode becomes read-only until "Reopen".
- **Export (clipboard, no new plugins):**
  - **Copy close-out report**: plain text, the screen above in prose and lines.
  - **Copy guest list as CSV**: RFC 4180 quoting; columns `name,email,phone,tier,party,status,method,amount,currency,arrived_at,code,note`.
  - Both confirm with a snackbar.
- The host dashboard (`host_analytics_screen.dart`) reads the same ledger: taken by method across events, owed, average per head, check-in rate. It shows nothing invented and no projections.

**M4. Depth: empty, error, offline states and reuse (plan criterion 3)**
- **Empty states, in this app's own words** (no "Nothing saved yet" or "Your data" furniture):
  - No events: "Your first door list starts here. Set up an event, its tiers and who's coming." with a **Set up an event** button.
  - No guests: "No one on the list yet." with **Add a guest** and **Paste a list**.
  - Door with no guests: walk-in sales still work.
  - Close-out before any money: "Nothing taken yet."
- **Run it again**: on any past event, copies title, kind, venue, address, capacity, tiers and duration into a new draft with no guests and no money.
- **Search** on the events list (title, venue), plus Upcoming / Past segments.
- **Corrupt store**: when `eventspark.hosted` fails to decode, the app does not crash (it already returns empty, `app_state.dart` `build`). It also keeps the raw string under `eventspark.hosted.corrupt-<timestamp>` and shows a one-time notice: "Your events couldn't be read. A copy was kept; contact support." No silent data loss.
- **Offline**: no feature needs the network. There is no offline banner. Only ads and crash reports go online, and both already fail silently.
- **Past events** keep their ledger and close-out, viewable and exportable.

**M5. Its own identity: palette, type, shape, home, shell (plan criterion 4)**
- **Palette, "Marquee"** (replace every value in `app_colors.dart` and `app_theme.dart`; brand `F57F17` and the category tints go):
  - Seed and primary: **marquee plum `0xFF4A1942`**. Accent: **bulb amber `0xFFF0AE3C`** (amended 2026-10-14; was `E8A33D`).
  - Light canvas: **ticket-stub paper `0xFFFAF4EC`**. Dark canvas and door mode: **backstage `0xFF1B1418`**. Text: **ink `0xFF2A1F26`**.
  - Arrived and paid: **stamp green `0xFF246F50`** (amended 2026-10-14; was `2E7D5B`). Owes, danger and "already in": **stamp red `0xFFA8322D`**.
  - I grepped every portfolio `lib/` tree and all real-apps specs for these seven hexes: no other app or spec uses any of them. (I dropped my first amber choice, `F2B33D`, because CalcMaster uses it.)
  - Contrast I computed (WCAG formula): white on plum 13.92:1; ink on paper 14.53:1; plum on paper 12.74:1; green on paper 5.55:1 (was 4.57:1 for `2E7D5B`); red on paper 6.08:1; amber on backstage 9.33:1 (was 8.40:1 for `E8A33D`); paper on backstage 16.57:1. Add a test that asserts at least 4.5:1 for every text pair the theme uses.
- **Typography.** Bundle three SIL OFL fonts with their `OFL.txt` under `mobile/assets/fonts/`, declared in `pubspec.yaml`, with no runtime fetch:
  - **Bricolage Grotesque** for display: titles, door counts, money totals.
  - **Plus Jakarta Sans** for body and UI (amended 2026-10-14; was Figtree).
  - **Kode Mono** for door codes, the code field and CSV previews (amended 2026-10-14; was Martian Mono).
  - Remove Inter and its licence file.
  - Sources resolve (`curl -L`, HTTP 200): `github.com/google/fonts/raw/main/ofl/bricolagegrotesque/BricolageGrotesque[opsz,wdth,wght].ttf` (408,496 B, 2026-10-12), `ofl/plusjakartasans/PlusJakartaSans[wght].ttf` (176,288 B, 2026-10-14), `ofl/kodemono/KodeMono[ROND,wdth,wght].ttf` (260,444 B, 2026-10-14), and each family's `OFL.txt`. None of the three licences names a Reserved Font Name.
  - No portfolio app's `pubspec.yaml` or `lib/` uses any of the three, and no other real-apps spec proposes them. Atkinson Hyperlegible was my first body choice, but the AGrammarly spec has claimed it.
  - **Amendment, 2026-10-14 (repair round, software-developer; chief-of-staff to confirm).** QA found that the uniqueness claims above no longer held. Figtree was bundled by DriftDate (`pubspec.yaml:134`, `3b1e887`), daily-pulse (`pubspec.yaml:93`) and ChefCount (`pubspec.yaml:75`), and Martian Mono by CodeDeal (`mobile/codedeal_app/pubspec.yaml:77`). All four commits came before EventSpark's `157ee7e3`. Green `2E7D5B` is in DriftDate (`lib/theme/drift_colors.dart:84`) and also GadgetNest (`lib/core/theme/app_colors.dart:76,94`, `e1d6433`, before EventSpark). Amber `E8A33D` is in Kinnav (`lib/theme/app_theme.dart:22`, committed after EventSpark). The earlier apps keep what they shipped first. For the amber, changing EventSpark was the only way to restore uniqueness without editing another repo. So EventSpark moved to Plus Jakarta Sans, Kode Mono, green `246F50` and amber `F0AE3C`, and the icon and splash were redrawn with the new amber (`tool/draw_icon.py`). Check run on 2026-10-14: `rg -il` over every repo under `/Users/spatchava/agl` (excluding build output, `.dart_tool`, Pods, `.dist`) for `246F50`, `F0AE3C`, `plus ?jakarta|kode ?mono` found no file outside EventSpark. `A8322D` appears only in the NearServe and Verba specs, as the colour they avoided because EventSpark uses it. `test/theme_test.dart` now fails if `2E7D5B`, `E8A33D`, Figtree or Martian Mono comes back.
- **Shape language: "ticket stub".** Event and summary cards use a custom `ShapeBorder` with a half-circle notch on each side and a dashed perforation line between the event block and its numbers, with 4 px corners. This replaces the 12 px `AppCard`. Door results look like a stamp: a rotated outline label, "IN 9:42 PM" or "OWES $20".
- **Home layout: "Next door".** There is no feed and no rails. Top to bottom:
  1. A **ticket-stub hero** for the next event: countdown, heads booked / capacity, owed total, a bar per tier, and a large **Open the door** button (enabled from 3 hours before the start).
  2. Today and upcoming events.
  3. Past events, with **Run it again**.
  4. The search field.
- **Shell:**
  - Remove the 5-tab `NavigationBar` entirely. The app is one stack: Home → Event (segmented **Guests · Door · Ledger**) → details. Settings is a gear in the Home app bar.
  - On iOS use `CupertinoIcons`, Cupertino page transitions and `.adaptive` switches and dialogs. Android keeps Material icons with the same palette.
- **Ads:**
  - Remove `AglAdBanner` from the shell, and remove the tab-change interstitial (`AglAds.onTransition()`, `app_router.dart:248`).
  - Put one inline `AglAdBanner` at the end of the Home list, below Past.
  - No ads on any event screen, the door, the ledger, close-out, forms or Settings. `agl_ads` itself is not changed.
  - This is a founder decision (§8.3). If the founder declines, keep the interstitial on Home ↔ Settings only, never on door screens. Approval request: `reports/approvals/2026-10-14-eventspark-ads-placement.md`, issue #40 (filed 2026-10-14, waiting for the founder).

**M6. Icon and launch screen of its own (plan criterion 4)**
- **New app icon, not from `generate_app_icons.py`.** An amber ticket stub with a punched hole and a plum check stamp, on a plum rounded square. No Material glyph, no diagonal gradient.
  - Draw it with an EventSpark-only script committed in the repo (`mobile/tool/draw_icon.py`, Pillow, run with `python3 -I`).
  - Output every iOS `AppIcon.appiconset` size (the 1024 has no alpha) and every Android mipmap and adaptive layer.
  - Delete the `"EventSpark"` row at `agl-manifest/scripts/generate_app_icons.py:68`, so a later run cannot overwrite the new icon. Tell the chief-of-staff about it, because that script is shared.
- **Launch screen.** `LaunchScreen.storyboard` background becomes plum `4A1942` (red 0.290, green 0.098, blue 0.259) with the new stub mark centred. `LaunchImage` is regenerated from the mark. The storyboard shasum must no longer be `3f6a9b27…`. Android `launch_background.xml` and the `values-v31` splash use the same colour and mark.
- Do not touch `ios/Runner.xcodeproj/project.pbxproj` or `ios/Podfile.lock`. Replacing images inside existing asset catalogs does not need either.

**M7. Onboarding and Settings copy of its own (plan criteria 1 and 4)**
- **First launch**, two short steps, skippable, with no account and no permission prompts:
  1. "What name goes on your passes?": host name, used in copied passes and reports.
  2. "How do guests pay you?": multi-select Cash, Venmo, Zelle, Cash App, PayPal, Card reader, Other, or "My events are free". This sets the methods door mode offers.
  Then the app lands on **Set up an event**.
- **Settings sections:**
  - **Hosting**: host name, payment methods, default currency.
  - **Appearance**: System / Light / Dark.
  - **Your events, on this phone**: copy all events as CSV; delete all data, with confirmation.
  - **Privacy**: privacy policy link; the `Privacy choices` tile where UMP requires it (kept, legally needed); a plain sentence on what leaves the phone (ads, crash reports, and analytics if kept, §8.4).
  - **Help**: contact support, licences, version.
- Remove "How we make money", the "Build" row (`settings_screen.dart:183`, which shows "debug · sample catalogue"), and the Menu and Profile screens.

**M8. Honesty: banned phrases and truthful numbers (plan criterion 5)**
- No user-visible string in `lib/` contains: "coming soon", "in this build", "this build", "not available yet", "not connected", "sample", "example", "Simulator", "ticketing partner", "public catalogue".
- Every number on screen comes from the host's own entries. No seeded events, guests, organisers, ratings or promo codes, not even in debug builds or screenshots.
- No demo logins, no remote config switches, no build flags that hide screens, no reviewer, region or date detection, no hidden gestures. Every feature is reachable on one device from the first screen after onboarding.
- In-app text never claims online sales, payment processing or syncing. Where it matters, the guest-list footer says once: "EventSpark doesn't take payments. It records the ones you take."

**M9. Proven (plan criterion 6)**
- `flutter analyze` is clean and every test passes. No test of kept behaviour is deleted or skipped (deletions only under M1's rule).
- New tests, at minimum:
  - **Ledger maths**: heads in vs capacity with party sizes; taken counts only `paid`; partial payment leaves the remainder owed; close-out expected cash = float + cash collected; Over / Short / Balanced; per-method and per-tier totals; no-shows and still-owing lists.
  - **Tier capacity**: overall and per-tier limits with party size; walk-in refused when full or when the tier's sales window is closed.
  - **Door flow** (widget): an owing guest's "Collect & check in" records method, amount and arrival in one action; an already-in code shows the red banner; undo reverts all three action types.
  - **Codes**: two new events produce different codes for sequence 0; no duplicate codes within an event across 1,000 guests; a legacy event (no salt) still validates its old codes.
  - **Migration**: a base-SHA `eventspark.hosted` JSON loads with a "General" tier, guests keep their `paidCents` as paid/comp, no guest is lost; obsolete keys are deleted; a corrupt blob is preserved under the `.corrupt-` key and the notice flag is set.
  - **Persistence round-trip** for tiers, party size, payment and close-out.
  - **Paste import**: one-name-per-line; CSV with quoted commas; duplicates flagged; over-capacity rows flagged; nothing saved before confirm.
  - **CSV export quoting** (names with commas, quotes and newlines).
  - **Run it again** copies tiers but not guests or money.
  - **Banned-phrase test**: scans string literals in `lib/**/*.dart` for the M8 list.
  - **Theme test**: seed is `0xFF4A1942`; font families are Bricolage Grotesque, Plus Jakarta Sans and Kode Mono (amended 2026-10-14 with M5; Figtree and Martian Mono must not come back); `F57F17` and `FF6B35` (TripNest) do not appear in `lib/`; the contrast pairs pass.
  - **Shell test**: no `NavigationBar` in the tree; `AglAdBanner` appears only on Home.
- **Screenshots**: rewrite `integration_test/store_screenshots_test.dart` so it creates a real event in the test (tiers, a pasted list, three door actions, one walk-in, a close-out) and captures from that. The developer launches on the iOS simulator and attaches screenshots of Home, Door mode, Close-out and onboarding to the report (memory: "build it and look at it").
- Commits are path-limited (never `git add -A`; §9) and pushed to `main`.

### SHOULD (valuable; build after the MUSTs)
- **S1. Run sheet**: a simple per-event timeline the host types (doors 7:00, set 8:00, last entry 10:30), shown on the door header. This replaces the deleted catalogue `agenda.dart` with something the host creates.
- **S2. Refunds**: mark a paid guest refunded (method and amount). Close-out subtracts cash refunds from expected cash.
- **S3. Waitlist tier**: when the event is full, new guests go to a waitlist; removing a guest offers to promote the first one.
- **S4. Door counter mode** for free events: a big +/− heads counter with in/out (re-entry), for events without a list.
- **S5. System share sheet** for the pass, report and CSV via `share_plus`, once `ios/Podfile.lock` no longer has someone else's uncommitted edits.
- **S6. QR on the pass** (pure-Dart `qr` rendering) so a guest can show it. Scanning needs a camera plugin (native), so it is blocked by the same Podfile.lock rule; typed codes remain the door path.
- **S7. Localise the new strings** through `agl_i18n` keys. Translate only what is actually translated, and keep the review notes honest about partial translation.

### MUST NOT
- No guest-facing discovery, browsing, "events near you", saved events, or reservations of other people's events.
- No travel search or booking hand-offs (TripNest's job). No affiliate links, no commission code.
- No payment processing, no card entry, no claim that EventSpark moves money.
- No Supabase, accounts or sync in this round. Multi-door sync would need backend tables and migrations (Charter §2), so it is a later, founder-approved project.
- No invented events, guests, organisers, ratings or totals anywhere, including screenshots.

---

## 4. Data source
- **All data is on-device**: events, tiers, guests, payments, door actions, close-outs and settings in SharedPreferences (existing `sharedPreferencesProvider`), as versioned JSON.
- **No Supabase and no public API.** The job needs none. I checked no API because none is used.
- **Clipboard** (`flutter/services` `Clipboard`) for paste import and every export. This adds no plugin.
- **Fonts**: bundled OFL files, sources verified HTTP 200 (M5).
- What leaves the phone is unchanged from today: AdMob ad requests after UMP consent where required; Crashlytics reports; and Firebase Analytics and Performance through `AglInsights.init` (`lib/main.dart:24-28`), unless the founder drops them (§8.4). No guest names, emails, phone numbers or amounts are sent anywhere.

---

## 5. Out of scope
- Online ticket sales, payment processing, payouts.
- Camera scanning, Wallet passes, printing (each needs a native plugin and so is blocked by the `Podfile.lock` rule).
- Multi-device door sync, cohosts, accounts (needs backend migrations; Charter §2).
- Changes to `agl_ads`, `agl_i18n` or `agl_observability`.
- Editing `store/apps/EventSpark.json`, `store/privacy/*.json`, anything under `agl-manifest/docs`, or anything under `mobile/fastlane/` (another workstream, plus other people's uncommitted edits). Proposals are in §6.
- Replying to Apple or resubmitting (Charter §1).

---

## 6. Store impact (proposals for store-compliance to apply after the build. Nothing here has been applied.)

**Name.** "iEventSpark" uses the portfolio's "i" prefix; plain "EventSpark" belongs to another developer (`_name_note`). Candidates, in order: "EventSpark Door List", "EventSpark: Guest List & Door", "EventSpark Host Ledger". The founder picks (§8.1). App Store Connect is the only place to check availability. The home-screen name stays "EventSpark".

**Subtitle (30 characters or fewer):** "Guest list, tiers & cash door" (29).

**Promotional text (new):** "Run the door at your own events. Know who's paid, who owes, and whether the cash box balances, with no ticketing fees and no accounts."

**Description: rewrite.** Do not open with the app name. No ALL-CAPS headings. No "GOING / coming soon" section. Do not reuse the shared ads paragraph wording. Suggested opening: "You take the money your own way: cash at the door, Venmo, Zelle. EventSpark keeps the list straight." Then, in plain sentences:
- tiers and capacity;
- pasting a guest list;
- door mode (codes, names, collect what's owed, walk-ins);
- close-out (cash box over or short, totals per method, no-shows, CSV);
- everything on your phone, no account, works without signal;
- one honest sentence each on ads and crash reports (and analytics if kept).
Never say "sell tickets online". Keywords: drop "nearby, conference, agenda, local". Use "guest list,door,check in,cash box,host,tiers,rsvp,supper club,fundraiser,walk-in".

**Screenshots (retake all, from the real flow in the integration test; no Settings, no empty states):**
1. Home: the Next-door ticket stub with tier bars.
2. Door mode: an owing guest with "Collect $20 & check in" and method buttons.
3. Door mode: the "Already in at 9:42 PM" stamp, or a walk-in sale.
4. Guest list with filter chips (Owes selected).
5. Close-out: the cash box shown as "Short $5", plus per-method totals.
iPad: the same flows at iPad size.

**Play feature graphic:** new art from the new icon and palette (plum, amber stub, Bricolage Grotesque), replacing the Flutter logo. Do not use the shared generated layout.

**Review notes.** Write them for this app only. Do not use the "2. DEVICES…" skeleton, and do not paste the subtitle as the audience. Content:
- Who it is for: independent hosts who collect payment themselves and run their own door.
- How to test on one device with no login:
  1. complete the two onboarding steps;
  2. set up an event starting within 3 hours;
  3. add two guests (one owing);
  4. open the door;
  5. collect and check in;
  6. sell a walk-in;
  7. close out with a counted cash amount.
- Nothing is gated, remotely switched, region-dependent or time-dependent. The only time rule is that the door button enables 3 hours before an event's start, which the reviewer controls by choosing the start time.
- External services: AdMob (Home only), Crashlytics, and Firebase Analytics and Performance if kept. The app processes no payments.
- Devices tested: list **only** physical devices a human actually used. If none, say simulator only. Never repeat "a build that cannot start never ships".

**Privacy label.** The current label is the shared 20-app body. It is accurate today only because `AglInsights.init` runs (`main.dart:28`). If the founder drops analytics and performance (§8.4), the proposed label is: DEVICE_ID + ADVERTISING_DATA (third-party advertising, not linked) and CRASH_DATA (app functionality, not linked), nothing else. Play Data safety to match. Guest data stays on the device and is not "collected" in Apple's sense. The policy-page wording, if changed, is a Charter §6 decision.

**Category.** Primary BUSINESS, secondary PRODUCTIVITY. It is currently ENTERTAINMENT / LIFESTYLE. Founder decision (§8.2).

---

## 7. Files the developer will touch (expected; for review routing)
- **Rewrite**: `lib/main.dart`, `lib/core/router/app_router.dart`, `lib/core/config/app_config.dart`, `lib/core/theme/{app_theme,app_colors}.dart`, `lib/core/state/{app_state,serialisation}.dart`, `lib/core/engine/{event_engine,ticketing}.dart`, `lib/core/widgets/{common_widgets,event_cards,copy_to_clipboard}.dart`, `lib/core/design/*`, `lib/features/host/*`.
- **New**: `lib/features/{home,door,ledger,onboarding,settings}/*` and `lib/core/engine/ledger.dart`.
- **Delete**: the files listed in M1.
- **Other**: `pubspec.yaml` (fonts, removing pure-Dart deps only), `mobile/assets/fonts/*`, `test/**`, `integration_test/store_screenshots_test.dart`, `ios/Runner/Assets.xcassets/{AppIcon.appiconset,LaunchImage.imageset}`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `android/app/src/main/res/{mipmap-*,drawable*/launch_background.xml,values*/styles.xml}`, `mobile/tool/draw_icon.py`, and `agl-manifest/scripts/generate_app_icons.py` (delete one row; coordinate).

## 8. Founder decisions (not taken by the office)
1. The App Store name to replace "iEventSpark" (candidates in §6).
2. The category change to Business / Productivity.
3. Ads: dropping the tab-change interstitial and the shell banner for a single inline Home banner (Charter §3, money; may change ad revenue).
4. Whether to drop Firebase Analytics and Performance (`AglInsights.init`), leaving only ads and crash reports. This shrinks the privacy label to one of its own and matches the "nothing about your guests leaves the phone" promise. The office's recommendation is yes.
5. Confirming that the guest marketplace is removed for good, rather than kept for a future ticketing partnership. The spec assumes removal: it is what made the app read as a template and an unfinished product.
6. A human screen recording on a physical iPhone of the M-flow (set up → door → close-out), for any future Resolution Center reply. Only a human can make it.

## 9. Other people's uncommitted work in this repo (do not touch)
`git status --short` at base `cb272a3`:
- modified: `mobile/fastlane/metadata/android/en-US/full_description.txt`, `mobile/fastlane/metadata/android/en-US/images/phoneScreenshots/0{1..5}.png`, `.../tenInchScreenshots/0{1..4}.png`, `mobile/fastlane/metadata/en-US/description.txt`, `mobile/fastlane/metadata/review_information/notes.txt`, `mobile/fastlane/screenshots/en-US/ipadpro13-0{1..4}.png`, `mobile/fastlane/screenshots/en-US/iphone69-0{1..5}.png`, `mobile/ios/Podfile.lock`;
- untracked: `mobile/fastlane/metadata/android/en-US/images/tenInchScreenshots/05.png`, `mobile/fastlane/screenshots/en-US/ipadpro13-05.png`.

Never commit, revert, stash or overwrite them. Commit with explicit paths only. Because `ios/Podfile.lock` belongs to someone else, this spec forbids adding or removing any native plugin (M1, M3, S5, S6). None of the files this spec asks the developer to change is in that list.
