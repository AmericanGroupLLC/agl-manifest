# Per-app store submission checklist

Every line is a real check against the tree, the store record, or an
artefact on disk - regenerate with `python3 scripts/store_checklist.py`
rather than editing. `HUMAN` marks the things no script can settle: a
console login, a questionnaire, or a credential that does not exist yet.

## Summary

| App | pass | fail | human |
| --- | ---: | ---: | ---: |
| AeroSwift | 21 | 2 | 1 |
| AGCleaner | 23 | 1 | 1 |
| AGrammarly | 24 | 1 | 1 |
| AGRecorder | 23 | 1 | 1 |
| AGStudio | 23 | 1 | 1 |
| ApexMarketWatch | 23 | 1 | 1 |
| BodyQuest | 23 | 2 | 1 |
| BuddyPlay | 23 | 1 | 1 |
| CalcMaster | 26 | 0 | 1 |
| CarDeal | 23 | 1 | 1 |
| ChefCount | 24 | 1 | 1 |
| CodeDeal | 23 | 1 | 1 |
| daily-pulse | 24 | 2 | 1 |
| DriftDate | 25 | 1 | 1 |
| EventSpark | 23 | 1 | 1 |
| FashionFactory | 22 | 2 | 1 |
| GadgetNest | 21 | 2 | 1 |
| GroceryMatch | 23 | 2 | 1 |
| HerJourney | 23 | 2 | 1 |
| HomeWise | 23 | 1 | 1 |
| iMaps | 26 | 0 | 1 |
| iMeasure | 24 | 1 | 1 |
| Kinnav | 25 | 1 | 1 |
| MileMaster | 24 | 1 | 1 |
| MyCard | 23 | 1 | 1 |
| MyFinance | 24 | 1 | 1 |
| MyHealth | 23 | 2 | 1 |
| NearServe | 23 | 1 | 1 |
| NewsBoard | 23 | 1 | 1 |
| NexusTransferPay | 23 | 1 | 1 |
| Photriya | 25 | 1 | 1 |
| PilotEnRoute | 25 | 1 | 1 |
| PlantPulse | 21 | 2 | 1 |
| radiotune | 23 | 2 | 1 |
| RideZap | 23 | 1 | 1 |
| RoomCraft | 23 | 1 | 1 |
| TripNest | 25 | 0 | 1 |
| Uscis-Case | 26 | 0 | 1 |
| Verba | 22 | 2 | 1 |
| VirtuBand | 26 | 0 | 1 |
| WiFiTrail | 24 | 1 | 1 |
| yourtube | 22 | 2 | 1 |

**49 failing checks across 42 apps.**

## AeroSwift

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.aeroswift |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 3e57e7e5d53c |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## AGCleaner

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agcleaner |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 365e5ce1f05a |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## AGRecorder

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agrecorder |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | df06aa0c917f |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## AGStudio

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.agstudio |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | ed447ff572bf |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## ApexMarketWatch

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.apexmarketwatch |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | de92aa1b1d32 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## BuddyPlay

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.buddyplay |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 264a7dd6ea47 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## CarDeal

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.cardeal |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | cb90fedca983 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## ChefCount

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.chefcount |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | bd40d0d34bbb |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | ChefCount |
| Play title | PASS | ChefCount |
| Full description | PASS | 1500 chars |
| Play short description (<=80) | PASS | 68 chars |
| App Store keywords (<=100) | PASS | 80 chars |
| Promotional text (<=170) | PASS | 128 chars |
| Primary category | PASS | FOOD_AND_DRINK |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 2 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## EventSpark

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.eventspark |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | c80cc094a4e3 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## GadgetNest

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.gadgetnest |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 50dcbac6c563 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## HerJourney

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.herjourney |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## HomeWise

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.homewise |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 21da48bf39fd |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## MileMaster

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.milemaster |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 6b495e921f1b |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iMileMaster |
| Play title | PASS | MileMaster |
| Full description | PASS | 1896 chars |
| Play short description (<=80) | PASS | 70 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 149 chars |
| Primary category | PASS | BUSINESS |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## MyCard

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.mycard |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | f095b1456bf3 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## MyFinance

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.myfinance |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | f9e5b93a1be4 |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | iMyFinance |
| Play title | PASS | MyFinance |
| Full description | PASS | 1659 chars |
| Play short description (<=80) | PASS | 78 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 132 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## NearServe

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.nearserve |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 64b8d5465535 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| App Store name | PASS | iNewsBoard |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Full description | PASS | 3256 chars |
| Play short description (<=80) | PASS | 45 chars |
| App Store keywords (<=100) | PASS | 98 chars |
| Primary category | PASS | FINANCE |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## PlantPulse

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.plantpulse |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | b833e597c8d1 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## RideZap

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.ridezap |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 5c6bd5b8c6b2 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## RoomCraft

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.roomcraft |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | d3d7bf7737c3 |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Screenshots (Apple >=1, Play >=2) | PASS | 5 captured ['1320x2868'] |
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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | no Play entry - MA-021 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | PASS | internal app sharing link issued |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

## WiFiTrail

| Check | State | Detail |
| --- | :-: | --- |
| Android .aab signed with this app's upload key | PASS | SIGNED |
| Android .apk (release, sideload/test) | PASS | SIGNED |
| iOS .ipa exported for the App Store | PASS | EXPORTED |
| Binaries newer than the app icon | PASS |  |
| Bundle id / applicationId | PASS | com.americangroupllc.wifitrail |
| Release signing configured | PASS | upload keystore matched |
| App icon (1024, opaque, not a placeholder) | PASS | 0335cd95483d |
| Play feature graphic 1024x500 | PASS |  |
| Screenshots (Apple >=1, Play >=2) | PASS | 3 captured ['1320x2868'] |
| App Store name | PASS | WiFiTrail |
| Play title | PASS | WiFiTrail |
| Full description | PASS | 2211 chars |
| Play short description (<=80) | PASS | 69 chars |
| App Store keywords (<=100) | PASS | 77 chars |
| Promotional text (<=170) | PASS | 135 chars |
| Primary category | PASS | UTILITIES |
| Per-app review notes | PASS |  |
| Privacy & support URLs resolve (HTTP 200) | PASS |  |
| Account-deletion page (if accounts) | n/a |  |
| iOS privacy manifest | PASS |  |
| iOS purpose strings for linked APIs | PASS |  |
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | PASS | declaration matches the shipped binary |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | PASS | uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

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
| Export compliance answered | PASS | ITSAppUsesNonExemptEncryption=false |
| Apple age rating answered | n/a |  |
| Play IARC questionnaire | HUMAN | no API - Play Console only |
| Build live on App Store Connect | FAIL | no ASC record or not uploaded |
| Play delivery to account users | FAIL | still a Draft app in Console - MA-022 |
| Firebase config (crash reporting works) | PASS | android=y ios=y ios-bundled=y |

