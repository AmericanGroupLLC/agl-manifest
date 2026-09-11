/// Shared internationalization for the American Group LLC mobile portfolio.
///
/// An app adopts this in four steps:
///
/// ```dart
/// // 1. Build and load the controller before runApp.
/// final locale = AglLocaleController();
/// await locale.load();
///
/// // 2. Drive MaterialApp from it.
/// ListenableBuilder(
///   listenable: locale,
///   builder: (context, _) => MaterialApp(
///     locale: locale.locale,
///     supportedLocales: locale.supportedLocales,
///     localizationsDelegates: aglLocalizationsDelegates(
///       AppLocalizations.delegate,   // this app's own strings
///     ),
///     ...
///   ),
/// )
///
/// // 3. Read shared strings from AglL10n, app strings from AppLocalizations.
/// Text(AglL10n.of(context)!.actionSave)
///
/// // 4. Offer the picker.
/// AglLanguageScreen(controller: locale)
/// ```
///
/// The split matters: "Save", "Cancel" and "Search" are translated once here
/// for the whole portfolio, so the same button never reads two different ways
/// in two AGL apps, and a new app starts with 66 strings already done.
library;

export 'package:flutter_localizations/flutter_localizations.dart'
    show
        GlobalMaterialLocalizations,
        GlobalWidgetsLocalizations,
        GlobalCupertinoLocalizations;

export 'l10n/generated/agl_localizations.dart' show AglL10n;
export 'src/agl_locales.dart';
export 'src/delegates.dart';
export 'src/language_screen.dart';
export 'src/locale_controller.dart';
