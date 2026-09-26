# Crashlytics

Crash reporting for the AGL portfolio, on the Firebase project
**`americangroupllc-5bdfc`**
([console](https://console.firebase.google.com/u/0/project/americangroupllc-5bdfc/crashlytics)).

---

## The rule that shapes all of this

`Firebase.initializeApp()` throws `[core/no-app]` when the config files are
absent. If that exception escapes `main()`, the app dies **before** `runApp()`
and launches to a blank window. Verba hit exactly that, and its code still
carries the comment.

So every app wires Firebase through a guarded module and **runs fine
unreported** when Firebase is missing. Adding crash reporting must never be
able to take an app down.

## What each app gets

`lib/core/observability/crash_reporting.dart`:

| Function | Purpose |
| --- | --- |
| `initCrashReporting()` | Initialises Firebase, routes `FlutterError.onError` and `PlatformDispatcher.onError` to Crashlytics. Returns false and logs if unavailable. |
| `recordError(e, stack, reason:, fatal:)` | Non-fatal report. Safe when reporting is inactive. |
| `logBreadcrumb(msg)` | Adds context to the next report. |
| `setUserId(id)` | Ties a report to an opaque id — never an email or name. |
| `guardedMain(body)` | Runs startup in a zone whose uncaught errors are reported. |
| `crashReportingActive` | Whether reporting is actually live. |

Collection is **disabled in debug** so developer noise does not bury real user
crashes.

`main()` calls it before `runApp()`:

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initCrashReporting();
  runApp(const MyApp());
}
```

## Status

Wired and verified: **CarDeal, MyHealth, GadgetNest, RoomCraft, WiFiTrail**.
Verba had its own Firebase bootstrap already. Rollout to the rest is in
progress; the script is `agl_crashlytics_rollout.py` (recreate from this doc if
the temp copy is gone — it copies the module, runs `flutter pub add`, wires
`main()`, and raises the iOS target).

**Reporting is not live anywhere yet**, because no app has its config files.

## Activating it — what only you can do

1. Firebase console → **Project settings → Your apps**. Register each app with
   the bundle id from `status.csv` if it is not
   already there.
2. Download **`google-services.json`** into `android/app/` and
   **`GoogleService-Info.plist`** into `ios/Runner/`.
3. Android only — add the Gradle plugins:

   ```kotlin
   // android/settings.gradle.kts
   id("com.google.gms.google-services") version "4.4.2" apply false
   id("com.google.firebase.crashlytics") version "3.0.2" apply false

   // android/app/build.gradle.kts
   id("com.google.gms.google-services")
   id("com.google.firebase.crashlytics")
   ```

   **Do not add these before the JSON exists** — the plugin fails the build
   outright when it cannot find `google-services.json`. That is why they are
   not committed already.

4. Upload dSYMs for readable iOS stack traces. The Fastlane `ios beta` lane can
   do this once `FirebaseCrashlytics/upload-symbols` is available.

## iOS deployment target

The Firebase SDK requires **iOS 15.0**. Any app being wired has its `Podfile`
and every `IPHONEOS_DEPLOYMENT_TARGET` raised from 13.0 to 15.0. This drops
support for iOS 13 and 14 — worth knowing before release, though both are well
below Apple's current minimum for new submissions.

## Verifying it works, once configured

```sh
flutter run --release
# then, from a debug build with collection forced on:
FirebaseCrashlytics.instance.crash();
```

A report appears in the console within a couple of minutes. Until then
`crashReportingActive` is false and `recordError` only logs locally — which is
the correct, honest behaviour rather than pretending to report.
