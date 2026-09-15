# Store-release readiness

Measured across 43 repositories (43 of them Flutter apps) by `scripts/audit_release_readiness.py`. Raw data: [`release-readiness.json`](release-readiness.json).

## Portfolio totals

| Signal | Apps with it | Apps without |
| --- | ---: | ---: |
| Release signing config | 43 | 0 |
| Crashlytics wired in main() | 42 | 1 |
| firebase_crashlytics dependency | 7 | 36 |
| google-services.json | 0 | 43 |
| GoogleService-Info.plist | 0 | 43 |
| google_mobile_ads dependency | 11 | 32 |
| Android AdMob app id | 11 | 32 |
| iOS AdMob app id | 11 | 32 |
| Fastlane Fastfile | 43 | 0 |
| Release workflow | 43 | 0 |
| CI workflow | 41 | 2 |
| Store metadata | 43 | 0 |
| l10n.yaml | 11 | 32 |
| iOS privacy manifest | 43 | 0 |

## Per-app

| App | ver | sign | crash | ads(A/i) | fastlane | CI | locales | l10n calls | tests |
| --- | --- | :-: | :-: | :-: | :-: | :-: | ---: | ---: | ---: |
| AeroSwift | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 12 |
| AGCleaner | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 6 |
| AGrammarly | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 8 |
| AGRecorder | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 7 |
| AGStudio | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 135 | 13 |
| ApexMarketWatch | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 12 |
| BodyQuest | 1.1.0+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 13 |
| BuddyPlay | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 12 |
| CalcMaster | 4.0.2+5 | yes | yes | yes/yes | yes | yes | 12 | 58 | 24 |
| CarDeal | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 1 | 18 |
| ChefCount | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 7 |
| CodeDeal | 1.4.0+14 | yes | yes | —/— | yes | yes | 19 | 0 | 11 |
| daily-pulse | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 82 | 16 |
| DriftDate | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 20 |
| EventSpark | 1.0.0+2 | yes | yes | —/— | yes | yes | 0 | 0 | 14 |
| FashionFactory | 2.2.0+4 | yes | — | —/— | yes | yes | 0 | 0 | 43 |
| GadgetNest | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 11 |
| GroceryMatch | 2.1.0+2 | yes | yes | —/— | yes | yes | 0 | 0 | 48 |
| HerJourney | 1.2.0+3 | yes | yes | —/— | yes | yes | 0 | 0 | 9 |
| HomeWise | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 10 |
| iMaps | 1.0.2+5 | yes | yes | yes/yes | yes | yes | 15 | 34 | 29 |
| iMeasure | 5.0.1+3 | yes | yes | yes/yes | yes | yes | 0 | 0 | 13 |
| Kinnav | 1.0.1+4 | yes | yes | —/— | yes | yes | 6 | 161 | 25 |
| MileMaster | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 5 |
| MyCard | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 11 |
| MyFinance | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 6 |
| MyHealth | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 23 |
| NearServe | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 22 |
| NewsBoard | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 9 |
| NexusTransferPay | 1.0.0+1 | yes | yes | —/— | yes | yes | 25 | 16 | 10 |
| Photriya | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 26 |
| PilotEnRoute | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 0 | 27 |
| PlantPulse | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 13 |
| portfolio-board | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 10 |
| radiotune | 2.0.1+3 | yes | yes | yes/yes | yes | yes | 0 | 0 | 13 |
| RideZap | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 17 |
| RoomCraft | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 7 |
| TripNest | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 0 | 16 |
| Uscis-Case | 1.0.2+4 | yes | yes | yes/yes | yes | yes | 0 | 0 | 12 |
| Verba | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 1 | 33 |
| VirtuBand | 1.0.1+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 9 |
| WiFiTrail | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 5 | 8 |
| yourtube | 1.0.2+4 | yes | yes | yes/yes | yes | yes | 0 | 0 | 17 |

## Blocking gaps, by app

- **FashionFactory** — crash reporting not initialised in main()
