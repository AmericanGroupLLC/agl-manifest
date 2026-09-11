import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'agl_locales.dart';

/// The active locale, persisted across launches.
///
/// A plain [ChangeNotifier] rather than anything framework-specific, because
/// the portfolio is split between Riverpod, provider and bare setState. Every
/// one of those can listen to this; none of them has to adopt another package
/// to do it.
class AglLocaleController extends ChangeNotifier {
  AglLocaleController({List<Locale> extraLocales = const <Locale>[]})
      : supportedLocales = AglLocales.withExtras(extraLocales);

  /// Storage key. Shared across the portfolio on purpose — someone who sets an
  /// AGL app to Spanish has told us something about every AGL app they install.
  static const String prefsKey = 'agl_locale';

  /// What this app ships. [AglLocales.standard], plus any extras it passed in.
  final List<Locale> supportedLocales;

  Locale? _locale;

  /// The user's explicit choice, or `null` for "follow the device".
  ///
  /// `null` is the right default. A phone already set to Spanish should show a
  /// Spanish app without the user having to find a setting, and Flutter's own
  /// locale resolution does that for free when [MaterialApp.locale] is null.
  Locale? get locale => _locale;

  /// Whether the resolved locale reads right to left.
  ///
  /// Falls back to the platform locale when the user has made no choice, so
  /// this is correct before as well as after they pick one.
  bool isRtl(BuildContext context) => AglLocales.isRtl(
      (_locale ?? Localizations.localeOf(context)).languageCode);

  /// Reads the stored choice. Call before `runApp` so a returning user never
  /// sees a frame of the wrong language.
  Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final code = prefs.getString(prefsKey);
      if (code == null || code.isEmpty) return;
      final match = supportedLocales
          .where((l) => l.languageCode == code)
          .cast<Locale?>()
          .firstWhere((l) => true, orElse: () => null);
      // A stored language this build no longer ships resolves to the device
      // rather than to a hardcoded English.
      if (match != null) {
        _locale = match;
        notifyListeners();
      }
    } catch (_) {
      // No preferences available — a fresh install, or a test harness with no
      // platform channels. Following the device locale is a fine outcome, and
      // failing startup over a stored preference would not be.
    }
  }

  /// Sets the language. Pass `null` to go back to following the device.
  Future<void> setLocale(Locale? value) async {
    if (_locale == value) return;
    _locale = value;
    // Notify first: the UI should not wait on disk to redraw.
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      if (value == null) {
        await prefs.remove(prefsKey);
      } else {
        await prefs.setString(prefsKey, value.languageCode);
      }
    } catch (_) {
      // The choice still applies for this session; it just will not survive a
      // restart. Better than throwing out of a tap handler.
    }
  }
}
