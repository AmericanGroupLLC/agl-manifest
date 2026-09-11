# agl_i18n

Shared internationalization for the American Group LLC mobile portfolio.

One locale set, one locale controller, one language picker, and the common UI
vocabulary translated once for all 42 apps.

## Why this is a package and not a file each app copies

Before this existed, every app that had any i18n at all had invented its own.
They disagreed about almost everything:

| | |
| --- | --- |
| Languages shipped | 3, 6, 9, 11, 12, 13, 15, 16 and 25 depending on the app |
| Mechanism | Flutter `gen-l10n` in five apps, a hand-rolled `Map` in ten, nothing in the rest |
| Where the picker lived | Five different files with five different designs, and most apps had none |

The practical consequences: a store listing could promise a language the binary
did not contain, "Cancel" was translated separately in every app that needed it
(and inconsistently), and adding a thirteenth language meant editing 42 repos.

## The split

- **This package** owns the languages, the controller, the picker, and the
  vocabulary every app shares — buttons, navigation labels, auth fields, empty
  and error states. 66 keys.
- **Each app** owns the strings only it has, in its own ARB files.

An app's delegate is installed *first*, so an app can override a shared string
when its context genuinely needs different wording.

## Adopting it

```yaml
# pubspec.yaml
dependencies:
  agl_i18n:
    git:
      url: https://github.com/AmericanGroupLLC/AmericanGroupLLC-Backend.git
      path: packages/agl_i18n
      ref: dev
```

```dart
// main.dart
final locale = AglLocaleController();
await locale.load();          // before runApp: no flash of the wrong language
runApp(MyApp(locale: locale));

ListenableBuilder(
  listenable: locale,
  builder: (context, _) => MaterialApp(
    locale: locale.locale,
    supportedLocales: locale.supportedLocales,
    localizationsDelegates: aglLocalizationsDelegates(
      AppLocalizations.delegate,      // this app's own strings
    ),
    home: const HomeScreen(),
  ),
)
```

```dart
Text(AglL10n.of(context)!.actionSave)          // shared
Text(AppLocalizations.of(context)!.myAppKey)   // this app's
```

Offer the picker from settings:

```dart
Navigator.of(context).push(MaterialPageRoute(
  builder: (_) => AglLanguageScreen(controller: locale),
));
```

Or drop the list into an existing settings page with `AglLanguageList`.

### Keeping languages an app already had

An app shipping beyond the standard twelve passes them in. Nothing is ever
dropped:

```dart
AglLocaleController(extraLocales: const [Locale('tr'), Locale('id')]);
```

## The languages

`en, es, zh, hi, fr, ar, de, ja, pt, ko, it, ru`

Chosen to cover the largest App Store and Play markets, and to include a
right-to-left script — Arabic ships in every app, so RTL layout bugs surface in
development instead of in review.

Adding a thirteenth is now one change here rather than 42: add
`lib/l10n/agl_<code>.arb`, add the `Locale` to `AglLocales.standard`, add a
native name to `AglLocales.nativeNames`, and add it to `rtlLanguageCodes` if it
reads right to left.

## `null` means "follow the device"

`AglLocaleController.locale` starts null and stays null until the user picks a
language. That is the correct default: someone whose phone is already in Spanish
should get a Spanish app without hunting for a setting. Flutter's own locale
resolution does the work when `MaterialApp.locale` is null.

A stored language a later build no longer ships resolves back to the device
rather than being forced to English.

## Tests

29 tests, and they are the contract for 42 apps. They check that every ARB
carries every key, that no locale silently repeats the English string (with a
documented per-locale exemption list for genuine cognates — Italian really does
say "Password"), that every English string has a description for whoever
translates it next, that the picker renders and switches, and that Arabic lays
out right to left even while the surrounding app is in English.

```sh
flutter test
flutter gen-l10n     # after editing any ARB
```

## CI

The dependency is a git reference to a private repository, so a CI runner needs
credentials to resolve it. In GitHub Actions:

```yaml
- run: git config --global url."https://x-access-token:${{ secrets.AGL_PAT }}@github.com/".insteadOf "https://github.com/"
```
