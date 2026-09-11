# agl_observability

Crash reporting for the AGL portfolio, on Firebase project
**`americangroupllc-5bdfc`**.

## The rule this package exists to enforce

`Firebase.initializeApp()` throws `[core/no-app]` when the config files are
absent. If that escapes `main()`, the app dies **before** `runApp()` and
launches to a blank window. Verba hit exactly that.

So every path here is guarded. An app with no `google-services.json` runs
exactly as it did before, unreported, and `AglCrash.isActive` says so honestly
rather than pretending.

## Wiring an app

```yaml
dependencies:
  agl_observability:
    git:
      url: https://github.com/AmericanGroupLLC/AmericanGroupLLC-Backend.git
      path: packages/agl_observability
      ref: dev
```

```dart
Future<void> main() async {
  await AglCrash.runGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    await AglCrash.init(environment: 'production', appName: 'MyApp');
    runApp(const MyApp());
  });
}
```

| Call | When |
| --- | --- |
| `AglCrash.init(...)` | once, before `runApp` |
| `AglCrash.runGuarded(body)` | wraps `main`, catches errors raised before the binding exists |
| `AglCrash.recordError(e, s, reason:)` | a caught failure the user recovered from |
| `AglCrash.log(msg)` | breadcrumb for the next report |
| `AglCrash.setScreen(route)` | from a `NavigatorObserver` |
| `AglCrash.setAuthenticated(bool)` | at sign-in and sign-out |
| `AglCrash.setUserId(opaqueId)` | only an opaque id — never an email or a name |
| `AglCrash.sendTestReport()` | verification, safe to leave in a debug screen |

Every report already carries `app_version`, `build_number`, `package_name`,
`environment` and `release_mode`.

## Collection is off in debug

Developer noise would bury real user crashes. Pass `enableInDebug: true` only
while verifying the pipeline.

## Verifying

`AglCrash.sendTestReport()` files a **non-fatal**; it appears in the console
under Crashlytics → Non-fatals within a couple of minutes. There is
deliberately no `crash()` helper — a real crash call is one careless merge away
from shipping.

## What only a console can give you

1. Firebase console → Project settings → Your apps → register the bundle id.
2. Download `google-services.json` → `android/app/`, `GoogleService-Info.plist`
   → `ios/Runner/`.
3. Nothing else. The Gradle plugins apply themselves the moment the JSON
   exists — see `android/app/build.gradle.kts` in any rolled-out app.

Until then reporting stays inactive, which is the correct behaviour rather than
a silent failure.
