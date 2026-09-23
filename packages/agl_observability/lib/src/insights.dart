import 'dart:async';

import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_performance/firebase_performance.dart';
import 'package:firebase_remote_config/firebase_remote_config.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import 'telemetry.dart';

/// The Firebase products that cost nothing on the Spark plan, wired once.
///
/// Analytics, Performance Monitoring and Remote Config are free at any volume,
/// need no per-app console work beyond the config files every AGL app already
/// ships, and are independent of each other. They are grouped here so an app
/// gains all three from one call.
///
/// This follows the same rule as [AglCrash]: **telemetry must never take an
/// app down.** Every product is initialised in its own try/catch, every getter
/// answers honestly when the product is inactive, and an app with no Firebase
/// config behaves exactly as it did before — silently unreported.
///
/// ```dart
/// await AglCrash.init(environment: AppEnv.name);
/// await AglInsights.init(appName: 'CalcMaster');
/// ```
///
/// Deliberately *not* here, because each needs per-app console configuration
/// that does not exist yet and would fail closed rather than silently:
/// Cloud Messaging (an APNs key per bundle id), App Check (a DeviceCheck and
/// Play Integrity provider per app) and In-App Messaging (campaigns).
abstract final class AglInsights {
  static bool get analyticsActive => _analytics != null;
  static bool get performanceActive => _performance != null;
  static bool get remoteConfigActive => _remoteConfig != null;

  static FirebaseAnalytics? _analytics;
  static FirebasePerformance? _performance;
  static FirebaseRemoteConfig? _remoteConfig;

  /// A navigator observer that logs screen views, or null when Analytics did
  /// not start. Add it to `MaterialApp.navigatorObservers`.
  static NavigatorObserver? get navigatorObserver => _navigatorObserver;
  static NavigatorObserver? _navigatorObserver;

  /// Starts every free product that can start. Returns the ones that did.
  ///
  /// Safe to call more than once; the second call is a no-op. Call after
  /// [AglCrash.init], which is what initialises Firebase itself — if Firebase
  /// never came up, this returns an empty set without touching anything.
  ///
  /// [defaults] seed Remote Config so the very first launch, before any fetch
  /// completes, reads real values rather than empty ones.
  static Future<Set<String>> init({
    String? appName,
    bool enableInDebug = false,
    Map<String, dynamic> defaults = const {},
    Duration remoteConfigMinimumFetchInterval = const Duration(hours: 1),
  }) async {
    final started = <String>{};
    if (Firebase.apps.isEmpty) {
      AglLog.write(
        'Insights inactive — Firebase is not initialised. Call AglCrash.init '
        'first; an app with no Firebase config runs unreported by design.',
        level: AglLogLevel.warning,
      );
      return started;
    }

    // Collection off in debug for the same reason crash reporting is: developer
    // traffic pollutes the funnels real users are measured by.
    final collect = enableInDebug || kReleaseMode;

    if (_analytics == null) {
      try {
        final analytics = FirebaseAnalytics.instance;
        await analytics.setAnalyticsCollectionEnabled(collect);
        if (appName != null) {
          await analytics.setDefaultEventParameters({'app_name': appName});
        }
        _analytics = analytics;
        _navigatorObserver =
            FirebaseAnalyticsObserver(analytics: analytics);
        started.add('analytics');
      } catch (error) {
        AglLog.write('Analytics did not start: $error',
            level: AglLogLevel.warning);
      }
    }

    if (_performance == null) {
      try {
        final performance = FirebasePerformance.instance;
        await performance.setPerformanceCollectionEnabled(collect);
        _performance = performance;
        started.add('performance');
      } catch (error) {
        AglLog.write('Performance monitoring did not start: $error',
            level: AglLogLevel.warning);
      }
    }

    if (_remoteConfig == null) {
      try {
        final config = FirebaseRemoteConfig.instance;
        await config.setConfigSettings(RemoteConfigSettings(
          fetchTimeout: const Duration(seconds: 10),
          // Zero in debug so a developer can see a console change immediately;
          // throttled in release so launches are not spent on network.
          minimumFetchInterval:
              kReleaseMode ? remoteConfigMinimumFetchInterval : Duration.zero,
        ));
        if (defaults.isNotEmpty) await config.setDefaults(defaults);
        _remoteConfig = config;
        started.add('remote_config');
        // Not awaited: a slow or offline fetch must not delay first frame.
        // Defaults are already live, and the fetched values apply next launch.
        unawaited(config.fetchAndActivate().catchError((Object error) {
          AglLog.write('Remote Config fetch failed: $error',
              level: AglLogLevel.warning);
          return false;
        }));
      } catch (error) {
        AglLog.write('Remote Config did not start: $error',
            level: AglLogLevel.warning);
      }
    }

    AglLog.write('Insights active: ${started.join(', ')}',
        level: AglLogLevel.info);
    return started;
  }

  // --- Analytics -----------------------------------------------------------

  /// Records an event. Silently ignored when Analytics is inactive.
  static Future<void> logEvent(String name,
      {Map<String, Object>? parameters}) async {
    final analytics = _analytics;
    if (analytics == null) return;
    try {
      await analytics.logEvent(name: name, parameters: parameters);
    } catch (error) {
      AglLog.write('logEvent($name) failed: $error',
          level: AglLogLevel.warning);
    }
  }

  /// Ties events to a user. Pass null on sign-out.
  static Future<void> setUserId(String? id) async {
    final analytics = _analytics;
    if (analytics == null) return;
    try {
      await analytics.setUserId(id: id);
    } catch (error) {
      AglLog.write('setUserId failed: $error', level: AglLogLevel.warning);
    }
  }

  // --- Remote Config -------------------------------------------------------

  /// Reads a flag, answering [fallback] when Remote Config is inactive or the
  /// key is absent. Never throws, so it is safe in a build method.
  static bool flag(String key, {bool fallback = false}) {
    final config = _remoteConfig;
    if (config == null) return fallback;
    try {
      return config.getAll().containsKey(key) ? config.getBool(key) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  static String setting(String key, {String fallback = ''}) {
    final config = _remoteConfig;
    if (config == null) return fallback;
    try {
      final value = config.getString(key);
      return value.isEmpty ? fallback : value;
    } catch (_) {
      return fallback;
    }
  }

  static int number(String key, {int fallback = 0}) {
    final config = _remoteConfig;
    if (config == null) return fallback;
    try {
      return config.getAll().containsKey(key) ? config.getInt(key) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  // --- Performance ---------------------------------------------------------

  /// Times [body] as a custom trace and returns its result.
  ///
  /// The trace is best-effort: if Performance is inactive, or starting or
  /// stopping the trace throws, [body] still runs and its value or error is
  /// propagated unchanged. Instrumenting code must not change what it measures.
  static Future<T> trace<T>(String name, Future<T> Function() body) async {
    final performance = _performance;
    if (performance == null) return body();

    Trace? trace;
    try {
      trace = performance.newTrace(name);
      await trace.start();
    } catch (error) {
      AglLog.write('trace($name) did not start: $error',
          level: AglLogLevel.warning);
      trace = null;
    }

    try {
      return await body();
    } finally {
      if (trace != null) {
        try {
          await trace.stop();
        } catch (error) {
          AglLog.write('trace($name) did not stop: $error',
              level: AglLogLevel.warning);
        }
      }
    }
  }

  /// Resets state between tests. Not for production use.
  @visibleForTesting
  static void resetForTest() {
    _analytics = null;
    _performance = null;
    _remoteConfig = null;
    _navigatorObserver = null;
  }
}
