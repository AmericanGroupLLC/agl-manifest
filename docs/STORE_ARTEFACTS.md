# Store artefacts — rebuilt end to end

Rebuilt 2026-09-15 after the identifier change to `com.americangroupllc.<lowercase>`,
the placeholder-icon replacement, the foldable layout work and the honesty
remediation. Every earlier artefact was stale and was deleted before this run.

| App | .aab | .apk | .ipa | ipa signature verified |
| --- | :-: | :-: | :-: | :-: |
| AeroSwift | SIGNED | SIGNED | EXPORTED | yes |
| AGCleaner | SIGNED | SIGNED | EXPORTED | yes |
| AGrammarly | SIGNED | SIGNED | EXPORTED | yes |
| AGRecorder | SIGNED | SIGNED | EXPORTED | yes |
| AGStudio | SIGNED | SIGNED | EXPORTED | yes |
| ApexMarketWatch | SIGNED | SIGNED | EXPORTED | yes |
| BodyQuest | SIGNED | SIGNED | EXPORTED | yes |
| BuddyPlay | SIGNED | SIGNED | EXPORTED | yes |
| CalcMaster | SIGNED | SIGNED | EXPORTED | yes |
| CarDeal | SIGNED | SIGNED | EXPORTED | yes |
| ChefCount | SIGNED | SIGNED | EXPORTED | yes |
| CodeDeal | SIGNED | SIGNED | EXPORTED | yes |
| daily-pulse | SIGNED | SIGNED | EXPORTED | yes |
| DriftDate | SIGNED | SIGNED | EXPORTED | yes |
| EventSpark | SIGNED | SIGNED | EXPORTED | yes |
| FashionFactory | SIGNED | SIGNED | EXPORTED | yes |
| GadgetNest | SIGNED | SIGNED | EXPORTED | yes |
| GroceryMatch | SIGNED | SIGNED | EXPORTED | yes |
| HerJourney | SIGNED | SIGNED | EXPORTED | yes |
| HomeWise | SIGNED | SIGNED | EXPORTED | yes |
| iMaps | SIGNED | SIGNED | EXPORTED | yes |
| iMeasure | SIGNED | SIGNED | EXPORTED | yes |
| Kinnav | SIGNED | SIGNED | EXPORTED | yes |
| MileMaster | SIGNED | SIGNED | EXPORTED | yes |
| MyCard | SIGNED | SIGNED | EXPORTED | yes |
| MyFinance | SIGNED | SIGNED | EXPORTED | yes |
| MyHealth | SIGNED | SIGNED | EXPORTED | yes |
| NearServe | SIGNED | SIGNED | EXPORTED | yes |
| NewsBoard | SIGNED | SIGNED | EXPORTED | yes |
| NexusTransferPay | SIGNED | SIGNED | EXPORTED | yes |
| Photriya | SIGNED | SIGNED | EXPORTED | yes |
| PilotEnRoute | SIGNED | SIGNED | EXPORTED | yes |
| PlantPulse | SIGNED | SIGNED | EXPORTED | yes |
| portfolio-board | SIGNED | SIGNED | EXPORTED | yes |
| radiotune | SIGNED | SIGNED | EXPORTED | yes |
| RideZap | SIGNED | SIGNED | EXPORTED | yes |
| RoomCraft | SIGNED | SIGNED | EXPORTED | yes |
| TripNest | SIGNED | SIGNED | EXPORTED | yes |
| Uscis-Case | SIGNED | SIGNED | EXPORTED | yes |
| Verba | SIGNED | SIGNED | EXPORTED | yes |
| VirtuBand | SIGNED | SIGNED | EXPORTED | yes |
| WiFiTrail | SIGNED | SIGNED | EXPORTED | yes |
| yourtube | SIGNED | SIGNED | EXPORTED | yes |

**43/43 .aab** and **43/43 .apk**, each signed with that
app's *own* upload key — 43 distinct keys, because Play binds one per app.
**43/43 .ipa** exported for the App Store;
all 43 signed `Apple Distribution: American Group LLC (TLH7Z3G27A)` with
`get-task-allow = false`, `codesign --verify --strict` passing, and a bundle id
matching the manifest.

## What this does not prove

That the apps behave correctly once installed. Only 2 of 43 have been launched
and looked at. Compiling and signing is not working.
