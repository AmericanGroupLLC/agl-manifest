import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../l10n/generated/agl_localizations.dart';

/// The delegate list every AGL app installs.
///
/// Bundles the three Flutter globals — without them Material's own strings
/// ("OK", the date picker, the text-selection menu) stay English however well
/// the app is translated — with this package's shared catalogue.
///
/// Pass the app's own generated delegate as [appDelegate]; anything else it
/// needs goes in [extra].
List<LocalizationsDelegate<dynamic>> aglLocalizationsDelegates(
  LocalizationsDelegate<dynamic>? appDelegate, {
  List<LocalizationsDelegate<dynamic>> extra = const [],
}) =>
    <LocalizationsDelegate<dynamic>>[
      if (appDelegate != null) appDelegate,
      AglL10n.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
      ...extra,
    ];
