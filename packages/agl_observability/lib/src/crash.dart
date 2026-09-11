import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'telemetry.dart';

/// Crash reporting, wired once and safe everywhere.
///
/// Every method is a no-op when reporting is inactive — which is the case in
/// tests, on unsupported platforms, and in any build whose Firebase config
/// files are absent. Nothing here throws.
abstract final class AglCrash {
  /// Whether reports are actually reaching Crashlytics.
  ///
  /// False is the honest answer in a build with no `google-services.json` /
  /// `GoogleService-Info.plist`, and the app should behave identically either
  /// way. Surface it in a debug/settings screen rather than assuming.
  static bool get isActive => _active;
  static bool _active = false;

  static FirebaseCrashlytics? _crashlytics;

  /// Initialises Firebase and routes framework and platform errors to
  /// Crashlytics. Returns whether reporting became active.
  ///
  /// Call after `WidgetsFlutterBinding.ensureInitialized()` and before
  /// `runApp()`. Collection is off in debug builds unless [enableInDebug] is
  /// set: developer noise would bury real user crashes, and Crashlytics
  /// batches debug reports until the next launch anyway.
  ///
  /// [environment] is recorded as a custom key — 'production', 'staging',
  /// 'development'. [appName] labels reports when several apps share the
  /// Firebase project, which every AGL app does.
  static Future<bool> init({
    String environment = 'production',
    String? appName,
    bool enableInDebug = false,
    FirebaseOptions? options,
  }) async {
    if (_active) return true;

    try {
      await Firebase.initializeApp(options: options);
    } catch (error) {
      // No config files, or no platform channel (widget tests). Both are
      // expected states, not failures worth shouting about.
      AglLog.write(
        'Crash reporting inactive — Firebase did not initialise ($error). '
        'Add google-services.json and GoogleService-Info.plist to enable it.',
        level: AglLogLevel.warning,
      );
      return false;
    }

    try {
      final crashlytics = FirebaseCrashlytics.instance;
      await crashlytics
          .setCrashlyticsCollectionEnabled(enableInDebug || kReleaseMode);

      // Chain rather than replace: a host app may already have installed a
      // handler, and dropping it would silently stop its logging.
      final previousFlutterOnError = FlutterError.onError;
      FlutterError.onError = (details) {
        previousFlutterOnError?.call(details);
        crashlytics.recordFlutterFatalError(details);
      };

      final previousPlatformOnError = PlatformDispatcher.instance.onError;
      PlatformDispatcher.instance.onError = (error, stack) {
        crashlytics.recordError(error, stack, fatal: true);
        return previousPlatformOnError?.call(error, stack) ?? true;
      };

      _crashlytics = crashlytics;
      _active = true;

      await _attachStandardKeys(environment: environment, appName: appName);
      return true;
    } catch (error) {
      AglLog.write('Crash reporting failed to start: $error',
          level: AglLogLevel.warning);
      return false;
    }
  }

  /// Version, build number, environment and app name on every report, so a
  /// crash can be pinned to a specific build without asking the user.
  static Future<void> _attachStandardKeys({
    required String environment,
    String? appName,
  }) async {
    await setKey('environment', environment);
    await setKey('release_mode', kReleaseMode);
    if (appName != null) await setKey('app', appName);
    try {
      final info = await PackageInfo.fromPlatform();
      await setKey('app_version', info.version);
      await setKey('build_number', info.buildNumber);
      await setKey('package_name', info.packageName);
    } catch (_) {
      // package_info_plus needs a platform channel; absent in tests.
    }
  }

  /// Runs [body] in a zone whose uncaught asynchronous errors are reported.
  ///
  /// `PlatformDispatcher.onError` catches most of these on its own in modern
  /// Flutter; the zone is belt and braces for errors raised before the
  /// binding exists — which is precisely where a startup crash lives.
  static Future<void> runGuarded(FutureOr<void> Function() body) {
    final completer = Completer<void>();
    runZonedGuarded<Future<void>>(
      () async {
        try {
          await body();
        } finally {
          if (!completer.isCompleted) completer.complete();
        }
      },
      (error, stack) {
        recordError(error, stack, reason: 'Uncaught zone error', fatal: true);
        if (!completer.isCompleted) completer.complete();
      },
    );
    return completer.future;
  }

  /// Reports a non-fatal error. Safe whether or not reporting is active.
  ///
  /// Use this for a caught failure the user recovered from — a request that
  /// retried, a parse that fell back to a default. The user sees a friendly
  /// message; the diagnostics come here.
  static Future<void> recordError(
    Object error,
    StackTrace? stack, {
    String? reason,
    bool fatal = false,
  }) async {
    if (!_active) {
      AglLog.write('(unreported) ${reason ?? 'error'}: $error',
          level: AglLogLevel.warning);
      return;
    }
    try {
      await _crashlytics!
          .recordError(error, stack, reason: reason, fatal: fatal);
    } catch (_) {
      // Reporting a crash must never itself crash the app.
    }
  }

  /// Adds a breadcrumb to the next report. Never log personal data.
  static Future<void> log(String message) async {
    AglLog.write(message, level: AglLogLevel.debug);
    if (!_active) return;
    try {
      await _crashlytics!.log(message);
    } catch (_) {}
  }

  /// Records which screen the user is on, so a report says where it happened.
  /// Wire it to a `NavigatorObserver` or a router listener.
  static Future<void> setScreen(String routeName) =>
      setKey('screen', routeName);

  /// Records whether the session is authenticated — never who.
  static Future<void> setAuthenticated(bool value) =>
      setKey('authenticated', value);

  /// Attaches an arbitrary non-PII key to subsequent reports.
  static Future<void> setKey(String key, Object value) async {
    if (!_active) return;
    try {
      await _crashlytics!.setCustomKey(key, value);
    } catch (_) {}
  }

  /// Ties reports to an opaque, stable id so a support ticket can be matched
  /// to a crash.
  ///
  /// Pass a UUID or a hashed id — **never** an email, phone number or name.
  /// Both stores treat a crash log carrying an email as a data disclosure you
  /// have to declare.
  static Future<void> setUserId(String opaqueId) async {
    if (!_active) return;
    try {
      await _crashlytics!.setUserIdentifier(opaqueId);
    } catch (_) {}
  }

  /// Clears the user id at sign-out.
  static Future<void> clearUserId() => setUserId('');

  /// Sends a *non-fatal* test report, to prove the pipeline end to end.
  ///
  /// Deliberately not `FirebaseCrashlytics.instance.crash()`: a real crash
  /// call is one careless merge away from shipping. This appears in the
  /// console under Non-fatals within a couple of minutes.
  ///
  /// Returns false when reporting is inactive, which is itself the answer to
  /// "is Crashlytics configured yet".
  static Future<bool> sendTestReport() async {
    if (!_active) return false;
    await recordError(
      StateError('AGL Crashlytics verification report'),
      StackTrace.current,
      reason: 'Deliberate verification — not a real failure',
    );
    try {
      await _crashlytics!.sendUnsentReports();
    } catch (_) {}
    return true;
  }

  /// Test seam. Resets the singleton state between tests.
  @visibleForTesting
  static void resetForTest() {
    _active = false;
    _crashlytics = null;
  }
}
