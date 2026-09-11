# Required files

Every file that has to exist before an app can be built, signed and shipped,
and exactly where it goes. Regenerate with `python3 scripts/status.py`;
also published as [`files.csv`](files.csv).

None of these are in git. Two reasons, and they are different: the signing
material is secret and must never be committed, while the Firebase files are
not secret — Google documents them as shipping inside the binary — and are
absent only because nobody has downloaded them yet.

## Once for the whole portfolio

| File | Where it comes from | Where it goes | Needed for |
| --- | --- | --- | --- |
| `AuthKey_<KEYID>.p8` | App Store Connect → Users and Access → Keys. Downloads once. | `ASC_KEY_CONTENT` secret, base64 | every iOS lane |
| Play service-account JSON | Play Console → Setup → API access → create a service account → grant *Release manager* | `PLAY_SERVICE_ACCOUNT_JSON` secret | Play upload |
| Apple distribution certificate + provisioning profiles | `bundle exec fastlane match appstore` on a Mac signed into the Apple account | the `match-certificates` branch | iOS signing on CI |
| A GitHub token | GitHub → Developer settings | `AGL_PACKAGES_TOKEN` organization secret | cloning the apps, and `flutter pub get` reaching the shared packages |

## Per app

`google-services.json` and `GoogleService-Info.plist` come from the Firebase
console for project `americangroupllc-5bdfc`, registered against the package
name and bundle id in the row. A mismatched package name is not a warning —
Crashlytics silently reports nothing, which looks exactly like an app that
never crashes.

`key.properties` and the keystore are the Android upload key. **Lose a
keystore with Play App Signing off and that app can never be updated again.**

| # | App | Package / bundle id | google-services.json | GoogleService-Info.plist | key.properties | Keystore |
| --: | --- | --- | --- | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/AGCleaner-upload.jks` |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/AGrammarly-upload.jks` |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/AGRecorder-upload.jks` |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/BodyQuest-upload.jks` |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/CalcMaster-upload.jks` |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/CarDeal-upload.jks` |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/ChefCount-upload.jks` |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | `mobile/codedeal_app/android/app/google-services.json` | `mobile/codedeal_app/ios/Runner/GoogleService-Info.plist` | `mobile/codedeal_app/android/key.properties` | `~/agl/.secrets/keystores/CodeDeal-upload.jks` |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/daily-pulse-upload.jks` |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/DriftDate-upload.jks` |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/EventSpark-upload.jks` |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.styleradar` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/FashionFactory-upload.jks` |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/GadgetNest-upload.jks` |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/GroceryMatch-upload.jks` |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | A `com.americangroupllc.her_journey`<br>i `com.americangroupllc.herJourney` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/HerJourney-upload.jks` |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/HomeWise-upload.jks` |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/iMaps-upload.jks` |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/iMeasure-upload.jks` |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/MileMaster-upload.jks` |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/MyFinance-upload.jks` |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/MyHealth-upload.jks` |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/NearServe-upload.jks` |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/NewsBoard-upload.jks` |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` | `flutter-mobile-app/android/app/google-services.json` | `flutter-mobile-app/ios/Runner/GoogleService-Info.plist` | `flutter-mobile-app/android/key.properties` | `~/agl/.secrets/keystores/NexusTransferPay-upload.jks` |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/Photriya-upload.jks` |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/PilotEnRoute-upload.jks` |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/portfolio-board-upload.jks` |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.ratiotune` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/radiotune-upload.jks` |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/RideZap-upload.jks` |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/RoomCraft-upload.jks` |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | `mobile/android/app/google-services.json` | `mobile/ios/Runner/GoogleService-Info.plist` | `mobile/android/key.properties` | `~/agl/.secrets/keystores/TripNest-upload.jks` |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/Uscis-Case-upload.jks` |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/Verba-upload.jks` |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/VirtuBand-upload.jks` |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/WiFiTrail-upload.jks` |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | `android/app/google-services.json` | `ios/Runner/GoogleService-Info.plist` | `android/key.properties` | `~/agl/.secrets/keystores/yourtube-upload.jks` |

**36 of 36 apps have no Firebase config at all.** Until they do, `AglCrash.isActive` is false in every build and no crash is reported. The Gradle plugins apply themselves the moment the JSON appears — there is no code change waiting behind it.

The keystores already exist for most apps; the five repositories whose GitHub secrets are missing or misnamed are listed in [PENDING.md](PENDING.md) §3.
