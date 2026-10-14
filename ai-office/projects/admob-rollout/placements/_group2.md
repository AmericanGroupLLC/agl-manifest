# AdMob placements, group 2 (Monetization, 2026-10-14)

This is a read-only plan. No app repo was edited, built or committed. Each app has its own `<repo>.json` next to this file, with a file:line for every claim. Founder rule "Fit per app" applied: no app open ads and no rewarded interstitials anywhere, and the existing banners stay.

| App | Native where | Rewarded what | Interstitial | Blockers |
| --- | --- | --- | --- | --- |
| AGCleaner | no. The duplicate-group list is a merge work queue of the user's contacts, and History is a rarely long audit log | no. Nothing to reward (no quota, no IAP) | present (return to Home, `lib/app/app.dart:137`). **remove** | agl_ads lock 97e9a7f is older than cb21ee5. Age rating falls back to `default.json` (advertising: false) although banners show. Founder question 3 is open |
| BodyQuest | no. Children in the audience | no. Children in the audience. The RewardedAd is loaded but never shown | loaded, never shown. **remove** | Kids/families: parent plus child aged 8-12, and Young Explorer = Kids mode. No banner is shown anywhere. F2 (drop AdMob/UMP) is open. Own AdService on google_mobile_ads 5.x. Ratings file says advertising: true |
| CodeDeal | no. A native ad between the user's own promo codes could pass for a code | no | none. **remove** (keep absent) | Founder decision D6 (retire or keep). Age rating falls back to default (advertising: false). Lock d5e5b72 |
| GadgetNest | no. Household list is the user's own few devices. The spec forbids ads on the picker | no | none. **remove** (keep absent) | Pivot decision. Age rating falls back to default. Lock d5e5b72 |
| iMeasure | no. Job readings are professional records in a grouped list | no. Export is part of the core job | present (own AdService, every 3rd tool closed). **remove** | Not on AglAds: move the banner to AglAdBanner and delete the interstitial. 23 dead .ts/.tsx files under lib/. Q2 is open. Lock f0fc3b2 |
| MyHealth | no. Health context. The exercise library is the only possible place, and F2 limits ads to one Timeline banner | no | none. **remove** (keep absent) | F2 (ads in a medical record) is open. Age rating falls back to default. Lock 7b3c98e |
| PilotEnRoute | no. Logbook already has the in-list banner, and the weather lists are go/no-go safety data | no. The loader is for 'exam questions' the app no longer has. Never shown | loaded, never shown. **remove** | Not on AglAds: swap AdBannerWidget for AglAdBanner and drop the interstitial and rewarded loaders. Lock f0fc3b2 |
| RoomCraft | **yes.** `lib/materials/shops_section.dart:244` (ShopsSection, OpenStreetMap shop results, at most 20). Small template, one after the 10th shop | no. The suggestion cap of 3 and the shop cap of 20 are design choices, not quotas | none. **remove** (keep absent) | Lock 7b3c98e (needs `flutter pub upgrade agl_ads`). Age rating falls back to default. Native unit ids exist |
| WiFiTrail | **yes.** `lib/features/history/history_screen.dart:172` (HistoryScreen readings). Small template, every 10 readings, hidden while a test runs | no | present (opening History or Compare). **remove** | Lock 7b3c98e (needs `flutter pub upgrade agl_ads`). Age rating falls back to default. Founder question 2 is open |

Notes
- Every app in this group resolves agl_ads to a commit older than cb21ee5 in `pubspec.lock`. Before using `AglNativeAd` or `AglAds.showRewarded`, run `flutter pub upgrade agl_ads`. Each lock was checked with `git merge-base --is-ancestor`.
- Age rating: `scripts/deliver_metadata.py:48` uses `store/ratings/default.json` (line 16 `"advertising": false`) for any app without its own ratings file. AGCleaner, CodeDeal, GadgetNest, MyHealth, RoomCraft and WiFiTrail show banners but have no ratings file. This is for store-compliance to fix.
- No app in the group has a free quota or premium tier, so honest rewarded placements are zero.
- Not verified: native template rendering on iOS under google_mobile_ads 5.3.1 and 9.1.0. No build or device run was done.
