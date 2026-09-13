# Store release playbook

Everything needed to take an AGL Flutter app from the repository to the App
Store and Google Play, and the measured state of the portfolio against it.

- Per-app numbers: [`RELEASE_READINESS.md`](RELEASE_READINESS.md), regenerated
  with `python3 scripts/audit_release_readiness.py`.
- Delivery path and store accounts: [`RELEASE_PIPELINE.md`](RELEASE_PIPELINE.md).
- Identifiers: [`APP_IDENTIFIERS.md`](APP_IDENTIFIERS.md).
- Credentials status: [`CREDENTIALS_STATUS.md`](CREDENTIALS_STATUS.md).

> **No app in this portfolio is store-ready.** Thirteen values can only come
> from a console this repository does not have (§11), and until they exist no
> app can be signed, no crash can be reported, and no listing can be filled in.
> What follows is everything that *could* be done without them.

## Where the portfolio stands

Measured, not asserted — regenerate with
`python3 scripts/audit_release_readiness.py`.

| Signal | Before | Now |
| --- | ---: | ---: |
| Crash reporting wired in `main()` | 5 / 37 | 36 / 37 |
| Fastlane uploads a dSYM | 12 / 37 | 37 / 37 |
| Fastlane uploads a Play mapping file | 0 / 37 | 37 / 37 |
| iOS privacy manifest, inside the app target | 0 / 37 | 37 / 37 |
| Release signing, no silent debug fallback | 35 / 37 | 37 / 37 |
| CI and release workflows that can run | 31 / 37 | 37 / 37 |
| UMP consent for ads | 1 / 11 ad apps | 11 / 11 |
| The twelve languages declared and resolving | 13 / 37 | 36 / 37 |
| Store copy held in one place | 0 / 37 | 37 / 37 |
| Firebase config present | 0 / 37 | **0 / 37 — needs a console** |
| App's own strings translated | 4 / 37 | **4 / 37 — still open** |

---

## 1. Prioritized issues

Severity is about what it costs at the store, not how hard it is to fix.

### Blockers — an app cannot ship, or ships broken

Status as of 2026-09-10: B2–B7 are **fixed and pushed**. B1 is the one nobody in
this repository can close — it needs a Firebase console.

| # | Issue | Apps | Root cause | Fix | Verify |
| --- | --- | --- | --- | --- | --- |
| B1 | **No Firebase config anywhere.** Crash reporting is dead in every build. | 37 / 37 | `google-services.json` and `GoogleService-Info.plist` have never been downloaded from the console | §11 item 3. The code is wired and waiting; the Gradle plugins apply themselves the moment the JSON appears | `AglCrash.isActive` is true at runtime, and a non-fatal appears in the console |
| B2 | **Ads requested with no consent flow.** Fixed. | was 10 of the 11 ad apps | UMP was implemented in TripNest only | `agl_ads` owns the UMP calls; each app keeps its own ad service and gained a gate. Async call sites await `canRequestAds()`, synchronous ones read `adsAllowed`, which is false until consent resolves | `test/ads_consent_test.dart` in each app walks `lib/` and fails if any ad is constructed without a check in the enclosing method — confirmed to fail when a guard is removed |
| B7 | **Adding Crashlytics raised the iOS floor without saying so.** `firebase_core` 4.x requires iOS 15.0; 24 apps targeted 13.0 or 14.0. `analyze` and `test` stay green — `pod install` is what fails, and only an iOS build reaches it. | 24 | firebase_core 3.15.2 is fine at 14.0, 4.x is not | Podfile platform, post_install hook and every `IPHONEOS_DEPLOYMENT_TARGET` raised to 15.0 | six affected apps rebuilt for the simulator; `ios_deployment_targets` is now 15.0 in 34 of 37 |
| B3 | **CI and release workflows ran Flutter at the repo root** in the 11 apps whose project lives in a subdirectory. `flutter pub get` found no `pubspec.yaml`, so those pipelines could never have produced an artifact. | 10 | workflows copied from a root-layout app | `defaults.run.working-directory`, plus `working-directory` on `ruby/setup-ruby` (which does not honour `defaults`) | the workflow reaches the build step |
| B4 | **A release build signed with the debug key.** Two apps had only the `flutter create` template's `signingConfig = signingConfigs.getByName("debug")`. *(The first audit said six; four of those were false positives from a detector that insisted on the name `release` and on `key.properties` — VirtuBand names its config `upload`, and three others read the material from the environment. The detector was corrected; the count is 2.)* | HomeWise, portfolio-board | the `flutter create` default was never replaced | the standard `signingConfigs` block, which warns loudly instead of silently substituting the debug key | `release_signing` is now 37/37 and `debug_signing_in_release` 0/37 |
| B5 | **No mapping file reached Play, and dSYMs reached Crashlytics from 12 apps of 37.** A release crash is an unreadable stack of hex. | 37 / 25 | Fastlane lanes never uploaded them | `upload_dsyms` in the iOS build lane; `mapping_paths:` on every `upload_to_play_store` | a symbolicated frame in the Crashlytics console |
| B6 | **AdMob application id missing on iOS** in apps that show ads. The SDK throws `GADInvalidInitializationException` and iOS **terminates the app on every launch**. | audit column `ios_admob_id` | `GADApplicationIdentifier` absent from `Info.plist` | add it — Google's public test app id is correct until the app has its own iOS AdMob app | launch on a device and confirm it stays up |

### High

| # | Issue | Apps | Fix |
| --- | --- | --- | --- |
| H1 | Two Fastfiles in one repo — the lanes shell out with `cd ..` relative to the fastlane directory, so only the one beside `pubspec.yaml` can build. The root copy runs and fails. | AGrammarly, NearServe, NewsBoard, NexusTransferPay | **delete the root copy** — left in place, since deleting a whole config is the owner's call |
| H1b | **`android/app/` held both `build.gradle` and `build.gradle.kts`, disagreeing on the application id and on signing.** The Groovy file was correct; the `.kts` was the untouched template with a different applicationId, debug signing and no minify. Gradle resolves Groovy first, so the template was inert — but it is the file an automated change reaches for first. | daily-pulse, PilotEnRoute | template deleted, Firebase moved into the live file |
| H1c | An app whose published privacy policy promises *"No crash-reporting service"*, enforced by a test over the dependency list | FashionFactory | **crash reporting deliberately not added.** Adding it means changing a user-facing promise, the policy, the privacy manifest and both store disclosures — the owner's decision, not a rollout's |
| H2 | CI workflows left over from the Expo era: they ran Jest and `eas config` against a Flutter tree | 15 | replaced with the standard Flutter CI |
| H3 | ~~No `UIApplicationSceneManifest` → black screen on launch~~ **Not reproducible on Flutter 3.44.2.** Fourteen apps have a `SceneDelegate` and no manifest; CalcMaster is one, and it was built, installed and launched — it renders normally. Left alone rather than mass-editing 14 plists on a stale belief. Still a watch item: every iOS build prints *"UIScene lifecycle support will soon be required"* | 14 | revisit when Flutter makes it mandatory |
| H4 | No `PrivacyInfo.xcprivacy`, or one that existed but was not a member of the Runner target — a manifest that is not in Copy Bundle Resources is never copied into the `.app`, so Apple never sees it | 17 written, 18 registered in the Xcode project | now 37/37, verified by building WiFiTrail and finding the file inside `Runner.app` |
| H5 | Test coverage far below the size of the app. Re-measured 2026-09-13: the worst ratios are now MyHealth (2,062 lib LOC per test file), NexusTransferPay (1,783), PilotEnRoute (1,542), EventSpark (1,507), Photriya (1,469) | MyHealth, NexusTransferPay, PilotEnRoute, EventSpark, Photriya | see `PRODUCT_AUDIT.md`, regenerated by `scripts/audit_product_quality.py` |
| H6 | Apps shipped no localization while the listings could offer twelve languages | was 24 | `agl_i18n` adopted: the twelve declared, delegates installed, `locale` null so the device decides, `CFBundleLocalizations`/`resConfigs` aligned. **Step one of two** — the shared vocabulary is translated, each app's own copy is not. `l10n_callsites` is the measure, and only 4 apps are above 20 |
| H7 | `intl` pinned so tightly that adding `flutter_localizations` made the app unresolvable | 18 | `intl: any` — `flutter_localizations` depends on one exact version, and it is the only thing that should decide |

### Medium

- `NSAllowsArbitraryLoads` present in any app — narrow it to the hosts that need it, or remove it. App Review asks.
- Backup and data-extraction rules declared in 5 apps of 37: without them Android backs up whatever is in shared preferences, including tokens.
- `minSdk`/`targetSdk` inherited from the Flutter Gradle plugin in 28 apps. That tracks the SDK version and is fine, but pin `targetSdk` deliberately before a release so a toolchain bump cannot change the API level Play sees.

### Low

- `withOpacity` deprecations across most apps.
- `print()` in one app (three call sites) — anything on stdout lands in logcat.
- One hard-coded credential-shaped literal in Verba. Confirm it is a public key.

---

## 2. File-by-file implementation plan

Per app. Paths are relative to the Flutter project (see `app_dir` in
`release-readiness.json`; eleven apps are in a subdirectory).

| File | Change |
| --- | --- |
| `pubspec.yaml` | `agl_observability` (all), `agl_ads` (ad apps), `agl_i18n` (localized apps) as git dependencies on `ref: dev` |
| `lib/main.dart` | `AglCrash.init(...)` immediately after `WidgetsFlutterBinding.ensureInitialized()`; where the app has its own `ErrorReporter`, point its sink at `AglCrash` rather than installing a second set of handlers |
| `android/settings.gradle[.kts]` | google-services and crashlytics plugins declared `apply false` |
| `android/app/build.gradle[.kts]` | apply them **inside `if (file("google-services.json").exists())`**, plus the release `signingConfig` |
| `android/app/src/main/AndroidManifest.xml` | `com.google.android.gms.ads.APPLICATION_ID` for ad apps |
| `ios/Runner/Info.plist` | `GADApplicationIdentifier`, `UIApplicationSceneManifest`, usage descriptions |
| `ios/Runner/PrivacyInfo.xcprivacy` | required-reason API declarations |
| `fastlane/Fastfile` | `upload_dsyms` lane called from the iOS build lane; `mapping_paths:` on Play uploads |
| `.github/workflows/ci.yml` | analyze, test, Android bundle, iOS no-codesign |
| `.github/workflows/release.yml` | manual dispatch → Fastlane, `production` environment on the release lane |

`scripts/agl_rollout.py` applies all of it idempotently:

```sh
python3 scripts/agl_rollout.py --list
python3 scripts/agl_rollout.py --steps crashlytics,fastlane_symbols,privacy_manifest,workflows --all
```

It prints `MANUAL …` for anything whose shape it does not recognise rather than
guessing.

---

## 3. The code

Three shared packages, so a fix lands once rather than 37 times.

| Package | What it owns |
| --- | --- |
| [`agl_observability`](../packages/agl_observability) | Crashlytics bootstrap, non-fatals, breadcrumbs, custom keys, release-silent logging |
| [`agl_ads`](../packages/agl_ads) | UMP consent, test/production unit selection, interstitial caps, adaptive banner |
| [`agl_i18n`](../packages/agl_i18n) | the twelve standard languages, locale controller, picker, shared vocabulary |

### `main()`

```dart
Future<void> main() async {
  await AglCrash.runGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();

    // Crash reporting first, so anything that fails after this point is
    // reported. Inactive and harmless until the Firebase config is added.
    await AglCrash.init(environment: AppEnv.name, appName: 'MyApp');

    // Ads never block the first frame.
    AglAds.configure(AglAdIds.fromEnvironment(
      androidAppId: 'ca-app-pub-8528784688453695~XXXXXXXXXX',
      iosAppId: AglAdIds.testIosAppId,
    ));
    unawaited(AglAds.initialize());

    runApp(const MyApp());
  });
}
```

### Android — Gradle

```kotlin
// android/settings.gradle.kts — classpath only
plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    // …
    id("com.google.gms.google-services") version "4.4.2" apply false
    id("com.google.firebase.crashlytics") version "3.0.2" apply false
}
```

```kotlin
// android/app/build.gradle.kts — after the plugins block
// Conditional deliberately: the Google Services plugin fails the build when
// google-services.json is absent, so applying it unconditionally would break
// every app that does not have its Firebase config yet. This way, enabling
// Crashlytics is a file drop with no code change and no new release.
if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
}
```

### Android — signing

```kotlin
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
val hasReleaseSigning = keystorePropertiesFile.exists()
if (hasReleaseSigning) {
    keystorePropertiesFile.inputStream().use { keystoreProperties.load(it) }
}

android {
    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = keystoreProperties["storeFile"]?.let { file(it) }
                storePassword = keystoreProperties["storePassword"] as String?
                keyAlias = keystoreProperties["keyAlias"] as String?
                keyPassword = keystoreProperties["keyPassword"] as String?
            }
        }
    }
    buildTypes {
        release {
            signingConfig = if (hasReleaseSigning) {
                signingConfigs.getByName("release")
            } else {
                project.logger.warn(
                    "WARNING: android/key.properties not found - signing the " +
                        "release build with the DEBUG key. This artifact " +
                        "cannot be uploaded to Google Play."
                )
                signingConfigs.getByName("debug")
            }
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}
```

`android/key.properties` is **gitignored**:

```properties
storePassword=…
keyPassword=…
keyAlias=upload
storeFile=/absolute/path/upload.jks
```

### iOS — `Info.plist`

```xml
<key>GADApplicationIdentifier</key>
<string>ca-app-pub-3940256099942544~1458002511</string>

<key>UIApplicationSceneManifest</key>
<dict>
	<key>UIApplicationSupportsMultipleScenes</key>
	<false/>
	<key>UISceneConfigurations</key>
	<dict>
		<key>UIWindowSceneSessionRoleApplication</key>
		<array>
			<dict>
				<key>UISceneClassName</key>
				<string>UIWindowScene</string>
				<key>UISceneDelegateClassName</key>
				<string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
				<key>UISceneConfigurationName</key>
				<string>flutter</string>
				<key>UISceneStoryboardFile</key>
				<string>Main</string>
			</dict>
		</array>
	</dict>
</dict>
```

Both fail **after** a successful build, so a green `flutter build ios` proves
nothing. Launch and screenshot.

---

## 4. Android release

```sh
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build appbundle --release \
  --dart-define-from-file=env/prod.json      # AdMob units, API hosts
```

Then, from the app directory:

```sh
bundle install
bundle exec fastlane android beta        # Play internal, as a draft
bundle exec fastlane android release     # Play production, as a draft
```

Checklist before the first upload:

- [ ] `applicationId` matches the Play listing exactly and forever.
- [ ] `versionCode` is higher than anything previously uploaded. `flutter build` derives it from the `+N` in `pubspec.yaml`.
- [ ] Play App Signing is enabled; you upload with the **upload** key, Google re-signs with the app key.
- [ ] The keystore is backed up somewhere that is not this repository. Losing it and having App Signing off means the listing can never be updated.
- [ ] R8 on, `proguard-rules.pro` present, and a release build launched on a device — R8 strips reflective code, and the failure only appears in release.
- [ ] Data Safety form filled in and consistent with what the binary does.
- [ ] Target API level meets Play's current minimum for new releases.

---

## 5. iOS release

```sh
flutter clean
flutter pub get
cd ios && pod install && cd ..
flutter build ipa --release --dart-define-from-file=env/prod.json
```

```sh
bundle exec fastlane ios beta        # TestFlight
bundle exec fastlane ios release     # App Store Connect, not submitted
```

Archive by hand when you need Xcode's validation: **Product → Archive →
Distribute App → App Store Connect → Validate**. Validation catches a missing
usage description or an invalid entitlement before the upload does.

- [ ] Bundle id matches the App Store Connect record.
- [ ] Deployment target ≥ 14.0. **Verified**: with `firebase_core`/`firebase_crashlytics` added, `pod install` resolves Firebase iOS SDK 11.15.0 and the app builds at `platform :ios, '14.0'`. The earlier note in `CRASHLYTICS.md` that Firebase required 15.0 does not hold for these versions, and no deployment target was raised.
- [ ] Every permission the app uses has an `NS…UsageDescription` that describes the *user benefit*, not the API.
- [ ] `PrivacyInfo.xcprivacy` present **and referenced by the Xcode target**.
- [ ] `CFBundleShortVersionString` and `CFBundleVersion` increase.
- [ ] Privacy nutrition labels completed in App Store Connect.
- [ ] Encryption declaration answered (`ITSAppUsesNonExemptEncryption`).

---

## 6. Fastlane

Layout, per app, beside `pubspec.yaml`:

```
fastlane/
  Appfile      app identifier, team ids
  Fastfile     the lanes
  Matchfile    only if match is used for signing
Gemfile        pins the fastlane version — always `bundle exec`
```

Lanes, identical across the portfolio:

| Lane | iOS | Android |
| --- | --- | --- |
| `test` | `flutter test` | `flutter test` |
| `signing` | `match`, skipped when `MATCH_GIT_URL` is unset | n/a |
| `build` | signed IPA, then `upload_dsyms` | signed AAB |
| `upload_dsyms` | dSYMs → Crashlytics | n/a |
| `metadata` | `deliver`, listing only | `supply`, listing only |
| `beta` | TestFlight | Play internal |
| `release` | App Store Connect | Play production, draft |

Every credential comes from the environment; nothing secret is in the repo:

```
ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_CONTENT   App Store Connect API key (.p8, base64)
MATCH_GIT_URL, MATCH_PASSWORD                optional; automatic signing without them
PLAY_JSON_KEY_FILE                           path to the Play service-account JSON
ANDROID_KEYSTORE_PATH, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, ANDROID_KEY_PASSWORD
```

---

## 7. CI/CD

Two workflows per repository.

**`ci.yml`** — every push and pull request: `flutter pub get` → `analyze` →
`test` → Android AAB (unsigned, proving the release build compiles) → iOS
`--no-codesign`. Artifacts uploaded.

**`release.yml`** — `workflow_dispatch` with `platform` and `lane` inputs, runs
Fastlane. The `release` lane runs in the `production` GitHub environment:

```yaml
environment: ${{ inputs.lane == 'release' && 'production' || '' }}
```

Add required reviewers to that environment in **Settings → Environments →
production** and a store-facing deploy waits for a human. `beta` does not.

Repository secrets:

| Secret | Used for |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | `base64 -i upload.jks` |
| `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` | signing |
| `PLAY_SERVICE_ACCOUNT_JSON` | Play Developer API |
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_CONTENT` | App Store Connect API |
| `MATCH_GIT_URL`, `MATCH_PASSWORD`, `MATCH_GIT_BASIC_AUTHORIZATION` | optional signing |

Gitignored, always: `**/key.properties`, `*.jks`, `*.keystore`, `*.p8`, `*.p12`,
`*.mobileprovision`, `google-services.json`, `GoogleService-Info.plist`,
`fastlane/play-service-account.json`, `env/*.json` except the example.

Environments: `env/dev.json`, `env/staging.json`, `env/prod.json`, passed with
`--dart-define-from-file`. Only the example file is committed.

---

## 8. Verifying Crashlytics

1. `google-services.json` → `android/app/`, `GoogleService-Info.plist` → `ios/Runner/`.
2. `flutter build apk --release` and install it. The Gradle plugins apply themselves; the build log shows the Crashlytics tasks running.
3. In the app, call `AglCrash.sendTestReport()` from a debug/settings screen.
4. Crashlytics console → **Non-fatals**, within a couple of minutes.
5. Confirm the report carries `app_version`, `build_number`, `environment` and `screen`.
6. For iOS, run `bundle exec fastlane ios upload_dsyms` and confirm **dSYMs: 0 missing** in the console.

There is deliberately no `crash()` helper in `agl_observability`. A real crash
call is one careless merge from shipping.

---

## 9. AdMob validation and policy

- [ ] Application id in `AndroidManifest.xml` **equals** the one passed to `AglAds.configure`, and the same on iOS in `Info.plist`. A mismatch terminates the iOS app at launch.
- [ ] A debug build shows Google's test creatives. If it shows a real ad, stop: that is invalid traffic and it is how accounts get suspended.
- [ ] Production units come from `--dart-define`, never from source.
- [ ] A GDPR message is published in **AdMob → Privacy & messaging**. With the device region set to an EEA country, the form appears before the first ad request.
- [ ] Settings offers a privacy-options row where `AglConsent.isPrivacyOptionsRequired()` is true.
- [ ] The banner sits in layout flow, not over content, and takes no space before it fills.
- [ ] No interstitial in the first two transitions, none within three minutes of the last, and none during sign-in or payment.
- [ ] `app-ads.txt` published on the developer domain and reachable.
- [ ] The privacy policy names Google AdMob and links its policy; Play Data Safety and the App Store privacy labels both declare advertising data.
- [ ] `NSUserTrackingUsageDescription` and an ATT prompt if any SDK tracks across apps. Ours do not by default.

---

## 10. QA before release

Commands:

```sh
flutter analyze
flutter test --coverage
flutter build appbundle --release && flutter build ipa --release
```

| Area | Check |
| --- | --- |
| Fresh install | first launch, permissions, onboarding, no crash |
| Upgrade | install the previous version, upgrade in place, data survives |
| Offline | airplane mode: friendly errors, no spinner that never ends |
| Slow network | throttle to 2G; timeouts fire, retries are bounded |
| Session expiry | force a 401; the app returns to sign-in without a loop |
| Deep links | every route opens cold and warm |
| Android back | back from every screen, and from the root |
| iOS gestures | edge swipe back, home indicator, no gesture conflict |
| Sizes | 320dp phone, tablet, landscape |
| Accessibility | TalkBack/VoiceOver reach every control; 48dp targets; 200% text |
| Dark mode | every screen, both modes |
| Ads | test fill, no fill, offline; never over content |
| Consent | EEA region shows the form; choice persists; privacy options reopen it |
| Crashlytics | a non-fatal arrives, symbolicated |
| Release build | run the **release** artifact on a device, not the debug build |
| Performance | first frame under two seconds; no jank scrolling a long list |
| Privacy | no PII in logs; no secret in the binary (`strings`) |

---

## 11. What only you can supply

Everything below needs an account this repository does not have. Each blocks
release.

| # | Value | Where it goes | Console |
| --- | --- | --- | --- |
| 1 | Android package name, confirmed per app | `applicationId`, Play listing | Play Console |
| 2 | iOS bundle id, confirmed per app | Xcode, App Store Connect | Apple Developer |
| 3 | **`google-services.json` + `GoogleService-Info.plist`** | `android/app/`, `ios/Runner/` | Firebase — project `americangroupllc-5bdfc` |
| 4 | AdMob **app** id per app and platform | `AndroidManifest.xml`, `Info.plist`, `AglAds.configure` | AdMob |
| 5 | AdMob **unit** ids | `env/prod.json`, never committed | AdMob |
| 6 | Play service-account JSON | `PLAY_SERVICE_ACCOUNT_JSON` secret | Play Console → API access |
| 7 | Apple Team ID | `Appfile`, Xcode | Apple Developer |
| 8 | App Store Connect API key (.p8, key id, issuer id) | `ASC_*` secrets | App Store Connect → Users and Access → Keys |
| 9 | Upload keystore + passwords | `ANDROID_KEYSTORE_BASE64` and friends | generated once, backed up off-repo |
| 10 | Signing certificates / provisioning profiles, or a match repo | `MATCH_*` secrets | Apple Developer |
| 11 | Privacy policy URL that resolves | both listings, in-app link | your hosting |
| 12 | Support URL and contact email | both listings | your hosting |
| 13 | Store listing text, screenshots, icon per app and language | `fastlane/metadata/` | — |

Items 1–5 and 9–10 are hard blockers for a binary. Items 11–13 are hard
blockers for a listing.
