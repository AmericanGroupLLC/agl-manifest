# Capability matrix

Platform support, sign-in, and every AdMob identifier the portfolio uses.
Regenerate with `python3 scripts/status.py`.

## Platforms and sign-in

`yes` means the platform is present **and** deliverable — a real signing
config and a `beta` lane. `build only` means the project builds but delivery
is not wired yet.

| # | App | Package / bundle id | Android | iOS | Sign-in | Login screen | Account optional |
| --: | --- | --- | :-: | :-: | --- | :-: | :-: |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | yes | yes | none | — | — |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` | yes | yes | none | — | — |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | yes | yes | none | — | — |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | yes | yes | Supabase + Google + Apple | yes | yes |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | yes | yes | Supabase + Google + Apple | yes | yes |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | yes | yes | none | — | — |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | yes | yes | none | — | — |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | yes | yes | none | — | — |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` | yes | yes | Supabase + Google + Apple | yes | yes |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | yes | yes | Supabase + Google + Apple | yes | — |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | yes | yes | none | — | — |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.styleradar` | yes | yes | none | — | — |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` | yes | yes | none | — | — |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` | yes | yes | Supabase + Firebase + Google + Apple | yes | yes |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | A `com.americangroupllc.her_journey`<br>i `com.americangroupllc.herJourney` | yes | yes | Supabase + Google + Apple | — | — |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | yes | yes | none | — | — |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | yes | yes | Supabase + Google + Apple | yes | yes |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | yes | yes | Supabase + Google + Apple | yes | — |
| 19 | [Kinnav](https://github.com/AmericanGroupLLC/Kinnav) ⚠️ | `com.americangroupllc.kinnav` | yes | yes | Supabase + Google + Apple | — | — |
| 20 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | yes | yes | none | — | — |
| 21 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | yes | yes | none | — | — |
| 22 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` | yes | yes | Supabase + Google + Apple | yes | yes |
| 23 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | yes | yes | none | — | — |
| 24 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` | yes | yes | none | — | — |
| 25 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` | yes | yes | Biometric | — | — |
| 26 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | yes | yes | Supabase + Firebase + Google + Apple | yes | yes |
| 27 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | yes | yes | Supabase + Google + Apple | yes | yes |
| 28 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` | yes | yes | none | — | — |
| 29 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.ratiotune` | yes | yes | Supabase + Google + Apple | yes | — |
| 30 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | yes | yes | none | — | — |
| 31 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | yes | yes | none | — | — |
| 32 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | yes | yes | none | — | — |
| 33 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | yes | yes | Supabase + Google + Apple | yes | yes |
| 34 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | yes | yes | none | — | yes |
| 35 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | yes | yes | Supabase | yes | yes |
| 36 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | yes | yes | none | — | — |
| 37 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | yes | yes | Supabase + Google + Apple | yes | yes |
| 38 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` _(reserved)_ | — | — | — | — | — |
| 39 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `com.americangroupllc.agstudio` _(reserved)_ | — | — | — | — | — |
| 40 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `com.americangroupllc.apexmarketwatch` _(reserved)_ | — | — | — | — | — |
| 41 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `com.americangroupllc.buddyplay` _(reserved)_ | — | — | — | — | — |
| 42 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `com.americangroupllc.mycard` _(reserved)_ | — | — | — | — | — |
| 43 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` _(reserved)_ | — | — | — | — | — |

17 of 37 Flutter apps have a sign-in dependency; the rest need no account at all. 6 apps are not ported yet and have no Flutter package name to register.

## AdMob

11 of 37 Flutter apps serve ads.

**Application ids** are declared in `AndroidManifest.xml` and `Info.plist` and
must match what is passed to `AglAds.configure`. A mismatch is not a degraded
experience — on iOS the SDK throws `GADInvalidInitializationException` and iOS
terminates the app on every launch.

**Unit ids** are never committed. They are read from `--dart-define` at build
time, so a build without them serves Google's public test units — the safe
default rather than a broken one. The values below are the console record,
shown here so there is one place to check them against AdMob.

The package name in each row is what AdMob asks for when you add the app,
and what Play and `keytool` use — so this table is the one to work from when
creating AdMob entries, upload keys or store records.

| # | App | Package / bundle id | Android app id | iOS app id | Android banner | Android interstitial |
| --: | --- | --- | --- | --- | --- | --- |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | `ca-app-pub-8528784688453695~5377349094` | `ca-app-pub-8528784688453695~9148987425` | `ca-app-pub-8528784688453695/7665581023` | `ca-app-pub-8528784688453695/7474009334` |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | `${admobAppId}` _(build-time)_ | `$(ADMOB_APP_ID)` _(build-time)_ | `ca-app-pub-8528784688453695/1143402684` | `ca-app-pub-8528784688453695/8340879191` |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | `ca-app-pub-8528784688453695~9265279754` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/1222409251` | `ca-app-pub-8528784688453695/9950162694` |
| 27 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | `${admobAppId}` _(build-time)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 29 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.ratiotune` | `ca-app-pub-8528784688453695~7770953426` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/4087643109` | `ca-app-pub-8528784688453695/2327055058` |
| 32 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | `ca-app-pub-8528784688453695~8044208178` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/3721819782` | `ca-app-pub-8528784688453695/5528514029` |
| 33 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | `ca-app-pub-8528784688453695~2309537905` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/5539491423` | `ca-app-pub-8528784688453695/9095593054` |
| 34 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 35 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | `ca-app-pub-8528784688453695~2836542125` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/6914604113` | `ca-app-pub-8528784688453695/9569471431` |
| 37 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |

**9 apps still carry Google's test application id on iOS** — correct while an app has no iOS AdMob app of its own, and the thing to replace when one is created: BodyQuest, iMeasure, PilotEnRoute, radiotune, TripNest, Uscis-Case, Verba, VirtuBand, yourtube.

No app has iOS unit ids at all, so iOS release builds serve test ads by
design until an iOS AdMob app exists for them.

## Consent

Every ad app gates its requests on UMP consent — `AglConsent` in `agl_ads`,
with a per-app test that fails if any ad is constructed without a check in
the enclosing method. It stays dormant until a GDPR message is published in
AdMob → Privacy & messaging; see [PENDING.md](PENDING.md) row 7.
