# Approval request — AdMob placements per app (native added, interstitials removed)

Date: 2026-10-14 · Prepared by: monetization (AI office) · Charter §3 (money)

## Decision needed

Approve the per-app ad changes below. They follow the founder's "fit per app" answer of 2026-10-14 (chat): add a format only where it has a natural place, no app-open ads, no rewarded interstitial.

## What changes

The per-app review is in `projects/admob-rollout/placements/<repo>.json`, with file:line evidence for every recommendation. The summary is in `../docs/ADMOB_PLAN.md`. RideZap is excluded because it becomes a game (#46).

| App | Native row | Interstitial | Open items from the review |
| --- | --- | --- | --- |
| AeroSwift | add: mobile/lib/features/airports/airport_board_screen.dart (AirportBoardScreen, departures/arrivals board list) | remove | agl_ads must be re-resolved to include agl-manifest cb21ee5 (AglNativeAd / showRewarded): pubspec.lock resolved-ref is 904d8e9c958c71a9e171b |
| AGCleaner | — | remove | agl_ads is locked in pubspec.lock to 97e9a7f (resolved-ref, line 17), which does not contain agl-manifest cb21ee5 (checked with `git merge-b |
| AGRecorder | add: lib/screens/library_view.dart (LibraryView) | remove | agl_ads in pubspec.lock resolves to 97e9a7f, an ancestor of cb21ee5 (checked with git merge-base --is-ancestor): AglNativeAd / AglAds.showRe |
| ApexMarketWatch | add: mobile/lib/features/filings/filings_screen.dart (FilingsScreen, 13F position-change cards) | remove | agl_ads must be re-resolved to include agl-manifest cb21ee5 (AglNativeAd / showRewarded): pubspec.lock resolved-ref is 904d8e9c958c71a9e171b |
| CarDeal | add: mobile/lib/features/complaints/complaint_list_screen.dart (ComplaintListScreen) | — | pubspec.lock pins agl_ads at 97e9a7f (mobile/pubspec.lock) (pubspec.lock grep), which predates cb21ee5 and has no ad_native.dart (git cat-fi |
| ChefCount | add: lib/features/recipes/recipes_screen.dart (RecipesScreen, recipe card list) | — | agl_ads must be re-resolved to include agl-manifest cb21ee5 (AglNativeAd / showRewarded): pubspec.lock resolved-ref is 97e9a7f40471bca73e66f |
| daily-pulse | add: lib/presentation/screens/lists/article_list.dart (ArticleListBody) - used by Bright side, World editions, Search and Topic screens | — | pubspec.lock pins agl_ads at d5e5b72, which predates agl-manifest cb21ee5 (git merge-base --is-ancestor: not contained); run `flutter pub up |
| DriftDate | — | remove | Founder decision F7 (keep the single Matches banner or remove AdMob from DriftDate; recommended: remove) is open: spec DriftDate.md:396; agl |
| GroceryMatch | add: lib/features/stores/stores_screen.dart (StoresScreen, list view of nearby supermarkets) | remove | pubspec.lock pins agl_ads at d5e5b72, which predates agl-manifest cb21ee5 (git merge-base --is-ancestor: not contained); run `flutter pub up |
| HerJourney | — | remove | Founder decision F2 (ads in a reproductive-health app) is open: spec HerJourney.md:302; agl_ads lock d5e5b72 predates cb21ee5 (not needed fo |
| iMaps | — | remove | iMaps serves ads through its own lib/services/admob_service.dart on google_mobile_ads (pubspec.yaml:68), not through AglAds/AglAdBanner. agl |
| iMeasure | — | remove | Move onto agl_ads: replace AdService and BannerAdSlot (google_mobile_ads ^9.1.0 used directly, pubspec.yaml:67) with AglAds.configure/initia |
| MileMaster | — | remove | Founder question 5 (keep interstitial on return from Full log) is open: spec MileMaster.md:486; agl_ads lock 7b3c98e predates cb21ee5 (not n |
| NearServe | add: mobile/lib/features/directory/directory_screen.dart (_Results) | — | pubspec.lock pins agl_ads at 7b3c98e, which predates agl-manifest cb21ee5 (git merge-base --is-ancestor: not contained); run `flutter pub up |
| NewsBoard | add: mobile/lib/features/sections/sections_screen.dart (SectionsScreen) | — | agl_ads in pubspec.lock resolves to 7b3c98e, an ancestor of cb21ee5 (checked with git merge-base --is-ancestor): AglNativeAd / AglAds.showRe |
| PlantPulse | — | remove | agl_ads AglAds.initialize() preloads an interstitial on every launch even if the app never calls onTransition (packages/agl_ads/lib/src/ads. |
| portfolio-board | — | remove | Founder question (remove AdMob from the internal build, M4; recommended yes) is open: spec portfolio-board.md:195. If yes, the banner and in |
| radiotune | add: lib/screens/genre_stations_screen.dart (GenreStationsScreen) | remove | pubspec.lock pins agl_ads at 7b3c98e (pubspec.lock) (pubspec.lock grep), which predates cb21ee5 and has no ad_native.dart (git cat-file chec |
| RoomCraft | add: lib/materials/shops_section.dart (ShopsSection / _ShopsSectionState, 'Near <place>' results card) | — | agl_ads is locked in pubspec.lock to 7b3c98e (resolved-ref, line 17), which does not contain agl-manifest cb21ee5 (checked with `git merge-b |
| Verba | add: lib/features/history/history_screen.dart (HistoryScreen) | — | Founder Q3 (spec Verba.md:397): keep or remove AdMob in Verba. If it is removed, native = no.; Verba serves ads through its own google_mobil |
| WiFiTrail | add: lib/features/history/history_screen.dart (HistoryScreen / _HistoryScreenState) | remove | agl_ads is locked in pubspec.lock to 7b3c98e (resolved-ref, line 17), which does not contain agl-manifest cb21ee5 (checked with `git merge-b |
| yourtube | add: lib/presentation/screens/search/search_screen.dart (search results list) | — | yourtube imports agl_ads only for AglConsent (lib/main.dart:45-49, ad_banner_widget.dart:35) and never calls AglAds.configure, so AglNativeA |

- **Rewarded: none.** No app has an honest, non-essential reward (no free quota, no premium extra). RideZap, as a game, is the exception and goes through #46.
- **Banners stay** as they are, except where an app's own open founder question already covers them (for example Uscis-Case's banner on the case screen, and DriftDate/HerJourney decisions F7/F2).

## Why now

- The shared package can now show native and rewarded ads (commit cb21ee5).
- Since commit 8c75368, apps without interstitials no longer send a wasted ad request at launch.
- **Safety:** the iMaps interstitial can appear after an incident report made while navigating (`iMaps/lib/services/admob_service.dart:165-182` has no navigation check, per the review). That one should be fixed even if nothing else is approved.

## Exact action

Answer "approve placements", or list exceptions (for example "keep interstitial in X"). The office will then:
1. Upgrade agl_ads in each app.
2. Wire `AglNativeAd` at the cited list and remove the `onTransition` call sites.
3. Run analyze and tests, and launch at least one app on the simulator to show a test native ad.
4. Re-run `scripts/admob_plan.py`.

## Evidence

- Placement JSONs: 43 files, all parse, every claim cites file:line.
- `python3 scripts/admob_plan.py --check` → 516 units, 0 problems.

## Risks / how to undo

- Removing interstitials lowers ad revenue in those apps. The office has no revenue data per app to quantify this (not verified).
- Native templates are untested on a device so far (google_mobile_ads 5.3.1 and 9.1.0).
- Each change is a normal app commit and can be reverted.
