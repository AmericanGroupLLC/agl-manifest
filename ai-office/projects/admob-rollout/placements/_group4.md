# AdMob native / rewarded placement — group 4

Monetization role, 2026-10-14. Read-only plan under the founder's "Fit per app" decision. No app repo was edited, staged or built. Per-app detail with file:line evidence is in `<repo>.json` next to this file.

| App | Native where | Rewarded what | Interstitial | Blockers |
| --- | --- | --- | --- | --- |
| AGRecorder | Yes. `lib/screens/library_view.dart` (LibraryView), small, 1 per 10 LibraryCards, only when the list has more than 10 (`:80-86`). Not in the Marks inbox. | No: no quota, premium or IAP exists | present (`home_screen.dart:107`): **remove** (task-focused utility) | agl_ads lock 97e9a7f predates cb21ee5, needs `pub upgrade`; founder Q2 open (spec :221); store copy describes ads |
| CalcMaster | No: only the user's short Sheets list (finance-adjacent), already has a banner | No: Pro/IAP removed in a4c0e19, nothing to reward | not present (dead code in `ad_service.dart:117-170`): **remove** | Brief is stale: no RevenueCat in current code. Uses own AdService, not AglAds.configure |
| DriftDate | No: Discover is a deck of real people, Matches are personal | No: no premium (spec :377), dating safety | present (`main_tabs.dart:94`): **remove** | Founder F7 (remove ads; spec :396) open |
| HerJourney | No: only list is the History log of health data | No: health context, nothing to reward | present (`root_scaffold.dart:16,47`): **remove** | Founder F2 (ads in reproductive health; spec :302) open |
| MileMaster | No: Full log is an IRS tax record (finance), already ends with a banner | No: export etc. free and unlimited | present (`logbook_screen.dart:93`): **remove** (task-focused business utility) | Founder Q5 (spec :486) open |
| NewsBoard | Yes. `mobile/lib/features/sections/sections_screen.dart` (SectionsScreen), SliverList.builder `:93-95`, small, 1 per 8 stories; same pattern optional in search results (`search_screen.dart:157-159`) | No: no quota; old "Premium/AI summaries" house ad is being deleted | present (`main_shell.dart:64`): **keep** (browsing, capped 3 min) | agl_ads lock 7b3c98e predates cb21ee5; Q3 BBC/NPR syndication terms open (spec :338); if S1 inline banner lands, native replaces it, not both |
| portfolio-board | No: internal staff tool, so impressions would be self-generated (invalid-traffic risk) | No | present (`router.dart:104`): **remove** | Founder question: remove AdMob entirely (M4, spec :195) open |
| Uscis-Case (v2) | No: only browse list is official Federal Register notices (Sources, ≤20 items); an ad among them risks reading as an official notice (spec :299) | No: v2 limits are USCIS-quota/abuse guards (v2 spec :387-388), not a free tier | not present (`ad_service.dart:8-10`): **remove** (keep none) | Q4 + VERIFY-23 (USCIS terms on ad-supported use) open; existing banner sits on the case-detail data screen, flagged for decision; own AdService, not AglAds |

## Checked across the group
- **Kids / Families:** none of the 8. Categories are UTILITIES, LIFESTYLE (DriftDate is 18+), HEALTH_AND_FITNESS, BUSINESS, NEWS and PRODUCTIVITY, and `docs/store-policy/<repo>.md` says "1.3 Kids Category: no" for each. The Play target-audience forms are not verifiable by API.
- **App open and rewarded interstitial:** no for all 8, per the founder decision.
- **Ad units:** `docs/admob-ids.json` has android/ios native and rewarded units for all 8. `scripts/agl_paths.py:142-160` already passes `ADMOB_NATIVE_*` and `ADMOB_REWARDED_*` at build time.
- **Package version:** every app's `pubspec.lock` pins agl_ads to a commit that predates cb21ee5 (checked with `git merge-base --is-ancestor`). The two apps that get native (AGRecorder, NewsBoard) need `flutter pub upgrade agl_ads` first.
- **Net result:** native in 2 apps (AGRecorder, NewsBoard) and rewarded in none. No app in this group has an honest, non-essential extra to reward.
