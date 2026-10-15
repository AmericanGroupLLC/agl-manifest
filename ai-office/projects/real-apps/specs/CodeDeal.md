# Spec: CodeDeal becomes the wallet for the promo codes you already have, and tells you which one to use at checkout

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/CodeDeal` (app at `mobile/codedeal_app`), branch `main`, base_sha `40c66e7cdf4d5ce2dde5d5410ca484634aed2066`
- Apple: rejected under **4.3 / 4.2.6** (the identical 26-app message, `/Users/spatchava/agl/.dist/rejections.json` key `CodeDeal`, version 1.4.0, 2 threads). The same file also records **Guideline 4** ("the user is taken to the default web browser to sign in or register") and **2.1(a)** ("We were unable to use the core feature, HOME, because an error message displayed at the home page", iPhone 17 Pro Max, iOS 27.0). Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:41` (group G9, recommendation D6: "Retire CodeDeal unless a code source and backend are funded").
- Baseline, measured today: `flutter analyze` in `mobile/codedeal_app` gives "No issues found! (ran in 46.7s)". I did **not** run `flutter test` (not verified).

**Founder decision first (Charter §8).** D6 recommends retiring CodeDeal. This spec is the **keep** path, and it changes the premise of D6: the product below needs **no** code feed, no backend and no money. It runs entirely on the device. If the founder still chooses to retire the app, nobody should build this spec. See founder_questions.

**Uncommitted work by other people is in this repo. Do not touch it.** `git status --short` today shows 12 modified files, all under `mobile/codedeal_app/fastlane/` (descriptions, `review_information/notes.txt`, Play and App Store screenshots). No file this spec asks you to change (`lib/`, `test/`, `pubspec.yaml`, `assets/`, `ios/Runner/Info.plist`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets/`, `android/app/src/main/AndroidManifest.xml`, `android/app/src/main/res/`) has uncommitted edits right now. `ios/Runner.xcodeproj/project.pbxproj` and `ios/Podfile.lock` are clean today, but adding plugins will change them. If either shows someone else's edits when you start, stop and report it. Do not edit them by hand.

---

## 1. Problem

### What the app is today (read in full: every file in `lib/`, 5,534 lines including generated l10n)

| Area | State | Evidence |
|---|---|---|
| Data source | **None.** Every screen calls a tRPC server. Its base URL comes only from `--dart-define=API_BASE` and is empty by default, so the client makes no requests and every provider throws `TrpcException.notConfigured`. | `lib/core/network/trpc_client.dart:14` (`kDefaultBaseUrl = String.fromEnvironment('API_BASE')`), `:54` (`isConfigured`), `lib/core/api/providers.dart:118-185` |
| Home / Deals / Search / Category / Store / Deal detail | **Empty shells in every release build.** Each one shows `ServiceUnavailablePanel`: "Deals service unavailable … This version of CodeDeal is not connected to a deals service". This is store screenshot 01 and the 2.1(a) "error message at the home page". | `lib/features/_shared/state_panels.dart:286-324` |
| Server in the repo | A tRPC + MySQL server exists in `web-app/server/` (`overlap.md:41` says the repo has no server. That is wrong. It is in `web-app/`, not `src/`). Its keyless "public coupon" source is a **hard-coded list of 67 codes, all flagged `verified: true`**, with no verification in the code (`web-app/server/_core/affiliate/publicCoupons.ts:40-133`, e.g. `"NORD72"`, `"SHEIN15"`). The other sources need paid or keyed affiliate accounts (`awin.ts`, `cj.ts`, `impact.ts`, `rakuten.ts`, `couponApi.ts`, `linkMyDeals.ts`). **Reviving it would ship invented data.** It must not be used. | `grep -c 'verified: true' publicCoupons.ts` gives 67 |
| Accounts | Supabase email/password sign-in, now in-app (commit `6d8e6fd`). It unlocks nothing: the profile screen has only Settings, Sign out and Delete account. The code comments themselves say referrals and notifications "need a deals-server session that Supabase sign-in never creates". Sign-in page headline "Welcome back" is a cross-portfolio tell. | `lib/features/profile/profile_page.dart:88-96`, `lib/features/auth/sign_in_page.dart:133` |
| Referrals / Notifications | **Orphaned and dead.** Routes exist (`lib/main.dart:121-122`) but nothing links to them. Referral shows "Referral links are not available yet." | `lib/features/referral/referral_page.dart:46` |
| Settings | Accent-colour swatches **save a preference that nothing reads** (dead control). The language chip list is the app's own 19 locales, but most screen text is English only (the store notes admit it). "Release notes →" opens a GitHub README. | `lib/features/settings/settings_page.dart:84,199` (only reader/writer of `'accent'`), `:237` |
| Voice search | `speech_to_text` with microphone and speech prompts (`ios/Runner/Info.plist:29-32`), searching a server that does not exist. | `lib/features/search/search_page.dart:22-60` |
| Persistence | **None** of the user's own. Nothing the user makes is kept. | no local store in `lib/` beyond prefs for language/accent |
| Paywall copy | Leftover ARB key `premiumAdFree` "Ad-free experience" (the paywall was removed in `4b341f0`, the string stayed). Shared with CalcMaster, MyFinance, iMaps. | `lib/l10n/app_en.arb:27` |
| Identity | Template. Dark-only (`themeMode: ThemeMode.dark`, `lib/main.dart:144`). Tailwind neon palette A855F7 / 22D3EE / EC4899 / 34D399 (`lib/core/theme.dart:11-28`). Font is the system default (`'SF Pro Text'`/`'Roboto'` names, nothing bundled, `theme.dart:36,78`). Shared Material 3 shell: `NavigationBar` with `AglAdBanner` directly above it, hidden on the profile tab (`lib/main.dart:237,253`). Splash is the shared storyboard (sha1 `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, measured today). The icon is three neon bars on a blue gradient with an "i" badge and pre-rounded dark corners (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png`, viewed). Generic hero copy "Find the Best Deals, Save More Every Day" (`lib/features/home/home_page.dart:132`). |
| Review notes | `fastlane/metadata/review_information/notes.txt:17` (committed at HEAD, verified with `git show HEAD:…`) says "Demo account: qa@safecodeg.com", a domain that is not ours. `store/apps/CodeDeal.json` says qa@americangroup.ai. The notes also use the shared "2. DEVICES…" skeleton, the simulator claim, and "Intended audience: Promo codes that work" (the subtitle pasted in). | file read today |

### Why Apple sees a template
1. **4.3(b): an opportunistic copy of a crowded category that cannot even do the copy.** RetailMeNot, PayPal Honey, Rakuten, Coupert and Capital One Shopping all serve feed-based promo codes. (Verified today: they exist on the US App Store, through the keyless iTunes Search API, e.g. `RetailMeNot: Rewards & Codes`, id521207075, 543,261 ratings.) CodeDeal has no feed, so it shows "Deals service unavailable".
2. **4.2.6 tells:** the shared splash, shell, banner position, sign-in family, neon Tailwind palette, generic hero copy, and a third-party domain in the review notes.
3. **2.1(a):** the reviewer's first screen was an error. Any build without a server always shows it.

## 2. User and product decision

**User:** an online shopper who **already receives** promo codes and loses them. They come in newsletter emails, order-confirmation "15% off your next order" footers, influencer posts and texts from friends. At checkout they cannot remember which code they have for this store, which one is still valid, or which gives the most off *this* cart. They are not hunting for new codes (that is RetailMeNot or Honey). They want to use the ones they already have.

**Core job (one, done well):** capture a code you received in seconds, and at checkout get **the best code you hold for this store and this cart total**, copied and ready to paste.

**Signature feature: "Checkout mode — best of *your* codes for this cart."**
- The user taps **At checkout**, picks the store (from their own stores) and types the cart subtotal.
- The app ranks every active code they hold for that store by **real saving on that subtotal**:
  - percent codes: `min(subtotal × p, cap)`
  - fixed-amount codes: the amount, only if `subtotal ≥ minimum spend`
  - free-shipping codes: listed as "Free shipping", with a number only if the user typed a shipping cost
  - expired codes, and codes the user marked "didn't work", are excluded and shown greyed below with the reason
- It shows **threshold nudges** from the user's own codes: "Add $7.50 to unlock $20 off (code from 3 Oct email)".
- One tap copies the top code. After copying, the app asks **"Did it work?"** (Worked, with an optional amount actually saved / Didn't work, with a reason: expired, minimum not met, not valid on these items, other). The answer is stored on the code, so a failing code drops out of checkout mode next time.
- Capture is **paste-first**. The user pastes the whole promo text (email paragraph, Instagram caption, SMS). A deterministic on-device parser proposes code, discount type and amount, minimum spend, cap, expiry date and store (from a URL or domain in the text). The user confirms or edits every field. Nothing is saved without that confirmation, and no field is ever guessed into existence: anything the parser did not find stays blank.
- Data: **100% on-device** (SQLite). No network call for app features, no Supabase, no account, no API. No keyless API is needed, so none was curl-verified for app data.

**Competitors (existence verified today with `curl https://itunes.apple.com/lookup?id=…`; descriptions read; none installed or used):**
- RetailMeNot, PayPal Honey, Rakuten, Coupert, Capital One Shopping: feed-based. They find public codes and cashback, not the codes a user received personally. The comparison is on the description only.
- Personal coupon wallets exist: **Snip It! Your Coupon Wallet** (id6788089941, released 2026-07-22, 0 ratings: camera scan, expiry reminders, savings total, store credit), **CouponCrowd – Coupon Wallet** (id6751547665: photo/email/link capture, reminders, community codes), **RedeemCode: Promo Code Manager** (id6743789699: for developers distributing App Store codes, not shoppers).
- **The honest angle:** none of those App Store descriptions mention ranking your saved codes against a cart total, minimum-spend/cap-aware savings, unlock-threshold nudges, or a per-code worked/didn't-work record that removes dead codes from checkout. That is checkout mode. *Claim limited to their App Store descriptions as fetched 2026-10-12. Not verified by using the apps.* A plain "coupon wallet with reminders" would be 4.3(b) against Snip It and CouponCrowd, so **checkout mode is not optional**.

**Must not duplicate:**
- GroceryMatch: no grocery coupons, flyers or store circulars. CodeDeal is for codes typed into an online checkout.
- FashionFactory / GadgetNest: no price comparison, no product catalog, no retailer prices.
- MyCard: no card numbers, IDs, loyalty-card barcodes or biometric vault.
- MyFinance: no budgets, no spending ledger. "Saved so far" counts only amounts the user entered after "Worked".

---

## 3. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app). Each one is testable.

**M1. Core job end to end, no server anywhere (plan criteria 1, 5).**
- Delete the deals client and every screen that depends on it. That means `lib/core/network/trpc_client.dart`, `lib/core/api/providers.dart`, `lib/features/{home,deals,search,category,store,deal_detail,referral,notifications}/`, `lib/features/_shared/deal_card.dart`, and `ServiceUnavailablePanel`/`ApiErrorView`/`ErrorPanel` in `state_panels.dart`, plus their routes in `lib/main.dart:104-128`.
- Delete accounts. That means `lib/core/auth/` (`supabase_config.dart`, `auth_repository.dart`), `lib/features/auth/`, `lib/features/profile/`, `Supabase.initialize` (`lib/main.dart:64-69`), and from `pubspec.yaml`: `supabase_flutter`, `dio`, `flutter_secure_storage`, `speech_to_text`, `dynamic_color`, `cached_network_image`, `json_annotation`/`json_serializable`/`build_runner` if unused.
- Remove `NSMicrophoneUsageDescription` and `NSSpeechRecognitionUsageDescription` (`ios/Runner/Info.plist:29-32`) and the matching Android permissions.
- With no account there is nothing to delete, so 5.1.1(v) no longer applies. "Erase all codes on this device" (M5) is the replacement.
- Fresh install → wallet (empty state, M4) → **Add code** → paste text → confirm → the code appears in the wallet → **At checkout** → store + subtotal → ranked result → copy → "Did it work?" → answer stored. Every visible control does something real. No route, tile or setting is left without a working destination.
- Test: a widget test drives exactly that path on an in-memory database and asserts the stored outcome.

**M2. Signature feature: checkout mode (plan criterion 2).** A pure Dart `lib/domain/checkout_ranker.dart` implements the rules in section 2. A sibling `lib/domain/promo_parser.dart` extracts the fields below from pasted text, and returns *null* for anything not found:
- code candidates: 4–20 characters A–Z/0–9 with at least one letter, preferring tokens after "code", "use", "promo", "coupon" or "enter"; never common words such as HTTPS, ORDER or FREE alone
- `N% off`, `$N off`, "free shipping"
- minimum spend: "on orders over $N", "when you spend $N", "$N+"
- cap: "up to $N" after a percent
- expiry: "expires", "ends", "valid until", "through", each followed by a date in `Oct 31`, `October 31, 2026`, `10/31`, `31/10/2026` or ISO form, using the device locale's day/month order
- store: from the first URL or domain in the text

Tests: table-driven unit tests, at least 15 parser cases (including text with no code → null code, and two candidate codes → both offered) and at least 10 ranker cases (minimum not met, cap binding, tie, expired, failed, free shipping with and without a shipping cost, unlock nudge amount).

**M3. Depth: persistence, search/filter, share/export, reminders (plan criterion 3).**
- SQLite via `sqflite` (or `drift`). Tables: `codes` (id, store, code, kind, amount, min_spend, cap, expires_on, source_note, created_at, archived) and `outcomes` (code_id, at, worked, saved_amount, reason). Data survives relaunch (tested with a reopened database).
- Wallet search (store, code or note text) and filters: **Expiring in 7 days**, **Active**, **Used**, **Didn't work**, **Expired**. Default sort: soonest expiry first, then no-expiry codes.
- Share one code as plain text (`share_plus`, iPad popover anchored: reuse the anchor pattern from `deal_card.dart:24-37` before deleting that file). **Export all codes as CSV** through the share sheet.
- **Expiry reminder** with `flutter_local_notifications`, on-device only: a notification the day before `expires_on` at 9:00 local time. Permission is asked **only** when the user first switches "Remind me" on for a code, never at launch. If permission is denied, the toggle shows "Notifications are off in Settings" with a button to the system settings.
- "Saved so far" on the wallet header = the sum of `saved_amount` the user entered. It is hidden when there are none. No estimates.

**M4. Real empty, error and edge states.**
- Empty wallet: "No codes yet. Paste a promo email or type a code you received." and one button **Add code**. No carousel, no "Get started".
- Checkout mode with no codes for that store: "You have no codes for {store}." plus **Add one**.
- A parser that finds nothing keeps the text and opens manual entry with the code field focused.
- A database open failure shows a full-screen message with **Try again** and **Export what can be read**, never a blank screen. `main()` must still reach `runApp` (keep the existing best-effort pattern, `lib/main.dart:50-60`).
- There is no "offline" state because nothing uses the network (state this in a code comment). The app must work in airplane mode (asserted by the absence of any HTTP client in `pubspec.yaml`, see M7).

**M5. Own identity: template tells removed (plan criterion 4). Concrete choices:**
- **Colour:** light-first "carbon-copy ticket" look. Background `#F2F4FA` (cool paper), ink `#141B34`, primary/seed **`#2B3FCB`** (carbon-paper cobalt), expiring `#E8A317`, worked `#1F8A4C`, didn't-work `#C2362F`. A matching dark scheme generated from the same seed follows the system setting (`ThemeMode.system`). Remove `ThemeMode.dark`, `CodeDealColors` neon tokens and every A855F7/22D3EE/EC4899/34D399 literal. Remove `DynamicColorBuilder`, so wallpaper colour cannot override the brand.
- **Typography, bundled under `assets/fonts/` (no runtime download):** **Hanken Grotesk** (UI) and **Martian Mono** (every promo code, amount and date on a ticket). Both are SIL OFL fonts. The developer confirms the licence from each family's `OFL.txt` and commits it next to the font files. Neither font appears in any other AGL app's pubspec (`grep` of `*/pubspec.yaml` today: no match) or in any other spec under `specs/`.
- **Shape language:** each code is a ticket: a rounded rectangle with two semicircular notches and a dashed perforation line (`CustomClipper` + `CustomPainter`). The stub shows the expiry and the body shows the code. No `BorderRadius.circular(12)` cards.
- **Home layout:** a single wallet screen, no bottom `NavigationBar`, no tabs. Large title "Wallet", tickets grouped by store, a pinned **At checkout** button at the bottom, and **Add code** in the app bar. On iOS: `CupertinoSliverNavigationBar` large title, `CupertinoIcons`, `CupertinoActionSheet` for destructive confirmations, `CupertinoSwitch` for "Remind me". Material equivalents on Android.
- **Onboarding:** none beyond the empty state in M4, with no sign-in wall.
- **Settings:** a short sheet: Reminder time, Export CSV, Erase all codes on this device (confirmation), Privacy choices (only where UMP requires it: keep `AglConsent` logic and `test/ads_privacy_test.dart` cases), version. Delete the accent swatches, the GitHub release-notes link and the debug "Server" card.
- **Splash:** replace the shared `LaunchScreen.storyboard` with one whose background is `#2B3FCB`, with a centred white ticket-stub vector (not the app icon). Its sha1 must differ from `3f6a9b27d8…`. Android `launch_background.xml` uses the same colour.
- **Icon:** a new hand-built ticket stub with perforation in `#2B3FCB` on `#F2F4FA`, full-bleed square (no pre-rounded corners, no "i" badge, no Material glyph, not from `scripts/generate_app_icons.py`). Regenerate all iOS sizes and Android mipmaps.
- **Copy:** delete the hero "Find the Best Deals, Save More Every Day", "Welcome back", "Trending Deals", the `premiumAdFree` "Ad-free experience" key and every key with no remaining reader from all ARB files.
- **Ads:** no shell-anchored banner. If the founder keeps ads (founder_questions), there is one `AglAdBanner` as the last item of the wallet list scroll only, never on checkout mode, the add/confirm sheet or settings. `AglAds.onTransition()` is removed (there are no tabs to transition between). Adapt the `ads_privacy_test.dart` banner-placement cases to these rules.

**M6. Honest (plan criterion 5).**
- No seeded, sample or fixture codes anywhere in `lib/` or `assets/` (test fixtures stay in `test/`).
- No `--dart-define` that changes behaviour or content (e.g. `SCREENSHOT`, `API_BASE`). No remote config read. No region, date or reviewer detection beyond the UMP consent check.
- No string in `lib/` or the ARB files may contain "not connected", "unavailable", "coming soon", "in this build" or "not available yet". A test greps for these.

**M7. Proven (plan criterion 6).**
- `flutter analyze` clean, and `flutter test` all green.
- New tests cover M1–M6, including a `release_sanity_test.dart` case that fails if `pubspec.yaml` lists `dio`, `http`, `supabase_flutter` or `speech_to_text`, or if `Info.plist` contains a microphone or speech key.
- Tests that exercised deleted features (`trpc_client_test.dart`, `deals_query_test.dart`, `auth_session_test.dart`, and the deals/ServiceUnavailable cases in `boot_test`, `honest_states_test`, `navigation_test`, `accessibility_test`, `responsive_layout_test`, `foldable_layout_test`, `settings_persistence_test`, `widget_test`) are **rewritten for the wallet** where the property still applies (boot, accessibility labels, responsive/foldable layout, settings persistence). They are removed only with the feature they tested. The commit message lists every removed test file and why.
- Do not delete or skip a test to go green.
- `release_sanity_test.dart` infra checks stay.
- Commit path-limited (never `fastlane/`) and push to main.
- Launch the app on the iOS simulator, screenshot the empty wallet, add-code and checkout screens, and look at them (memory: "build it and look at it").

### SHOULD
- **S1. Capture from a screenshot:** on-device text recognition feeding the same parser. iOS: Apple Vision `VNRecognizeTextRequest` through a small method channel (works on the simulator). Android: `google_mlkit_text_recognition` (on-device, no key). If it is not finished, the button must not exist (no dead control).
- **S2. Paste detection:** when the app is opened and the clipboard looks like a promo code (iOS `UIPasteControl`-style user-initiated paste only, never silent clipboard reads), offer "Add this code?".
- **S3. Store-level history:** per store, the share of the user's codes that worked, from their own outcomes only.
- **S4. Translations:** ship only locales whose ARB files cover 100% of the new keys. Otherwise reduce `supportedLocales` to `en` and say so in the notes. Never list 19 locales with English screens again.
- **S5. Home-screen widget** listing codes expiring this week (iOS WidgetKit / Android Glance). Only if M1–M7 are done.

## 4. Data source
- **On-device only:** SQLite file in the app documents directory, local notifications scheduled on the device, clipboard read only on a user tap.
- **No** Supabase project use (CodeDeal stops using `smvvjivvlprjhzhoizym`), no keyless API, no paid API, no keys.
- The `web-app/` server and its 67 hard-coded "verified" codes must not be connected (section 1).
- Retained infrastructure: `agl_observability` (Crashlytics/Analytics/Performance, existing behaviour), `agl_ads` + UMP (only if ads are kept).

## 5. Store impact (proposals for store-compliance. **Not applied**: `store/apps/*.json`, fastlane metadata and `docs/` are owned by another workstream right now)

**Listing copy (`store/apps/CodeDeal.json` `copy.en`):**
- name: keep `CodeDeal`.
- subtitle: `Your best code at checkout` (26 characters).
- short_description (Play, max 80): `Keep the promo codes you get and know which one saves most on this cart.`
- description (proposal. It does not open with the app name and has no ALL-CAPS section skeleton): "Promo codes arrive everywhere: a newsletter, an order receipt, a friend's text. When you finally check out, you can't find them, or you don't know which one is worth the most. Paste the whole message and CodeDeal picks out the code, the discount, any minimum spend or cap, and the expiry date. You check each field before it is saved. At checkout, tell it the store and your subtotal. It ranks the codes you hold by what they actually take off that cart, tells you if a few dollars more would unlock a bigger one, and copies the best code in one tap. Mark whether it worked, and codes that failed stop being suggested. A reminder the day before a code expires is optional. Export everything as CSV whenever you like. There is no account: your codes stay on this phone. [Ads paragraph, if ads are kept, in the app's own words. It must say where ads appear (bottom of the wallet list only) and how to reach Privacy choices. The legal wording is a founder/Charter §6 decision.]"
- keywords: `promo code wallet,coupon code,discount code,checkout,voucher,expiry reminder,best coupon,savings`
- Remove the `_blocker` section once a build implementing M1 exists. Its premise (a deals backend) no longer applies.
- `differentiation` answers to rewrite: Q1–Q3 from section 2 of this spec, including the named wallet competitors and the checkout-mode difference, and the limit "based on their store descriptions". Q6: not a feature of GroceryMatch, FashionFactory, GadgetNest or MyCard, for the reasons under "Must not duplicate". Q7: infrastructure only (`agl_observability`, `agl_ads`), **and no longer Supabase**.

**Screenshots (iPhone 6.9", iPad 13", Play phone/tablet): retake all.** Today's 3 iPhone shots include "Deals service unavailable" and an empty search.
1. Checkout mode: store + subtotal, ranked codes, unlock nudge.
2. Wallet with tickets grouped by store, the expiring filter visible.
3. Paste → parsed fields being confirmed.
4. "Did it work?" sheet.
5. Empty wallet (honest first-run).

Capture from the release build with ads in their real state (not a `SCREENSHOT=true` build). The codes shown must be ones the capturer actually received (keep the source emails on file). Nothing is seeded into the binary.

**Review notes (`review_information.notes` and `fastlane/metadata/review_information/notes.txt`):**
- Delete the demo-account line entirely, including `qa@safecodeg.com` (`notes.txt:17`). There is no sign-in.
- Delete "Supabase" from external services.
- Drop the shared "2. DEVICES…" skeleton and the simulator/emulator sentence. State the physical device the build was actually launched on, or nothing.
- Write the audience from section 2 (not the subtitle).
- Give steps: "Tap Add code, paste any promotional text (sample for testing, not a real offer: `Use code SPRING20 for 20% off orders over $50, up to $15 off. Expires Dec 31.`), confirm, then tap At checkout, choose the store and enter 60."
- State: "no account, no network features, all data on device".

**Privacy label (`store/privacy/CodeDeal.json`):** remove `EMAIL_ADDRESS`, `NAME`, `USER_ID` (no account) and set `_derived_from.account` to false. Keep `DEVICE_ID`/`ADVERTISING_DATA` only if ads stay. `CRASH_DATA`, `PRODUCT_INTERACTION` and `PERFORMANCE_DATA` stay for `agl_observability`. CodeDeal then leaves the 13-app identical label group. The privacy-policy wording is founder (Charter §6).

**Category:** keep SHOPPING. Age rating unchanged (no user-generated content shared publicly, no web view).

## 6. Out of scope
- Any code feed, scraping, affiliate links, cashback, a community-shared code database, or the `web-app/` server.
- Accounts, cloud sync, Supabase, email forwarding, a share extension (S1/S2 are the capture extensions allowed).
- Grocery coupons, store flyers, price comparison, product catalogs, gift-card or store-credit balances, loyalty-card barcodes.
- Paywall or in-app purchase (Charter §3).
- Editing `store/apps/*.json`, fastlane metadata, `docs/`, replying to Apple, submitting or uploading for review (Charter §1, 5.6 freeze MA-043).

---

## 7. Developer notes (software-developer, 2026-10-12, commit `cf94a3b`): store impact to apply, and what is still blocked

Not applied to `store/`, fastlane or `docs/` (owned by another workstream).

- **Review notes, add:** "The app is in English only (supportedLocales = en)." (S4: the other 18 ARB files do not cover the wallet's text.) "Ads: one banner at the end of the wallet list, nowhere else; Privacy choices is in Settings where UMP requires it."
- **Screenshots:** `integration_test/store_screenshots_test.dart` now captures only honest fresh-install screens (empty wallet, Add code, Settings) and fails if the device already has codes. The shots that show codes (checkout ranking, tickets, parsed fields, "Did it work?") must be taken by hand with codes the capturer actually received, as section 5 says.
- **Blocked, needs the founder:** the legacy deals client is still in the repo but unreachable from `lib/main.dart`. That means the tRPC screens, Supabase sign-in, voice search, `core/theme.dart` and the old settings page; `test/honesty_test.dart` pins all 18 files. A guardrail stopped the deletion because the user had not explicitly asked for it. Until it is approved, these stay too: `dio`, `supabase_flutter`, `speech_to_text`, `dynamic_color`, `go_router`, `url_launcher`, `flutter_secure_storage`, `cached_network_image` and `json_*` in pubspec, and `NSMicrophoneUsageDescription`/`NSSpeechRecognitionUsageDescription` in Info.plist. Because those packages stay, the M7 `release_sanity` check (fail if pubspec lists dio/http/supabase_flutter/speech_to_text or Info.plist has mic/speech keys) was not added: it would fail today. Once deletion is approved, the follow-up is mechanical: delete those files and `test/support/legacy_app.dart` with the legacy tests (`trpc_client_test`, `deals_query_test`, `auth_session_test`, `navigation_test`, `boot_test`, `honest_states_test`, `accessibility_test`, `responsive_layout_test`, `foldable_layout_test`, `settings_persistence_test`, and the legacy groups of `ads_privacy_test`). Then drop the packages and keys, empty `_legacyPendingDeletion`, and add the `release_sanity` case.
