# AdMob placements — group 1 (Monetization, 2026-10-14)

Read-only plan under the founder's "Fit per app" rule (2026-10-14). Per-app detail, with file:line evidence, is in `<repo>.json` next to this file. App open = no and rewarded interstitial = no for every app. The existing banners stay.

| App | Native where | Rewarded what | Interstitial | Blockers |
| --- | --- | --- | --- | --- |
| AeroSwift | Yes: Boards flight list, `mobile/lib/features/airports/airport_board_screen.dart:274`, small, after flight 10 then every 10 (in-list banner after flight 5 stays) | No: no quota or premium; CSV export already free | Present (tab switch, `app/app.dart:87`) → **remove** (time-critical spotting moments; judgment call) | agl_ads lock predates cb21ee5; OpenSky non-commercial terms vs ads (spec F1) open |
| ApexMarketWatch | Yes: Filings 13F move cards, `mobile/lib/features/filings/filings_screen.dart:168`, small, after cards 20 and 40 (banner after card 10 stays; list capped at 50) | No: the 50-card cap is for performance, not a free tier; CSV export free | Present (tab switch, `home_shell.dart:51`) → **remove** (finance, quick checks; spec Q2) | agl_ads lock predates cb21ee5; spec Q1 name / Q2 interstitial open |
| ChefCount | Yes: Recipes list (40 bundled recipes + the user's own), `lib/features/recipes/recipes_screen.dart:200`, small, every 10 | No | Not present → keep out (**remove**) | agl_ads lock predates cb21ee5 |
| FashionFactory | No: the lists are the user's own orders and returns (sizes, prices paid); no content feed | No: CSV export free | Not present → keep out (**remove**) | Only if a format is added later: agl_ads upgrade |
| iMaps | No: the feeds are safety alerts (USGS/NWS/roadworks), where an ad row could be mistaken for an alert | No: premium has no purchase path; `showRewarded` has no caller | Present (after incident report, `report_incident_screen.dart:88`) → **remove**. Source reading shows no navigation guard, so it can reach a driver mid-route | Uses its own AdMobService, not AglAds; ad-units-plan.csv wrongly marks rewarded/native "Shown in app = yes"; ad files are someone else's uncommitted work |
| MyFinance | No: sensitive finance; the lists are personal transactions and schedules | No | Not present → keep out (**remove**) | — |
| Photriya | No: the Swatchbook is the user's own colour library (unsure; chose no) | No: all 5 export formats free | Present (after a finished photo session, `swatchbook_screen.dart:58`) → **keep** (natural break, capped) | — |
| RideZap | No: the lists are the user's own trips and fares; quick-decision flow | No | Not present → keep out (**remove**) | Founder D1 (retire into TripNest) open |
| VirtuBand | No: the Library is the user's own songs; Instruments is a small fixed set | No (`ads_service.dart:89`: deliberately none) | Not present → keep out (**remove**) | Own BannerAdSlot, no AglAds.configure; iOS-ads claim in notes unverified (spec Q3) |

Common facts:
- All 9 apps resolve agl_ads to a commit older than cb21ee5 (each `pubspec.lock` resolved-ref; checked with `git merge-base --is-ancestor`). The three apps getting native (AeroSwift, ApexMarketWatch, ChefCount) must run `flutter pub upgrade agl_ads` and ship `ADMOB_NATIVE_ANDROID/IOS` dart-defines. The units already exist as DONE in `store/admob/ad-units-plan.csv`.
- No app in this group is a kids/families app: none is in the KIDS category, and `store/ratings` has no `kidsAgeBand`.
- No app in this group has an existing free quota or non-essential premium extra, so rewarded = no for all 9.

Not verified: nothing was built or run on a device. The iMaps "interstitial can show while navigating" finding comes from reading the source only.
