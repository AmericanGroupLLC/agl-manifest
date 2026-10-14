# AdMob placements — group 5 (Monetization, 2026-10-14)

Read-only plan under the founder's "Fit per app" rule (2026-10-14). Per-app detail, with file:line evidence, is in `<repo>.json` next to this file. App open = no and rewarded interstitial = no for every app. The existing banners stay.

| App | Native where | Rewarded what | Interstitial | Blockers |
| --- | --- | --- | --- | --- |
| AGStudio | No: the only list is a grid of the user's own prints (`gallery_screen.dart:209-220`). A template row does not fit a print-shaped grid cell, and the gallery already has a banner at its foot | No: the 30 s wait is Pollinations' upstream limit (an ad cannot lift it); the 200-print cap is a disk guard | Present (when Prints opens, `studio_screen.dart:198`) → **keep** (natural break, capped; creative app) | — |
| CarDeal | Yes: NHTSA owner-complaints list, `mobile/lib/features/complaints/complaint_list_screen.dart:122-127`, small, every 8 (up to 200 complaints) | No: free by design, no quota; Compare's 4-car cap is a layout limit | Not present → keep out (**remove**); spec Q2 open | agl_ads lock 97e9a7f predates cb21ee5 |
| EventSpark | No: Home lists the host's own few events, next to private guest and money data | No | Not present → keep out (**remove**); door use is task-focused | Ad placement still pending founder (issue #40) |
| HomeWise | No: finance. Homes = the user's saved homes with budget verdicts; Schedule = an amortization table | No | Not present → keep out (**remove**) | Banner placement founder Q2 open |
| MyCard | No: sensitive. The only list is the user's encrypted cards | No | Not present → keep out (**remove**) | Founder Q3 may remove ads entirely |
| NexusTransferPay | No: finance/payments. The lists are the user's own transfers | No (also avoids 3.1.1 questions; Apple 2.1(b) IAP issue open) | Not present → keep out (**remove**) | Founder Q1 keep/retire, Q3 IAP products open |
| radiotune | Yes: genre/country/language station list, `lib/screens/genre_stations_screen.dart:146-158`, **small** template (no media view, so no audio), every 8 (up to 60 stations). Optional: Dial station search results | No: no quota or premium, and a rewarded video would cut into playback | Present (every tab change, `main_shell.dart:110`, no playing check) → **remove** (or gate on `!isPlaying`). Founder rule: never interrupt playback | agl_ads lock 7b3c98e predates cb21ee5; this goes against spec radiotune.md:187 ("onTransition stays"), so the founder must confirm |
| Verba | Yes, **if founder Q3 keeps AdMob**: translation history, `lib/features/history/history_screen.dart:173-178`, small, every 10 (up to 500 entries) | No: the only quota is MyMemory's upstream allowance | Not present (`showInterstitialIfReady` has no caller) → keep out (**remove**); quick travel use | Founder Q3; app has its own ad service and never calls `AglAds.configure`; lock f0fc3b2 predates cb21ee5; google_mobile_ads ^5.1.0 vs agl_ads >=5.2.0; no banner placed despite CSV "Shown in app = yes" |

Common facts:
- All 8 apps resolve agl_ads to a commit older than cb21ee5 (each `pubspec.lock` resolved-ref). None of those commits has `ad_native.dart` (`git cat-file`), and each is an ancestor of cb21ee5 (`git merge-base --is-ancestor`). Apps that get native (CarDeal, radiotune, Verba) must run `flutter pub upgrade agl_ads`.
- Native and rewarded unit ids exist for all 8 apps (`store/admob/ad-units-plan.csv`, status DONE; `docs/admob-ids.json`). `scripts/build_release.py:450` passes them as `ADMOB_NATIVE_*` / `ADMOB_REWARDED_*` dart-defines through `scripts/agl_paths.py:142-159`.
- No app in this group is a kids/families app. `docs/store-policy/<repo>.json` Apple 1.3 says applies=false for all 8, and no primary category is KIDS.
- No app in this group has an in-app free quota or a non-essential premium extra, so rewarded = no for all 8.
- `agl-manifest/apps.json` is stale for radiotune: it lists a Google test iOS app id, but the app code and Info.plist carry the real one.

Not verified: nothing was built, run or tested on a device. Whether a radiotune interstitial ducks or pauses the stream was not observed; the finding comes from reading the code only.
