# Registering the apps in Firebase

Everything in the code is wired and inert. `AglCrash.isActive` is false in
every build because no app has its config files, and the Gradle plugins apply
themselves the moment `google-services.json` appears — see
[`CRASHLYTICS.md`](CRASHLYTICS.md). This is the one-pass list for the console.

Project: **americangroupllc-5bdfc** —
[console](https://console.firebase.google.com/u/0/project/americangroupllc-5bdfc/crashlytics)

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
| AGrammarly | `com.americangroup.agrammarly` | `com.americangroup.agrammarly` | `mobile/android/app/` | `mobile/ios/Runner/` |
| AGRecorder | `com.americangroupllc.agrecorder` | `com.americangroupllc.agrecorder` | `android/app/` | `ios/Runner/` |
| BodyQuest | `com.americangroup.bodyquest` | `com.americangroup.bodyquest` | `android/app/` | `ios/Runner/` |
| CalcMaster | `com.americangroupllc.calcmaster` | `com.americangroupllc.calcmaster` | `android/app/` | `ios/Runner/` |
| CarDeal | `com.americangroupllc.cardeal` | `com.americangroupllc.cardeal` | `mobile/android/app/` | `mobile/ios/Runner/` |
| ChefCount | `com.americangroupllc.chefcount` | `com.americangroupllc.chefcount` | `android/app/` | `ios/Runner/` |
| CodeDeal | `com.americangroupllc.codedeal` | `com.americangroupllc.codedeal` | `mobile/codedeal_app/android/app/` | `mobile/codedeal_app/ios/Runner/` |
| daily-pulse | `com.americangroup.dailypulse` | `com.americangroup.dailypulse` | `android/app/` | `ios/Runner/` |
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
| NewsBoard | `com.americangroup.newsboard` | `com.americangroup.newsboard` | `mobile/android/app/` | `mobile/ios/Runner/` |
| NexusTransferPay | `com.americangroupllc.nexuspay` | `com.americangroupllc.nexuspay` | `flutter-mobile-app/android/app/` | `flutter-mobile-app/ios/Runner/` |
| Photriya | `com.americangroupllc.photriya` | `com.americangroupllc.photriya` | `android/app/` | `ios/Runner/` |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | `com.americangroupllc.pilotenroute` | `android/app/` | `ios/Runner/` |
| portfolio-board | `com.americangroupllc.portfolioboard` | `com.americangroupllc.portfolioboard` | `mobile/android/app/` | `mobile/ios/Runner/` |
| radiotune | `com.americangroup.ratiotune` | `com.americangroup.ratiotune` | `android/app/` | `ios/Runner/` |
| RideZap | `com.americangroupllc.ridezap` | `com.americangroupllc.ridezap` | `mobile/android/app/` | `mobile/ios/Runner/` |
| RoomCraft | `com.americangroupllc.roomcraft` | `com.americangroupllc.roomcraft` | `android/app/` | `ios/Runner/` |
| TripNest | `com.americangroupllc.tripnest` | `com.americangroupllc.tripnest` | `mobile/android/app/` | `mobile/ios/Runner/` |
| Uscis-Case | `com.americangroupllc.usciscase` | `com.americangroupllc.usciscase` | `android/app/` | `ios/Runner/` |
| Verba | `com.americangroupllc.verba` | `com.americangroupllc.verba` | `android/app/` | `ios/Runner/` |
| VirtuBand | `com.americangroupllc.virtuband` | `com.americangroupllc.virtuband` | `android/app/` | `ios/Runner/` |
| WiFiTrail | `com.americangroupllc.wifitrail` | `com.americangroupllc.wifitrail` | `android/app/` | `ios/Runner/` |
| yourtube | `com.americangroup.yourtube` | `com.americangroup.yourtube` | `android/app/` | `ios/Runner/` |

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
