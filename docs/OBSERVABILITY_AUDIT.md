# Observability audit — crash reporting, symbol upload, iOS floor

Audit date: 2026-09-13. Scope: the 43 apps in `apps.json`.
Method: static inspection of every app's `lib/main.dart`, its crash-reporting
helper, its `fastlane/Fastfile`, its `android/app/build.gradle[.kts]`, its
`ios/Podfile` and its `ios/Runner.xcodeproj/project.pbxproj`. No app repository
was modified. No iOS build was run, so nothing below is confirmed against a real
`pod install`, a real archive or a real upload.

---

## 0. The finding that outranks the rest

**No app in the portfolio has `android/app/google-services.json` or
`ios/Runner/GoogleService-Info.plist`, and no app has a `firebase_options.dart`
or passes `options:` to `AglCrash.init`. Checked all 43; zero hits.**

That makes the whole chapter below conditional. `AglCrash.init` registers its
handlers only *after* `Firebase.initializeApp()` succeeds:

```dart
// packages/agl_observability/lib/src/crash.dart:41-55
try {
  await Firebase.initializeApp(options: options);
} catch (error) {
  AglLog.write('Crash reporting inactive — Firebase did not initialise ...');
  return false;            // <-- returns before any handler is installed
}
```

With no config file, `initializeApp()` throws `[core/no-app]`, `init()` returns
`false`, and **neither `FlutterError.onError` nor
`PlatformDispatcher.instance.onError` is touched**. The same early return exists
in every per-app copy of the shim (`initCrashReporting`).

So today, in every app, crash reporting is inert — not broken, but inert. The
per-app verdicts in section 1 describe what would happen **the day the Firebase
config files land**. That is the state worth auditing, because it is the state
nobody will re-check.

The same fact disables the Android side: the Crashlytics Gradle plugin is
applied conditionally —

```kotlin
// AGCleaner/android/app/build.gradle.kts:15-18
if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
}
```

— so the plugin's automatic mapping-file upload never runs either.

---

## 1. Per-app crash-handler verdict

Legend:

- **REAL** — a handler that reaches Crashlytics is installed on both channels
  and nothing later in `main()` overwrites it.
- **DEGRADED** — installed, but a later call replaces one channel, or downgrades
  fatality, or a guarded zone swallows startup errors into a sink that discards
  them in release.
- **DECORATIVE** — `AglCrash.init()` is called and then both of its handlers are
  overwritten by something that does not report anywhere. The init call is
  cosmetic.
- **EXCLUDED** — deliberate policy exclusion.

| # | App | Guarded zone | Verdict | Evidence / what actually happens |
|---|-----|--------------|---------|----------------------------------|
| 1 | AeroSwift | `AglCrash.runGuarded` | REAL | `main.dart:3` wraps everything; `init` at `:9` inside the zone. Both channels chained; zone handler is `AglCrash.recordError(fatal: true)`. |
| 2 | AGCleaner | none | REAL | `init` first, then two awaits before `runApp`. Both channels intact. |
| 3 | AGrammarly | none | DEGRADED | `ErrorReporter.install()` runs after `init` and **replaces** `PlatformDispatcher.instance.onError` without chaining (`core/services/error_reporter.dart:73`). Sink is `AglCrash.recordError`, so platform errors still arrive — but as **non-fatal**, not fatal. `FlutterError` chain is preserved (`:61` keeps `previousOnError`). |
| 4 | AGRecorder | none | REAL | Same shape as AGCleaner. |
| 5 | AGStudio | `AglCrash.runGuarded` | REAL | `main.dart:74`. Zone wraps three awaits and `runApp`. |
| 6 | ApexMarketWatch | none | REAL | Does not use the shared package — `mobile/lib/core/crash_reporting.dart` installs both channels itself (`:57` chains `FlutterError`, `:70` sets `PlatformDispatcher`). Deliberately rethrows `WatchlistStore.open` failures *after* reporting them. |
| 7 | BodyQuest | none | DEGRADED | Same `ErrorReporter.install()` platform-channel replacement as AGrammarly. |
| 8 | BuddyPlay | `AglCrash.runGuarded` | REAL | `main.dart:206`. |
| 9 | CalcMaster | none | DEGRADED | Same as AGrammarly. |
| 10 | CarDeal | none | REAL | Calls both `AglCrash.init` **and** the local `initCrashReporting`. Both chain `FlutterError`; the second replaces `PlatformDispatcher` with another Crashlytics-recording handler, so nothing is lost. Framework errors will be recorded **twice**. |
| 11 | ChefCount | none | REAL | Two lines: `init`, `runApp`. |
| 12 | CodeDeal | none | REAL | `init` first; three guarded awaits follow. |
| 13 | daily-pulse | none | DEGRADED | Same as AGrammarly. |
| 14 | DriftDate | `ErrorReporter.runGuarded` | DEGRADED | Three problems. (a) `main.dart:428` calls `ErrorReporter.runGuarded(...)` **without awaiting it**, so `main` returns immediately. (b) `ErrorReporter.install()` replaces the platform channel un-chained. (c) `CrashReporting.install()` at `:441` **reassigns `ErrorReporter.sink` to Sentry** (`services/crash_reporting.dart:50`), discarding the `AglCrash` sink set at `:433` — so in any build with `SENTRY_DSN` set, framework and platform errors go to Sentry only and Crashlytics sees nothing. |
| 15 | EventSpark | local `runGuarded` | DEGRADED | `core/telemetry/telemetry.dart:97` installs handlers routed at the global `telemetry`, which is **never reassigned** — it stays `DebugTelemetry`, which drops everything in release (`:48 if (!kReleaseMode)`). The `FlutterError` and `PlatformDispatcher` chains survive because `AglCrash.init` chains on top of them, but **the zone handler (`telemetry.dart:121`) reports only to `DebugTelemetry`**, and all of `_startUp` runs inside that zone. Uncaught async startup errors are lost in release. |
| 16 | FashionFactory | n/a | EXCLUDED | No Firebase dependency, no Crashlytics, `installErrorHandlers()` is local-only. Its published policy promises no crash-reporting service and a test enforces it. **Not a defect. Do not change.** |
| 17 | GadgetNest | none | REAL | Same double-registration shape as CarDeal. |
| 18 | GroceryMatch | none | **DECORATIVE** | `AglCrash.init` at `main.dart:77`, then `AppErrorHandling.install()` at `:85` **replaces both** `FlutterError.onError` (`core/utils/app_error_boundary.dart:46`, no chaining) and `PlatformDispatcher.instance.onError` (`:59`, no chaining). Both route to `_report`, which calls `onReport` — and `AppErrorHandling.onReport` is **never assigned anywhere in `lib/` or `test/`** (grep returns only the two doc comments). Net effect: `debugPrint` and nothing else. The Crashlytics init is pure decoration. |
| 19 | HerJourney | none | DEGRADED | Same as AGrammarly. |
| 20 | HomeWise | none | REAL | |
| 21 | iMaps | none | DEGRADED | Same as AGrammarly. |
| 22 | iMeasure | none | REAL (by accident) | `main.dart:47` replaces `PlatformDispatcher.instance.onError` un-chained, with a comment claiming "There is no crash reporter in this build" — which is stale. It survives only because the replacement calls `FlutterError.reportError(...)`, which re-enters `FlutterError.onError`, which is still the `AglCrash` chain. Reports arrive, tagged `library: 'iMeasure'`. Fragile: delete the `reportError` call and the channel goes dark silently. |
| 23 | Kinnav | bare `runZonedGuarded` | DEGRADED | `main.dart:37` sets `FlutterError.onError` **after** `init` with no chaining, routing framework errors to `analytics.recordError` — and `analytics` is `NoopAnalyticsService` (`services/analytics_service.dart:26`), never reassigned, `debugPrint` in debug only. The zone handler at `:915` is the same noop. `PlatformDispatcher` survives as the `AglCrash` handler, but the zone intercepts async errors inside `main` before it. Framework errors are lost. |
| 24 | MileMaster | none | REAL | |
| 25 | MyCard | `AglCrash.runGuarded` | REAL | `main.dart:12`; `init` inside `bootstrap()` at `:33`. |
| 26 | MyFinance | none | REAL | |
| 27 | MyHealth | none | REAL | Double registration (`AglCrash.init` + `initCrashReporting`), same as CarDeal. `Monitoring.init()` and the later `ErrorReporter.sink` assignment only affect deliberately-reported errors, not the framework channels. |
| 28 | NearServe | none | REAL | |
| 29 | NewsBoard | none | DEGRADED | Same as AGrammarly. |
| 30 | NexusTransferPay | Sentry `appRunner` | REAL | `init` first; `SentryFlutter.init` chains rather than replaces. Sentry path only active when `SENTRY_DSN` is defined and not debug. |
| 31 | Photriya | bare `runZonedGuarded` | **DECORATIVE** | `main.dart:36` and `:47` replace **both** `FlutterError.onError` and `PlatformDispatcher.instance.onError` after `init`, with handlers that only call `_log.e(...)`. The zone handler at `:1189` also only logs. Nothing reaches Crashlytics. The `AglCrash.init` call at `:27` accomplishes nothing. |
| 32 | PilotEnRoute | none | DEGRADED | Same as AGrammarly. |
| 33 | PlantPulse | `AglCrash.runGuarded` | REAL | `main.dart:1270`. |
| 34 | portfolio-board | none | REAL | |
| 35 | radiotune | bare `runZonedGuarded` | DEGRADED | `main.dart:40` replaces `FlutterError.onError` after `init` with `presentError` plus the comment "Hook a crash reporter here when one is provisioned" — the crash reporter *is* provisioned, three lines above. Framework errors are lost. `PlatformDispatcher` survives. Zone handler is `debugPrint` (`:1404`). |
| 36 | RideZap | none | REAL | |
| 37 | RoomCraft | none | REAL | Double registration, same as CarDeal. |
| 38 | TripNest | local `runGuarded` | DEGRADED | Identical to EventSpark: `core/telemetry/telemetry.dart:96`, `telemetry` never reassigned from `DebugTelemetry`, zone-level startup errors dropped in release. |
| 39 | Uscis-Case | none | DEGRADED | Same as AGrammarly. |
| 40 | Verba | none | REAL | `main.dart` path is fine. Note `lib/core/services/analytics_service.dart:38-58` has the entire Crashlytics block commented out — dead code, not a live handler, and harmless because `main` does not depend on it. |
| 41 | VirtuBand | none | DEGRADED | Same as AGrammarly. |
| 42 | WiFiTrail | none | REAL | Double registration, same as CarDeal. |
| 43 | yourtube | none | DEGRADED | Same as AGrammarly. |

**Tally:** 24 REAL, 16 DEGRADED, 2 DECORATIVE (GroceryMatch, Photriya),
1 EXCLUDED (FashionFactory).

### The two systemic patterns

**Pattern A — the shared `ErrorReporter.install()` drops the platform chain.**
Eleven apps ship a byte-identical `error_reporter.dart` whose `install()`
carefully chains `FlutterError.onError` and then does *not* chain
`PlatformDispatcher.instance.onError`:

```dart
final previousOnError = FlutterError.onError;
FlutterError.onError = (details) { report(...); previousOnError?.call(details); };

// no `previous` capture here:
PlatformDispatcher.instance.onError = (error, stack) {
  report(error, stack, context: 'platform');
  return true;
};
```

Because these apps also set `ErrorReporter.sink = AglCrash.recordError`, the
errors still reach Crashlytics — but through `recordError`, whose `fatal`
defaults to `false`. Every uncaught async error in these apps will be filed as a
**non-fatal**, which means it never appears in the crash-free-users metric and
never pages anyone. Affected: AGrammarly, BodyQuest, CalcMaster, daily-pulse,
DriftDate, HerJourney, iMaps, NewsBoard, PilotEnRoute, Uscis-Case, VirtuBand,
yourtube.

**Pattern B — a second handler installed after `init` that reports nowhere.**
GroceryMatch, Photriya, Kinnav and radiotune each assign `FlutterError.onError`
(and in two cases `PlatformDispatcher.instance.onError`) *after* `AglCrash.init`
without capturing the previous handler. Every one of them routes to a sink that
is a no-op or a debug logger. These are the cases the brief called decorative,
and they will look identical to a working app in `flutter analyze`, in
`flutter test`, and in a manual smoke run.

---

## 2. Symbol upload — iOS dSYMs and Play mapping files

### 2a. No app has an Xcode dSYM upload build phase

Checked `ios/Runner.xcodeproj/project.pbxproj` in all 43 apps for
`upload-symbols`, a `FirebaseCrashlytics` script reference, or any build phase
whose name contains "symbol". **Zero hits in all 43.** The only
`PBXShellScriptBuildPhase` entries present are the stock Flutter `Run Script` /
`Thin Binary` and the CocoaPods `[CP] …` phases.

This is not necessarily wrong — the portfolio has chosen Fastlane over a build
phase — but it means **a dSYM is uploaded only when someone runs the Fastlane
lane**. An Xcode build, an archive from the IDE, or a `flutter build ipa` on its
own uploads nothing.

### 2b. Fastlane dSYM lanes — three tiers

**Tier 1 — path-correct, plist-gated (32 apps).** AeroSwift, AGCleaner,
AGrammarly, AGRecorder, ApexMarketWatch, CalcMaster, CarDeal, ChefCount,
daily-pulse, DriftDate, EventSpark, FashionFactory, GadgetNest, HerJourney,
HomeWise, Kinnav, MileMaster, MyFinance, MyHealth, NearServe, NewsBoard,
NexusTransferPay, Photriya, PlantPulse, portfolio-board, radiotune, RideZap,
RoomCraft, TripNest, Verba, WiFiTrail, yourtube.

Shape (AGCleaner `fastlane/Fastfile:144-171`):

```ruby
plist = File.expand_path("../ios/Runner/GoogleService-Info.plist", __dir__)
unless File.exist?(plist)
  UI.important("No GoogleService-Info.plist — skipping dSYM upload.")
  next
end
archive = Dir[File.expand_path("../build/ios/archive/*.xcarchive", __dir__)].max_by { |f| File.mtime(f) }
path = File.join(archive, "dSYMs") if archive
...
upload_symbols_to_crashlytics(
  dsym_path: path, gsp_path: plist,
  binary_path: Dir[File.expand_path("../ios/Pods/FirebaseCrashlytics/upload-symbols", __dir__)].first
)
```

Verified: `__dir__` resolves to the app's own `fastlane/` dir in all 32, so
`../ios/Runner/` and `../ios/Pods/` are real directories in each. For the four
apps whose Flutter project is in a subdirectory but which also carry a legacy
root-level `fastlane/` (AGrammarly, NearServe, NewsBoard, NexusTransferPay), the
**app-directory** Fastfile is the correct one and is the one measured here; the
root-level Fastfile has no symbol paths at all and should be deleted so nobody
runs it by mistake.

`build/ios/archive/*.xcarchive` does not exist in any checkout — expected, it is
a build output. Correct for `flutter build ipa`, which writes exactly there.

Because the lane bails on a missing `GoogleService-Info.plist` and **no app has
one**, all 32 of these lanes are currently a logged skip. That is correct
behaviour, not a bug — but it means nobody has ever seen one of these lanes
actually upload anything.

**Tier 2 — gated behind an env var nobody sets (7 apps).** BodyQuest,
GroceryMatch, iMaps, iMeasure, PilotEnRoute, Uscis-Case, VirtuBand:

```ruby
dsyms = File.expand_path("../build/ios/archive/Runner.xcarchive/dSYMs", __dir__)
if File.directory?(dsyms) && ENV["CRASHLYTICS_ENABLED"] == "1"
  upload_symbols_to_crashlytics(dsym_path: dsyms)
else
  UI.message("Skipping dSYM upload ...")
end
```

The path is right. `CRASHLYTICS_ENABLED` is set **nowhere in the portfolio** —
grep across every repo returns exactly these 7 Fastfiles and no CI workflow, no
shell script, no `.env`. These lanes are dead code as configured.

**Tier 3 — path is wrong; the lane targets a project that is not the shipping
app (4 apps).**

| App | Fastfile line | Path referenced | Reality |
|-----|---------------|-----------------|---------|
| AGStudio | `fastlane/Fastfile:37,46` | `aQuantum/ios/aQuantum.xcworkspace` / `iQuantum/ios/iQuantum.xcworkspace`, dSYMs from `SharedValues::DSYM_OUTPUT_PATH` | Both workspaces exist, but they are the **legacy React Native** apps. The shipping Flutter app is `AGStudio/mobile/ios/Runner.xcworkspace`, which this Fastfile never builds. Uploads the wrong binary's symbols, or none. |
| BuddyPlay | `fastlane/Fastfile:21,22,27` | `ios/BuddyPlay.xcodeproj` | `BuddyPlay/ios/` contains only `project.yml` and sources — **no `.xcodeproj` exists**. The lane fails at `increment_build_number`. The Flutter app is at `BuddyPlay/mobile/ios/Runner.xcodeproj`. `upload_symbols_to_crashlytics` is called bare, with no `dsym_path`. |
| MyCard | `fastlane/Fastfile:21,22,27` | `Card/ios/Card.xcodeproj` | **Does not exist** (`MyCard/Card/ios/` has no `.xcodeproj`). Flutter app is `MyCard/mobile/ios/Runner.xcodeproj`. Bare `upload_symbols_to_crashlytics`. |
| CodeDeal | `fastlane/Fastfile:9,11,16` | `sh("cd .. && flutter build ipa")`, ipa `../build/ios/ipa/CodeDeal.ipa`, dsym `../build/ios/archive/Runner.xcarchive/dSYMs` | The `..` is the **repo root**, which has no `pubspec.yaml`; the app is at `CodeDeal/mobile/codedeal_app`. As a bare relative string, `dsym_path` resolves outside the repo entirely. |

These four are the "configured against the wrong path" case the brief warned
about. Because two of them (`BuddyPlay`, `MyCard`) call
`upload_symbols_to_crashlytics` with no `dsym_path` at all, Fastlane falls back
to `SharedValues::DSYM_OUTPUT_PATH` from a `build_app` that will already have
failed — so the failure is loud, not silent. AGStudio's is the dangerous one: it
would succeed and upload symbols for the wrong application.

### 2c. Play mapping-file upload

40 of 43 apps pass `mapping_paths` to `upload_to_play_store` in both the `beta`
and `release` Android lanes:

```ruby
mapping_paths: Dir[File.expand_path("../build/app/outputs/mapping/release/mapping.txt", __dir__)]
```

Missing entirely in **AGStudio, BuddyPlay, MyCard** — the same three legacy
Fastfiles from tier 3.

The path is the correct AGP output location. But `Dir[...]` returns `[]` when the
file is absent, and `upload_to_play_store(mapping_paths: [])` is a silent no-op —
the AAB uploads, the mapping does not, and nothing in the log says so. That
matters for the **12 apps where R8 is not enabled at all**, so `mapping.txt` is
never produced:

> AeroSwift, AGCleaner, AGRecorder, AGStudio, ApexMarketWatch, BuddyPlay,
> ChefCount, MyCard, MyFinance, PlantPulse, RoomCraft, WiFiTrail

(no `minifyEnabled` / `isMinifyEnabled` in their `android/app/build.gradle[.kts]`).
For these the missing mapping is harmless *today* — unobfuscated traces need no
mapping — but the moment anyone turns on shrinking for app-size reasons, Play
and Crashlytics both go unreadable and the upload will keep reporting success.

The remaining 30 apps do set `minifyEnabled = true`, so they will produce a
mapping and the glob will find it.

CI collects mapping files as a 90-day artifact
(`agl-manifest/.github/workflows/deliver.yml:180-187`, and per-app
`release.yml`), but with `if-no-files-found: ignore` — so the same 12 apps
produce an empty artifact with no warning. **No CI workflow anywhere uploads
dSYMs to Crashlytics.**

---

## 3. iOS deployment floor

`firebase_core` 4.x requires iOS 15.0. Checked the `platform :ios` line in
`ios/Podfile` and every `IPHONEOS_DEPLOYMENT_TARGET` in
`ios/Runner.xcodeproj/project.pbxproj` for all 43 apps.

**Result: no Firebase app is below 15.0.** Podfile and Xcode agree in every
single app — there is no app where one says 15.0 and the other says 12.0, which
is the failure mode that would survive analyze and test.

| Floor | Apps |
|-------|------|
| 15.0 | 40 apps (Podfile and Xcode both 15.0) |
| 15.1 | EventSpark |
| 16.0 | GroceryMatch |
| 13.0 | FashionFactory — **see below** |

**FashionFactory** is the only app under 15.0: `ios/Podfile` has its
`platform :ios, '13.0'` line **commented out** (so CocoaPods falls back to its
own default) and `IPHONEOS_DEPLOYMENT_TARGET = 13.0` in the pbxproj. This is
**not a defect**: FashionFactory has no `firebase_core` dependency at all (no
entry in its `pubspec.lock`), so there is no 15.0 requirement to violate. Leave
it alone.

Five apps additionally pin the target for all pods in a Podfile `post_install`
hook — BodyQuest `= '15.0'`, iMaps `= '15.0'`, Kinnav `= '15.0'`, yourtube
`= '15.0'`, GroceryMatch `= '16.0'` — which is the belt-and-braces version and
the pattern the rest should copy, because without it CocoaPods leaves individual
pod targets at their own (often lower) defaults.

One related version fact, recorded so nobody rediscovers it as a surprise:
**four apps resolve `firebase_core` 3.15.2 while the other 38 resolve 4.14.0** —
BodyQuest, GroceryMatch, Photriya, Verba (from their `pubspec.lock`).
FashionFactory has no `firebase_core` entry at all. This split is deliberate:
`packages/agl_observability/pubspec.yaml` declares
`firebase_core: ">=3.6.0 <5.0.0"` and `firebase_crashlytics: ">=4.1.0 <6.0.0"`
with a comment explaining that pinning either would force the other family to
move in the same commit, and that only long-stable APIs are used. Worth knowing
when reading a report, not worth fixing. None of the four is below the 15.0 iOS
floor regardless.

---

## 4. What to fix, in order

1. **GroceryMatch and Photriya** — the crash wiring reports to nothing. Either
   chain the new handlers onto the previous ones, or delete the second
   installation. (GroceryMatch: assign `AppErrorHandling.onReport =
   AglCrash.recordError`. Photriya: chain, do not replace.)
2. **Kinnav and radiotune** — same class, one channel each.
3. **The 12 `ErrorReporter.install()` apps** — chain `PlatformDispatcher` and
   pass `fatal: true` for platform-channel errors, so they count as crashes.
4. **AGStudio, BuddyPlay, MyCard, CodeDeal** — the Fastfiles point at legacy
   non-Flutter projects. AGStudio's is the one that could silently upload the
   wrong app's symbols.
5. **EventSpark and TripNest** — point the global `telemetry` at an `AglCrash`
   adapter; right now the zone handler discards startup errors in release.
6. **DriftDate** — `await` the guarded zone, and decide whether Sentry or
   Crashlytics owns the sink rather than having the later `install()` win.
7. **The 7 `CRASHLYTICS_ENABLED` apps** — either set the variable in CI or drop
   the gate.
8. **Firebase config files** — until `google-services.json` and
   `GoogleService-Info.plist` exist, everything above is theoretical.

---

## Not verified

- No iOS build, `pod install`, archive or Fastlane lane was executed. Every
  path claim is from filesystem inspection, not from a run.
- No Android build was attempted (no Gradle network egress in this sandbox), so
  the "R8 produces no mapping.txt" conclusion is read from the Gradle files, not
  observed.
- Whether `upload_symbols_to_crashlytics` would succeed once a plist exists is
  unverified; only the input paths were checked for existence.
- `flutter analyze` and `flutter test` were not run — this is a read-only audit
  and no app code was changed.
