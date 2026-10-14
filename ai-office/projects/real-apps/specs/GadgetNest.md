# Spec — GadgetNest: when does each device in your household stop getting security updates?

Author: product-manager (AI office) · Date: 2026-10-12 · Project: real-apps
Repo: `/Users/spatchava/agl/GadgetNest` · base_sha `58759f69521fde6a01fcddba825f92e97818746c` · branch `main`
Apple: rejected under 4.3 / 4.2.6 (`.dist/rejections.json` key `GadgetNest`; the text is the account-wide 4.3 message, md5 f5127d27). Google Play: PRODUCTION_DRAFT_STAGED.

> **This spec is a pivot, and the pivot needs a founder decision first (founder question 1).**
> `overlap.md` G9 recommends (D5) that GadgetNest be merged into FashionFactory if a price feed is funded, and retired if not. This spec is a third option. GadgetNest drops price comparison completely and becomes a different product that works today on keyless public data. It does not touch FashionFactory's job. Nobody should build this until the founder has chosen between pivot, merge and retire.

---

## 0. What the app is today (measured at base_sha)

Baseline: `flutter analyze` reports "No issues found! (ran in 14.9s)". `flutter test` reports "+338: All tests passed!". I ran both in this session.

| Area | What exists | Verdict |
|---|---|---|
| `lib/core/config/app_config.dart:14-17` | `GADGETNEST_INVENTORY` defaults to `'sample'`, and the comment there says "Sample inventory is deterministic and invented". | The product's only data is invented. |
| `lib/core/engine/catalog.dart` (660 lines) | Nine retailers, every `affiliateProgram: null`. Invented products and prices, e.g. `Pixel 10 Pro 256GB` at `https://www.amazon.com/dp/pixel-10-pro` (:137-160). | Fake data. Release builds hide it. |
| `lib/core/state/app_state.dart:23-27` | `catalogProvider` returns `{}` when `pricesBlockedProvider` is true. In release that is always true (`app_config.dart:47-48`, `sampleDataBlocked`). | **A release build lists no products at all.** Home, Browse, Deals, Compare, My list and Saved are all empty shells. |
| Home / Browse / Deals / Compare / Product / Saved / Category / Build list | About 2,100 lines of screens, a 3D "deals carousel" (`deals_carousel_3d.dart`, `tilt_3d.dart`), and a modelled price history chart that says on screen it is "generated for demonstration, not observed" (`price_history_chart.dart:93`). | Dead in release. |
| Build list (`build_list_screen.dart`, `pricing.dart`) | A basket optimiser: one order versus a split order. The logic is real and tested (`pricing_test.dart`, 24 tests). | Needs prices, so it is dead in release. |
| On-screen "this app does not work" copy | `common.dart:181` "Live prices are unavailable"; `common.dart:188` "GadgetNest is not connected to a retailer feed in this build"; `deals_carousel_3d.dart:215` and `product_card.dart:94` "Price unavailable in this build"; `deals_screen.dart:46`; `saved_screen.dart:30`; `browse_screen.dart:88`; `compare_screen.dart:47`; `home_screen.dart:75` "Price comparison is not connected…"; Settings "Where prices come from" (`settings_screen.dart:73-86`). | Template tell, and an admission that the app has no job. |
| Shell (`core/widgets/app_shell.dart`) | Material 3 `NavigationBar` with five tabs, `AglAdBanner` directly above it (:97), and `AglAds.onTransition()` interstitial on tab change (:108). | The portfolio's shared shell. |
| Compile-time data switches | `GADGETNEST_ALLOW_SAMPLE_DATA` turns invented prices on in a release build (`app_config.dart:28-30`). `SCREENSHOT` (`storeCapture`, :52) changes behaviour during store capture. | Build-time, not remote, but they are switches that change what the app shows. Remove them. |
| Theme | Brand `#0E7C86` teal, `fontFamily: 'Inter'` (bundled, `pubspec.yaml`, `app_theme.dart:27`), radius 12/16 everywhere, Material icons. | Inter is a portfolio tell (13 apps). |
| Identity files | Icon from `scripts/generate_app_icons.py:69` (`"devices_other"`, `#1B1B3A`→`#3F51B5`). `LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (the 37-app copy). `CFBundleDisplayName` = `GadgetNest` and Android label `GadgetNest` (both correct). pubspec description "GadgetNest — the cheapest place to buy the gadget you want." | Icon and splash are tells. |
| Store copy (`store/apps/GadgetNest.json`) | "GadgetNest is being built … It is not there yet". Short description "Early access. Not yet connected to any retailer, so no products or prices show." Category SHOPPING. The `_blocker` says do not resubmit (risk of a 4.2 minimum-functionality rejection). | Listing describes an app with no function. |
| Privacy label (`store/privacy/GadgetNest.json`) | DEVICE_ID and ADVERTISING_DATA (third-party advertising) and CRASH_DATA, all not linked. | This is the 4-app label. It stays accurate under this spec (see §7). |

Uncommitted changes by other people (`git status --short` at base_sha): `fastlane/**` (descriptions, notes, screenshots) and `ios/Podfile.lock`. Do not touch, revert or commit them. `lib/`, `test/`, `integration_test/`, `ios/Runner/`, `android/app/src/`, `assets/` and `pubspec.yaml` are clean, so every file this spec needs is free to edit. Because new plugins change `ios/Podfile.lock`, which someone else has edited, the developer must **not commit `Podfile.lock`**. Let `pod install` update it locally and report it (see M8).

---

## 1. Problem

Apple sees a shopping app that says on every screen that it has nothing to show. That is minimum functionality (4.2), and it looks like a reskinned commerce template (4.3 / 4.2.6). The job it advertises, comparing prices across retailers, needs a paid or partner retailer feed, which the founder has not funded. It is also FashionFactory's job for a different category, a 4.3(a) duplicate inside our own account (`overlap.md` G9). Nothing an engineer can do in this session makes price comparison real.

## 2. User and core job

**User:** the person who looks after the family's devices: their own phone, a partner's, a hand-me-down phone for a child, a parent's old iPad, a Galaxy Tab, a Kindle. They keep being caught out by questions like "is Mum's iPad still safe to use for banking?", "is this old Pixel OK to give to Leo, and for how long?" and "which device do we need to replace first?"

**Core job (one sentence):** list every phone, tablet, watch and e-reader in the household, and see in one place **when each one stops getting security updates**, ordered by what runs out first, with a reminder before it happens.

**Owns (portfolio boundary):** device software-support lifespan for a household. A search of `overlap.md` and every app's `lib/` for warranty, recall, serial number or "end of life" found no sibling app that does this.
**Must not duplicate FashionFactory:** no prices, no retailers, no deals, no "where to buy", no price alerts, no affiliate links.
**Must not duplicate WiFiTrail or AGCleaner:** no speed test, no storage cleaning, no device diagnostics.

## 3. Competitors and the honest angle

Internet search was disabled in this session (the WebSearch hook returned "Internet mode is not enabled"). Instead I queried Apple's public App Store Search API (`itunes.apple.com/search`, US store, top 25 per query) and read the returned descriptions. This shows what the apps *say* they do. It is not a hands-on test.

- **Warranty and receipt trackers** (queries "warranty tracker", "warranty", "receipt warranty"). The category is crowded: dozens of near-identical apps, e.g. *Warranty Keeper App*, *Warranty Tracker: ShieldLog*, *Keep Receipt*, *Slipvault*, *Covered: Warranty Tracker*. Some advertise recall alerts: *CoverlyAI* (on its paid tier), *CoverKeep*, and *Manifest: Home Inventory* ("Daily checks against official recall feeds…"). **So "warranty tracker" or "recall alerts" as the main feature would itself be 4.3(b): "indistinguishable from what's already widely available".** Neither is our signature.
- **Home inventory apps** (query "home inventory"): *Under My Roof*, *Home Contents*, *Sortly*, *Boxes*, *Nest Egg*. They catalogue belongings for insurance and organising.
- **Software-support lifespan.** Across 174 distinct apps returned by nine queries ("warranty tracker", "home inventory", "warranty", "receipt warranty", "security updates phone", "end of support", "software support end", "device lifespan", "update support checker"), **no description mentions per-device security-update end dates.** The only descriptions containing "security update", "end of support" or "end of life" were two security/antivirus apps (TotalAV, True Phone Security AntiSpy), one camera viewer announcing its own end of support (LILINViewer), and an end-of-life care companion (Better End). This is evidence of absence in the top search results, not a full market audit. In store copy, say "competitor not verified" rather than "the only app that…".
- **Apple Settings / Google Settings** show the *current* OS version on *this* device. As far as I know, neither shows other household devices or an end date. Not verified on a device.

**Angle:** we do not compete on receipts or insurance inventory. We compete on **"how long is this device safe to keep using?"** across the whole household, from a public, sourced dataset, with the honest answer where the maker publishes no date.

## 4. Signature feature: the Support Clock

Data: **endoflife.date** (MIT-licensed, community-maintained, keyless). Verified this session:
- `curl https://endoflife.date/api/v1/products` → HTTP 200 in 0.18 s; `access-control-allow-origin: *`.
- `GET /api/v1/categories/device` lists 21 products, including `iphone, ipad, apple-watch, pixel, pixel-watch, samsung-mobile, samsung-galaxy-tab, samsung-galaxy-watch, oneplus, fairphone, motorola-mobility, nokia, sony-xperia, surface, kindle, chromecast, google-nexus`.
- Real fields per release, e.g. `pixel` "Pixel 10 Pro": `releaseDate 2025-08-28, eolFrom 2032-08-01, eoasFrom 2032-08-01`, labels `eol = "Security Updates"`, `eoas = "Android Updates"`. `samsung-mobile` "Galaxy M47 5G": `eolFrom 2032-07-04`. `iphone` "XS": `isEol true, eolFrom 2026-04-22, supportedIosVersions "12 - 18"`. `iphone` "11": `isEol false, eolFrom null, supportedIosVersions "13 - 27"`. `kindle` "Kindle Scribe - 2022 Release": `eolFrom 2029-12-31`.
- Licence: `raw.githubusercontent.com/endoflife-date/endoflife.date/master/LICENSE` is MIT.

What the user gets:
1. **This device in one tap.** On first run, "Check this iPhone" reads the model name on the device (`device_info_plus` 13.x `IosDeviceInfo.modelName`, e.g. "iPhone 16 Pro", which I confirmed in the package source; Android: `AndroidDeviceInfo.manufacturer` + `model`) and matches it locally against the product file. If no release matches confidently, the app does not guess. It opens the picker filtered to the maker.
2. **Any other device by picker.** Maker → model, from the live product files, searchable ("tab s7", "kindle paperwhite").
3. **A status for each device, worded exactly per the data:**
   - `eolFrom` in the future → "Security updates until Aug 2032 · 5 yr 10 mo left" (countdown in months; "Android upgrades until …" shown as a second line where `eoasFrom` exists).
   - `eolFrom` within 12 months → "Ending soon: security updates stop Mar 2027".
   - `isEol true` → "No longer gets security updates (since Apr 2026)".
   - `isEol false` and `eolFrom null` (all current iPhones, iPads, Apple Watch) → "Still supported — Apple does not announce an end date. Runs iOS 13–27." **No estimate, no prediction.**
   - Unknown kinds of gadget (headphones, consoles, cameras) can be added by hand with a name only. Their status reads "No public support data for this kind of device". They exist so the household list is complete; they never get a fabricated date.
4. **Reminders.** Local notifications (`flutter_local_notifications`, no server) 6 months and 30 days before each `eolFrom`. Permission is requested only when the user turns on reminders for the first time.
5. **When the source changes, you see it.** Product files are cached on the device with their `last_modified`. On each refresh, if a tracked device's `eolFrom`/`isEol` changed (makers do extend support), the device shows "Support date changed: was Jul 2030, now Jul 2032", and the change is listed in the device's history.
6. **Privacy by design:** the app downloads whole product files (`/api/v1/products/<maker>`) and matches on the device. It never sends the user's model, device list or names anywhere.

## 5. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. Remove the dead commerce app completely.**
- Delete: `core/engine/{catalog,pricing,affiliate,models}.dart`; `features/{browse,deals,compare,product,saved,build_list}/`; `core/widgets/{deals_carousel_3d,tilt_3d,product_card}.dart`; the price/stock/condition widgets in `common.dart` (`PricesUnavailable`, `SampleDataBanner`, buy buttons, condition chips); price/condition tokens in `app_colors.dart`.
- `app_config.dart`: remove `inventory`, `supplierConfigured`, `allowSampleData`, `affiliateMarker`, `storeCapture` / `SCREENSHOT`, `pricesUnavailable`, `sampleDataBlocked`, `demoingSampleData` and `buildDescription`. **No `--dart-define` may change what the app shows.**
- Remove every on-screen string listed in §0 ("in this build", "not connected", "Live prices are unavailable", "Where prices come from", "Retailer links", "Read the full disclosure", modelled-history copy).
- Tests that cover removed code (`pricing_test.dart`, `affiliate_test.dart`, `production_test.dart`, `tilt_3d_test.dart`, and the price-related cases in `widget_test.dart` and `semantics_test.dart`) are **replaced** by tests of the new behaviour (M8). The commit message lists each removed test file and what replaces it. Removing tests for deleted code is allowed. Removing tests for code that stays is not.

**M2. The Support Clock (§4), end to end on a fresh install, with real data.**
- New data layer `lib/data/eol_client.dart`: `GET https://endoflife.date/api/v1/products/<name>` for the maker files the household uses, plus `/api/v1/categories/device` for the picker's maker list. 15 s timeout. Parses the v1 schema (`result.releases[]`: `name, label, releaseDate, isEol, eolFrom, isEoas, eoasFrom, isDiscontinued, isMaintained, custom`) and `result.labels` (wording of "Security Updates" versus "Supported" versus "End of Servicing Date" comes from the source, per maker).
- Status rules exactly as in §4.3. **No date is ever shown that is not in the source.** `eolFrom == null` never becomes a guess.
- On-device matcher for "Check this device": normalise and match `modelName` (strip "iPhone "/"iPad " prefix, case and punctuation) against `label`. Exactly one hit → add it. Zero or several → open the picker pre-filtered. Never auto-pick from several.
- Each device row and detail page shows "Source: endoflife.date" with the product's `links.releasePolicy` (the maker's policy page) as a tappable link, and "data updated <last_modified>".

**M3. Household list with depth (the home screen).**
- Persistence: devices stored on the device (JSON in `shared_preferences` or a file in Application Support): `{id, product, releaseName, nickname, person, addedAt, purchaseDate?, notes?, lastKnown{eolFrom,isEol}}`. They survive restart. Edit nickname, person, purchase date and notes. Delete with confirmation.
- **Person:** each device has an optional owner name ("Mum", "Leo"). Filter chips: Everyone · each person · Ending within 12 months · No longer supported.
- Search across nickname, model and person.
- Sort: "Runs out first" (default; `isEol` first, then `eolFrom` ascending, "not announced" next, manual gadgets last) or "Recently added".
- **Share/export:** "Share household report" produces plain text through the system share sheet (`share_plus`), for example:
  ```
  GadgetNest — household devices (12 Oct 2026)
  Mum   · iPad (7th gen)   · No security updates since …
  Leo   · Pixel 8a         · Security updates until …
  Me    · iPhone 16 Pro    · Supported; Apple announces no end date
  Source: endoflife.date
  ```
  The dates come from the data at export time; the example shows only the layout.
- Empty state (first run, nothing added): "Which of your devices still get security updates?" with buttons **Check this iPhone/phone** and **Add a device**.
- **Offline:** the last fetched product files are cached with their fetch time, so the list works offline and says "Offline — showing support dates from 3 Oct". With no cache and no network, adding a device shows "Can't reach endoflife.date. Check your connection and try again" with Retry. Saved devices still list with their `lastKnown` status.
- Error state: an HTTP error or JSON that will not parse shows "endoflife.date didn't answer properly" with Retry, and keeps the cache. The app never crashes.
- Refresh: pull to refresh. Automatic refresh at launch when the cache is older than 7 days. No background fetch.

**M4. Reminders and change detection (§4.4–4.5).**
- A per-device "Remind me" toggle, plus a global default in Settings. When on, notifications are scheduled at `eolFrom − 6 months` and `eolFrom − 30 days`, 09:00 local time, but only if those dates are in the future. Rescheduled on every refresh and cancelled on delete. Devices with no `eolFrom` cannot have reminders, and the toggle explains why.
- On refresh, compare with `lastKnown`. A change shows a badge on the row and a line in the device detail's history; then `lastKnown` is updated.
- iOS: notification permission is requested on the first toggle, not at launch. Android 13+: `POST_NOTIFICATIONS` runtime request at the same moment. Use only inexact scheduling (no `SCHEDULE_EXACT_ALARM`); day-level accuracy is enough.

**M5. Its own identity (distinct from all 42 siblings).**
- *Palette ("circuit board")*. Light: background bone `#F4F3EE`, ink text `#13221D`, seed and primary PCB green `#1F4D3A`, accent copper `#B8652A`, muted `#5E6B66`. Status colours: supported `#2E7D5B`, ending soon `#C27C0E`, ended `#A63A2B`. Dark (follows the system): background `#0E1A16`, text `#E8ECE6`, same accents. A `grep` of every app's `*.dart` under `/Users/spatchava/agl` and of all sibling specs found **0** uses of these ten hexes (control: the same grep finds `F59E0B` in 27 files). Remove `#0E7C86`. No Tailwind default hex anywhere in `lib/`.
- *Typography*: **Red Hat Text** for UI and **Red Hat Mono** for every date, countdown and model identifier. Bundle the variable TTFs under OFL from `github.com/google/fonts/tree/main/ofl/redhattext` and `…/ofl/redhatmono` (directory listing checked via the GitHub API; `RedHatMono[wght].ttf` download returned HTTP 200). Remove the Inter assets and `fontFamily: 'Inter'`. No runtime font download. No other app or sibling spec uses Red Hat (grep: 0 hits).
- *Shape language*: "component on a board". Cards have 6 dp corners and a 1 px copper-at-20% hairline instead of elevation. The status is a horizontal **lifespan bar** on each row: release date → today → `eolFrom`, the elapsed part filled in status colour, with a copper "today" tick. For "not announced", the bar is open-ended (dashed right end). For manual gadgets, there is no bar.
- *Home layout*: no bottom `NavigationBar`. App bar: "GadgetNest", plus share and settings icons. A top card for **"This phone"**. Below it, a **Timeline/List** segmented control (`CupertinoSlidingSegmentedControl` on iOS, `SegmentedButton` on Android). Timeline view: a vertical year ruler (current year → furthest `eolFrom`) with each device pinned at the year its updates end, plus a "No announced end" lane and an "Ended" lane at the top. List view: the filterable, searchable list from M3. A large "+ Add device" button.
- *Onboarding*: one screen, shown once (flag in `shared_preferences`), skippable. Title "Which of your devices still get security updates?". Two lines: "Add every phone, tablet, watch and e-reader at home" · "See what runs out first, and get a reminder before it does". Buttons "Check this iPhone" and "Skip".
- *Settings* (own copy, not the shared furniture): reminders default; refresh now, with the last refresh time; "Data source: endoflife.date (community-maintained, MIT). Dates are what manufacturers publish; Apple does not publish end dates." with a link; Language (shared `AglLanguageScreen` may stay; it is infrastructure); Privacy choices (keep; legally required); Privacy policy / Terms links; "Erase everything on this device" (keep: devices, cache, reminders, onboarding flag). Remove "Where prices come from" and "Retailer links".
- *App icon*: drawn by hand, **not** from `generate_app_icons.py`. A bone `#F4F3EE` square with a PCB-green rounded phone outline whose screen holds a copper three-quarter arc (a clock running down). No Material glyph and no diagonal gradient. Remove the `"GadgetNest"` entry at `scripts/generate_app_icons.py:69`, or make the script skip it, so a re-run cannot overwrite the icon. That script is in agl-manifest/scripts, not under docs/ or store/.
- *Launch screen*: background `#F4F3EE`, with the new mark centred, so `LaunchScreen.storyboard` no longer hashes to `3f6a9b27d8…`. Android `launch_background.xml` uses the same colour.
- *pubspec* `description`: "Track when each device in your household stops getting security updates."

**M6. Ads placed for the new app, with no shared shell.**
- One `AglAdBanner` at the bottom of the household List/Timeline only. Never on onboarding, the picker, device detail, or Settings.
- Remove `AppShell` and the tab-change `AglAds.onTransition()` call: there are no tabs. Whether to add an interstitial anywhere else is founder question 4. Until it is answered, add none.

**M7. Honest, and 5.6-safe.**
- Real data only: endoflife.date responses, the device's own model name, and what the user types. No sample devices, no seeded household, no invented dates, and no fixture data in a release build.
- No account, no login, no demo mode, no reviewer/region/date detection, no hidden gestures. Every feature is reachable from the home screen by a visible control within two taps.
- `lib/` reads no Firebase Remote Config value. `main.dart` already skips `AglInsights` (`main.dart:20-24`); keep it that way.
- Unit tests use a **captured real response**: a trimmed copy of `/api/v1/products/pixel`, `/iphone` and `/samsung-mobile` saved under `test/fixtures/` with the capture date in the file name. It is real data, used only by tests.

**M8. Proven.**
- `flutter analyze`: no issues. `flutter test`: all pass. The new suite must cover at least:
  1. v1 parsing of the three fixtures, including `labels` wording per maker and null `eolFrom`.
  2. Status rules with an injected clock: future, within 12 months, ended, not announced, and manual gadget. The month countdown is correct across a year boundary.
  3. The matcher: "iPhone 16 Pro" → `iphone/16-pro`; an ambiguous name → no auto-pick; an unknown name → picker.
  4. Reminder schedule: 6 months and 30 days before; nothing scheduled in the past; nothing scheduled with null `eolFrom`; cancelled on delete.
  5. Change detection: an `eolFrom` change produces a badge and a history entry, and `lastKnown` is updated.
  6. Persistence round trip; filters (person, ending soon, ended); search; "runs out first" ordering.
  7. Cache/offline: a failed fetch with a cache shows the "Offline — showing … from <date>" banner; with no cache it shows the Retry state; a malformed JSON response falls back to the cache without a crash.
  8. The export text has exactly the M3 layout.
  9. Onboarding shows once and Skip works.
  10. Tell guard: `lib/` contains none of "in this build", "not connected", "coming soon", "unavailable in", "Where prices come from", `0xFF0E7C86`, `'Inter'`, `String.fromEnvironment('GADGETNEST_`, `SCREENSHOT`, `RemoteConfig`, `Catalog`, `affiliate`. `pubspec.yaml` lists no Inter asset. `Info.plist` `CFBundleDisplayName` equals the store name.
  11. The accessibility, foldable and layout-resilience tests are rewritten against the new screens: same breakpoints, 2.0× text, 48 dp targets, contrast ≥ 4.5:1 for the status colours on both backgrounds.
- `integration_test/store_screenshots_test.dart` is rewritten to add real devices through the picker against the live API (no fixture in screenshots). `integration_test/app_test.dart` is updated.
- Commits are path-limited: never `git add -A`. Never stage `fastlane/` or `ios/Podfile.lock`; if a plugin changes `Podfile.lock`, leave it unstaged and report it. Push to `main`. Then launch on an iPhone simulator and look at it (lesson: a white screen once passed green tests). Screenshot onboarding, the Timeline, the List with a filter, and a device detail.

### SHOULD

- S1. **Recall check for chargers, power banks and accessories** (US only), against CPSC's keyless API: `https://www.saferproducts.gov/RestWebServices/Recall?format=json&ProductName=<brand>`. Verified this session: HTTP 200, but **slow (15–20 s per query)**. Its matching is a substring match (`ProductName=Anker` also returned "Trankerloop Baby Bath Seats"), so filter on the device by whole-word brand and by `Products[].Type` (e.g. "Adapter/Power Supply/Charger/Battery"). Show a result only as "Possible match — check the model number" with the official `URL`, and let the user mark it "Not mine". Competitors already advertise recall alerts (§3), so this is depth, not the signature.
- S2. Computers by OS: add a Mac or PC by its OS version (`/api/v1/products/macos`, `/windows`), shown as "macOS 14 security support until …".
- S3. Hand-down check: from a device's detail, "Give to someone" changes the owner and shows "<n> years of security updates left for <person>".
- S4. Optional warranty-end date per device with its own reminder. It stays a field, not a feature, to keep out of the crowded warranty category.
- S5. iOS-native touches: `CupertinoIcons` in the device rows, swipe-to-delete, and a home-screen widget showing what runs out next (only if done with real data).
- S6. Full translations for the 12 locales the portfolio ships (today most screen text is English only, per the current review notes).

## 6. Data source

- **endoflife.date** public API v1 (keyless, MIT, CORS `*`). Hosts: `endoflife.date`. Verified this session with curl (§4). Add it to the hosts that `scripts/verify_api_hosts.py` checks when the developer runs it.
- **On-device:** model name (`device_info_plus`), the household list, cache and reminders (`shared_preferences` / Application Support), local notifications (`flutter_local_notifications`).
- **(S1 only)** CPSC SaferProducts Recall API, `www.saferproducts.gov` (keyless, verified, slow).
- No Supabase, no account, no paid API, no key.

New dependencies (latest versions checked on pub.dev; all keyless): `http` 1.6.0, `device_info_plus` 13.3.0, `flutter_local_notifications` 22.3.2 (with `timezone` 0.11.2), `share_plus` 13.3.1. The installed SDK is Flutter 3.44.2, which meets their `flutter >=3.38.1` floor.

## 7. Store impact (proposals only; store-compliance applies them; this spec edits no store/ or fastlane file)

**Name:** keep "GadgetNest". "Nest" now means "the household's gadgets", which fits. Founder question 3.

**Category:** SHOPPING → **UTILITIES**. A pivot away from shopping changes the category; listed as founder question 2 because it goes with the pivot.

**Subtitle (≤30):** "Security-update end dates" (25 characters). It replaces "For anyone buying a gadget".

**Promotional text:** "Add the phones, tablets and watches at home and see which one stops getting security updates first."

**Description (draft).** It does not open with the app name, has no ALL-CAPS headings, and makes no "only app" claim.
> Every phone, tablet and watch stops getting security updates one day. Most people find out years late. Add the devices in your home — your phone in one tap, the rest from a list of makers and models — and see when each one's updates end, ordered by what runs out first.
>
> Each device shows a lifespan bar from its release to the last security update its maker has published, with a countdown. Where a maker announces no end date, as Apple does, the app says so instead of guessing, and shows the system versions the device runs.
>
> Assign devices to people, filter to "ending within a year", search, and share a plain-text household report. Turn on a reminder and you'll be told six months and one month before a device's updates stop. If a maker extends support, the new date shows up with what it was before.
>
> Dates come from endoflife.date, a public, community-maintained record of manufacturer support policies, with a link to each maker's own policy page. Your device list stays on this phone; the app downloads the public lists and matches on the device.
>
> The app is free and shows a Google AdMob banner on the home list. Where the law requires it you are asked for consent first, and you can change it any time in Settings › Privacy choices.

**Short description (Play, ≤80):** "See when each phone, tablet and watch at home stops getting security updates." (77 characters)

**Keywords:** `security updates,end of life,software support,android updates,ios support,old phone,family devices,tablet` (re-check the 100-character limit when applying).

**Screenshots to retake**, all from the rewritten `store_screenshots_test.dart` against the live API. Device models are chosen in the run. Every date is whatever endoflife.date returns on capture day.
1. Timeline: devices pinned by end year, with "Ended" and "No announced end" lanes.
2. List filtered to "Ending within 12 months", with person chips.
3. Device detail: lifespan bar, countdown, Android-upgrades line, source and policy link, reminder toggle.
4. "This phone" check result straight after onboarding.
5. The household report in the share sheet.

No Settings screenshots (two of today's four are Settings). Redraw the Play feature graphic with the new icon and palette; drop the Flutter logo.

**Review notes (written for this app; not the shared skeleton, not starting at "2.")**
- What it is for: tracking when each device in a household stops receiving security updates. Who: the person who looks after the family's devices: phones handed down to children, a parent's tablet.
- How to try it in 60 seconds: launch → "Check this iPhone" → the device appears with its status → "+ Add device" → Samsung → pick any Galaxy model → it shows "Security updates until <date>" → switch to Timeline → open a device → turn on "Remind me" (the notification permission is asked here) → share icon → household report.
- Data source: the public endoflife.date API (no key, no account). The device list never leaves the phone. Apple publishes no iPhone end dates, so the app shows "Apple does not announce an end date" for supported iPhones; this is deliberate, not missing data.
- No account, no login, no server of ours; every feature is visible from the home screen.
- External services: endoflife.date (public data); Google AdMob (home list only, UMP consent); Firebase Crashlytics.
- Testing: state only the devices actually used. Drop the "simulators … a build that cannot start never ships" boilerplate. A physical-device screen recording is still owed under Apple 2.1 (`docs/APPLE_REQUIREMENTS.md`, `recording_on_file`, a human task).
- Delete the "9. STATE OF THIS BUILD" section, the `_blocker`, and "Intended audience: For anyone buying a gadget".
- `differentiation` §3 (gap) can then be answered concretely from §3 of this spec. §6 (could it be an IAP in another app): no; no sibling app tracks device support.

**Privacy label:** the categories do not change. The app sends no user data to endoflife.date (it downloads whole public files; the device model is matched locally). Notifications are local. The device list stays on the device. AdMob (DEVICE_ID, ADVERTISING_DATA) and Crashlytics (CRASH_DATA) are unchanged, so the current 4-app label stays truthful. Do not make it different artificially.

**Privacy policy page contradicts the app (hand-off to store-compliance / website, added 2026-10-13).** https://www.americangroup.ai/policy/gadgetnest/privacy.html says the app shows no ads, sends no crash reports and uses only the INTERNET permission. The app ships Google AdMob (banner on the home list, UMP consent), Firebase Crashlytics, and on Android `POST_NOTIFICATIONS` and `RECEIVE_BOOT_COMPLETED` (local reminders). The page must be corrected before any resubmission. It is legal text (Charter §6), so the founder approves the wording; the software-developer has not edited it.

## 8. Out of scope

- Any price, retailer, deal, affiliate or "where to buy" feature (FashionFactory's job, and unfunded).
- Predicting end dates the maker has not published (no "estimated" iPhone dates).
- Receipt scanning, OCR, insurance inventory, warranty claims, cloud sync, accounts, Supabase.
- Device diagnostics, battery health, storage cleaning, speed tests (sibling apps' jobs).
- Background fetch or server push; reminders are local, from cached dates.
- Editing store JSON, fastlane metadata, or docs/ (other workstreams own them), uploading builds, submitting, or replying to Apple.

## 9. Founder questions

1. **Pivot, merge or retire?** `overlap.md` D5 recommends merging GadgetNest into FashionFactory if a price feed is funded, and retiring it otherwise. This spec proposes a third path: keep the listing and turn it into a household security-update tracker on keyless public data, with no overlap with FashionFactory. Retiring or merging is a Charter §8 decision. A product pivot of this size should not start without your approval either.
2. With the pivot, the App Store / Play category changes from Shopping to Utilities. Approve?
3. Keep the name "GadgetNest", or rename to say what it does? (A rename means a new App Store name check, plus home-screen and listing changes.)
4. Ads: the current app shows an interstitial on tab changes. The new app has no tabs, so this spec ships a banner on the home list only. Add an interstitial anywhere (it touches revenue, §3), or keep banner only?
5. Play: the app is PRODUCTION_DRAFT_STAGED with the old "not connected" listing. Should the staged draft be discarded until the pivoted build is ready? (Play policy action, §1.)

---

## 10. Build notes (software-developer, 2026-10-12)

Built and pushed as GadgetNest `e1d6433` on `main` (parent `8873a63`, which another session pushed after base_sha). Icon-script change: agl-manifest `18f7dff`. Founder question 1 (pivot / merge / retire, issue #25, D5) had **no answer** when this was built. The change is reversible (`git revert e1d6433`), and nothing in store/, fastlane/ or App Store Connect was touched.

Deviations from the spec, and why:
- **Dark-theme status colours.** The spec asked for "same accents" in dark mode and ≥ 4.5:1 for status colours on both backgrounds. Those two cannot both hold. Measured on #0E1A16: #2E7D5B = 3.57:1, #A63A2B = 2.77:1; on bone, #C27C0E = 3.06:1. The light-theme bar fills are the spec hexes. Status *text* uses darker (light theme: #276A4D, #8A5A06) or lighter (dark theme: #6FCB9C, #E3A43F, #EE8C7C) steps of the same hues. Dark ended-bar fill is #D0604E (3:1 non-text). `accessibility_test.dart` measures every pair.
- **Language row.** The spec allowed keeping `AglLanguageScreen`, but the app at base_sha had no language setting (the locale follows the device), so none was added.
- **Theme switch.** The old Appearance radio group is gone; dark mode follows the system, as §M5 says.
- **Report status wording** uses the app's own status sentences (e.g. "Still supported — Apple does not announce an end date"), not the shortened example in §M3.
- **Picker scope.** The device category's `intel-processors`, `nvidia-gpu`, `sns-hardware` and `raspberry-pi` files are hidden. They are not household devices with a security-update life, and Raspberry Pi's only date is "Discontinued".
- **`scripts/verify_api_hosts.py` was not run**, because it always writes `docs/api-hosts.json` (another workstream's file). endoflife.date was checked with curl instead: HTTP 200 on `/api/v1/products/{pixel,iphone,samsung-mobile}` and `/api/v1/categories/device`, 2026-10-12. The script discovers hosts from code, so the next run will pick it up.

SHOULD items S1–S6 were **not built**.

Store impact additions (for store-compliance, to apply after the founder decides):
- Review notes: the notification permission prompt appears when "Remind me" is first switched on (device detail, or Settings › Reminders), never at launch.
- Privacy label: unchanged, as §7 says. The new network traffic is downloads of public endoflife.date files with no user data in the request (`eol_parsing_test.dart` asserts the request has no query string).
- Screenshots: `integration_test/store_screenshots_test.dart` captures 01 onboarding, 02 this phone (only when the simulator's model matches exactly), 03 timeline, 04 list filtered to "Ending within 12 months", 05 device detail. The share-sheet frame (§7 item 5) is not captured, because the system share sheet is outside the Flutter view.

### Continuation (software-developer, 2026-10-13)

Pushed on GadgetNest `main`: `6e4ae13` (AdSlot: a filled AglAdBanner keeps its own 50 pt height instead of taking the screen; "Source: endoflife.date · updated <date>" on every sourced household row), `4e1721f` (device-page bar end date right-aligned; Timeline trace straightened), `b988216` (store screenshot test fixed and run green on an iPhone 17 Pro simulator against the live API; `[CP] Copy Pods Resources` build phase for the AdMob/UMP resource bundles). `ios/Podfile.lock` left uncommitted.

Deviation recorded (M2): each household row names the source and the source file's date; the maker's policy page is a tappable link on the device page, one tap away, not on the row itself (a link inside a tappable card would be a second, small tap target).

Founder question 1 (pivot / merge / retire, issue #25) is still unanswered. No store resubmission until it is.


### Repair round (software-developer, 2026-10-14)

**M8 simulator launch, done on the final code.** `flutter drive --driver=test_driver/integration_test.dart --target=integration_test/store_screenshots_test.dart` on an existing iPhone 17 simulator (iOS 27.1, `A0B7ECD5-…`), fresh install, live endoflife.date, Google's test banner unit: "All tests passed." The frames are committed in agl-manifest at `ai-office/projects/real-apps/evidence/GadgetNest/2026-10-14-c8bc744/` (01 onboarding, 02 this phone, 03 Timeline, 04 List filtered to "Ending within 12 months", 05 device detail). The banner fills at its own 50 pt height under the home list in 03 and 04 and covers nothing.

Why QA's run failed, and what made it run: on this Mac `xcode-select -p` is `/Library/Developer/CommandLineTools`, so `xcrun --show-sdk-path --sdk iphonesimulator` fails, and the Dart hooks runner (`hooks_runner-1.1.1/lib/src/build_runner/build_runner.dart:600-622`) passes only an allow-list of variables to `objective_c`'s build hook, which drops `DEVELOPER_DIR`. That is the `Bad state: No element` at `objective_c-9.5.0/hook/build.dart:198`. It fails the same way with the sandbox off. The `sandbox-exec: sandbox_apply` lines are Swift macro-plugin warnings and are not fatal. Workaround used, nothing committed and nothing system-wide changed: a `/tmp` directory first on `PATH` holding an `xcrun` shim that sets `DEVELOPER_DIR=/Applications/Xcode_27.1.0_27A9275_fb.app/Contents/Developer` and execs `/usr/bin/xcrun`, plus `DEVELOPER_DIR` exported for `flutter` itself. `sudo xcode-select -s` to the Xcode app would fix it for every session (a human action).

Two defects seen on the screens in the first run (on b988216), both fixed in GadgetNest `c8bc744`:
- The "Remind me" switch, when off, was nearly invisible: Material takes the off thumb and outline from `colorScheme.outline`, which is the 20% copper hairline. Off and enabled now use muted. New test `accessibility_test` "an enabled switch is visible on a card, on and off" (both themes) fails on b988216 and passes on c8bc744.
- Frame 04 was taken where the filter tap left the scroll, so the Add device button covered the row's "Source: endoflife.date" line (`before_04_list_b988216_fab_over_source_line.png`). The app already pads the list 96 pt at the bottom, so scrolling to the end clears it. The test now scrolls to the end before the shot. App layout unchanged.

Seen and left as they are: on 03 and 04 the "This phone" card is partly scrolled under the app bar, because the taps scroll the list. Store-compliance may prefer to crop or re-order frames. Dark mode was not looked at on the simulator; its colours are covered by `accessibility_test`.

**Privacy policy.** Approval request `ai-office/reports/approvals/2026-10-14-gadgetnest-privacy-policy.md` (Charter §6), with an `ai-office` / `needs-founder` issue. The office has not edited the page.

**Founder question 1 (issue #25)** is still open with no comments (checked with `gh issue view 25`). No store resubmission until it is answered.
