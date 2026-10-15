# Spec: ChefCount becomes "cook it before it goes off"

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/ChefCount`, branch `main`, base_sha `0be1fd1f0e33b967ee527597828b52b24ef7f19d` (`git rev-parse HEAD`, run today)
- Apple: rejected under **5.6** on 2026-10-08T14:19:32Z (`/Users/spatchava/agl/.dist/rejections.json` key `ChefCount`, 1 thread). It is the same 5.6 text that went to 16 apps within one minute, and it names no feature. Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:38` (G6, ChefCount vs GroceryMatch). **ChefCount owns "cook from what you have".** GroceryMatch owns the shopping trip: the list, nearby stores and Nutri-Score.
- Baseline, measured today in the repo: `flutter analyze` gave "No issues found! (ran in 17.7s)". `flutter test` gave "+134: All tests passed!".

**Other people have uncommitted work in this repo. Leave it alone.** `git status --short` today shows `fastlane/**` modified: 16 screenshots, `fastlane/metadata/review_information/notes.txt`, and 4 untracked `*-05.png`. `ios/Podfile.lock` is modified too. None of the files this spec changes has uncommitted edits right now: `lib/`, `test/`, `integration_test/`, `pubspec.yaml`, `assets/`, `ios/Runner/Info.plist`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets`, `ios/Runner/PrivacyInfo.xcprivacy`, `android/app/src/main/**`. If that changes before you start, stop and report it. Never `git add -A`.

---

## 1. Problem

### What the app is today (I read all of `lib/`: `main.dart` 1937 lines, `domain/` 911 lines, `photo_note.dart` 64 lines)

| Area | State | Evidence |
|---|---|---|
| Kitchen inventory | **Real, thin.** Items have a quantity, a unit, an optional use-by date and a category. They persist as JSON in SharedPreferences under `chefcount.inventory.v1`. The load error is real and has a retry, and writes are refused while the saved data is unreadable. **No edit UI:** an item can only be removed with an X. `InventoryController.update` exists but nothing calls it. No search or sort in the Kitchen tab. | `lib/domain/inventory_store.dart:19-172`, `lib/main.dart:1512-1767` (X button at 1758-1762) |
| Ingredient picker | Real. 35 bundled staples, prefix-first search, add a custom name, and a use-by date pre-filled from `typicalShelfLifeDays`, labelled "Suggested … Check the package". | `lib/domain/catalogue.dart:14-50,62-77`, `lib/main.dart:380-984` |
| Recipe matching | **Real, shallow.** It checks presence only: "a kitchen holding one egg still 'has' eggs". It ignores use-by dates completely, so the ranking never helps the user use food before it goes off. | `lib/domain/recipe_matcher.dart:4-10,26-34` |
| Recipe catalogue | **12 recipes**, ported from the old React Native app, with no structured amounts. Four categories are offered in the filter, and `dessert` exists in the enum but has no recipe. | `lib/domain/catalogue.dart:79-383`, `lib/main.dart:1003` |
| "Use soon" | One red text banner listing names due within 3 days. It is not linked to any recipe. | `lib/main.dart:1629-1654`, `recipe_matcher.dart:39-50` |
| Fridge photo note | **Vestigial.** One photo, "nothing reads it", and the copy is mostly disclaimers. It is a leftover of the fake fridge-OCR scan that was deleted on 2026-09-15 (`store/apps/ChefCount.json` `_was_blocked_resolved`). It costs a camera and photo-library permission for no job. | `lib/photo_note.dart:1-64`, `lib/main.dart:676-757`, `ios/Runner/Info.plist:33-36` |
| Recipe detail | Ingredients you have / need, steps, and Amazon affiliate search links for missing groceries and tools, with the disclosure shown on screen. No share, no "I cooked this", no way to record anything. | `lib/main.dart:1210-1508` |
| Profile tab | **Filler.** A chef emoji plus three counters (ingredients / ready / 12 recipes) and the region-conditional Privacy choices row. | `lib/main.dart:1771-1882` |
| History / analytics of own use | **None.** Nothing records what was cooked, used up or thrown away. | no such code in `lib/` |
| Identity | **Template.** `class C` palette monolith (`lib/main.dart:45-58`) with Tailwind red-500 `EF4444` (`:54`). Dark-only `ThemeData`, `fromSeed(orange FF6B35)` (`:156-164`). The orange `FF6B35` is also TripNest's brand (diagnosis: EventSpark vs TripNest). System font. Four equal emoji tabs plus `AglAdBanner` in the shell just above them (`:241-242`). Generator icon `restaurant_menu` #BF360C→#FF7043 (`agl-manifest/scripts/generate_app_icons.py:67`). Shared splash (`LaunchScreen.storyboard` sha1 `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, re-measured today). Home-screen name `Chefcount` (`ios/Runner/Info.plist:10`), Android `chefcount` (`AndroidManifest.xml:3`). |
| Ads | Shell banner (`lib/main.dart:241`). Interstitial on tab change (`:203-207`), which `agl_ads` suppresses for the first 2 transitions and caps at one every 3 minutes (`packages/agl_ads/lib/src/ads.dart:24-26,145`). |
| Network / backend | None for the core job. No Supabase and no HTTP client in `pubspec.yaml`. Only AdMob, Crashlytics and outbound Amazon links. No `AglInsights`/Remote Config (`lib/main.dart:28` comment; grep of `lib/` today found no `RemoteConfig`, `kReleaseMode` branching, date or locale checks). |

### What Apple saw (the submitted screenshots)
I extracted `fastlane/screenshots/en-US/iphone69-01..04.png` **at HEAD** and looked at them: 01 is the Add picker, 02 is Recipes with every card "0/6, 0/5 … ingredients in your kitchen", 03 is "Kitchen is empty", and 04 is Profile with "0 Ingredients · 0 Ready to cook · 12 Recipes". **The listing never shows the core job working.** (Someone else's uncommitted re-capture is in the working tree. I did not use it or judge it.)

### Why Apple would see a template or hidden features
1. **4.3 / 4.2.6 look.** This is the portfolio-wide scaffold: `class C`, dark plus neon accent, emoji tab bar with the ad banner above it, generated glyph icon, shared splash, flutter-create display name, stock Material on iPhone. With only 12 recipes and presence-only matching, it is "indistinguishable from what's already widely available". SuperCook already does presence matching against a large recipe set (section 2).
2. **5.6 candidates in this binary and listing.** None is confirmed as the cause, because Apple named no feature.
   - **The ads behave differently in a short session.** The listing says "now and then, a full-screen ad when you switch tabs", but the first 2 tab changes never show one and a 3-minute cap follows (`ads.dart:24-26,145`). A reviewer can easily finish without seeing the ad the listing describes.
   - **Store screenshots come from builds that never load ads** (`--dart-define=SCREENSHOT=true`, `ads.dart:38-44`).
   - **Region-conditional UI:** the Privacy choices row renders only when UMP says it is required (`lib/main.dart:1909-1912`).
   - **History:** the app shipped a fake fridge "scan" that hashed the file name (`store/apps/ChefCount.json` `_was_blocked_resolved.previous.evidence`). Commit `2b0082c` (2026-10-09) says its screenshots were "signed in with the QA account", in an app that has no sign-in. Apple may still associate the bundle with the old behaviour. **Not verified.**
3. **The copy tells against itself.** The description spends a section on what the photo does *not* do. The review notes give "Intended audience: Kitchen stock and recipes", which is the subtitle pasted in.

## 2. User and product decision

**User:** a person who cooks at home most weeknights for 1 to 4 people. They buy food in a weekly shop and regularly throw away spinach, cream, chicken or berries because they forgot them. At 6 pm they open the fridge and ask: *what can I make tonight that uses up what's about to go off?*

**Core job (one, done well):** keep an honest list of what is in the kitchen with use-by dates, and every evening answer "what should I cook tonight" **ordered by what needs using first**. When the user cooks, the kitchen updates itself.

**Signature feature: "Use It Up". Recipes ranked by what expires first, cooked with a swap, and a record of what you saved.**
1. **Rescue ranking.** Each recipe gets a *rescue score* from the held ingredients it uses, weighted by days left: due today 5, 1 day 4, 2 days 3, 3 days 2, 4 to 7 days 1, otherwise 0. Expired items score 0 and get a "check it first" badge. They are never recommended silently. "Tonight" lists recipes that are cookable now (or with one swap), sorted by rescue score, then match %. Each card shows the chips of the at-risk items it uses, e.g. "uses Spinach (today), Heavy Cream (2 days)".
2. **Cook with a swap.** A bundled, on-device substitution table, e.g. Heavy Cream ← Milk + Butter, Lemon ← Lime / White Wine Vinegar, Spaghetti ← any long pasta, Parmesan ← Pecorino / Cheddar, Greek Yogurt ← Sour Cream, Sourdough ← any bread, Fresh Basil ← Dried Basil. A recipe that misses ingredients but has a held swap for each of them, at most 1 swap, shows "Cook with a swap: Milk + Butter for Heavy Cream". Each swap row carries the label "Kitchen rule of thumb". Every swap is authored in-house and has a test.
3. **"I cooked this."** On a recipe, one button opens a sheet listing each held ingredient the recipe uses, pre-filled with the recipe's amount scaled by servings. The user adjusts amounts or taps "Used it all", and confirms. The kitchen deducts the amounts (an item at 0 is removed), and a *cook event* is saved: recipe, date, servings, items used, and which of them were within 3 days of their date.
4. **Saved vs binned.** Removing an item asks "Used it", "Binned it" or "Just remove", with "Just remove" for mistakes. Together with the cook events this gives a month view on the Kitchen screen: "October: 14 items used before their date · 2 binned". These are the user's own counts. No money values, no CO₂ figures, no national averages.

**Why it is distinct (competitors checked today via the keyless iTunes Search/Lookup API, `itunes.apple.com/lookup?id=…`. These are the apps' own App Store descriptions, not hands-on tests):**
- **SuperCook – Recipe By Ingredient** (AMR Systems LLC, id1477747816, 4.8★ / 21,802 ratings): "SuperCook only shows you recipes that require the ingredients you already have." Its description mentions expiry only in a rhetorical question and describes **no use-by tracking or expiry-first ranking**.
- **NoWaste: Food Inventory List** (KH Creations ApS, id926211004): inventory with "Expiration date tracking with reminders", plus "Recipes, shopping lists and meal plans". Its description describes **no recipe ranking by what expires first, and no deduction on cooking**.
- **Pantry & Fridge: FridgeBuddy** (id1500190823): inventory, barcode scanning via Open Food Facts, and reminders. Its description lists no recipes.
- ChefCount's honest angle is the join between the two halves: **expiry-first recipe ranking, swaps, and a kitchen that updates when you cook**. All of it is offline, with no account. I make no claim that competitors "can't" do this. The store copy (section 5) describes only what ChefCount does.

**Data: 100% on-device.** No Supabase, no API, no keys. I checked TheMealDB as a recipe source today: `curl https://www.themealdb.com/api.php` says "You can use the test API key "1" during development … However you must become a supporter if releasing publicly on an appstore." That is a paid production key (Charter §3), so it is **not used**. I tried the USDA FoodKeeper JSON (`fsis.usda.gov/shared/data/EN/foodkeeper.json`) and got HTTP 403 from this machine. It is **not verified** and is not required (see S3).

**Lane boundary with GroceryMatch (MUST NOT):** no shopping list, no "add missing to list", no store finder, no prices, no Nutri-Score, no barcode lookup.

---

## 3. Acceptance criteria

### MUST: what Apple needs to see a real, distinct app. Each one is testable.

**M1. Core job end to end on a fresh install (plan criterion 1).**
First-run quick-stock (M5) → "Tonight" shows real ranked results → open a recipe → "I cooked this" → the kitchen deducts → Kitchen shows the change and the month tally. On a Kitchen item, tapping the row opens an **edit sheet** (quantity, unit, use-by, "Used it / Binned it / Just remove"). This wires up `InventoryController.update`. Every visible control does something. Remove the Profile tab and its three counters. The Fridge photo note is removed: `lib/photo_note.dart`, the `image_picker` and `path_provider` dependencies, `NSCameraUsageDescription` and `NSPhotoLibraryUsageDescription` (`Info.plist:33-36`), and any camera permission in `AndroidManifest.xml`. On upgrade, delete the old `fridge_note.jpg` from the documents directory and the `chefcount.fridge_photo_path` key.

**M2. Signature feature "Use It Up" (criterion 2).** Implement items 1 to 4 of section 2 in pure Dart under `lib/domain/` (`rescue.dart`, `swaps.dart`, `cook_log.dart`), with no Flutter imports, so unit tests cover them.
- `Recipe` gains `List<RecipeIngredient>` with `name`, `amount`, `unit` (from `kUnits`) and `optional`. Deduction converts only within a fixed table (tsp↔tbsp↔cups↔ml; g↔oz↔lb). When units don't convert, the sheet pre-fills nothing and offers "Some" / "All of it" / a number in the item's own unit. It never guesses a conversion.
- Rescue score, swap eligibility and deduction are deterministic and need no network.

**M3. Real catalogue depth.** At least **36 bundled recipes** (now 12), at least 4 in every category the filter shows, including Dessert (the enum value already exists). Each has structured amounts, servings, honest times, and steps written for this app. Do not copy text from websites or cookbooks. Calories: keep the existing 12 values only if the developer can state their source, otherwise drop the calorie field everywhere. Do not invent new calorie numbers. Every recipe ingredient must exist in `ingredientCatalogue` (extend it as needed). The existing test that every recipe is reachable from the picker keeps passing.
- **"Your recipes":** the user can add their own recipe (title, servings, ingredients picked from the catalogue or custom, steps). It is persisted, matched and rescue-ranked like a bundled one, and can be edited and deleted.

**M4. Depth (criterion 3).**
- **Persistence:** inventory (existing key, migrated in place), cook events, removal outcomes, user recipes, favourites (a heart on a recipe) and onboarding-done. Store them in SharedPreferences JSON with versioned keys `chefcount.cooklog.v1`, `chefcount.recipes.v1`, and so on, using the same corrupt-data rules as `decodeInventory` (`inventory_store.dart:60-82`): a bad entry drops only that entry.
- **Search / filter / sort:** Kitchen gets a search field, category chips, and sort by use-by / name / recently added. Recipes get a search over title and ingredient, chips (All · Breakfast · Lunch · Dinner · Snack · Dessert · Favourites · Mine), and a toggle "Cookable now".
- **Share:** "Share recipe" sends plain text (title, ingredients with amounts, steps) through the system share sheet (`share_plus`, keyless). No kitchen-list export, because that edges into a shopping list.
- **States:** a first-run state (M5). Tonight with an empty kitchen says "Add what's in your kitchen to see what you can cook" and offers one button. Tonight with nothing cookable shows the 3 closest recipes with what each is missing, and never an empty screen. Nothing due soon reads "Nothing needs using up this week". The existing load-error/retry state stays and extends to the new stores. Share failure gets a snackbar. The app makes no network calls for its job, so there is no offline state. Say that in a code comment, not on screen.

**M5. Own identity, not the shared scaffold (criterion 4).** Use these values exactly:
- **Palette "cookbook".** Light is the default and follows the system. Background crème `#FBF7EF`, surface `#FFFFFF`, ink `#2B2622`, secondary text `#6E655B`, hairline `#E4DBCB`, primary aubergine `#5C2A4D`, "use soon" saffron `#E6B04A` as a badge fill with ink text (as text on crème use `#8A5D0A`), "expired" tomato `#B83A26`, "cookable" herb `#4F7A3A`. Dark: background `#1C1A17`, surface `#262320`, text `#F1EBE0`, primary `#D9A3C8`, saffron `#E6B04A`, tomato `#E07A62`, herb `#A8C98F`. Build an explicit `ColorScheme`, not `fromSeed`. Contrast I computed (WCAG): aubergine on crème 10.38:1, ink on crème 14.01:1, `#8A5D0A` on crème 5.38:1, tomato on crème 5.35:1, herb on crème 4.70:1, dark text on dark bg 14.63:1. A grep for every one of these hexes over `*.dart` and `*.md` in `/Users/spatchava/agl` today found 0 files. The palette is deliberately not green-led, so it does not read as GroceryMatch (primary `#1B4332`, `GroceryMatch/lib/core/theme/app_colors.dart:5`), and not orange (TripNest/old ChefCount `FF6B35`).
- **Typography:** bundle **Young Serif** (`YoungSerif-Regular.ttf`) for screen titles, recipe titles and the month tally, and **Figtree** (`Figtree[wght].ttf`, variable) for everything else. Use tabular figures for quantities and day counts. Both are SIL OFL in `github.com/google/fonts` `ofl/youngserif` and `ofl/figtree`. I listed both directories with `gh api` today. Ship `OFL.txt` under `assets/fonts/` and register it with `LicenseRegistry`. A grep today found neither font in any app under `/Users/spatchava/agl` or in any other real-apps spec (Fraunces and IBM Plex are already taken by other specs).
- **Shape language:** recipe cards are drawn like index cards: an 8 px radius, a 1 px hairline border and a thin aubergine rule under the title. No filled 12 px dark blobs. Use-by is shown as a **day-count pill** ("2d", "today", "expired"), saffron or tomato. No emoji in the chrome (tab bar, headers). Emoji may stay as ingredient markers in lists.
- **Home layout, "Tonight"** (replaces the 4 emoji tabs): a large-title "Tonight" with today's date. (a) A horizontal **"Use soon" shelf** of item pills, soonest first, each tappable to edit. (b) **"Cook tonight"**: the top rescue-ranked recipes with their at-risk chips and a "Cook with a swap" tag where it applies. (c) A compact **"Your kitchen"** card (item count, n due this week, this month's used/binned tally) that opens Kitchen. A floating **Add** button opens the picker. Navigation: 3 destinations, **Tonight · Kitchen · Recipes**, and Settings behind a gear icon in the Tonight bar. **On iOS**, use `CupertinoTabScaffold`/`CupertinoTabBar` with `CupertinoIcons`, `CupertinoSliverNavigationBar` large titles, and `CupertinoActionSheet` for the Used/Binned/Remove choice. Android uses Material 3 equivalents with the same palette.
- **Code structure:** split `lib/main.dart` into `lib/app/` (theme, shell) and `lib/features/tonight|kitchen|recipes|add|settings/`. **No `class C`.**
- **Onboarding (first run only), job-specific:** title "What's in your kitchen right now?", with a 4-column grid of 24 common staples from the catalogue. Tapping one adds it with its suggested date. A primary button "Show me what I can cook" goes to Tonight. A text button reads "I'll add things later". Do not use "Get started", "Welcome" or marketing copy.
- **Settings (own screen, own copy):** Swaps I never want (turn individual swaps off) · Default use-by suggestions on/off · Language (shared `AglLanguageScreen` may stay; today the app is English-only, `lib/main.dart:133`) · Privacy choices · Privacy policy · About (version, font licences, "Recipes and swaps are written for ChefCount").

**M6. Remove this app's template tells (criterion 4).**
- **New icon, not from the generator:** a crème `#FBF7EF` skillet seen from above, with a saffron `#E6B04A` three-quarter countdown arc inside the pan, on a flat aubergine `#5C2A4D` square. Draw it as vector geometry, with no Material glyph and no gradient. Regenerate every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset` and every `android/app/src/main/res/mipmap-*` size, plus the adaptive foreground and background. Delete the `"ChefCount"` entry at `agl-manifest/scripts/generate_app_icons.py:67` so a re-run cannot overwrite it (scripts/ is not on the do-not-edit list).
- **Own launch screen:** `LaunchScreen.storyboard` with background crème `#FBF7EF` and the skillet mark (dark variant `#1C1A17`), plus a new `LaunchImage`. Its sha1 must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- `CFBundleDisplayName` = `ChefCount` (`Info.plist:10`) and `android:label="ChefCount"` (`AndroidManifest.xml:3`). Also update the `pubspec.yaml` description and delete the flutter-create comment boilerplate.
- No Tailwind default hexes in `lib/` (`EF4444` today, plus the usual set `F59E0B 10B981 3B82F6 8B5CF6 06B6D4 EC4899`). No dark-only theme.
- **Ad slot out of the shell:** `AglAdBanner` no longer sits between the content and the tab bar. Proposal, pending founder question 2: one banner placed as a separated, labelled row at the end of the Recipes list and of the Kitchen list. Never on Tonight's first screenful, onboarding or the cook sheet.

**M7. Honest, and nothing that could read as hidden (criterion 5, Apple 5.6).**
- Real data only: the user's own entries, bundled recipes/swaps/staples authored for the app, and their own cook/bin history. No sample kitchen, no demo stats, no invented calories, prices, "money saved" or CO₂. The existing "never claims to recognise anything" test (`test/widget_test.dart:433-480`) keeps its banned-word grep across all new screens.
- **Privacy choices is always visible** in Settings. Where UMP requires it, it opens Google's form (`AglConsent.showPrivacyOptions`). Elsewhere it opens a short sheet that explains the ads in this region, in wording checked against what `packages/agl_ads` actually does. The two tests that assert the row is *hidden* (`test/widget_test.dart:390,420`) are **replaced** by tests asserting it is present in both consent states. Say in the commit message that this is an intended behaviour change, not a deleted test.
- **Interstitial:** the tab-switch interstitial (`lib/main.dart:203-207`) goes in the new layout. Pending founder question 2, either there is none, or there is one only after a completed "I cooked this", with **no warm-up suppression**, so a reviewer sees exactly what a user sees. The store copy and review notes must describe the final behaviour exactly.
- No demo login, no remote switches (add a test that greps `lib/` for `AglInsights`, `RemoteConfig`, `kReleaseMode`/`kDebugMode` feature branches, `Platform.localeName`, and date-gated `DateTime(20`, and fails on any hit outside an allow-list), no hidden gestures, no long-press-only actions, no debug menus. Every feature is reachable in 2 taps or fewer from Tonight.
- Copy states what the app does in positive terms. Drop the disclaimer paragraphs (the fridge-photo "does not analyse…" text goes with the feature).

**M8. Proven (criterion 6).** `flutter analyze` clean. Every test passes. No test skipped. The only replaced tests are the two Privacy-choices assertions (M7) and the photo-note test `widget_test.dart:477` (its feature is removed in M1). Name all three in the commit message. New tests, at least:
- `test/rescue_test.dart`: score weights per day band. Expired items score 0 and get flagged. Ties fall back to match % and then catalogue order. A recipe using a due-today item outranks one using only long-life items.
- `test/swaps_test.dart`: each swap rule. At most 1 swap per recipe. Swaps the user disabled in Settings are ignored. Swap candidates must be held.
- `test/cook_log_test.dart`: deduction with matching and convertible units (3 tbsp from 1 cup leaves 0.8125 cups, displayed as "0.81"). Non-convertible units never auto-deduct. An item reaching 0 is removed. The event records rescued items (≤3 days). Month tally counts used vs binned only from real events.
- `test/catalogue_test.dart`: ≥36 recipes, ≥4 per filter category, every ingredient in the catalogue, every amount uses a `kUnits` unit, no duplicate ids.
- `test/persistence_test.dart`: cook log, removal outcomes, user recipes and favourites survive reload. Corrupt entries are dropped one by one. The v1 inventory still loads. The old photo-note file and key are cleaned up.
- Widget tests: onboarding shows once and its taps stock the kitchen. Tonight orders by rescue score and shows at-risk chips. "I cooked this" deducts and updates the tally. The edit sheet changes quantity and date. Kitchen search, chips and sort work. Recipe search, chips and "Cookable now" work. A user recipe can be added, matched and deleted. Share hands the expected text to an injected sharer.
- `test/identity_test.dart`: no `class C`. None of the listed Tailwind hexes. Young Serif and Figtree declared and present on disk. Light and dark themes defined. LaunchScreen sha1 differs from the shared one. `CFBundleDisplayName == 'ChefCount'`. No `AglAdBanner` inside the shell `Column` above the navigation bar.
- `integration_test/store_screenshots_test.dart`: update it so it stocks the kitchen through onboarding and the edit sheet (with real dates relative to "today"), cooks one recipe, then captures the 5 screens in section 5.
- **Launch it and look at it:** build for the iOS simulator (iPhone and iPad) and the Android emulator, and screenshot Tonight, a recipe with a swap, the cook sheet, Kitchen and Settings, in light and dark. Green tests do not prove the screens render.
- Commit path-limited (`git add lib test integration_test pubspec.yaml pubspec.lock assets ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets ios/Runner/PrivacyInfo.xcprivacy android/app/src/main`, and the generator script in agl-manifest separately). Never `fastlane/` or `ios/Podfile.lock`. Push to `main`.

**M9. Store impact written down (criterion 7):** section 5. store-compliance applies it. The office does not submit (5.6 freeze, MA-043).

### SHOULD (valuable, not required for resubmission)
- **S1. Use-by reminders:** one local notification at a time the user picks (default 17:00) listing items due tomorrow, via `flutter_local_notifications`, on-device. Ask permission only when the user turns it on in Settings.
- **S2. "Enough?" check:** where units convert, mark a held ingredient "you have less than the recipe needs" instead of presence-only.
- **S3. Sourced shelf-life suggestions:** replace the in-house `typicalShelfLifeDays` with USDA FoodKeeper values, bundled with attribution, but only after a developer downloads the dataset and confirms its terms. It returned 403 from this machine today (not verified).
- **S4. Leftovers as items:** "I cooked this" can add "Leftovers: <recipe>" to the kitchen with a 3-day use-by.
- **S5.** Translate the new strings into the shared locales and only then declare them (today `kSupportedLocales` is English only, `lib/main.dart:133`).

---

## 4. Data source
- **Kitchen, cook log, removal outcomes, user recipes, favourites, settings:** on-device SharedPreferences JSON (versioned keys). Never uploaded. Deleted with the app.
- **Recipes, swaps, staples, suggested shelf lives:** bundled Dart constants authored for ChefCount, shipped in the binary. No download.
- **No Supabase, no public API, no keys.** TheMealDB was rejected: an app-store release needs a paid supporter key (quoted in section 2). Open Food Facts barcode lookup was rejected because it belongs to GroceryMatch's lane (Nutri-Score, scanning).
- **Off-device, unchanged and already disclosed:** Google AdMob (consent via UMP) and Firebase Crashlytics (crash reports only). Outbound Amazon affiliate search links stay on the recipe detail screen with the visible disclosure (`lib/main.dart:1212-1226`), pending founder question 3.

## 5. Store impact (proposals only. I edited nothing under `store/apps/`, `fastlane/` or `docs/`)

**Name:** ChefCount (unchanged). Home-screen name becomes `ChefCount` (M6).
**Subtitle (≤30):** "Cook it before it goes off" (26 chars).
**Promotional text (≤170):** "See what your kitchen can cook tonight, starting with what expires first. Swaps for a missing ingredient. Works offline, no account." (132)
**Play short description (≤80):** "Your kitchen sorted by use-by date, and the recipes that use it up tonight." (75)
**Keywords (≤100):** `pantry,use by,expiry,leftovers,recipes,what to cook,food waste,fridge,ingredients,substitutes,meal` (98)

**Description (proposed. It does not open with the app name, uses no ALL-CAPS section skeleton, and does not repeat the portfolio's shared ads paragraph word for word):**
> The spinach is due tomorrow, there's half a carton of cream, and it's 6 pm. Tell ChefCount what's in your kitchen and it puts tonight's recipes in order of what needs using first.
>
> Tonight. A shelf of what's about to go off, and the recipes that use the most of it. Every card shows which at-risk items it uses.
>
> Cook with a swap. Missing heavy cream but have milk and butter? Recipes that work with one simple swap are marked, and every swap is listed on the recipe.
>
> I cooked this. Tap it when you're done and your kitchen updates itself: the amounts the recipe used come off your list.
>
> Used, not binned. When you take something off the list, say whether you used it or threw it away. Each month shows your own tally of food used before its date.
>
> Your recipes too. Add the dishes you actually make, and they're ranked alongside the 36+ recipes written for ChefCount. Search, filter by meal, keep favourites, and share any recipe as text.
>
> Everything stays on your phone: no account, no sign-in, and it works offline. ChefCount is free and shows Google AdMob ads [store-compliance: describe the final placement from founder question 2 exactly]; where the law requires consent, Google asks first, and Settings → Privacy choices is always there. Crash reports go to Firebase Crashlytics so bugs can be fixed. Some recipe pages link to Amazon searches for tools and ingredients; these are affiliate links and the page says so.

(store-compliance must check the ads and affiliate sentences against the shipped build before using them. Delete the affiliate sentence if founder question 3 removes the links.)

**Screenshots: retake all 5 from the release build with a kitchen stocked through the app (integration test, M8). iPhone 6.9", iPad 13", Play phone and tablet:**
1. Tonight: the Use soon shelf (today / 1d / 2d pills) and "Cook tonight" cards with at-risk chips.
2. Recipe detail with "Cook with a swap: Milk + Butter for Heavy Cream".
3. The "I cooked this" sheet with amounts pre-filled.
4. Kitchen: search, category chips, day-count pills, and the month tally "used before their date · binned".
5. Recipes: filter chips, including "Mine", and a user-added recipe in the list.
The current set (HEAD: empty kitchen, "0/6" cards, empty Kitchen, all-zero Profile) must not be reused. The 5 new shots must each show a different screen, which fixes the near-duplicate pair. Founder question 4 covers whether the listing shows the ad slot.

**Play feature graphic:** rebuild from the new skillet mark, palette and Young Serif wordmark. The current `fastlane/metadata/android/en-US/images/featureGraphic.png` shows the Flutter logo (portfolio diagnosis).

**Review notes (proposed, bespoke. Replaces the shared "2. DEVICES…" skeleton):**
> ChefCount is a kitchen inventory with use-by dates that ranks recipes by what needs using first.
> To try it: on first launch tap a few staples (for example Spinach, Eggs, Heavy Cream, Butter, Parmesan Cheese), then "Show me what I can cook". Tonight lists recipes that use the items closest to their date. Open one → "I cooked this" → Confirm, and the Kitchen tab shows the amounts removed and the month tally. Recipes → + adds your own recipe.
> No account or login. Everything is on the device and works offline. Every feature is reachable from the first screen. Nothing is controlled by a server, by region, by date or by build type. The only regional difference is Google's ads consent form (EEA/UK/CH). Settings → Privacy choices is visible everywhere.
> Ads: [final placement and frequency from founder question 2, stated exactly, with no warm-up exceptions].
> Tested on: [QA fills in the physical iPhone/iPad models and iOS versions actually used. Do not list simulators as devices.]
> Contact: [a real named person, founder question 5].

**Privacy (App Store label / Play data safety):** after M1 the app no longer accesses the camera or the photo library, so remove both usage strings and any matching declarations. The data collected stays the same: crash data via Crashlytics, and device identifiers for AdMob as already declared. store-compliance should answer ChefCount's label on its own instead of reusing the 20-app identical label. Any privacy-policy wording change is a founder decision (Charter §6).

**Category:** FOOD_AND_DRINK (unchanged).

## 6. Out of scope
- Shopping lists, "add missing to list", store finder, prices, Nutri-Score, barcode or receipt scanning. These are GroceryMatch's lane or need data we don't have.
- Photo, camera or "AI" recognition of fridge contents, in any form.
- Meal planning calendars, nutrition tracking, calorie goals, diets.
- Remote recipe feeds (TheMealDB needs a paid key), accounts, sync, household sharing, Supabase tables.
- Money-saved, CO₂ or "average household" waste figures. We have no source.
- Editing `store/apps/ChefCount.json`, fastlane metadata or `docs/`. Uploading, submitting or replying to Apple.

## 7. Founder questions
1. **Keep ChefCount separate (recommended) or have GroceryMatch absorb it?** (Charter §8. Overlap G6.) This spec assumes it stays separate, and GroceryMatch drops its pantry stock levels and meal planner.
2. **Ads (Charter §3, revenue):** approve moving the banner out of the shell into one in-list row on Recipes and Kitchen, and removing the tab-change interstitial. The alternative is one interstitial only after "I cooked this", **without** the shared warm-up suppression (`agl_ads` `warmupTransitions = 2`). The warm-up means a short review session sees different ad behaviour from the listing, which is a 5.6 risk.
3. **Amazon affiliate links (Charter §3):** keep the tool and missing-ingredient search links on the recipe screen, or remove the missing-ingredient links so nothing in ChefCount looks like shopping (GroceryMatch's lane)?
4. **Screenshots and ads:** store screenshots come from `SCREENSHOT=true` builds that never load ads. Is that acceptable, or should the listing show the ad slot?
5. **App Review contact:** replace "App Reviewer" with a real named person for this app (Charter §1/§7)?
6. **5.6 is account-wide** (16 identical messages within one minute). Who replies to Apple, and when (Charter §1, MA-043 freeze)? This app-level fix alone may not lift it.
7. **Calories:** the 12 ported recipes carry calorie numbers with no recorded source (`catalogue.dart:1-9` says they were "extracted mechanically" from the old RN app). Drop calories from the app (recommended), or does someone own sourcing them?

---

## 8. Implementation record (software-developer, 2026-10-12)

What was built, so store-compliance can describe the shipped build exactly. Base `0be1fd1`; the commit hash is in the run report.

**Ads, as built (founder question 2 still open; the build takes the spec's first option):**
- **No interstitial at all.** The tab-change `AglAds.onTransition()` call is gone and nothing else calls it (`test/honesty_test.dart` fails on any `onTransition`/`InterstitialAd` in `lib/`). So there is no warm-up and no frequency cap that a short review session could miss.
- **One AdMob banner** in normal layout flow at the very end of the Kitchen list and at the very end of the Recipes list (`honesty_test.dart` pins those two files as the only ones containing `AglAdBanner(`). None on Tonight, onboarding, the recipe screen, the cook sheet or Settings. No "Advertisement" label was added: the banner is zero-height until Google fills it, so a label would sit over empty space.
- Known side effect, not changed (shared package): `AglAds.initialize()` in `packages/agl_ads` still preloads one interstitial after consent even though ChefCount never shows it. Changing that is a shared-package decision.

**Privacy choices:** always visible in Settings. Where UMP says a form is required it opens Google's form; elsewhere it opens a short sheet: "ChefCount shows Google AdMob ads: one banner at the end of the Kitchen and Recipes lists. Where the law requires it (the EEA, the UK and Switzerland) Google asks for your consent before any ad is requested … Google has not asked for consent where you are, so there is nothing to change here. Your kitchen list, recipes and history stay on this device and are never sent with an ad request."

**Calories:** dropped everywhere (founder question 7, recommended option). No calorie figure is shown or stored. If the founder wants them back, someone has to source them first.

**Amazon links (founder question 3 open):** unchanged from before — missing-ingredient and tool search links with the on-screen disclosure, only on the 12 ported recipes that carried them. The 28 new recipes have no grocery or tool links.

**Language row:** not added. The app is English-only (`kSupportedLocales = [Locale('en')]`), so a language picker would offer one choice. S5 is not done.

**SHOULD items:** S2 "Enough?" is done (recipe screen shows "You have 1 pcs, less than the recipe needs" where units convert; nothing where they don't). S1 reminders, S3 FoodKeeper, S4 leftovers, S5 translations are not done.

**Fills for section 5 placeholders (proposed text for store-compliance):**
- Description, ads sentence: "ChefCount is free and shows one Google AdMob banner at the end of the Kitchen and Recipes lists; there are no full-screen ads. Where the law requires consent, Google asks first, and Settings → Privacy choices is always there."
- Description, "36+ recipes" → the build ships **40** bundled recipes (Breakfast 7, Lunch 8, Dinner 11, Snack 7, Dessert 7).
- Description, tally sentence, matching the screen: "Each month shows your own tally of food used and binned." (The Kitchen line reads e.g. "October: 4 used (1 close to their date) · 0 binned".)
- Review notes, Ads line: "One AdMob banner at the end of the Kitchen and Recipes lists. No interstitial or full-screen ad anywhere, and no warm-up period: the first session behaves like every other."
- Review notes, "To try it": first launch shows "What's in your kitchen right now?"; tap staples, then "Show me what I can cook". On a recipe, "I cooked this" → Confirm. Kitchen → tap any item to edit it; the X asks Used it / Binned it / Just remove. Recipes → + adds your own recipe. Settings is the gear on Tonight.
- Privacy label: remove camera and photo-library access (both usage strings are gone from Info.plist; Android never declared a camera permission). Data collected unchanged: Crashlytics crash data; AdMob device identifiers.
- Screenshots: the five named in section 5 are produced by `integration_test/store_screenshots_test.dart` as `01_tonight`, `02_recipe_with_swap`, `03_cook_sheet`, `04_kitchen`, `05_recipes_mine` (store-compliance maps them to fastlane names). The app follows the system light/dark setting; run once per appearance for dark frames.
- Feature graphic: not rebuilt here (it lives under `fastlane/`, which this workstream does not touch). The new mark is drawn by `ChefCount/tool/draw_icon.py`; palette and fonts are in section M5.
