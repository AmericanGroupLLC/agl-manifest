import 'package:flutter/foundation.dart';

enum AglLogLevel { debug, info, warning, error }

/// Logging that is silent in release builds.
///
/// `print()` in a released app is a leak: on Android anything written to
/// stdout lands in logcat, readable by `adb logcat` on any device with
/// developer options on. Every AGL app routes diagnostics through here, which
/// compiles down to nothing in release except for warnings and errors — and
/// those go to `debugPrint`, not `print`, so they are rate-limited rather than
/// able to drop lines under load.
abstract final class AglLog {
  /// Set false to silence even warnings, e.g. in a noisy test.
  static bool enabled = true;

  static void write(String message, {AglLogLevel level = AglLogLevel.debug}) {
    if (!enabled) return;
    final isProblem =
        level == AglLogLevel.warning || level == AglLogLevel.error;
    if (kReleaseMode && !isProblem) return;
    debugPrint('[AGL:${level.name}] $message');
  }
}
