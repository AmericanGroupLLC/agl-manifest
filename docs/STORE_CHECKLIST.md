# Per-app store submission checklist

Every line is a real check against the tree, the store record, or an
artefact on disk - regenerate with `python3 scripts/store_checklist.py`
rather than editing. `HUMAN` marks the things no script can settle: a
console login, a questionnaire, or a credential that does not exist yet.

## Summary

| App | pass | fail | human |
| --- | ---: | ---: | ---: |
| AeroSwift | 15 | 7 | 3 |
| AGCleaner | 15 | 7 | 3 |
| AGrammarly | 16 | 7 | 3 |
| AGRecorder | 15 | 7 | 3 |
| AGStudio | 15 | 7 | 3 |
| ApexMarketWatch | 15 | 7 | 3 |
| BodyQuest | 16 | 8 | 3 |
| BuddyPlay | 15 | 7 | 3 |
| CalcMaster | 16 | 8 | 3 |
| CarDeal | 15 | 7 | 3 |
| ChefCount | 16 | 7 | 3 |
| CodeDeal | 15 | 7 | 3 |
| daily-pulse | 16 | 8 | 3 |
| DriftDate | 16 | 8 | 3 |
| EventSpark | 15 | 7 | 3 |
| FashionFactory | 16 | 7 | 3 |
| GadgetNest | 15 | 7 | 3 |
| GroceryMatch | 16 | 8 | 3 |
| HerJourney | 16 | 8 | 3 |
| HomeWise | 15 | 7 | 3 |
| iMaps | 16 | 8 | 3 |
| iMeasure | 16 | 8 | 3 |
| Kinnav | 16 | 8 | 3 |
| MileMaster | 16 | 7 | 3 |
| MyCard | 15 | 7 | 3 |
| MyFinance | 16 | 7 | 3 |
| MyHealth | 16 | 8 | 3 |
| NearServe | 15 | 7 | 3 |
| NewsBoard | 15 | 7 | 3 |
| NexusTransferPay | 15 | 7 | 3 |
| Photriya | 16 | 8 | 3 |
| PilotEnRoute | 16 | 8 | 3 |
| PlantPulse | 15 | 7 | 3 |
| portfolio-board | 16 | 7 | 3 |
| radiotune | 16 | 8 | 3 |
| RideZap | 15 | 7 | 3 |
| RoomCraft | 15 | 7 | 3 |
| TripNest | 16 | 7 | 3 |
| Uscis-Case | 16 | 8 | 3 |
| Verba | 16 | 7 | 3 |
| VirtuBand | 16 | 8 | 3 |
| WiFiTrail | 16 | 7 | 3 |
| yourtube | 15 | 8 | 3 |

**317 failing checks across 43 apps.**

## AeroSwift

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.aeroswift |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | AeroSwift |
| Play title | PASS | AeroSwift |
| Full description | PASS | 991 chars |
| Play short description (<=80) | PASS | 65 chars |
| App Store keywords (<=100) | PASS | 85 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## AGCleaner

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agcleaner |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | AGCleaner |
| Play title | PASS | AGCleaner |
| Full description | PASS | 1722 chars |
| Play short description (<=80) | PASS | 72 chars |
| App Store keywords (<=100) | PASS | 88 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## AGrammarly

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agrammarly |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | AGrammarly: Reply Helper |
| Play title | PASS | AGrammarly — Reply Helper |
| Full description | PASS | 1601 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 89 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | PRODUCTIVITY |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## AGRecorder

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agrecorder |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | AGRecorder |
| Play title | PASS | AGRecorder |
| Full description | PASS | 607 chars |
| Play short description (<=80) | PASS | 67 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## AGStudio

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agstudio |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | AGStudio |
| Play title | PASS | AGStudio |
| Full description | PASS | 481 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 86 chars |
| Primary category | PASS | PHOTO_AND_VIDEO |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## ApexMarketWatch

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.apexmarketwatch |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | ApexMarketWatch |
| Play title | PASS | ApexMarketWatch |
| Full description | PASS | 941 chars |
| Play short description (<=80) | PASS | 67 chars |
| App Store keywords (<=100) | PASS | 75 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## BodyQuest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.bodyquest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | BodyQuest: Health Game |
| Play title | PASS | BodyQuest — Health Game |
| Full description | PASS | 1458 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 96 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## BuddyPlay

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.buddyplay |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iBuddyPlay |
| Play title | PASS | BuddyPlay |
| Full description | PASS | 993 chars |
| Play short description (<=80) | PASS | 66 chars |
| App Store keywords (<=100) | PASS | 88 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## CalcMaster

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.calcmaster |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | CalcMaster: World Calc |
| Play title | PASS | CalcMaster — World Calculator |
| Full description | PASS | 3163 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 93 chars |
| Promotional text (<=170) | PASS | 145 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## CarDeal

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.cardeal |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iCarDeal |
| Play title | PASS | CarDeal |
| Full description | PASS | 781 chars |
| Play short description (<=80) | PASS | 18 chars |
| App Store keywords (<=100) | PASS | 87 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## ChefCount

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.chefcount |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | ChefCount |
| Play title | PASS | ChefCount |
| Full description | PASS | 1500 chars |
| Play short description (<=80) | PASS | 68 chars |
| App Store keywords (<=100) | PASS | 80 chars |
| Promotional text (<=170) | PASS | 128 chars |
| Primary category | PASS | FOOD_AND_DRINK |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## CodeDeal

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.codedeal |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | CodeDeal |
| Play title | PASS | CodeDeal |
| Full description | PASS | 477 chars |
| Play short description (<=80) | PASS | 30 chars |
| App Store keywords (<=100) | PASS | 71 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## daily-pulse

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.dailypulse |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Daily Pulse: Morning Brief |
| Play title | PASS | Daily Pulse — Morning Brief |
| Full description | PASS | 1448 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 94 chars |
| Promotional text (<=170) | PASS | 151 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## DriftDate

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.driftdate |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | DriftDate: Layered Dating |
| Play title | PASS | DriftDate — Layered Dating |
| Full description | PASS | 1526 chars |
| Play short description (<=80) | PASS | 72 chars |
| App Store keywords (<=100) | PASS | 84 chars |
| Promotional text (<=170) | PASS | 147 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## EventSpark

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.eventspark |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iEventSpark |
| Play title | PASS | EventSpark |
| Full description | PASS | 559 chars |
| Play short description (<=80) | PASS | 25 chars |
| App Store keywords (<=100) | PASS | 71 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## FashionFactory

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.fashionfactory |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Fashion Factory: Deals |
| Play title | PASS | Fashion Factory — Deals |
| Full description | PASS | 1238 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 96 chars |
| Promotional text (<=170) | PASS | 153 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## GadgetNest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.gadgetnest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | GadgetNest |
| Play title | PASS | GadgetNest |
| Full description | PASS | 700 chars |
| Play short description (<=80) | PASS | 70 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## GroceryMatch

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.grocerymatch |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | GroceryMatch: Save on Food |
| Play title | PASS | GroceryMatch — Save on Food |
| Full description | PASS | 1382 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 90 chars |
| Promotional text (<=170) | PASS | 163 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## HerJourney

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.herjourney |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | HerJourney: Cycle & Health |
| Play title | PASS | HerJourney — Cycle & Health |
| Full description | PASS | 1831 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 95 chars |
| Promotional text (<=170) | PASS | 163 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## HomeWise

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.homewise |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iHomeWise |
| Play title | PASS | HomeWise |
| Full description | PASS | 1101 chars |
| Play short description (<=80) | PASS | 61 chars |
| App Store keywords (<=100) | PASS | 90 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## iMaps

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.imaps |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iMaps: Navigate & Report |
| Play title | PASS | iMaps — Navigate & Report |
| Full description | PASS | 2065 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 93 chars |
| Promotional text (<=170) | PASS | 151 chars |
| Primary category | PASS | NAVIGATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## iMeasure

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.imeasure |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iMeasure: Measure & Level |
| Play title | PASS | iMeasure — Measure & Level |
| Full description | PASS | 1562 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 97 chars |
| Promotional text (<=170) | PASS | 161 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## Kinnav

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.kinnav |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Kinnav |
| Play title | PASS | Kinnav |
| Full description | PASS | 1913 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Promotional text (<=170) | PASS | 150 chars |
| Primary category | PASS | NAVIGATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## MileMaster

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.milemaster |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iMileMaster |
| Play title | PASS | MileMaster |
| Full description | PASS | 1896 chars |
| Play short description (<=80) | PASS | 70 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | BUSINESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## MyCard

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.mycard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iMyCard |
| Play title | PASS | MyCard |
| Full description | PASS | 1068 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 89 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## MyFinance

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.myfinance |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iMyFinance |
| Play title | PASS | MyFinance |
| Full description | PASS | 1659 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 132 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## MyHealth

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.myhealth |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | MyHealth: Fitness Tracker |
| Play title | PASS | MyHealth — Fitness Tracker |
| Full description | PASS | 1763 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 143 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## NearServe

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.nearserve |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | NearServe |
| Play title | PASS | NearServe |
| Full description | PASS | 609 chars |
| Play short description (<=80) | PASS | 40 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## NewsBoard

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.newsboard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iNewsBoard |
| Play title | PASS | NewsBoard |
| Full description | PASS | 2138 chars |
| Play short description (<=80) | PASS | 63 chars |
| App Store keywords (<=100) | PASS | 73 chars |
| Primary category | PASS | NEWS |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## NexusTransferPay

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.nexustransferpay |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | NexusTransferPay |
| Play title | PASS | NexusTransferPay |
| Full description | PASS | 3256 chars |
| Play short description (<=80) | PASS | 45 chars |
| App Store keywords (<=100) | PASS | 98 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## Photriya

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.photriya |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Photriya |
| Play title | PASS | Photriya |
| Full description | PASS | 1951 chars |
| Play short description (<=80) | PASS | 61 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 103 chars |
| Primary category | PASS | PHOTO_AND_VIDEO |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## PilotEnRoute

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.pilotenroute |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | PilotEnRoute: Pilot Training |
| Play title | PASS | PilotEnRoute — Pilot Training |
| Full description | PASS | 1618 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 99 chars |
| Promotional text (<=170) | PASS | 152 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## PlantPulse

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.plantpulse |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | PlantPulse |
| Play title | PASS | PlantPulse |
| Full description | PASS | 1005 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## portfolio-board

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.portfolioboard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Portfolio Board |
| Play title | PASS | Portfolio Board |
| Full description | PASS | 2195 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Promotional text (<=170) | PASS | 154 chars |
| Primary category | PASS | PRODUCTIVITY |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## radiotune

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.radiotune |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Ratio Tune: Live Radio |
| Play title | PASS | Ratio Tune — Live Radio |
| Full description | PASS | 1191 chars |
| Play short description (<=80) | PASS | 76 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Promotional text (<=170) | PASS | 129 chars |
| Primary category | PASS | MUSIC |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## RideZap

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.ridezap |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | RideZap |
| Play title | PASS | RideZap |
| Full description | PASS | 686 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 74 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## RoomCraft

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.roomcraft |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | iRoomCraft |
| Play title | PASS | RoomCraft |
| Full description | PASS | 899 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 82 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## TripNest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.tripnest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | TripNest: Travel Booking |
| Play title | PASS | TripNest — Travel Booking |
| Full description | PASS | 1407 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 98 chars |
| Promotional text (<=170) | PASS | 143 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## Uscis-Case

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.usciscase |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | USCIS Case Lookup |
| Play title | PASS | Case Tracker for USCIS |
| Full description | PASS | 1971 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 169 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## Verba

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.verba |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | Verba: Voice Translator |
| Play title | PASS | Verba — Voice Translator |
| Full description | PASS | 1472 chars |
| Play short description (<=80) | PASS | 73 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Promotional text (<=170) | PASS | 150 chars |
| Primary category | PASS | EDUCATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## VirtuBand

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.virtuband |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | VirtuBand: Music Studio |
| Play title | PASS | VirtuBand — Music Studio |
| Full description | PASS | 1242 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 85 chars |
| Promotional text (<=170) | PASS | 152 chars |
| Primary category | PASS | MUSIC |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## WiFiTrail

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.wifitrail |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | WiFiTrail |
| Play title | PASS | WiFiTrail |
| Full description | PASS | 2211 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 135 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

## yourtube

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.yourtube |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | FAIL | no 1024 icon |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | not captured |
| App Store name | PASS | YourTube: Watch & Discover |
| Play title | PASS | yourtube |
| Full description | PASS | 733 chars |
| Play short description (<=80) | PASS | 37 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs serve the right page | HUMAN | not measured yet |
| Account-deletion page (if accounts) | FAIL | required by Play |
| iOS privacy manifest | FAIL |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | FAIL | key absent - ASC will ask on every upload |
| Apple age rating answered | FAIL | not measured yet |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | HUMAN | not measured yet |
| Firebase config (crash reporting works) | FAIL | android=n ios=n ios-bundled=n  <- plist not referenced by Xcode |

