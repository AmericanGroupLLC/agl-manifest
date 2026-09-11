# agl_ads

Google AdMob for the AGL portfolio: UMP consent, test-versus-production unit
selection, a frequency-capped interstitial, and a banner that occupies no space
until it fills.

## Three rules it enforces

1. **Consent gates the request, not just personalisation.** In the EEA, the UK
   and Switzerland an ad may not be *requested* until the user has been asked.
   Every load sits behind `AglConsent.canRequestAds()`, which fails closed.
2. **Production units only in a release build.** Requesting live ads from a
   development build is what gets an AdMob account suspended for invalid
   traffic.
3. **Ads are additive.** A failed load, an empty fill, or an SDK that never
   initialises leaves the app exactly as usable as it was.

## Wiring an app

```yaml
dependencies:
  agl_ads:
    git:
      url: https://github.com/AmericanGroupLLC/AmericanGroupLLC-Backend.git
      path: packages/agl_ads
      ref: dev
```

```dart
// main(), before runApp. Never awaited on the critical path.
AglAds.configure(AglAdIds.fromEnvironment(
  androidAppId: 'ca-app-pub-8528784688453695~XXXXXXXXXX', // = AndroidManifest
  iosAppId: AglAdIds.testIosAppId,                        // = Info.plist
));
unawaited(AglAds.initialize());
```

```dart
// In a screen, in normal layout flow.
const AglAdBanner(),

// After a navigation the user asked for.
AglAds.onTransition();
```

## Where the ids come from

| Id | Source | Committed? |
| --- | --- | --- |
| Application id | `AndroidManifest.xml`, `Info.plist`, passed to `configure` so a mismatch can be asserted | yes — it is in the binary anyway |
| Ad unit ids | `--dart-define`, or `--dart-define-from-file=env/prod.json` | **no** |

```sh
flutter build appbundle --release \
  --dart-define=ADMOB_BANNER_ANDROID=ca-app-pub-…/… \
  --dart-define=ADMOB_INTERSTITIAL_ANDROID=ca-app-pub-…/…
```

A unit left undefined means "this platform has no live unit yet" and that
platform serves test ads even in release — deliberate, so an app without its own
iOS AdMob app never reports iOS traffic against the Android units.

`--dart-define=ADMOB_TEST_DEVICES=ABCD1234,EFGH5678` makes a physical QA device
receive test fill.

## The application id must match the native file

A mismatch is not a degraded experience. On iOS the SDK throws
`GADInvalidInitializationException` and the app is **terminated on every
launch**. Assert it in the app's own test:

```dart
test('the manifest and the config agree', () {
  final manifest = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
  expect(manifest, contains(ids.androidAppId));
});
```

## Placement rules that keep an app in the stores

- The banner is zero-height until it fills, so it must live in layout flow — a
  `Column` child or `bottomNavigationBar` — never a `Stack` over content.
- `onTransition()` goes **after** the navigation completes, never before.
- Never call it during sign-in, checkout, or any flow a user cannot abandon.
- `AglAds.setSuspended(suspended: true)` for a paid tier or a sensitive flow.

## Consent forms are authored in the console

AdMob console → **Privacy & messaging** → publish a GDPR message. Until then
UMP reports "not required" everywhere and the consent code is a no-op. Publishing
switches it on with no app change and no new build.

Where a message applies, Google also requires a permanently available way to
change the choice: show a settings row when
`AglConsent.isPrivacyOptionsRequired()` is true, calling
`AglConsent.showPrivacyOptions()`.
