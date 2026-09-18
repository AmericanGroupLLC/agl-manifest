# Per-app store submission checklist

Every line is a real check against the tree, the store record, or an
artefact on disk - regenerate with `python3 scripts/store_checklist.py`
rather than editing. `HUMAN` marks the things no script can settle: a
console login, a questionnaire, or a credential that does not exist yet.

## Summary

| App | pass | fail | human |
| --- | ---: | ---: | ---: |
| AeroSwift | 20 | 1 | 3 |
| AGCleaner | 21 | 0 | 3 |
| AGrammarly | 21 | 1 | 3 |
| AGRecorder | 21 | 0 | 3 |
| AGStudio | 21 | 0 | 3 |
| ApexMarketWatch | 21 | 0 | 3 |
| BodyQuest | 22 | 1 | 3 |
| BuddyPlay | 21 | 0 | 3 |
| CalcMaster | 22 | 1 | 3 |
| CarDeal | 21 | 0 | 3 |
| ChefCount | 19 | 2 | 3 |
| CodeDeal | 21 | 0 | 3 |
| daily-pulse | 22 | 1 | 3 |
| DriftDate | 22 | 1 | 3 |
| EventSpark | 21 | 0 | 3 |
| FashionFactory | 22 | 0 | 3 |
| GadgetNest | 20 | 1 | 3 |
| GroceryMatch | 22 | 1 | 3 |
| HerJourney | 22 | 1 | 3 |
| HomeWise | 21 | 0 | 3 |
| iMaps | 23 | 0 | 3 |
| iMeasure | 22 | 1 | 3 |
| Kinnav | 23 | 0 | 3 |
| MileMaster | 19 | 2 | 3 |
| MyCard | 21 | 0 | 3 |
| MyFinance | 19 | 2 | 3 |
| MyHealth | 22 | 1 | 3 |
| NearServe | 21 | 0 | 3 |
| NewsBoard | 20 | 1 | 3 |
| NexusTransferPay | 18 | 3 | 3 |
| Photriya | 22 | 1 | 3 |
| PilotEnRoute | 22 | 1 | 3 |
| PlantPulse | 20 | 1 | 3 |
| portfolio-board | 21 | 1 | 3 |
| radiotune | 23 | 0 | 3 |
| RideZap | 21 | 0 | 3 |
| RoomCraft | 21 | 0 | 3 |
| TripNest | 22 | 0 | 3 |
| Uscis-Case | 23 | 0 | 3 |
| Verba | 20 | 2 | 3 |
| VirtuBand | 23 | 0 | 3 |
| WiFiTrail | 19 | 2 | 3 |
| yourtube | 22 | 0 | 3 |

**29 failing checks across 43 apps.**

## AeroSwift

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.aeroswift |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d3478881e04c |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
| App Store name | PASS | AeroSwift |
| Play title | PASS | AeroSwift |
| Full description | PASS | 991 chars |
| Play short description (<=80) | PASS | 65 chars |
| App Store keywords (<=100) | PASS | 85 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## AGCleaner

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agcleaner |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 77c906922e56 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | AGCleaner |
| Play title | PASS | AGCleaner |
| Full description | PASS | 1722 chars |
| Play short description (<=80) | PASS | 72 chars |
| App Store keywords (<=100) | PASS | 88 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## AGrammarly

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agrammarly |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 93f7d4982dff |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | AGrammarly: Reply Helper |
| Play title | PASS | AGrammarly — Reply Helper |
| Full description | PASS | 1601 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 89 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | PRODUCTIVITY |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## AGRecorder

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agrecorder |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 4157b8b26555 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | AGRecorder |
| Play title | PASS | AGRecorder |
| Full description | PASS | 607 chars |
| Play short description (<=80) | PASS | 67 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## AGStudio

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agstudio |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 19351391843f |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
| App Store name | PASS | AGStudio |
| Play title | PASS | AGStudio |
| Full description | PASS | 481 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 86 chars |
| Primary category | PASS | PHOTO_AND_VIDEO |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## ApexMarketWatch

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.apexmarketwatch |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 6806204856fd |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 4 captured ['1320x2868'] |
| App Store name | PASS | ApexMarketWatch |
| Play title | PASS | ApexMarketWatch |
| Full description | PASS | 941 chars |
| Play short description (<=80) | PASS | 67 chars |
| App Store keywords (<=100) | PASS | 75 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## BodyQuest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.bodyquest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 0728a46087a2 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 1 captured ['1320x2868'] |
| App Store name | PASS | BodyQuest: Health Game |
| Play title | PASS | BodyQuest — Health Game |
| Full description | PASS | 1458 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 96 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## BuddyPlay

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.buddyplay |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 0ea52e87574c |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iBuddyPlay |
| Play title | PASS | BuddyPlay |
| Full description | PASS | 993 chars |
| Play short description (<=80) | PASS | 66 chars |
| App Store keywords (<=100) | PASS | 88 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## CalcMaster

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.calcmaster |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d9d26cfca178 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 0 captured  |
| App Store name | PASS | CalcMaster: World Calc |
| Play title | PASS | CalcMaster — World Calculator |
| Full description | PASS | 3163 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 93 chars |
| Promotional text (<=170) | PASS | 145 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## CarDeal

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.cardeal |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 1bf430275466 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
| App Store name | PASS | iCarDeal |
| Play title | PASS | CarDeal |
| Full description | PASS | 781 chars |
| Play short description (<=80) | PASS | 18 chars |
| App Store keywords (<=100) | PASS | 87 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## ChefCount

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.chefcount |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | e4c3ca647b98 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | ChefCount |
| Play title | PASS | ChefCount |
| Full description | FAIL | missing |
| Play short description (<=80) | PASS | 56 chars |
| App Store keywords (<=100) | FAIL | missing |
| Primary category | PASS | FOOD_AND_DRINK |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## CodeDeal

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.codedeal |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 3c35bd963d2c |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
| App Store name | PASS | CodeDeal |
| Play title | PASS | CodeDeal |
| Full description | PASS | 477 chars |
| Play short description (<=80) | PASS | 30 chars |
| App Store keywords (<=100) | PASS | 71 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## daily-pulse

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.dailypulse |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 88f6d6c36bb8 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | Daily Pulse: Morning Brief |
| Play title | PASS | Daily Pulse — Morning Brief |
| Full description | PASS | 1448 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 94 chars |
| Promotional text (<=170) | PASS | 151 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## DriftDate

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.driftdate |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | ed9a84f651a6 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 0 captured  |
| App Store name | PASS | DriftDate: Layered Dating |
| Play title | PASS | DriftDate — Layered Dating |
| Full description | PASS | 1526 chars |
| Play short description (<=80) | PASS | 72 chars |
| App Store keywords (<=100) | PASS | 84 chars |
| Promotional text (<=170) | PASS | 147 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## EventSpark

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.eventspark |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | c0b27aa5caa4 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
| App Store name | PASS | iEventSpark |
| Play title | PASS | EventSpark |
| Full description | PASS | 559 chars |
| Play short description (<=80) | PASS | 25 chars |
| App Store keywords (<=100) | PASS | 71 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## FashionFactory

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.fashionfactory |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 262f191388b0 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | Fashion Factory: Deals |
| Play title | PASS | Fashion Factory — Deals |
| Full description | PASS | 1238 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 96 chars |
| Promotional text (<=170) | PASS | 153 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## GadgetNest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.gadgetnest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d67e0a6786ef |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
| App Store name | PASS | GadgetNest |
| Play title | PASS | GadgetNest |
| Full description | PASS | 700 chars |
| Play short description (<=80) | PASS | 70 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## GroceryMatch

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.grocerymatch |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 766ee6855483 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | GroceryMatch: Save on Food |
| Play title | PASS | GroceryMatch — Save on Food |
| Full description | PASS | 1382 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 90 chars |
| Promotional text (<=170) | PASS | 163 chars |
| Primary category | PASS | SHOPPING |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## HerJourney

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.herJourney |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 7e19bfa045ae |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | HerJourney: Cycle & Health |
| Play title | PASS | HerJourney — Cycle & Health |
| Full description | PASS | 1831 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 95 chars |
| Promotional text (<=170) | PASS | 163 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## HomeWise

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.homewise |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | a333a100f02b |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
| App Store name | PASS | iHomeWise |
| Play title | PASS | HomeWise |
| Full description | PASS | 1101 chars |
| Play short description (<=80) | PASS | 61 chars |
| App Store keywords (<=100) | PASS | 90 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## iMaps

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.imaps |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 880fa0330d26 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iMaps: Navigate & Report |
| Play title | PASS | iMaps — Navigate & Report |
| Full description | PASS | 2065 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 93 chars |
| Promotional text (<=170) | PASS | 151 chars |
| Primary category | PASS | NAVIGATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## iMeasure

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.imeasure |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | e224c360fb12 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iMeasure: Measure & Level |
| Play title | PASS | iMeasure — Measure & Level |
| Full description | PASS | 1562 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 97 chars |
| Promotional text (<=170) | PASS | 161 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## Kinnav

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.kinnav |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 6b981f7c9f98 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | Kinnav |
| Play title | PASS | Kinnav |
| Full description | PASS | 1913 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Promotional text (<=170) | PASS | 150 chars |
| Primary category | PASS | NAVIGATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## MileMaster

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.milemaster |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 896a79f219e2 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | MileMaster |
| Play title | PASS | MileMaster |
| Full description | FAIL | missing |
| Play short description (<=80) | PASS | 72 chars |
| App Store keywords (<=100) | FAIL | missing |
| Primary category | PASS | BUSINESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## MyCard

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.mycard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | a8396bf904f3 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iMyCard |
| Play title | PASS | MyCard |
| Full description | PASS | 1068 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 89 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## MyFinance

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.myfinance |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 7839d8cd6dbc |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | MyFinance |
| Play title | PASS | MyFinance |
| Full description | FAIL | missing |
| Play short description (<=80) | PASS | 28 chars |
| App Store keywords (<=100) | FAIL | missing |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## MyHealth

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.myhealth |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | cf26a8b793e5 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | MyHealth: Fitness Tracker |
| Play title | PASS | MyHealth — Fitness Tracker |
| Full description | PASS | 1763 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 143 chars |
| Primary category | PASS | HEALTH_AND_FITNESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## NearServe

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.nearserve |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 4854a5daa313 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
| App Store name | PASS | NearServe |
| Play title | PASS | NearServe |
| Full description | PASS | 609 chars |
| Play short description (<=80) | PASS | 40 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## NewsBoard

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.newsboard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 16aa785f8dfe |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | NewsBoard |
| Play title | PASS | NewsBoard |
| Full description | PASS | 2138 chars |
| Play short description (<=80) | PASS | 63 chars |
| App Store keywords (<=100) | PASS | 73 chars |
| Primary category | PASS | NEWS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## NexusTransferPay

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.nexustransferpay |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 18a039defc96 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | NexusTransferPay |
| Play title | PASS | NexusTransferPay |
| Full description | FAIL | missing |
| Play short description (<=80) | PASS | 45 chars |
| App Store keywords (<=100) | FAIL | missing |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## Photriya

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.photriya |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 98174dc8767c |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 0 captured  |
| App Store name | PASS | Photriya |
| Play title | PASS | Photriya |
| Full description | PASS | 1951 chars |
| Play short description (<=80) | PASS | 61 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 103 chars |
| Primary category | PASS | PHOTO_AND_VIDEO |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## PilotEnRoute

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.pilotenroute |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 3fcff1d8a365 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 0 captured  |
| App Store name | PASS | PilotEnRoute: Pilot Training |
| Play title | PASS | PilotEnRoute — Pilot Training |
| Full description | PASS | 1618 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 99 chars |
| Promotional text (<=170) | PASS | 152 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## PlantPulse

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.plantpulse |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 8d8f24553b3a |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | PlantPulse |
| Play title | PASS | PlantPulse |
| Full description | PASS | 1005 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## portfolio-board

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.portfolioboard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 3f4308930bf8 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 4 captured ['1320x2868'] |
| App Store name | PASS | portfolio-board |
| Play title | PASS | portfolio-board |
| Full description | PASS | 2195 chars |
| Play short description (<=80) | PASS | 75 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Promotional text (<=170) | PASS | 154 chars |
| Primary category | PASS | PRODUCTIVITY |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## radiotune

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.radiotune |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 3530bee5a1f8 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | Ratio Tune: Live Radio |
| Play title | PASS | Ratio Tune — Live Radio |
| Full description | PASS | 1191 chars |
| Play short description (<=80) | PASS | 76 chars |
| App Store keywords (<=100) | PASS | 81 chars |
| Promotional text (<=170) | PASS | 129 chars |
| Primary category | PASS | MUSIC |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## RideZap

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.ridezap |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 54e63146bb98 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
| App Store name | PASS | RideZap |
| Play title | PASS | RideZap |
| Full description | PASS | 686 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 74 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## RoomCraft

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.roomcraft |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | e30f2b400e71 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iRoomCraft |
| Play title | PASS | RoomCraft |
| Full description | PASS | 899 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 82 chars |
| Primary category | PASS | LIFESTYLE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## TripNest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.tripnest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d7df7967371f |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
| App Store name | PASS | TripNest: Travel Booking |
| Play title | PASS | TripNest — Travel Booking |
| Full description | PASS | 1407 chars |
| Play short description (<=80) | PASS | 79 chars |
| App Store keywords (<=100) | PASS | 98 chars |
| Promotional text (<=170) | PASS | 143 chars |
| Primary category | PASS | TRAVEL |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## Uscis-Case

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.usciscase |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | fdb8c722c1d6 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | USCIS Case Lookup |
| Play title | PASS | Case Tracker for USCIS |
| Full description | PASS | 1971 chars |
| Play short description (<=80) | PASS | 80 chars |
| App Store keywords (<=100) | PASS | 91 chars |
| Promotional text (<=170) | PASS | 169 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## Verba

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.verba |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 8787cb68431f |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | FAIL | 1 captured ['1320x2868'] |
| App Store name | PASS | Verba: Voice Translator |
| Play title | PASS | Verba — Voice Translator |
| Full description | PASS | 1472 chars |
| Play short description (<=80) | PASS | 73 chars |
| App Store keywords (<=100) | PASS | 92 chars |
| Promotional text (<=170) | PASS | 150 chars |
| Primary category | PASS | EDUCATION |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## VirtuBand

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.virtuband |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | c0b36e516dd8 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | VirtuBand: Music Studio |
| Play title | PASS | VirtuBand — Music Studio |
| Full description | PASS | 1242 chars |
| Play short description (<=80) | PASS | 77 chars |
| App Store keywords (<=100) | PASS | 85 chars |
| Promotional text (<=170) | PASS | 152 chars |
| Primary category | PASS | MUSIC |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## WiFiTrail

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.wifitrail |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d996011eb73a |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | WiFiTrail |
| Play title | PASS | WiFiTrail |
| Full description | FAIL | missing |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | FAIL | missing |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

## yourtube

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.yourtube |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 70a3e23fdf0f |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | YourTube: Watch & Discover |
| Play title | PASS | yourtube |
| Full description | PASS | 733 chars |
| Play short description (<=80) | PASS | 37 chars |
| App Store keywords (<=100) | PASS | 79 chars |
| Primary category | PASS | ENTERTAINMENT |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | PASS |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | HUMAN | ITSAppUsesNonExemptEncryption / ASC |
| Age rating questionnaire | HUMAN | Apple + Play IARC, per app |
| Build live on App Store Connect | PASS | uploaded |
| Play Console upload | HUMAN | no Play service-account JSON exists |
| Firebase config (crash reporting works) | PASS | android=y ios=y |

