# Store-release readiness

Measured across 43 repositories (43 of them Flutter apps) by `scripts/audit_release_readiness.py`. Raw data: [`release-readiness.json`](release-readiness.json).

## Portfolio totals

| Signal | Apps with it | Apps without |
| --- | ---: | ---: |
| Release signing config | 43 | 0 |
| Crashlytics wired in main() | 36 | 7 |
| firebase_crashlytics dependency | 6 | 37 |
| google-services.json | 0 | 43 |
| GoogleService-Info.plist | 0 | 43 |
| google_mobile_ads dependency | 11 | 32 |
| Android AdMob app id | 11 | 32 |
| iOS AdMob app id | 11 | 32 |
| Fastlane Fastfile | 40 | 3 |
| Release workflow | 40 | 3 |
| CI workflow | 41 | 2 |
| Store metadata | 42 | 1 |
| l10n.yaml | 11 | 32 |
| iOS privacy manifest | 37 | 6 |

## Per-app

| App | ver | sign | crash | ads(A/i) | fastlane | CI | locales | l10n calls | tests |
| --- | --- | :-: | :-: | :-: | :-: | :-: | ---: | ---: | ---: |
| AeroSwift | 1.0.0+1 | yes | — | —/— | — | — | 0 | 0 | 9 |
| AGCleaner | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 4 |
| AGrammarly | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 6 |
| AGRecorder | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 4 |
| AGStudio | 1.0.0+1 | yes | — | —/— | yes | yes | 12 | 135 | 10 |
| ApexMarketWatch | 1.0.0+1 | yes | — | —/— | — | — | 0 | 0 | 9 |
| BodyQuest | 1.1.0+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 6 |
| BuddyPlay | 1.0.0+1 | yes | — | —/— | yes | yes | 0 | 0 | 10 |
| CalcMaster | 4.0.2+5 | yes | yes | yes/yes | yes | yes | 12 | 58 | 21 |
| CarDeal | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 5 |
| ChefCount | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 4 |
| CodeDeal | 1.4.0+14 | yes | yes | —/— | yes | yes | 19 | 0 | 2 |
| daily-pulse | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 79 | 9 |
| DriftDate | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 18 |
| EventSpark | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 9 |
| FashionFactory | 2.2.0+4 | yes | — | —/— | yes | yes | 0 | 0 | 42 |
| GadgetNest | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 9 |
| GroceryMatch | 2.1.0+2 | yes | yes | —/— | yes | yes | 0 | 0 | 46 |
| HerJourney | 1.2.0+3 | yes | yes | —/— | yes | yes | 0 | 0 | 7 |
| HomeWise | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 5 |
| iMaps | 1.0.2+5 | yes | yes | yes/yes | yes | yes | 15 | 26 | 24 |
| iMeasure | 5.0.1+3 | yes | yes | yes/yes | yes | yes | 0 | 0 | 11 |
| Kinnav | 1.0.1+4 | yes | yes | —/— | yes | yes | 6 | 159 | 23 |
| MileMaster | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 3 |
| MyCard | 1.0.0+1 | yes | — | —/— | yes | yes | 0 | 0 | 8 |
| MyFinance | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 4 |
| MyHealth | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 8 |
| NearServe | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 5 |
| NewsBoard | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 7 |
| NexusTransferPay | 1.0.0+1 | yes | yes | —/— | yes | yes | 25 | 16 | 8 |
| Photriya | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 17 |
| PilotEnRoute | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 0 | 14 |
| PlantPulse | 1.0.0+1 | yes | — | —/— | — | — | 0 | 0 | 11 |
| portfolio-board | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 4 |
| radiotune | 2.0.1+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 12 |
| RideZap | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 5 |
| RoomCraft | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 4 |
| TripNest | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 0 | 14 |
| Uscis-Case | 1.0.2+4 | yes | yes | yes/yes | yes | yes | 0 | 0 | 10 |
| Verba | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 1 | 29 |
| VirtuBand | 1.0.1+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 7 |
| WiFiTrail | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 4 | 5 |
| yourtube | 1.0.2+4 | yes | yes | yes/yes | yes | yes | 0 | 0 | 6 |

## Blocking gaps, by app

- **AeroSwift** — crash reporting not initialised in main(); no Fastlane lanes; no release workflow
- **AGStudio** — crash reporting not initialised in main()
- **ApexMarketWatch** — crash reporting not initialised in main(); no Fastlane lanes; no release workflow
- **BuddyPlay** — crash reporting not initialised in main()
- **FashionFactory** — crash reporting not initialised in main()
- **MyCard** — crash reporting not initialised in main()
- **PlantPulse** — crash reporting not initialised in main(); no Fastlane lanes; no release workflow
