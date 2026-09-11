# Portfolio status

All 42 mobile apps in the organization — what each one is, where it
stands, and everything still needed to ship it. Regenerate with
`python3 scripts/status.py`; the same data as a spreadsheet is in
[`status.csv`](status.csv).

The package name in each row is the string AdMob, Play Console, App Store
Connect and `keytool` all ask for, so this is the table to work from when
creating AdMob apps, upload keys or store records.

| | Count |
| --- | ---: |
| Mobile apps in the org | 42 |
| Flutter, buildable today | 36 |
| Not ported yet | 6 |
| Serving ads | 11 |
| App Store record matching a live bundle id | 29 |
| Upload keystores loaded into this repo's secrets | 30 |
| Firebase config present | 0 of 36 |
| Binary anyone can download | 2 |

## 1. Every app

`yes` under a platform means present **and** deliverable — a real signing
config and a `beta` lane. `build only` means it compiles but delivery is not
wired.

| # | App | Package / bundle id | Status | Android | iOS | Ads | Sign-in | Store record | Build | Binaries |
| --: | --- | --- | --- | :-: | :-: | :-: | --- | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGCleaner | v1.0.0 | — |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | v1.0.0 | — |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGRecorder | v1.0.0 | — |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | BodyQuest | no release | — |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | Calculator: World Class | v1.0.0 | — |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iCarDeal | v1.0.0 | — |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | ChefCount | v1.0.0 | — |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | Does not compile — 5 analyzer errors | yes | yes | — | none | CodeDeal | v1.0.0 | — |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (optional) | **none** | no release | — |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple | iDriftDate | v1.0.0 | — |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iEventSpark | v1.0.0 | — |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.styleradar` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | StyleRadar | no release | — |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | no release | — |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | **none** | v1.0.0 | — |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | A `com.americangroupllc.her_journey`<br>i `com.americangroupllc.herJourney` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (no screen) | **none** | no release | — |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iHomeWise | v1.0.0 | — |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | iMaps Route | v1.0.0 | — |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | **none** | v1.0.0 | — |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iMileMaster | v1.0.0 | — |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iMyFinance | v1.0.0 | — |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` | Binary published | yes | yes | — | Supabase + Google + Apple (optional) | **none** | v1.1.0 | `myhealth-server-v1.1.0.tar.gz`, `MyHealth-web-v1.1.0.tar.gz` |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | NearServe | v1.0.0 | — |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | v1.0.0 | — |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Biometric (no screen) | **none** | v1.0.0 | — |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | Photriya Camera Colors | v1.0.0 | — |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | PilotEnRoute | no release | — |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | v1.0.0 | — |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.radiotune` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | RadioTune World | no release | — |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | RideZap | v1.0.0 | — |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iRoomCraft | v1.0.0 | — |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | TravelZap | no release | — |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | USCIS Case Lookup | v1.0.0 | — |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | **none** | v1.0.0 | — |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase (optional) | VirtuBand | v1.0.0 | — |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | WifiTrail | v1.0.0 | — |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | YourTube: Watch & Discover | no release | — |
| 37 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` _(reserved)_ | Not ported | — | — | — | — | **none** | — | — |
| 38 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `com.americangroupllc.agstudio` _(reserved)_ | Not ported | — | — | — | — | AGStudio | — | — |
| 39 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `com.americangroupllc.apexmarketwatch` _(reserved)_ | Not ported | — | — | — | — | ApexMarketWatch | — | — |
| 40 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `com.americangroupllc.buddyplay` _(reserved)_ | Not ported | — | — | — | — | iBuddyPlay | — | — |
| 41 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `com.americangroupllc.mycard` _(reserved)_ | Not ported | — | — | — | — | iMyCard | — | — |
| 42 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` _(reserved)_ | Not ported | — | — | — | — | **none** | — | — |

**Not in the organization.** Still delivered by this manifest, but the
repository is owned elsewhere and reachable only through a GitHub redirect.
If that redirect is removed, delivery for it stops.

| App | Where it lives now | Package |
| --- | --- | --- |
| Kinnav | `transferred to srpatcha/Kinnav; pushes follow a redirect` | `com.americangroupllc.kinnav` |

## 2. AdMob

Application ids are declared in `AndroidManifest.xml` and `Info.plist` and must
match what is passed to `AglAds.configure`. A mismatch is not a degraded
experience — on iOS the SDK throws `GADInvalidInitializationException` and iOS
terminates the app on every launch.

Unit ids are never committed. They are read from `--dart-define` at build time,
so a build without them serves Google's test units — the safe default rather
than a broken one. The values below are the console record.

| # | App | Package | Android app id | iOS app id | Android banner | Android interstitial |
| --: | --- | --- | --- | --- | --- | --- |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | `ca-app-pub-8528784688453695~5377349094` | `ca-app-pub-8528784688453695~9148987425` | `ca-app-pub-8528784688453695/7665581023` | `ca-app-pub-8528784688453695/7474009334` |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | `${admobAppId}` _(build-time)_ | `$(ADMOB_APP_ID)` _(build-time)_ | `ca-app-pub-8528784688453695/1143402684` | `ca-app-pub-8528784688453695/8340879191` |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | `ca-app-pub-8528784688453695~9265279754` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/1222409251` | `ca-app-pub-8528784688453695/9950162694` |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | `${admobAppId}` _(build-time)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.radiotune` | `ca-app-pub-8528784688453695~7770953426` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/4087643109` | `ca-app-pub-8528784688453695/2327055058` |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | `ca-app-pub-8528784688453695~8044208178` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/3721819782` | `ca-app-pub-8528784688453695/5528514029` |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | `ca-app-pub-8528784688453695~2309537905` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/5539491423` | `ca-app-pub-8528784688453695/9095593054` |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | `ca-app-pub-8528784688453695~2836542125` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/6914604113` | `ca-app-pub-8528784688453695/9569471431` |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |

**4 of these have no AdMob record at all** — they serve ads
against Google's test application id, so they earn nothing: BodyQuest, PilotEnRoute, Verba, yourtube.

**9 carry the test application id on iOS.** Correct while an
app has no iOS AdMob app of its own, and the thing to replace when one is
created: BodyQuest, iMeasure, PilotEnRoute, radiotune, TripNest, Uscis-Case, Verba, VirtuBand, yourtube. No app has iOS unit ids, so an iOS
release build serves test ads by design.

Every ad app gates its requests on UMP consent, with a per-app test that fails
if any ad is constructed without a check in the enclosing method. It stays
dormant until a GDPR message is published in AdMob → Privacy & messaging.

## 3. App Store Connect records

Live from the API on the last sync: **40 records exist**, and
**29 of 42** match a bundle id this portfolio builds.
Refresh with `bundle exec ruby scripts/appstore_records.rb`.

A bundle id that does not match a record is not a warning at upload time —
it is a rejected build.

**13 apps have no matching record:**

| # | App | Bundle id it builds with |
| --: | --- | --- |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `com.americangroupllc.herJourney` |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` |
| 37 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` |
| 42 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` |

**11 records match no app.** Mostly the rename history —
iFoodRadar became GroceryMatch, OfflineBuddy became Verba, iDealZap
became GadgetNest, StayDeal became TripNest. Each is a decision: rename
the record and keep its history, or leave it and create a new one. A
bundle id cannot be changed once an app is published.

| Bundle id | Store record |
| --- | --- |
| `com.americangroup.daily-pulse` | daily-pulse |
| `com.americangroupllc.Mykarma` | iMykarma |
| `com.americangroupllc.agrammarly` | AGrammarly |
| `com.americangroupllc.careerupgradeai` | CareerUpgradeAI |
| `com.americangroupllc.dealzap` | iDealZap |
| `com.americangroupllc.foodradar` | iFoodRadar |
| `com.americangroupllc.kinnav` | Kinnav |
| `com.americangroupllc.newsboard` | iNewsBoard |
| `com.americangroupllc.nexustransferpay` | NexusTransferPay |
| `com.americangroupllc.offlinebuddy` | OfflineBuddy |
| `com.americangroupllc.staydeal` | StayDeal |

## 4. Required files

None of these are in git, for two different reasons. The signing material is
secret and must never be committed. The Firebase files are **not** secret —
Google documents them as shipping inside the binary — and are absent only
because nobody has downloaded them yet.

Once for the whole portfolio:

| File | Where it comes from | Status |
| --- | --- | --- |
| `AuthKey_UV8NYF9767.p8` | App Store Connect → Users and Access → Keys | **loaded** into `ASC_KEY_CONTENT`, verified against the live API |
| Play service-account JSON | Play Console → Setup → API access → grant *Release manager* → download | **missing** |
| Distribution certificate + profiles | `bundle exec fastlane match appstore` on a Mac | **missing** |
| `AGL_PACKAGES_TOKEN` | GitHub → Developer settings | **missing** |

Per app. `key.properties` and the keystore are the Android upload key — **lose
a keystore with Play App Signing off and that app can never be updated again.**

| # | App | google-services.json | GoogleService-Info.plist | Keystore |
| --: | --- | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `mobile/codedeal_app/android/app/google-services.json` | `mobile/codedeal_app/ios/Runner/GoogleService-Info.plist` | **missing** |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `flutter-mobile-app/android/app/google-services.json` | `flutter-mobile-app/ios/Runner/GoogleService-Info.plist` | **missing** |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | loaded |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | loaded |

**36 apps have no Firebase config.** Until they do, `AglCrash.isActive` is
false in every build and no crash is reported. The Gradle plugins apply
themselves the moment the JSON appears — there is no code change waiting.

A placeholder is worse than nothing: MyHealth carries one for project
`myhealth-local-dev` with project_number `000000000000`, which would make
Crashlytics initialise against a project that does not exist. The sanity suite
rejects any config that is not `americangroupllc-5bdfc`.

## 5. Still to create

Everything here needs an account this repository does not have.

| # | What | Where | Unblocks | Status |
| --: | --- | --- | --- | --- |
| 1 | **`AGL_PACKAGES_TOKEN`** | GitHub → Developer settings. Read on the app repos and this manifest; **write** to publish binaries. Store it as an organization secret. | **Everything** — without it `flutter pub get` cannot reach the shared packages and nothing builds | **missing** |
| 2 | Play service-account JSON | Play Console → Setup → API access | Play upload, and listing which apps already have Play records | **missing** |
| 3 | `match` password / distribution certificate | A Mac signed into the Apple account | iOS signing on CI | **missing** |
| 4 | Firebase config files | Firebase console, project `americangroupllc-5bdfc` | Crash reporting | **36 of 36 missing** |
| 5 | AdMob apps + unit ids | AdMob console | Live ads for the apps that earn nothing today | **4 apps have no record** |
| 6 | A GDPR message | AdMob → Privacy & messaging | The consent form; the code is already in every ad app | **not published** |
| 7 | Store descriptions | `store/apps/<repo>.json`, then `scripts/store_metadata.py generate` | Both listings require one | **18 apps have none** |
| 8 | Privacy policy + support URLs | Your hosting | Both listings | templated; the pages must exist |

Already done and verified: the App Store Connect key and its issuer id, both
confirmed against the live API, and 30 upload keystores loaded here.

Apps still needing a store description: AGCleaner, AGRecorder, CarDeal, ChefCount, CodeDeal, EventSpark, GadgetNest, HomeWise, MileMaster, MyFinance, NearServe, NewsBoard, NexusTransferPay, portfolio-board, RideZap, RoomCraft, WiFiTrail, yourtube.
