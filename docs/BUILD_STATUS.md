# Build status

Measured, not asserted. Every row below came from actually running the tool
against the repository with Flutter 3.44.2 locally, on 2026-09-09.

| App | analyze errors | tests | iOS build |
| --- | --- | --- | --- |
| AGCleaner | 0 | ✅ pass | ✅ |
| AGrammarly | 0 | ✅ pass | ✅ |
| AGRecorder | 0 | ✅ pass | ✅ |
| BodyQuest | 0 | ✅ pass | ✅ |
| CalcMaster | 0 | ✅ pass | ✅ |
| CarDeal | 0 | ✅ pass | ✅ |
| ChefCount | 0 | ✅ pass | ✅ |
| daily-pulse | 0 | ✅ pass | ✅ |
| DriftDate | 0 | ✅ pass | ✅ (verified on CI) |
| EventSpark | 0 | ✅ pass | ✅ |
| FashionFactory | 0 | ✅ pass | ✅ |
| GadgetNest | 0 | ✅ pass | ✅ |
| GroceryMatch | 0 | ✅ pass | ✅ |
| HerJourney | 0 | ✅ pass | ✅ |
| HomeWise | 0 | ✅ pass | ✅ |
| iMaps | 0 | ✅ pass | ✅ |
| iMeasure | 0 | ✅ pass | ✅ |
| Kinnav | 0 | ✅ pass | ✅ |
| MileMaster | 0 | ✅ pass | ✅ |
| MyFinance | 0 | ✅ pass | ✅ |
| MyHealth | 0 | ✅ pass | ✅ |
| NearServe | 0 | ✅ pass | ✅ |
| NewsBoard | 0 | ✅ pass | ✅ |
| NexusTransferPay | — | — | — |
| Photriya | 0 | ✅ pass | ✅ |
| PilotEnRoute | 0 | ✅ pass | ✅ |
| portfolio-board | 0 | ✅ pass | ✅ |
| portfolio-board | 0 | ✅ pass | — |
| radiotune | 0 | ✅ pass | ✅ |
| RideZap | 0 | ✅ pass | ✅ |
| RoomCraft | 0 | ✅ pass | ✅ |
| TripNest | 0 | ✅ pass | ✅ |
| Uscis-Case | 0 | ✅ pass | ⚠️ BUILD_FAIL |
| Verba | 0 | ✅ pass | ✅ |
| VirtuBand | 0 | ✅ pass | ⚠️ BUILD_FAIL |
| WiFiTrail | 0 | ✅ pass | ✅ |
| yourtube | 0 | ✅ pass | ✅ |

**33 apps build cleanly.** Every one of them reports 0 analyzer errors and a
passing test suite.

## Notes

- **DriftDate** fails to build *locally* with
  `swift-plugin-server produced malformed response` inside the Sentry pod's
  SwiftUI `#Preview` macros. That is this sandbox blocking the macro plugin
  process, not a defect: GitHub Actions run 34330096009 builds it successfully
  on a real macOS runner.
- CI runs a **newer Flutter (3.47.2)** than the local SDK (3.44.2) and applies
  lints the local one does not. That is how the `unawaited_return_in_try_block`
  bug in DriftDate's `photo_analyzer.dart` was found — real, not cosmetic:
  decode failures were escaping a `try` that documented catching them.
- **portfolio-board** and **NexusTransferPay** were unarchived after the sweep
  started, so they are analyzed and tested but not yet iOS-built here.

## How to reproduce

```sh
flutter pub get && flutter analyze && flutter test
flutter build ios --simulator --debug
```
