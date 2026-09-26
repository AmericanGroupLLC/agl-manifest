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
> `com.americangroupllc.*` and are corrected here; `status.csv` is
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

Per-app registration state is the `firebase_present`, `firebase_android_path`
and `firebase_ios_path` columns of [`status.csv`](../status.csv).

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
