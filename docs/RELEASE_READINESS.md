# Store-release readiness

Measured across 43 repositories (37 of them Flutter apps) by `scripts/audit_release_readiness.py`. Raw data: [`release-readiness.json`](release-readiness.json).

## Portfolio totals

| Signal | Apps with it | Apps without |
| --- | ---: | ---: |
| Release signing config | 37 | 0 |
| Crashlytics wired in main() | 36 | 1 |
| firebase_crashlytics dependency | 6 | 31 |
| google-services.json | 0 | 37 |
| GoogleService-Info.plist | 0 | 37 |
| google_mobile_ads dependency | 11 | 26 |
| Android AdMob app id | 11 | 26 |
| iOS AdMob app id | 11 | 26 |
| Fastlane Fastfile | 37 | 0 |
| Release workflow | 37 | 0 |
| CI workflow | 37 | 0 |
| Store metadata | 37 | 0 |
| l10n.yaml | 10 | 27 |
| iOS privacy manifest | 37 | 0 |

## Per-app

| App | ver | sign | crash | ads(A/i) | fastlane | CI | locales | l10n calls | tests |
| --- | --- | :-: | :-: | :-: | :-: | :-: | ---: | ---: | ---: |
| AGCleaner | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 4 |
| AGrammarly | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 6 |
| AGRecorder | 1.0.0+1 | yes | yes | —/— | yes | yes | 12 | 3 | 4 |
| BodyQuest | 1.1.0+2 | yes | yes | yes/yes | yes | yes | 0 | 0 | 6 |
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
| MyFinance | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 4 |
| MyHealth | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 8 |
| NearServe | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 5 |
| NewsBoard | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 7 |
| NexusTransferPay | 1.0.0+1 | yes | yes | —/— | yes | yes | 25 | 16 | 8 |
| Photriya | 1.0.0+1 | yes | yes | —/— | yes | yes | 0 | 0 | 17 |
| PilotEnRoute | 1.0.0+1 | yes | yes | yes/yes | yes | yes | 0 | 0 | 14 |
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

- **FashionFactory** — crash reporting not initialised in main()
