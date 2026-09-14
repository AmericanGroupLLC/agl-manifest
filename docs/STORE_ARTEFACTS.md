# Store artefacts — both platforms, every app

Built on the development machine on 2026-09-14 and verified after the fact,
not asserted. Android bundles are compared against each app's own upload
keystore; iOS `.ipa`s are unzipped and re-checked with `codesign` and the
embedded provisioning profile.

Artefacts live in `/Users/spatchava/agl/.dist` (outside every git repo — 4.2 GB).

| App | .aab | MB | .ipa | MB | signature verified |
| --- | :-: | ---: | :-: | ---: | :-: |
| AeroSwift | SIGNED | 50 | EXPORTED | 21 | yes |
| AGCleaner | SIGNED | 46 | EXPORTED | 20 | yes |
| AGrammarly | SIGNED | 50 | EXPORTED | 21 | yes |
| AGRecorder | SIGNED | 46 | EXPORTED | 20 | yes |
| AGStudio | SIGNED | 51 | EXPORTED | 22 | yes |
| ApexMarketWatch | SIGNED | 50 | EXPORTED | 21 | yes |
| BodyQuest | SIGNED | 57 | EXPORTED | 25 | yes |
| BuddyPlay | SIGNED | 51 | EXPORTED | 21 | yes |
| CalcMaster | SIGNED | 61 | EXPORTED | 26 | yes |
| CarDeal | SIGNED | 53 | EXPORTED | 22 | yes |
| ChefCount | SIGNED | 47 | EXPORTED | 21 | yes |
| CodeDeal | SIGNED | 53 | EXPORTED | 22 | yes |
| daily-pulse | SIGNED | 72 | EXPORTED | 42 | yes |
| DriftDate | SIGNED | 61 | EXPORTED | 27 | yes |
| EventSpark | SIGNED | 98 | EXPORTED | 54 | yes |
| FashionFactory | SIGNED | 49 | EXPORTED | 20 | yes |
| GadgetNest | SIGNED | 50 | EXPORTED | 22 | yes |
| GroceryMatch | SIGNED | 61 | EXPORTED | 29 | yes |
| HerJourney | SIGNED | 56 | EXPORTED | 24 | yes |
| HomeWise | SIGNED | 53 | EXPORTED | 22 | yes |
| iMaps | SIGNED | 66 | EXPORTED | 29 | yes |
| iMeasure | SIGNED | 60 | EXPORTED | 26 | yes |
| Kinnav | SIGNED | 56 | EXPORTED | 32 | yes |
| MileMaster | SIGNED | 47 | EXPORTED | 20 | yes |
| MyCard | SIGNED | 51 | EXPORTED | 21 | yes |
| MyFinance | SIGNED | 47 | EXPORTED | 20 | yes |
| MyHealth | SIGNED | 59 | EXPORTED | 24 | yes |
| NearServe | SIGNED | 54 | EXPORTED | 22 | yes |
| NewsBoard | SIGNED | 52 | EXPORTED | 22 | yes |
| NexusTransferPay | SIGNED | 56 | EXPORTED | 24 | yes |
| Photriya | SIGNED | 65 | EXPORTED | 29 | yes |
| PilotEnRoute | SIGNED | 96 | EXPORTED | 53 | yes |
| PlantPulse | SIGNED | 49 | EXPORTED | 21 | yes |
| portfolio-board | SIGNED | 52 | EXPORTED | 22 | yes |
| radiotune | SIGNED | 62 | EXPORTED | 26 | yes |
| RideZap | SIGNED | 54 | EXPORTED | 22 | yes |
| RoomCraft | SIGNED | 47 | EXPORTED | 21 | yes |
| TripNest | SIGNED | 58 | EXPORTED | 25 | yes |
| Uscis-Case | SIGNED | 57 | EXPORTED | 25 | yes |
| Verba | SIGNED | 65 | EXPORTED | 30 | yes |
| VirtuBand | SIGNED | 57 | EXPORTED | 25 | yes |
| WiFiTrail | SIGNED | 45 | EXPORTED | 20 | yes |
| yourtube | SIGNED | 83 | EXPORTED | 48 | yes |

**43/43 Android bundles signed with the app's own upload key.**
**43/43 iOS archives exported as App Store `.ipa`s.**

Every `.ipa` is signed `Apple Distribution: American Group LLC (TLH7Z3G27A)`
with `get-task-allow = false`, and `codesign --verify --strict` passes on all 43.

## What this does and does not prove

It proves each app compiles and signs into an artefact a store will accept for
upload. It does not prove the app behaves correctly once installed — none of
these 43 builds has been launched and looked at.

MA-005 is closed: a distribution certificate exists (`Q385P88X3N`, valid to
2027-06-09) and all 43 App Store provisioning profiles were created from the
App Store Connect API and are ACTIVE.
