# Registering the apps in Firebase

> **Done — kept for the procedure, not the task.** Every one of the 43 apps is
> registered and carries its real config files, and Firebase is live on both
> platforms: Crashlytics, Analytics, Performance Monitoring and Remote Config.
> `scripts/firebase_register.py` did the registration; MA-006 records it.
>
> Two things this page used to get wrong. `AglCrash.isActive` is no longer
> false everywhere. And the portfolio spans **three** projects, not one — a
> project caps how many apps it holds, so the apps are split across
> `americangroupllc-5bdfc` (15), `americangroupllc-agl2` (15) and
> `americangroupllc-agl3` (13). Never assume an app is in `-5bdfc`; read the
> `project_id` out of the app's own `google-services.json`.
>
> The bundle ids in the table below were written before the move to
> `com.americangroupllc.*` and are corrected here; `docs/APP_IDENTIFIERS.md` is
> generated and is the source of truth.

## For each row

1. **Project settings → Your apps → Add app → Android**, package name exactly as
   below. Download `google-services.json` → the Android path.
2. **Add app → iOS**, bundle id exactly as below. Download
   `GoogleService-Info.plist` → the iOS path.
3. Commit both. They are **not** gitignored, deliberately: Google documents them
   as non-secret, they ship inside the binary anyway, and CI needs them in the
   checkout for the Crashlytics Gradle plugin to apply and upload a mapping file.

A mismatched package name is not a warning — Crashlytics silently reports
nothing, which looks exactly like an app that never crashes.

| App | Android package | iOS bundle id | google-services.json → | GoogleService-Info.plist → |
| --- | --- | --- | --- | --- |
| AGCleaner | `com.americangroupllc.agcleaner` | `com.americangroupllc.agcleaner` | `android/app/` | `ios/Runner/` |
| AGrammarly | `com.americangroupllc.agrammarly` | `com.americangroupllc.agrammarly` | `mobile/android/app/` | `mobile/ios/Runner/` |
| AGRecorder | `com.americangroupllc.agrecorder` | `com.americangroupllc.agrecorder` | `android/app/` | `ios/Runner/` |
| BodyQuest | `com.americangroupllc.bodyquest` | `com.americangroupllc.bodyquest` | `android/app/` | `ios/Runner/` |
| CalcMaster | `com.americangroupllc.calcmaster` | `com.americangroupllc.calcmaster` | `android/app/` | `ios/Runner/` |
| CarDeal | `com.americangroupllc.cardeal` | `com.americangroupllc.cardeal` | `mobile/android/app/` | `mobile/ios/Runner/` |
| ChefCount | `com.americangroupllc.chefcount` | `com.americangroupllc.chefcount` | `android/app/` | `ios/Runner/` |
| CodeDeal | `com.americangroupllc.codedeal` | `com.americangroupllc.codedeal` | `mobile/codedeal_app/android/app/` | `mobile/codedeal_app/ios/Runner/` |
| daily-pulse | `com.americangroupllc.dailypulse` | `com.americangroupllc.dailypulse` | `android/app/` | `ios/Runner/` |
| DriftDate | `com.americangroupllc.driftdate` | `com.americangroupllc.driftdate` | `android/app/` | `ios/Runner/` |
| EventSpark | `com.americangroupllc.eventspark` | `com.americangroupllc.eventspark` | `mobile/android/app/` | `mobile/ios/Runner/` |
| FashionFactory | `com.americangroupllc.styleradar` | `com.americangroupllc.styleradar` | `android/app/` | `ios/Runner/` |
| GadgetNest | `com.americangroupllc.gadgetnest` | `com.americangroupllc.gadgetnest` | `android/app/` | `ios/Runner/` |
| GroceryMatch | `com.americangroupllc.grocerymatch` | `com.americangroupllc.grocerymatch` | `android/app/` | `ios/Runner/` |
| HerJourney | `com.americangroupllc.her_journey` | `com.americangroupllc.herJourney` | `android/app/` | `ios/Runner/` |
| HomeWise | `com.americangroupllc.homewise` | `com.americangroupllc.homewise` | `mobile/android/app/` | `mobile/ios/Runner/` |
| iMaps | `com.americangroupllc.imaps` | `com.americangroupllc.imaps` | `android/app/` | `ios/Runner/` |
| iMeasure | `com.americangroupllc.imeasure` | `com.americangroupllc.imeasure` | `android/app/` | `ios/Runner/` |
| Kinnav | `com.americangroupllc.kinnav` | `com.americangroupllc.kinnav` | `android/app/` | `ios/Runner/` |
| MileMaster | `com.americangroupllc.milemaster` | `com.americangroupllc.milemaster` | `android/app/` | `ios/Runner/` |
| MyFinance | `com.americangroupllc.myfinance` | `com.americangroupllc.myfinance` | `android/app/` | `ios/Runner/` |
| MyHealth | `com.americangroupllc.myhealth` | `com.americangroupllc.myhealth` | `android/app/` | `ios/Runner/` |
| NearServe | `com.americangroupllc.nearserve` | `com.americangroupllc.nearserve` | `mobile/android/app/` | `mobile/ios/Runner/` |
| NewsBoard | `com.americangroupllc.newsboard` | `com.americangroupllc.newsboard` | `mobile/android/app/` | `mobile/ios/Runner/` |
| NexusTransferPay | `com.americangroupllc.nexuspay` | `com.americangroupllc.nexuspay` | `flutter-mobile-app/android/app/` | `flutter-mobile-app/ios/Runner/` |
| Photriya | `com.americangroupllc.photriya` | `com.americangroupllc.photriya` | `android/app/` | `ios/Runner/` |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | `com.americangroupllc.pilotenroute` | `android/app/` | `ios/Runner/` |
| portfolio-board | `com.americangroupllc.portfolioboard` | `com.americangroupllc.portfolioboard` | `mobile/android/app/` | `mobile/ios/Runner/` |
| radiotune | `com.americangroupllc.ratiotune` | `com.americangroupllc.ratiotune` | `android/app/` | `ios/Runner/` |
| RideZap | `com.americangroupllc.ridezap` | `com.americangroupllc.ridezap` | `mobile/android/app/` | `mobile/ios/Runner/` |
| RoomCraft | `com.americangroupllc.roomcraft` | `com.americangroupllc.roomcraft` | `android/app/` | `ios/Runner/` |
| TripNest | `com.americangroupllc.tripnest` | `com.americangroupllc.tripnest` | `mobile/android/app/` | `mobile/ios/Runner/` |
| Uscis-Case | `com.americangroupllc.usciscase` | `com.americangroupllc.usciscase` | `android/app/` | `ios/Runner/` |
| Verba | `com.americangroupllc.verba` | `com.americangroupllc.verba` | `android/app/` | `ios/Runner/` |
| VirtuBand | `com.americangroupllc.virtuband` | `com.americangroupllc.virtuband` | `android/app/` | `ios/Runner/` |
| WiFiTrail | `com.americangroupllc.wifitrail` | `com.americangroupllc.wifitrail` | `android/app/` | `ios/Runner/` |
| yourtube | `com.americangroupllc.yourtube` | `com.americangroupllc.yourtube` | `android/app/` | `ios/Runner/` |

## Verifying, once the files are in

```sh
flutter build apk --release          # the Crashlytics Gradle tasks appear in the log
# then, from a debug build with collection forced on:
#   AglCrash.sendTestReport()
```

It files a **non-fatal**, which shows up under Crashlytics → Non-fatals within a
couple of minutes. There is deliberately no `crash()` helper in
`agl_observability`: a real crash call is one careless merge from shipping.

For readable iOS stack traces, `bundle exec fastlane ios upload_dsyms` after a
build, then check **dSYMs: 0 missing** in the console.
