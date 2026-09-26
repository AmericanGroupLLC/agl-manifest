# Portfolio status

All 43 mobile apps in the organization — what each one is, where it
stands, and everything still needed to ship it. Regenerate with
`python3 scripts/status.py`; the same data as a spreadsheet is in
[`status.csv`](status.csv).

The package name in each row is the string AdMob, Play Console, App Store
Connect and `keytool` all ask for, so this is the table to work from when
creating AdMob apps, upload keys or store records.

| | Count |
| --- | ---: |
| Mobile apps in the org | 43 |
| Flutter, buildable today | 43 |
| Not ported yet | 0 |
| Serving ads | 11 |
| App Store record matching a live bundle id | 29 |
| Upload keystores loaded into this repo's secrets | 0 |
| Firebase config present | 43 of 43 |
| Binary anyone can download | 0 |
| Signed release bundle, verified against its upload key | 43 of 43 |

## 1. Every app

`yes` under a platform means present **and** deliverable — a real signing
config and a `beta` lane. `build only` means it compiles but delivery is not
wired.

| # | App | Package / bundle id | Status | Android | iOS | Ads | Sign-in | Store record | Build | Binaries |
| --: | --- | --- | --- | :-: | :-: | :-: | --- | --- | --- | --- |
| 1 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | — | — |
| 2 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGCleaner | — | — |
| 3 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroupllc.agrammarly` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGrammarly | — | — |
| 4 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGRecorder | — | — |
| 5 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `com.americangroupllc.agstudio` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | AGStudio | — | — |
| 6 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `com.americangroupllc.apexmarketwatch` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | ApexMarketWatch | — | — |
| 7 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroupllc.bodyquest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | **none** | — | — |
| 8 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `com.americangroupllc.buddyplay` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iBuddyPlay | — | — |
| 9 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | Calculator: World Class | — | — |
| 10 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iCarDeal | — | — |
| 11 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | ChefCount | — | — |
| 12 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | CodeDeal | — | — |
| 13 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroupllc.dailypulse` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (optional) | **none** | — | — |
| 14 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple | iDriftDate | — | — |
| 15 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iEventSpark | — | — |
| 16 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.fashionfactory` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | — | — |
| 17 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | — | — |
| 18 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | **none** | — | — |
| 19 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `com.americangroupllc.herjourney` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (no screen) | **none** | — | — |
| 20 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iHomeWise | — | — |
| 21 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | iMaps Route | — | — |
| 22 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | **none** | — | — |
| 23 | [Kinnav](https://github.com/AmericanGroupLLC/Kinnav) | `com.americangroupllc.kinnav` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (no screen) | Kinnav | — | — |
| 24 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iMileMaster | — | — |
| 25 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `com.americangroupllc.mycard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Biometric (no screen) | iMyCard | — | — |
| 26 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iMyFinance | — | — |
| 27 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (optional) | **none** | — | — |
| 28 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | NearServe | — | — |
| 29 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroupllc.newsboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iNewsBoard | — | — |
| 30 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexustransferpay` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Biometric (no screen) | NexusTransferPay | — | — |
| 31 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | Photriya Camera Colors | — | — |
| 32 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | PilotEnRoute | — | — |
| 33 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | — | — |
| 34 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | **none** | — | — |
| 35 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroupllc.radiotune` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | **none** | — | — |
| 36 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | RideZap | — | — |
| 37 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | iRoomCraft | — | — |
| 38 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | TravelZap | — | — |
| 39 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | USCIS Case Lookup | — | — |
| 40 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | **none** | — | — |
| 41 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase (optional) | VirtuBand | — | — |
| 42 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | WifiTrail | — | — |
| 43 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroupllc.yourtube` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | **none** | — | — |

## 2. Signed release bundles

Built locally with `python3 scripts/build_release.py`, which is cheaper than
a runner and works today — Android needs no macOS minutes and no CI secret.

Every bundle's signing certificate is compared against the upload keystore it
was meant to use, and the fingerprint is shown so the claim can be checked
rather than taken on faith. This is not ceremony: a release build with a
misconfigured `signingConfig` silently falls back to the debug key, exits 0,
and is rejected at upload. One app in this table was caught exactly that way.

**43 of 43** apps produce a verified signed bundle.

| # | App | AAB (Play) | APK (sideload) | Flavour | Signing certificate (SHA-256) |
| --: | --- | --- | --- | --- | --- |
| 1 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | 54 MB | 53 MB | — | `6C50F95AD50C5EFF` |
| 2 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | 51 MB | 50 MB | — | `089DF812DD7EB9D0` |
| 3 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | 54 MB | 52 MB | — | `843C7D4A1E327D00` |
| 4 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | 50 MB | 48 MB | — | `8DBBF8B4D11D34DA` |
| 5 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | 55 MB | 55 MB | — | `7D73F0C37088E29F` |
| 6 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | 53 MB | 53 MB | — | `0CD6B8946B12A62C` |
| 7 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | 61 MB | 59 MB | prod | `C6A3C1C570E1C39F` |
| 8 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | 55 MB | 54 MB | — | `0E601B3D12D0B438` |
| 9 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | 66 MB | 64 MB | prod | `2073F4958E35CF71` |
| 10 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | 57 MB | 57 MB | — | `CF11DBD2873808B6` |
| 11 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | 54 MB | 53 MB | — | `7936742F5C989564` |
| 12 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | 58 MB | 56 MB | — | `B61F34EBE60DFF33` |
| 13 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | 77 MB | 78 MB | prod | `AD4582F780FCB092` |
| 14 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | 65 MB | 66 MB | prod | `88AC08FC465D39B8` |
| 15 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | 104 MB | 147 MB | — | `186F66EB80AF5D7D` |
| 16 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | 51 MB | 52 MB | prod | `E265C0642A99DA55` |
| 17 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | 54 MB | 53 MB | — | `52B686735A576C4E` |
| 18 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | 65 MB | 64 MB | prod | `D5DBFDD0F484838D` |
| 19 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | 60 MB | 59 MB | prod | `5F018C068A100C07` |
| 20 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | 57 MB | 56 MB | — | `50C3A6FC08D81122` |
| 21 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | 71 MB | 69 MB | prod | `B74E83A44A11DF7A` |
| 22 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | 65 MB | 61 MB | prod | `EC5E6A8668B712CE` |
| 23 | [Kinnav](https://github.com/AmericanGroupLLC/Kinnav) | 61 MB | 60 MB | prod | `C4F2A4B6F7965A5C` |
| 24 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | 58 MB | 57 MB | — | `D14CB7E2BEA014E7` |
| 25 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | 55 MB | 54 MB | — | `18054934B2F1B6AB` |
| 26 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | 55 MB | 54 MB | — | `E485BD0690C73798` |
| 27 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | 63 MB | 64 MB | prod | `A693834AA710F05D` |
| 28 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | 58 MB | 57 MB | — | `96342EAA305E4DCB` |
| 29 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | 57 MB | 56 MB | — | `25D5C0D942A489F5` |
| 30 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | 61 MB | 61 MB | — | `5B6A4604F1861642` |
| 31 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | 70 MB | 68 MB | prod | `ED2D941BFF746590` |
| 32 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | 102 MB | 106 MB | prod | `767CD1F7FB490B7C` |
| 33 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | 53 MB | 52 MB | — | `101E79E6A14864C7` |
| 34 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | 57 MB | 56 MB | — | `F123FD917E9E9DC5` |
| 35 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | 67 MB | 63 MB | — | `A18905EBAF282BB1` |
| 36 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | 58 MB | 58 MB | — | `2731B1A2D0201887` |
| 37 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | 51 MB | 50 MB | — | `D3AAE284B3D6B1D4` |
| 38 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | 63 MB | 60 MB | — | `72D9176A72E4F875` |
| 39 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | 62 MB | 59 MB | prod | `565DBEE81C473EBC` |
| 40 | [Verba](https://github.com/AmericanGroupLLC/Verba) | 68 MB | 68 MB | prod | `5607DDEE124203A9` |
| 41 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | 62 MB | 59 MB | prod | `99635E5EB1FFB48D` |
| 42 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | 50 MB | 48 MB | — | `E0D8203064D9D384` |
| 43 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | 88 MB | 89 MB | prod | `2EA595F41FA61468` |

Both are published to a GitHub Release in each app's own repository, so an
app can be installed and tried without a build machine, a keystore or a Play
account. The APK sideloads onto a device; the AAB is what Play accepts and
cannot be installed by hand — neither one does both jobs.

Locally they are kept outside every git repository (`~/agl/.dist/`) so a stray
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
| 7 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroupllc.bodyquest` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 9 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | `ca-app-pub-8528784688453695~5377349094` | `ca-app-pub-8528784688453695~9148987425` | `ca-app-pub-8528784688453695/7665581023` | `ca-app-pub-8528784688453695/7474009334` |
| 21 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | `${admobAppId}` _(build-time)_ | `$(ADMOB_APP_ID)` _(build-time)_ | `ca-app-pub-8528784688453695/1143402684` | `ca-app-pub-8528784688453695/8340879191` |
| 22 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | `ca-app-pub-8528784688453695~9265279754` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/1222409251` | `ca-app-pub-8528784688453695/9950162694` |
| 32 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | `${admobAppId}` _(build-time)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 35 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroupllc.radiotune` | `ca-app-pub-8528784688453695~7770953426` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/4087643109` | `ca-app-pub-8528784688453695/2327055058` |
| 38 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | `ca-app-pub-8528784688453695~8044208178` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/3721819782` | `ca-app-pub-8528784688453695/5528514029` |
| 39 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | `ca-app-pub-8528784688453695~2309537905` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/5539491423` | `ca-app-pub-8528784688453695/9095593054` |
| 40 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| 41 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | `ca-app-pub-8528784688453695~2836542125` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/6914604113` | `ca-app-pub-8528784688453695/9569471431` |
| 43 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroupllc.yourtube` | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |

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
**29 of 43** match a bundle id this portfolio builds.
Refresh with `bundle exec ruby scripts/appstore_records.rb`.

A bundle id that does not match a record is not a warning at upload time —
it is a rejected build.

**14 apps have no matching record:**

| # | App | Bundle id it builds with |
| --: | --- | --- |
| 1 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` |
| 7 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroupllc.bodyquest` |
| 13 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroupllc.dailypulse` |
| 16 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.fashionfactory` |
| 17 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` |
| 18 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` |
| 19 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `com.americangroupllc.herjourney` |
| 22 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` |
| 27 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` |
| 33 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` |
| 34 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` |
| 35 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroupllc.radiotune` |
| 40 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` |
| 43 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroupllc.yourtube` |

**11 records match no app.** Mostly the rename history —
iFoodRadar became GroceryMatch, OfflineBuddy became Verba, iDealZap
became GadgetNest, StayDeal became TripNest. Each is a decision: rename
the record and keep its history, or leave it and create a new one. A
bundle id cannot be changed once an app is published.

| Bundle id | Store record |
| --- | --- |
| `com.americangroup.bodyquest` | BodyQuest |
| `com.americangroup.daily-pulse` | daily-pulse |
| `com.americangroup.radiotune` | RadioTune World |
| `com.americangroup.yourtube` | YourTube: Watch & Discover |
| `com.americangroupllc.Mykarma` | iMykarma |
| `com.americangroupllc.careerupgradeai` | CareerUpgradeAI |
| `com.americangroupllc.dealzap` | iDealZap |
| `com.americangroupllc.foodradar` | iFoodRadar |
| `com.americangroupllc.offlinebuddy` | OfflineBuddy |
| `com.americangroupllc.staydeal` | StayDeal |
| `com.americangroupllc.styleradar` | StyleRadar |

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
| 1 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 2 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 3 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 4 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 5 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 6 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 7 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 8 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 9 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 10 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 11 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 12 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `mobile/codedeal_app/android/app/google-services.json` | `mobile/codedeal_app/ios/Runner/GoogleService-Info.plist` | **missing** |
| 13 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 14 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 15 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 16 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 17 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 18 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 19 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 20 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 21 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 22 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 23 | [Kinnav](https://github.com/AmericanGroupLLC/Kinnav) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 24 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 25 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 26 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 27 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 28 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 29 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 30 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `flutter-mobile-app/android/app/google-services.json` | `flutter-mobile-app/ios/Runner/GoogleService-Info.plist` | **missing** |
| 31 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 32 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 33 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 34 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 35 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 36 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 37 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 38 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | **missing** |
| 39 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 40 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 41 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 42 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |
| 43 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | **missing** |

**0 apps have no Firebase config.** Until they do, `AglCrash.isActive` is
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
| 4 | Firebase config files | Firebase console, project `americangroupllc-5bdfc` | Crash reporting | **0 of 43 missing** |
| 5 | AdMob apps + unit ids | AdMob console | Live ads for the apps that earn nothing today | **4 apps have no record** |
| 6 | A GDPR message | AdMob → Privacy & messaging | The consent form; the code is already in every ad app | **not published** |
| 7 | Store descriptions | `store/apps/<repo>.json`, then `scripts/store_metadata.py generate` | Both listings require one | **0 apps have none** |
| 8 | Privacy policy + support URLs | Your hosting | Both listings | templated; the pages must exist |

Already done and verified: the App Store Connect key and its issuer id, both
confirmed against the live API, and 0 upload keystores loaded here.
