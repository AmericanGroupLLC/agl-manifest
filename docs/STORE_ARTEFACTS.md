# Store artefacts — every app, both platforms, all three formats

Built on the development machine on 2026-09-14 and **verified after the fact**.
Android bundles and APKs are checked against each app's own upload keystore;
each `.ipa` is unzipped and re-checked with `codesign` plus its embedded
provisioning profile; each store privacy/support URL was actually fetched.

Artefacts live in `/Users/spatchava/agl/.dist` (outside every git repo, 5.9 GB).

| App | .aab | MB | .apk | MB | .ipa | MB | ipa sig | policy URLs |
| --- | :-: | ---: | :-: | ---: | :-: | ---: | :-: | :-: |
| AeroSwift | SIGNED | 50 | SIGNED | 51 | EXPORTED | 21 | yes | 200 |
| AGCleaner | SIGNED | 46 | SIGNED | 46 | EXPORTED | 20 | yes | 200 |
| AGrammarly | SIGNED | 50 | SIGNED | 50 | EXPORTED | 21 | yes | 200 |
| AGRecorder | SIGNED | 46 | SIGNED | 46 | EXPORTED | 20 | yes | 200 |
| AGStudio | SIGNED | 51 | SIGNED | 52 | EXPORTED | 22 | yes | 200 |
| ApexMarketWatch | SIGNED | 50 | SIGNED | 51 | EXPORTED | 21 | yes | 200 |
| BodyQuest | SIGNED | 57 | SIGNED | 56 | EXPORTED | 25 | yes | 200 |
| BuddyPlay | SIGNED | 51 | SIGNED | 52 | EXPORTED | 21 | yes | 200 |
| CalcMaster | SIGNED | 61 | SIGNED | 61 | EXPORTED | 26 | yes | 200 |
| CarDeal | SIGNED | 53 | SIGNED | 54 | EXPORTED | 22 | yes | 200 |
| ChefCount | SIGNED | 47 | SIGNED | 47 | EXPORTED | 21 | yes | 200 |
| CodeDeal | SIGNED | 53 | SIGNED | 53 | EXPORTED | 22 | yes | 200 |
| daily-pulse | SIGNED | 72 | SIGNED | 75 | EXPORTED | 42 | yes | 200 |
| DriftDate | SIGNED | 61 | SIGNED | 63 | EXPORTED | 27 | yes | 200 |
| EventSpark | SIGNED | 98 | SIGNED | 140 | EXPORTED | 54 | yes | 200 |
| FashionFactory | SIGNED | 49 | SIGNED | 50 | EXPORTED | 20 | yes | 200 |
| GadgetNest | SIGNED | 50 | SIGNED | 51 | EXPORTED | 22 | yes | 200 |
| GroceryMatch | SIGNED | 61 | SIGNED | 61 | EXPORTED | 29 | yes | 200 |
| HerJourney | SIGNED | 56 | SIGNED | 56 | EXPORTED | 24 | yes | 200 |
| HomeWise | SIGNED | 53 | SIGNED | 53 | EXPORTED | 22 | yes | 200 |
| iMaps | SIGNED | 66 | SIGNED | 65 | EXPORTED | 29 | yes | 200 |
| iMeasure | SIGNED | 60 | SIGNED | 58 | EXPORTED | 26 | yes | 200 |
| Kinnav | SIGNED | 56 | SIGNED | 57 | EXPORTED | 32 | yes | 200 |
| MileMaster | SIGNED | 47 | SIGNED | 47 | EXPORTED | 20 | yes | 200 |
| MyCard | SIGNED | 51 | SIGNED | 52 | EXPORTED | 21 | yes | 200 |
| MyFinance | SIGNED | 47 | SIGNED | 47 | EXPORTED | 20 | yes | 200 |
| MyHealth | SIGNED | 59 | SIGNED | 61 | EXPORTED | 24 | yes | 200 |
| NearServe | SIGNED | 54 | SIGNED | 54 | EXPORTED | 22 | yes | 200 |
| NewsBoard | SIGNED | 52 | SIGNED | 53 | EXPORTED | 22 | yes | 200 |
| NexusTransferPay | SIGNED | 56 | SIGNED | 58 | EXPORTED | 24 | yes | 200 |
| Photriya | SIGNED | 65 | SIGNED | 64 | EXPORTED | 29 | yes | 200 |
| PilotEnRoute | SIGNED | 96 | SIGNED | 101 | EXPORTED | 53 | yes | 200 |
| PlantPulse | SIGNED | 49 | SIGNED | 49 | EXPORTED | 21 | yes | 200 |
| portfolio-board | SIGNED | 52 | SIGNED | 53 | EXPORTED | 22 | yes | 200 |
| radiotune | SIGNED | 62 | SIGNED | 60 | EXPORTED | 26 | yes | 200 |
| RideZap | SIGNED | 54 | SIGNED | 55 | EXPORTED | 22 | yes | 200 |
| RoomCraft | SIGNED | 47 | SIGNED | 48 | EXPORTED | 21 | yes | 200 |
| TripNest | SIGNED | 58 | SIGNED | 57 | EXPORTED | 25 | yes | 200 |
| Uscis-Case | SIGNED | 57 | SIGNED | 56 | EXPORTED | 25 | yes | 200 |
| Verba | SIGNED | 65 | SIGNED | 65 | EXPORTED | 30 | yes | 200 |
| VirtuBand | SIGNED | 57 | SIGNED | 56 | EXPORTED | 25 | yes | 200 |
| WiFiTrail | SIGNED | 45 | SIGNED | 45 | EXPORTED | 20 | yes | 200 |
| yourtube | SIGNED | 83 | SIGNED | 85 | EXPORTED | 48 | yes | 200 |

**43/43 `.aab`** and **43/43 `.apk`** signed with the app's own upload key (43 distinct keys — Play binds an upload key per app).
**43/43 `.ipa`** exported for the App Store.

Every `.ipa` is signed `Apple Distribution: American Group LLC (TLH7Z3G27A)` with
`get-task-allow = false`; `codesign --verify --strict` passes on all 43.
All 43/43 privacy and support URLs returned HTTP 200.

## What this proves, and what it does not

It proves every app compiles and signs into an artefact each store will accept
for upload, and that its policy URLs resolve. It does **not** prove the app
behaves correctly once installed — none of these 43 builds has been launched
and looked at. That remains the largest untested gap in the programme.
