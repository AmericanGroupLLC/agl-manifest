# Spec: FashionFactory stops being an empty price-comparison shell and becomes a size-and-returns file for people who buy clothes online

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/FashionFactory`, branch `main`, base_sha `aa936197f4f2b0c23ff6fdccd5961176ee3b0e67` (`git rev-parse HEAD`, `git branch --show-current`, both run today)
- Apple: rejected under **5.6** on 2026-10-08T14:19:21Z (`/Users/spatchava/agl/.dist/rejections.json` key `FashionFactory`, version 2.2.0, one thread). It is the same 5.6 text the other 15 apps got in the same minute. Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:41` (G9: FashionFactory / GadgetNest / CodeDeal, founder decision D5).
- Baseline, measured today: `flutter analyze` printed "No issues found! (ran in 29.4s)". `flutter test` printed "+908: All tests passed!".

> **Gate: founder decision D5 comes first.** overlap.md:41 recommends that FashionFactory absorb GadgetNest *if a price feed is funded*, and that both apps be retired if it is not. This spec is a third option: keep the app and give it a job that needs no price feed. If the founder picks "retire", drop this spec. If the founder funds a feed and merges the apps, this spec is replaced. The developer should start only once chief-of-staff confirms that D5 = "pivot per this spec". See founder question 1.

**Uncommitted work by other people is in this repo. Do not touch it.** `git status --short` today shows 23 modified files under `fastlane/` (metadata, every phone/tablet screenshot, `review_information/notes.txt`) and `ios/Podfile.lock`. None of the files this spec asks you to change (`lib/`, `test/`, `integration_test/`, `pubspec.yaml`, `assets/`, `assets-src/`, `ios/Runner/Info.plist`, `ios/Runner/AppDelegate.swift`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets`, `android/app/src/main/**`) has uncommitted edits right now. **Known conflict:** adding a plugin (M3 needs `flutter_local_notifications`) changes `ios/Podfile.lock` when pods are installed, and that file already holds someone else's edit. Do not stage or commit `ios/Podfile.lock`. Report it to chief-of-staff so the owner of that edit can reconcile it.

---

## 1. Problem

### What the app is today (read: every file in `lib/`, 43 files, plus `main.dart`, `app_config.dart`, `env/prod.json`, the screenshot integration test)

| Area | State | Evidence |
|---|---|---|
| Catalog (Home, Browse, Deals, Results, Product, Compare) | **Dead in every release build.** Without the `AGL_API_GATEWAY_URL`/`_KEY` defines the app uses `UnconnectedProductRepository`, and every fetch throws `PriceFeedNotConnected`. `env/prod.json` sets `"AGL_API_GATEWAY_URL": ""`. Every catalog tab shows the card "Prices are unavailable". | `lib/main.dart:78-89`, `lib/data/unconnected_product_repository.dart:1-46`, `lib/ui/widgets/catalog_states.dart:124`, `env/prod.json` |
| Search | Disabled. The hint reads "Search unavailable until prices are connected". | `lib/ui/app.dart` (BrandHeader `searchEnabled`), screenshot `fastlane/screenshots/en-US/iphone69-01.png` (viewed today) |
| Add a product (paste link) | **Hidden in release**: `onAdd` is null unless the catalog is ready. Even when it is shown, a link only matches products already in the catalog. "Creating a new tracked product needs the pricing gateway". | `lib/ui/app.dart` (`onAdd: catalogReady && facts.storeCount > 0 ? … : null`), `lib/domain/tracking.dart:1-22`, `lib/ui/screens/add_product_screen.dart:228` ("not registered in this build.") |
| Saved + per-item price alerts | Unreachable. An item can only be saved from a catalog product, so the list is empty for every real install. The alerts send no notification. | `lib/domain/saved.dart`, `lib/domain/alerts.dart:1-12` |
| Price history | Removed. The class exists but nothing builds one. | `lib/domain/price_history.dart:1-11` |
| Profile | The only screen that works: "Where prices come from", affiliate disclosure, "Your data stays on this device", and a Privacy choices row that appears **only where UMP requires it**. | `lib/ui/screens/profile_screen.dart:55,150,195-221` |
| Screenshot pipeline | `integration_test/store_screenshots_test.dart` captures the catalog **with gateway defines that the shipped build does not have**, under `SCREENSHOT=true`, which also suppresses ads. | file header lines 1-22, commit `3e93b8e` |
| Identity | Amazon's retail palette taken from mockups: navy `#131A22`/`#232F3E`, amber `#FF9900`, price red `#B12704`, text `#0F1111` (`lib/theme.dart:152-172`). `fontFamily: 'Roboto'` is not bundled, so iOS falls back to the system font (`lib/theme.dart:426`, `pubspec.yaml` has no `fonts:`). Five-tab bottom bar with `AglAdBanner` just above it, hidden on Profile (`lib/ui/app.dart:443-452`). Interstitial on every tab switch (`lib/ui/app.dart:157`). The icon is an amber hanger on a navy gradient (`assets-src/icon.svg`). |
| Template boilerplate | `lib/app_env.dart` is **byte-identical** (md5 `27af7749…`) to GroceryMatch, DriftDate, VirtuBand and Uscis-Case. Nothing in `lib/` imports it. Only `test/app_env_test.dart` uses it. Affiliate-family copy: "Where prices come from" (`profile_screen.dart:55`), "Nothing saved yet" (`saved_screen.dart:186`), "BEST VALUE" (`compare_screen.dart:184`), "Live prices not connected" (`disclosure.dart:125`). |
| Not a tell here | The launch storyboard is its own (sha1 `e43dd25e…`, navy background), not the shared `3f6a9b27d8…`. `CFBundleDisplayName` is "Fashion Factory", correctly cased. The privacy label is unique to this app (hash compared against all of `store/privacy/*.json`). |

### Why Apple saw hidden features (5.6) and an empty template (4.3 risk)
1. **The review build and the listing show different apps.** The screenshot script needs gateway defines, but the shipped build is compiled without them. If any store image ever showed products or prices, a reviewer opened an app where every tab says "Prices are unavailable". The compiled binary also contains Product, Compare, Add-a-product and Saved screens that a reviewer cannot reach. That matches "features that appear to have been intentionally hidden". (Which images Apple had when it judged the app: **not verified**. The `fastlane/` working tree holds other people's uncommitted screenshots. I viewed only `iphone69-01.png`, which shows "Prices are unavailable". The five iPhone files there have 5 different sha1s today.)
2. **The copy and the listing say the app does not work.** The subtitle is "Price comparison, coming soon". The description opens "—— Where it stands today —— Live store prices are not connected yet" (`store/apps/FashionFactory.json`).
3. **It is a reskin of a famous retailer** (Amazon colour values, same layout family as GadgetNest at 76% implementation similarity per `store/apps/FashionFactory.json` `differentiation` §5).
4. **There is no real data source, and none can be added in this session.** A paid price feed is a §3 decision. I also tried to check whether retailer product pages could be read without a key (Shopify storefront JSON). The AI-office judge **denied the probe** as a possible terms-of-service/CFAA problem. That route is closed unless the founder approves it (founder question 3). So the only honest data this app can have is data the user enters.

## 2. User and product decision

**User:** someone who buys most of their clothes and shoes online, from several brands and stores, and loses money and time on wrong sizes and missed return windows. A typical example: a 25–45-year-old who orders two sizes of the same jeans, keeps one, and has to remember which store, which size and by when.

**Core job (one, done well):** *"What size do I order at this brand, and what is still out for return?"* Log each online clothing or shoe order with the size you ordered. Mark it **Kept** or **Returned (too small / too big / too long / too short / didn't like / faulty)**. Never miss its return-by date.

**Signature feature: "My size at this brand", worked out from your own kept and returned orders, with return-window reminders.**
- Type or pick a brand (and optionally a category such as Jeans or Sneakers). The app answers from your history only, with the evidence behind it. For example: "Levi's · Bottoms → **W32 L32**. Kept W32 L32 twice (Mar 2026, Aug 2026). Returned W31 L32 as too small (Jun 2026)". Or: "Mixed results: kept M (slim cut), returned M (regular cut) as too big."
- With no history at that brand, it says so. It then shows what you kept in that category at other brands, labelled as other brands. **It never invents a brand size chart and never converts sizes it has no record of.**
- Every order in **Out for trial** shows a countdown to its return-by date. A **local** notification arrives 3 days before and on the morning of the last day. Scheduling happens on the device and nothing comes from a server.
- Why it is distinct. I checked the competitors' App Store listings today with Apple's keyless Search API (`https://itunes.apple.com/search?…&entity=software&country=us`). These claims rest **only on their listing text**. I did not install the apps.
  - **Clothi: Clothing Sizes Tracker** (id1547115025) stores "the clothing and shoe sizes of the whole family, brand by brand", fit by cut, size history and a size converter. Its listing does not mention order outcomes (kept vs returned) or return deadlines.
  - **Seel – Your Shopping Companion** (id6749478347) manages returns by syncing "orders through your Gmail" with AI. It needs mailbox access and does not learn your size per brand.
  - **Stylebook / Indyx / Acloset** are wardrobe and outfit apps with cost-per-wear. Their listings mention no per-brand size answers from returns.
  - FashionFactory's honest angle is the loop that connects these: **order → verdict → size answer**, on the device, with no mailbox access, no account and no brand charts of unknown accuracy.
  - Web search was unavailable in this session (the hook said "Internet mode is not enabled"). Any competitor beyond the four listings above: **competitor not verified**.
- Portfolio overlap: none. I grepped every Dart file under `/Users/spatchava/agl` for wardrobe, closet, cost-per-wear and outfit. The only hits were RoomCraft furniture ("Handleless wardrobe"). The new app does no price comparison (GadgetNest), no promo codes (CodeDeal) and no grocery (GroceryMatch). It also does no budgeting (MyFinance), because prices paid are optional and used only for the "money in returns" total.
- Data: 100% on-device, entered by the user. No network call for the core job.

**Removed scope:** perfume, watches and tech (tech belongs to GadgetNest), price comparison, deals, compare tables, affiliate tagging and the gateway client. Bags stay as a category ("One size" is allowed) because bags are returned too.

---

## 3. Acceptance criteria

### MUST (what Apple needs in order to see a real, distinct app). Each one is testable.

**M1. Core job end to end (plan criterion 1).** On a fresh install with no network:
- Onboarding (M5) → Home → **Add order** → brand (autocomplete from your own brands), category (Tops, Bottoms, Dresses & skirts, Outerwear, Shoes, Bags & accessories, Other), size, optional cut/style note, store, optional link, optional price and currency, order date (default today), return-by date (quick picks: 14 / 30 / 60 days from today, a custom date, or "No returns") → Save. The order appears under **Out for trial** with its countdown.
- Open the order → **Kept** / **Returned** (reason chips) / **Exchanged** (asks for the new size and creates a linked order that is out for trial) / Edit / Delete (with undo).
- Size input must handle letter sizes (XXS–4XL), numeric sizes (0–30, 32–56), waist × length (W28–W44 × L28–L36), shoe sizes with a system (US M / US W / UK / EU / cm) and "One size". It must also accept free text. Free text is stored as typed and simply has no ordering.
- **Paste link:** a "Paste" button reads the clipboard (on iOS this shows the system paste prompt), keeps the URL and names the store from the host through the existing registry (`lib/domain/stores.dart` `stores`, e.g. `asos.com` → ASOS). It falls back to the bare host. **The app never fetches the page**, and the field says so: "The link is saved so you can reopen the order. Fashion Factory doesn't read the page." Tapping a saved link opens it with `url_launcher` (already a dependency).
- Every visible control does something real. Remove the screens that cannot work, and their routes and code, so nothing dead is compiled in: `browse_screen`, `deals_screen`, `results_screen`, `product_screen`, `compare_screen`, `add_product_screen`, `saved_screen` (replaced), `catalog_states`, plus the domain/data files only they use: `catalog`, `compare`, `offers`, `price_track`, `price_history`, `filters`, `disclosure`, `alerts`, `tracking`, `product_repository`, `remote_product_repository`, `unconnected_product_repository`, `product_dto`, and the gateway half of `data/app_config.dart`. **No `AGL_API_GATEWAY_*` or `AGL_AFFILIATE_TAGS` define may be read anywhere in `lib/`** (the affiliate side has no revenue today: `env/prod.json` sets it to `""`). Remove the `http` dependency if nothing else uses it.

**M2. Signature feature: "My size at this brand" + return reminders (criterion 2).**
- `lib/domain/size_answer.dart` holds pure Dart with no Flutter import: `SizeAnswer answerFor({required String brand, Category? category, required List<Order> history})`.
  - Brand matching is normalised: case, diacritics, `&`/`and` and punctuation are ignored, so "Levi's", "LEVIS" and "levi’s" are one brand.
  - The answer is the most recently **kept** size for brand + category. Supporting evidence is every kept and returned order for that pair with date and reason. Conflicts are surfaced, never hidden: if the same size was both kept and returned, show "Mixed results" with each cut/note.
  - When sizes can be ordered (same scale), returned-too-small / too-big orders bound the answer and the copy says so: "Returned S as too small, kept M → M".
  - If the brand has no history for the category, fall back to (a) the same brand in other categories and (b) kept sizes in this category at other brands, each labelled as such. With no history at all: "No orders from Levi's yet. Log one and your size will show here."
  - No confidence percentages, no "most people", no built-in brand charts, no conversion tables.
- Home has a **"Find my size"** field. Typing a brand shows the answer card live. The brand page (from search or from the Brands list) shows the answer per category, then the order history.
- **Return reminders** use `flutter_local_notifications` + `timezone`/`flutter_timezone` (keyless pub packages; versions 22.1.0 and 5.1.0 are already in `~/.pub-cache`). Schedule two reminders per order (3 days before, and 09:00 local on the last day). Cancel them when the order is marked kept/returned or deleted, and reschedule them when the date is edited.
  - Ask for notification permission **just in time**, when the first order with a return date is saved. Show a one-line primer first: "Get a reminder before the return window closes?".
  - If permission is denied, the Out for trial section shows "Reminders are off" with a button that opens the system settings for the app. The countdown still works in the app.
  - iOS: register the plugin in `AppDelegate.swift` as the package README requires. Android: `POST_NOTIFICATIONS` and exact-alarm handling as the plugin README requires. If exact alarms are not granted, use inexact scheduling and say "around 9 am".

**M3. Depth (criterion 3).**
- **Persistence:** orders, brands and settings survive restarts and app updates. Use the existing `PreferencesStore`/`SharedPreferencesStore` with a versioned JSON schema (`orders.v1`) and a migration test. If the dataset outgrows it, a JSON file in Application Support is acceptable. Old v2.2 keys (saved list, alert switches, last category) are deleted on first launch of the new version. They can only be empty or stale, because nothing could be saved without a catalog.
- **Search and filter:** one search field across brand, store, size and notes. Filter chips: **Out for trial / Kept / Returned** and category. Sort: newest, return deadline, brand A–Z.
- **Share / export:**
  - (a) **"Share my sizes"** builds a plain-text card of the kept sizes for the brands the user ticks ("For gifts: Levi's Bottoms W32 L32; Nike Shoes US M 10…") and opens it in the system share sheet (`share_plus`, keyless).
  - (b) **Export all orders as CSV** via the share sheet.
  - Import is SHOULD S2.
- **Totals that come from the user's own data only** (Home header): "Out for trial: n · next deadline in d days" and, on the Insights row, "Returned this year: n orders · $X". The money total includes only orders that have a price entered and says "of orders with a price".
- **States:**
  - First run: no orders, onboarding done. It explains the loop in one sentence and has an "Add your first order" button.
  - A brand with no history.
  - Search with no results, including a button to add an order for that brand.
  - An overdue order: "Return window closed 2 days ago", with Kept / Returned still available.
  - Notifications denied.
  - Storage write failure: a snackbar, and the form keeps its contents.
  - There is no offline state because the core job makes no network calls. State that in a code comment, not on screen.

**M4. Own identity: not the Amazon reskin and not the shared scaffold (criterion 4).** Name these exactly in code:
- **Palette: "fitting room".** Light: background stone `#F3F4F1`, surface `#FFFFFF`, ink `#1B1A1F`, primary garnet `#7A1F3D` (primary buttons, the size answer), tape-measure yellow `#E8B931` (the size "chip" fill only, with ink text on it, never text colour), kept sage `#5E7D6A`, returned clay `#C2603F`, hairline `#E9EAE6`. Dark: background `#141216`, surface `#1F1C22`, text `#F1EEF2`, primary `#D46A8C`, kept `#8FB59D`, returned `#E38B6C`. Kept/returned are also marked by icon and label, never by colour alone. Keep `test/ui/contrast_test.dart`'s approach: recompute AA for every text/surface pair in both palettes. I grepped `.dart`, `.md` and `.svg` under `/Users/spatchava/agl` today. Apart from `#FFFFFF`, none of these hexes appears in any app or other spec. Delete the Amazon values `#131A22`, `#232F3E`, `#FF9900`, `#B12704`, `#0F1111` from `lib/`.
- **Typography:** bundle **Bodoni Moda** (`BodoniModa[opsz,wght].ttf`) for the brand wordmark, screen titles and the size answer, and **Jost** (`Jost[wght].ttf`) for all UI text. Both are OFL in github.com/google/fonts (`ofl/bodonimoda`, `ofl/jost`; I listed both directories with `gh api` today). Ship `OFL.txt` and register the licences with `LicenseRegistry`. Remove `fontFamily: 'Roboto'`. I grepped every `.dart`, `pubspec.yaml` and spec `.md` under `/Users/spatchava/agl`, and no other app uses either font.
- **Shape language:** size values are drawn as a "label tag", a 4 px-radius chip with a punched-hole dot on the left, in tape yellow. Cards use a 2 px radius and a 1 px hairline, which is sharp and tailored, not 12 px blobs. Return countdowns are a horizontal "measuring tape" bar with day ticks.
- **Home layout: no bottom tab bar and no five tabs.**
  - A large-title scroll view headed "Fashion Factory" (or the new name, see founder question 2) with Settings (gear) and Add (+) in the bar.
  - Then, in order: the **Find my size** field, **Out for trial** (sorted by days left, measuring-tape bars), **Brands** (alphabetical with each brand's latest kept size as a label tag) and **Insights** (returned this year, most-returned reason).
  - On iOS use `CupertinoSliverNavigationBar`, `CupertinoIcons`, `CupertinoActionSheet` for Kept/Returned/Exchanged and `showAdaptiveDialog` for delete confirmations. Android keeps the Material 3 equivalents.
- **Ads placement:** move `AglAdBanner` out of the shell. It becomes one inline slot at the end of the Home list and at the end of a brand page, never between the user and a form. Remove the interstitial on tab switch (`lib/ui/app.dart:157`), because there are no tabs. Founder question 4 covers whether to add an interstitial elsewhere.
- **Onboarding** (first run only, then never again):
  - Title "Order your size, not two."
  - Three lines: (1) "Log what you ordered and the size." (2) "Mark it kept or returned — and why." (3) "Next time, your size at that brand is here, and you'll get a nudge before a return window closes."
  - One button, "Add my first order", plus a "Skip" text button.
  - No "Get started", "Welcome" or "Welcome back".
- **Settings** (its own screen and its own copy): Reminder timing (3 days / 1 day / off) · Default currency · Export orders (CSV) · Share my sizes · Language (`AglLanguageScreen` may stay as shared infrastructure) · Privacy choices · Privacy policy · Delete all data (confirm, then wipe local storage and cancel all scheduled notifications) · About (version, font licences).
- **Code structure:** `lib/features/home|orders|brands|settings|onboarding/`, `lib/domain/` (orders, sizes, size_answer, stores), `lib/data/` (store, notifications). Delete `lib/app_env.dart` and `test/app_env_test.dart`: the file is unused by the app, and byte-identical to four other apps.

**M5. Remove this app's template tells (criterion 4).** After the change, `grep -rn` over `lib/` must return nothing for: "Prices are unavailable", "Live prices not connected", "not connected", "in this build", "coming soon", "Where prices come from", "Nothing saved yet", "BEST VALUE", "Biggest discounts", "Shop by category", "Get started", "AGL_API_GATEWAY", "AGL_AFFILIATE_TAGS", `fontFamily: 'Roboto'`, and the five Amazon hexes.
- **New icon,** not from `scripts/generate_app_icons.py` (FashionFactory is not in its DESIGN table, so nothing will overwrite it). The design is a garnet `#7A1F3D` garment label tag with a punched hole and a tape-yellow `#E8B931` stitched edge on stone `#F3F4F1`, drawn as vector geometry in `assets-src/icon.svg`. No Material glyph, no hanger, no diagonal gradient. Regenerate every iOS AppIcon size and every Android mipmap plus the adaptive foreground/background (`flutter_launcher_icons` is already configured in `pubspec.yaml`; change `adaptive_icon_background` and the web colours to the new palette).
- **Launch screen:** `LaunchScreen.storyboard` background `#F3F4F1` (dark `#141216`) with the label-tag mark. Replace `assets/splash.png`/`LaunchImage` accordingly.
- `pubspec.yaml` `description:` describes the new job. `agl.config.json` still describes the long-gone React Native "StyleRadar" app. Update its name, description, stack and design block to match this app, or delete it if nothing reads it (`grep` the manifest scripts first).

**M6. Honest, with nothing that could read as hidden (criterion 5, Apple 5.6).**
- Real data only. Every order, size and price comes from the user. No sample orders, no seeded brands, no example size answers, no screenshots built on fake history. Delete `test/support/sample_catalog.dart` along with the catalog it served. New test fixtures are built inline in tests, and none ships in `lib/`.
- **No build-time feature switches that change what a user sees.** With the gateway gone, a release build and a debug build show the same features. `SCREENSHOT=true` may still suppress ads in screenshot builds only if founder question 5 approves it. It must change nothing else.
- **Privacy choices row always visible** in Settings. Where UMP requires a form it opens `AglConsent.showPrivacyOptions`. Elsewhere it opens a short sheet explaining that Google's consent form does not apply in the user's region. Check the wording against `packages/agl_ads` before finalising it. Replace the conditional `_PrivacyChoices` (`profile_screen.dart:195-221`).
- No demo login, no remote config, no date/region/reviewer checks, no hidden gestures, no long-press-only actions, no debug menu. Every feature is reachable from Home in at most 2 taps.
- On-screen copy states what the app does in positive terms. The one constraint that matters is stated where it applies (the link field: "doesn't read the page"). No list of disclaimers.
- `docs/privacy-policy.html` (in the app repo) currently lists "Saved items and their price alerts" as on-device data (line 153). The new on-device data is orders, sizes, prices paid, return dates and scheduled local reminders. That is legal text (Charter §6). The developer drafts the diff and sends it to chief-of-staff as an approval request. **Do not edit the policy without founder approval.** If `test/security/privacy_policy_test.dart` asserts the old wording, leave that assertion in place, and report the release as blocked on founder question 6 rather than changing the test to fit.

**M7. Proven (criterion 6).**
- `flutter analyze` must be clean and every remaining test must pass.
- **Removed features take their tests with them in the same commit, and the commit message lists each deleted test file and why** (the feature no longer exists). That is not "deleting a test to go green". Every test about infrastructure that still exists must stay and pass: i18n, release config, hardening, accessibility, contrast, foldable/responsive, persistence and smoke. Adapt them to the new screens without weakening their assertions.
- New tests, at least:
  - `test/unit/size_parse_test.dart`: letter, numeric, W×L, shoe+system, "One size" and free text parse. Ordering holds within a scale and is absent across scales.
  - `test/unit/size_answer_test.dart`: picks the most recent kept size. Returned too-small/too-big bounds are applied and described. "Mixed results" when the same size was kept and returned. Brand normalisation ("Levi's" = "LEVIS" = "levi’s"). The fallbacks are labelled other-category / other-brand. Empty history gives the honest empty answer. No answer contains a size that is not in the history (property-style test over generated histories).
  - `test/unit/return_window_test.dart`: days-left/overdue maths across DST and month ends. Reminder times (3 days before, and 09:00 on the last day). "No returns" schedules nothing.
  - `test/unit/link_store_test.dart`: host → store via `stores.dart` (including `www.` and `m.` prefixes and regional TLDs). An unknown host shows the host. Invalid text is rejected. The app makes no HTTP call: assert that `lib/` imports no `package:http` / `dart:io HttpClient`.
  - `test/integration/order_store_test.dart`: orders round-trip and survive reload. The v2.2 keys are cleared on migration. "Delete all data" wipes everything.
  - `test/integration/reminders_test.dart` (fake scheduler): save schedules 2 reminders, Kept/Returned/Delete cancel them, and editing the date reschedules them.
  - Widget tests: onboarding shows once. Add order → appears in Out for trial. Mark returned (too small) → the brand answer updates. Find-my-size shows the answer card. Search and each filter chip narrow the list. Share-my-sizes text is exactly what was ticked. CSV export header and rows. The Privacy choices row is present in both consent states. The "Reminders are off" state appears when permission is denied.
  - `test/identity_test.dart`: none of the M5 banned strings or hexes in `lib/`. Bodoni Moda and Jost are declared in pubspec and present on disk. Light and dark themes both exist. No `NavigationBar`/bottom tab bar in `lib/`. The LaunchScreen storyboard contains the new background colour.
- Rewrite `integration_test/store_screenshots_test.dart` to drive the real app with **no gateway defines**. Data is entered through the UI in the test (orders the QA tester actually placed, see store impact). It must not depend on any build-time data source.
- Commit path-limited: `git add lib test integration_test pubspec.yaml pubspec.lock assets assets-src ios/Runner/Info.plist ios/Runner/AppDelegate.swift ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main agl.config.json`. **Never** add `fastlane/` or `ios/Podfile.lock`. Then push to `main`.
- **Launch it and look at it.** Build for the iOS simulator and screenshot onboarding, Home with orders, a brand page with the size answer, the Kept/Returned sheet and Settings. Green tests are not proof that the screens render.

**M8. Store impact written down (criterion 7).** See section 5. store-compliance applies it. The office does not submit anything (5.6 freeze, MA-043).

### SHOULD (valuable, not required for the resubmission)
- **S1. Label photo:** attach a photo of the size label or the garment to an order (`image_picker`, stored in the app's documents directory, never uploaded). It shows on the brand page next to the size.
- **S2. CSV import** of the M3 export format, so a user can move phones without an account.
- **S3. People:** sizes for a partner or child as separate profiles (each with its own brand answers). Clothi already does family profiles, so this is not the signature.
- **S4. Home-screen widget** (iOS WidgetKit / Android Glance) for "Out for trial: next deadline".
- **S5. Translations:** the app is English-only today (`lib/ui/app.dart` `appSupportedLocales`). Keep it that way until the new copy is translated, and keep `Info.plist` `CFBundleLocalizations` in step (`test/i18n_test.dart`).

---

## 4. Data source
- **All user-entered, stored on the device:** orders (brand, category, size, cut/note, store, link, price, currency, dates, status, reason), brands, settings. The store is `shared_preferences` (existing) or a JSON file in Application Support. Nothing is uploaded. Everything is deleted with the app or with Settings → Delete all data.
- **Store names from links:** the existing static registry `lib/domain/stores.dart` matches hosts only. No page is fetched.
- **Reminders:** local notifications scheduled on the device (`flutter_local_notifications`). No push service, no server.
- **No Supabase, no public API, no keys.** The core job makes no network call. AdMob (`agl_ads`) is unchanged and already disclosed.
- Considered and rejected: (a) the pricing gateway, because nothing deployed was found, `env/prod.json` leaves it empty, and paying for a feed is a founder decision; (b) reading retailer product pages or Shopify storefront JSON for live price/stock, because the AI-office judge denied the probe today on terms-of-service grounds (founder question 3).

## 5. Store impact (proposals only. I edited nothing under `store/apps/`, `fastlane/` or `agl-manifest/docs/`.)

**Name:** keep "Fashion Factory" unless the founder renames it (founder question 2). The store name today is "Fashion Factory: Deals", and "Deals" must go because the app has no deals. Proposal: **"Fashion Factory: Size & Returns"** (31 characters, too long for the 30-character limit), so use **"Fashion Factory: Fit File"** (25). If renamed, possible names are "Fitfile" or "Kept or Returned". App Store availability of either: **not verified**.

**Subtitle (30 max):** "Your size at every brand" (24). This replaces "Price comparison, coming soon".

**Promotional text:** "Log what you ordered and whether you kept it. Next time, Fashion Factory tells you your size at that brand — and reminds you before a return window closes."

**Play short description (80 max):** "Your size at every brand, from what you kept and returned. Return reminders." (76)

**Description (proposed; it does not open with the app name, uses no "—— heading ——" style, and has no shared ads paragraph):**
> Ordered two sizes again? Keep a record of every clothing and shoe order — the brand, the size, and whether it fit — and the next time you shop that brand, your size is waiting.
>
> Your size, from your own history
> Mark each order Kept or Returned, and why: too small, too big, too long, too short, didn't like it, faulty. Type a brand and see the size you kept there, with the orders behind it. If a cut runs differently, you'll see that too.
>
> Never miss a return window
> Add the return-by date when you order. Everything still out for trial is on the home screen with the days left, and a reminder arrives three days before and on the last day.
>
> Made for online shopping
> Paste the product link to keep it with the order — the store is recognised from the link. Search every order, filter by kept or returned, and share your sizes with someone buying you a gift. Export everything as a spreadsheet whenever you like.
>
> Private by default
> No account and no sign-in. Your orders stay on your phone, and reminders are scheduled on your phone. The app is free and shows ads from Google AdMob; where the law requires consent, Google asks first, and Settings → Privacy choices is always there.

(store-compliance: check the ads sentence against what `agl_ads` actually does before using it.)

**Keywords (100 max):** `clothing size,size by brand,returns,return reminder,shoe size,online shopping,fit,kept,wardrobe` (95)

**Category:** primary **SHOPPING**, secondary **LIFESTYLE**. This swaps the current pair, which is allowed because the two are still different. The job is buying online, and LIFESTYLE is the most crowded category in the portfolio (overlap.md:99).

**Screenshots: retake all of them** (iPhone 6.9", iPad 13", Play phone and tablet) from the release build with the rewritten integration test. The data must be the QA tester's own real orders, entered through the UI, never invented brands or histories meant to look like a real user.
1. Home: Out for trial with measuring-tape countdowns, and Brands with size tags.
2. A brand page: "Your size: W32 L32" with the kept/returned evidence.
3. The Kept / Returned sheet with reason chips.
4. Add order with a pasted link and the store recognised.
5. The return reminder notification and Settings → Reminder timing.

Drop every "Prices are unavailable" image. Rebuild the Play feature graphic from the new icon and palette.

**Review notes (proposed, written for this app; do not use the shared "2. DEVICES AND OS VERSIONS TESTED" skeleton):**
> Fashion Factory keeps a record of the user's online clothing and shoe orders — brand, size, kept or returned and why — and answers "what size do I order at this brand?" from that record. It also reminds the user before each return window closes.
> To try it: open the app → Skip or "Add my first order" → enter any brand (e.g. "Levi's"), category Bottoms, size W32 L32, return-by in 14 days → Save. Open the order → Returned → Too small. Add a second Levi's order, size W33 L32 → Kept. Type "Levi's" in Find my size on Home: the answer card shows W33 L32 with both orders. Allow notifications when asked to receive the return reminder.
> No account, no login, no server. Every feature is on the home screen. Nothing is region-, date- or server-controlled, and the release build is the same app as the screenshots. The app reads no web pages: a pasted link is only stored and reopened.
> The only regional difference is Google's ads consent form (EEA/UK/CH), which is reachable at any time from Settings → Privacy choices.
> Tested on: [QA fills in the physical iPhone/iPad models and iOS versions actually used. Simulators are not devices, and no device may be listed that was not used.]
> Contact: [a real named person, see founder question 7.]

**`differentiation` block (`store/apps/FashionFactory.json`) for store-compliance:**
- §1: the new core job.
- §3: the Clothi/Seel comparison from section 2, stated as "per their App Store listings".
- §5: replace "Closest other app: GadgetNest at 76%" after re-measuring on the new code.
- §6: answer "not a feature of DriftDate/NearServe/RoomCraft/daily-pulse" (it shares no job with them).

**Privacy label:** data collected by the developer does not change. Orders stay on the device, and AdMob's device ID / advertising data are as today. Local notifications are not data collection. Play data safety: the same. The privacy-policy text change is founder question 6.

**Release notes (3.0.0, a new product):** "Fashion Factory is now a size and returns record: log orders, mark them kept or returned, see your size at each brand, and get reminders before return windows close. Price comparison, which never had a live price source, has been removed."

## 6. Out of scope
- Any price comparison, price tracking, deals, coupons, affiliate links or price feeds (GadgetNest/CodeDeal/D5).
- Reading retailer pages, Shopify storefront JSON, emails or receipts (ToS risk, founder question 3; Seel's mailbox-sync model).
- Brand size charts, size conversion tables, body-measurement fit prediction, AR measuring (no verified source; anything else would be invented data).
- Wardrobe/outfit planning, cost-per-wear, outfit photos (a crowded category: Stylebook, Indyx, Acloset and others per their listings).
- Accounts, sync, Supabase, a paid tier.
- Editing `store/apps/FashionFactory.json`, fastlane metadata, `agl-manifest/docs`, or the app's `docs/privacy-policy.html` without approval. Uploading, submitting or replying to Apple.

## 7. Founder questions
1. **D5 for FashionFactory:** (a) pivot to the size-and-returns product in this spec, (b) fund a price feed and merge GadgetNest into FashionFactory (overlap.md:41), or (c) retire it (Charter §8)? This spec should be built only on (a).
2. **Name:** keep "Fashion Factory" with the new subtitle, or rename to something that says the job ("Fitfile", "Kept or Returned"; availability not verified)? A rename changes the display name, icon wordmark and listing. The bundle ID stays.
3. **Reading retailer pages:** the office judge blocked a check of public Shopify product JSON because of terms-of-service risk. Do you want legal review of that route for a future "is my size back in stock" feature? Until then it stays out of scope.
4. **Ads:** the tab-switch interstitial disappears with the tabs, and the banner becomes inline. Either change affects revenue (Charter §3). Accept, or name where an interstitial may appear (e.g. never inside the add-order flow)?
5. **Screenshot builds without ads (`SCREENSHOT=true`):** acceptable, or should listing screenshots show the real ad slot, so the listing and the binary match exactly given the 5.6 history?
6. **Privacy policy text** (`docs/privacy-policy.html`, Charter §6): approve the updated on-device data list (orders, sizes, prices paid, return dates, local reminders) once the developer drafts it?
7. **App Review contact:** replace "App Reviewer" with a real person's name for this app, and who replies to Apple about the account-wide 5.6 (Charter §1, MA-043 freeze)?

---

## 8. Implementation notes for store-compliance and QA (software-developer, 2026-10-12)

Proposals only; nothing under `store/apps/`, `fastlane/` or `agl-manifest/docs` was edited.

- **Version:** `pubspec.yaml` is `3.0.0+6`. Settings → About shows `3.0.0`.
- **Screenshots** (section 5 list) are produced by `integration_test/store_screenshots_test.dart`, which drives the release app (`lib/main.dart`, no defines) and types the QA tester's real orders into the Add order form. They are passed only to the test: `--dart-define=QA_ORDERS='[{"brand":…,"category":"bottoms","size":…,"store":…,"link":…,"returnPick":"30 days","verdict":"kept"|"returned:tooSmall"}, …]'`. Without QA_ORDERS the test fails rather than invent a history. Output names: `01_home_out_for_trial_and_brands`, `02_brand_size_answer`, `03_kept_or_returned`, `04_add_order_pasted_link`, `05_settings_reminder_timing`. Screenshot 5 in section 5 ("the return reminder notification") is not capturable in-app; the script captures Settings → Reminder timing. Orders are dated the day they are entered.
- **Review notes, exact UI words:** onboarding buttons are "Add my first order" and "Skip"; the reminder primer is "Get a reminder before the return window closes?" with "Not now" / "Allow"; the verdict button on an order is "Kept, returned or exchanged?"; Settings is the gear in the top bar; "Privacy choices" is always in Settings (it explains when Google's form does not apply).
- **Ads (founder question 4):** implemented as spec'd: one inline `AglAdBanner` at the end of Home and of a brand page, none on the form or in Settings, and no interstitial anywhere.
- **Permissions (Play data safety unchanged; policy text not):** Android source manifest adds `RECEIVE_BOOT_COMPLETED` (reminders survive a reboot); `flutter_local_notifications` merges `POST_NOTIFICATIONS` and `VIBRATE`. No exact-alarm permission is requested, so Android reminders are inexact and the app says "around 9 am". iOS asks for notification permission just in time.
- **Privacy policy (founder question 6):** drafted in `ai-office/reports/approvals/2026-10-12-fashionfactory-privacy-policy.md`. Until it is approved and applied, 3 assertions in `test/security/privacy_policy_test.dart` fail by design (left in place per M6), so the release is blocked on question 6.
- **Podfile.lock:** the new plugins change `ios/Podfile.lock` on `pod install`; that file holds someone else's uncommitted edit (CocoaPods 1.16.2 → 1.17.0). It was restored byte-for-byte after the local build and is not committed; its owner must reconcile it. The local `pod install` also added a "[CP] Copy Pods Resources" phase to `project.pbxproj`; not committed (CocoaPods re-adds it on any machine).
