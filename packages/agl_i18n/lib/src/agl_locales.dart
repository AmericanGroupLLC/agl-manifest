import 'package:flutter/widgets.dart';

/// The languages the American Group LLC portfolio ships in, and what every app
/// needs to know about them.
///
/// One list, one place. Before this existed each app declared its own set and
/// they disagreed — six locales in one app, nine in another, twenty-five in a
/// third — which meant a store listing could promise a language the binary did
/// not contain.
class AglLocales {
  const AglLocales._();

  /// The standard set. Order is the order a picker shows.
  ///
  /// Chosen to match the largest App Store and Play markets, and to include at
  /// least one right-to-left script so RTL bugs surface in development rather
  /// than in review.
  static const List<Locale> standard = <Locale>[
    Locale('en'), // English
    Locale('es'), // Español
    Locale('zh'), // 中文 (简体)
    Locale('hi'), // हिन्दी
    Locale('fr'), // Français
    Locale('ar'), // العربية
    Locale('de'), // Deutsch
    Locale('ja'), // 日本語
    Locale('pt'), // Português
    Locale('ko'), // 한국어
    Locale('it'), // Italiano
    Locale('ru'), // Русский
  ];

  /// Languages written right to left.
  ///
  /// Wider than [standard] on purpose: an app that adds Farsi, Hebrew or Urdu
  /// gets the correct text direction without touching this file.
  static const Set<String> rtlLanguageCodes = <String>{
    'ar', 'fa', 'he', 'ur', 'ps', 'sd', 'yi',
  };

  static bool isRtl(String languageCode) =>
      rtlLanguageCodes.contains(languageCode);

  /// Each language's name in its own script.
  ///
  /// A picker that lists "Japanese" in English is useless to someone who cannot
  /// read English — which is precisely the person reaching for it. Covers more
  /// than [standard] so an app that ships extra languages still gets a real
  /// name rather than a two-letter code.
  static const Map<String, String> nativeNames = <String, String>{
    'ar': 'العربية',
    'bn': 'বাংলা',
    'de': 'Deutsch',
    'en': 'English',
    'es': 'Español',
    'fa': 'فارسی',
    'fil': 'Filipino',
    'fr': 'Français',
    'he': 'עברית',
    'hi': 'हिन्दी',
    'id': 'Bahasa Indonesia',
    'it': 'Italiano',
    'ja': '日本語',
    'ko': '한국어',
    'nl': 'Nederlands',
    'pl': 'Polski',
    'pt': 'Português',
    'ru': 'Русский',
    'sw': 'Kiswahili',
    'th': 'ไทย',
    'tl': 'Tagalog',
    'tr': 'Türkçe',
    'uk': 'Українська',
    'ur': 'اردو',
    'vi': 'Tiếng Việt',
    'zh': '中文 (简体)',
  };

  /// The language's own name, or the code if we have no name for it. Returning
  /// the code is deliberate — it is visibly wrong, so it gets fixed.
  static String nativeName(String languageCode) =>
      nativeNames[languageCode] ?? languageCode;

  /// [standard] plus anything an app adds on top. Never removes a language:
  /// an app already shipping Turkish must not lose it by adopting this package.
  static List<Locale> withExtras(Iterable<Locale> extras) {
    final seen = <String>{for (final l in standard) l.languageCode};
    return <Locale>[
      ...standard,
      for (final l in extras)
        if (seen.add(l.languageCode)) l,
    ];
  }
}
