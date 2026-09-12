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
| Signed release bundle, verified against its upload key | 37 of 36 |

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

## 2. Signed release bundles

Built locally with `python3 scripts/build_release.py`, which is cheaper than
a runner and works today — Android needs no macOS minutes and no CI secret.

Every bundle's signing certificate is compared against the upload keystore it
was meant to use, and the fingerprint is shown so the claim can be checked
rather than taken on faith. This is not ceremony: a release build with a
misconfigured `signingConfig` silently falls back to the debug key, exits 0,
and is rejected at upload. One app in this table was caught exactly that way.

**37 of 37** apps produce a verified signed bundle.

| # | App | Bundle | Size | Flavour | Signing certificate (SHA-256) | Result |
| --: | --- | --- | ---: | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `AGCleaner-app-release.aab` | 48 MB | — | `089DF812DD7EB9D0` | signed |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `AGrammarly-app-release.aab` | 52 MB | — | `843C7D4A1E327D00` | signed |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `AGRecorder-app-release.aab` | 48 MB | — | `8DBBF8B4D11D34DA` | signed |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `BodyQuest-app-prod-release.aab` | 60 MB | prod | `C6A3C1C570E1C39F` | signed |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `CalcMaster-app-prod-release.aab` | 64 MB | prod | `2073F4958E35CF71` | signed |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `CarDeal-app-release.aab` | 54 MB | — | `CF11DBD2873808B6` | signed |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `ChefCount-app-release.aab` | 49 MB | — | `7936742F5C989564` | signed |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `CodeDeal-app-release.aab` | 55 MB | — | `B61F34EBE60DFF33` | signed |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `daily-pulse-app-prod-release.aab` | 75 MB | prod | `AD4582F780FCB092` | signed |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `DriftDate-app-prod-release.aab` | 64 MB | prod | `88AC08FC465D39B8` | signed |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `EventSpark-app-release.aab` | 102 MB | — | `186F66EB80AF5D7D` | signed |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `FashionFactory-app-prod-release.aab` | 51 MB | prod | `E265C0642A99DA55` | signed |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `GadgetNest-app-release.aab` | 53 MB | — | `52B686735A576C4E` | signed |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `GroceryMatch-app-prod-release.aab` | 64 MB | prod | `D5DBFDD0F484838D` | signed |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `HerJourney-app-prod-release.aab` | 58 MB | prod | `5F018C068A100C07` | signed |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `HomeWise-app-release.aab` | 53 MB | — | `50C3A6FC08D81122` | signed |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `iMaps-app-prod-release.aab` | 69 MB | prod | `B74E83A44A11DF7A` | signed |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `iMeasure-app-prod-release.aab` | 63 MB | prod | `EC5E6A8668B712CE` | signed |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `MileMaster-app-release.aab` | 50 MB | — | `D14CB7E2BEA014E7` | signed |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `MyFinance-app-release.aab` | 49 MB | — | `E485BD0690C73798` | signed |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `MyHealth-app-prod-release.aab` | 62 MB | prod | `A693834AA710F05D` | signed |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `NearServe-app-release.aab` | 54 MB | — | `96342EAA305E4DCB` | signed |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `NewsBoard-app-release.aab` | 54 MB | — | `25D5C0D942A489F5` | signed |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `NexusTransferPay-app-release.aab` | 59 MB | — | `5B6A4604F1861642` | signed |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `Photriya-app-prod-release.aab` | 68 MB | prod | `ED2D941BFF746590` | signed |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `PilotEnRoute-app-prod-release.aab` | 100 MB | prod | `767CD1F7FB490B7C` | signed |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `portfolio-board-app-release.aab` | 53 MB | — | `F123FD917E9E9DC5` | signed |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `radiotune-app-release.aab` | 65 MB | — | `A18905EBAF282BB1` | signed |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `RideZap-app-release.aab` | 53 MB | — | `2731B1A2D0201887` | signed |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `RoomCraft-app-release.aab` | 50 MB | — | `D3AAE284B3D6B1D4` | signed |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `TripNest-app-release.aab` | 61 MB | — | `72D9176A72E4F875` | signed |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `Uscis-Case-app-prod-release.aab` | 60 MB | prod | `565DBEE81C473EBC` | signed |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `Verba-app-prod-release.aab` | 68 MB | prod | `5607DDEE124203A9` | signed |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `VirtuBand-app-prod-release.aab` | 60 MB | prod | `99635E5EB1FFB48D` | signed |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `WiFiTrail-app-release.aab` | 47 MB | — | `E0D8203064D9D384` | signed |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `yourtube-app-prod-release.aab` | 87 MB | prod | `2EA595F41FA61468` | signed |

Bundles are kept outside every git repository (`~/agl/.dist/`) so a stray
`git add -A` cannot commit 60 MB binaries. The build tree each one came
from is deleted afterwards — 37 Flutter release trees are about 36 GB, and
keeping them filled this machine's disk on the first attempt.

## 3. AdMob

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

## 4. App Store Connect records

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

## 5. Required files

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

## 6. Still to create

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
