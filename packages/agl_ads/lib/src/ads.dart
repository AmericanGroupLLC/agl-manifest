import 'dart:async';

import 'package:agl_observability/agl_observability.dart';
import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'ad_ids.dart';
import 'consent.dart';

/// SDK initialisation and the interstitial lifecycle.
///
/// Every method is a no-op when the platform has no AdMob SDK, and every
/// failure is recorded and swallowed. Nothing here can fail an app.
abstract final class AglAds {
  static AglAdIds? _ids;
  static bool _initialised = false;

  /// Minimum gap between interstitials. Three minutes is deliberately
  /// conservative: Play and the App Store both police "ad density", and an
  /// interstitial on every transition is the single most common reason an
  /// update is rejected for disruptive advertising.
  static Duration minInterstitialInterval = const Duration(minutes: 3);

  /// Transitions to let pass before the first interstitial, so a user's first
  /// minute in the app is never interrupted.
  static int warmupTransitions = 2;

  static InterstitialAd? _interstitial;
  static bool _loading = false;
  static int _transitions = 0;
  static DateTime? _lastShown;
  static bool _suspended = false;

  /// The ids in force. Null until [configure] is called, which is itself the
  /// signal that this app has no ads.
  static AglAdIds? get ids => _ids;

  /// Store-screenshot builds (`--dart-define=SCREENSHOT=true`) never load ads:
  /// a simulator debug build can only show Google's "Test mode" ad, and it
  /// reached iMeasure's, iMaps' and Uscis-Case's App Store screenshots that way.
  static const bool _screenshotBuild = bool.fromEnvironment('SCREENSHOT');

  /// Whether ads are configured and the platform supports them.
  static bool get isEnabled => !_screenshotBuild && _ids != null && AglAdIds.isSupported;

  /// Declares this app's AdMob ids. Call once, from `main()`.
  static void configure(AglAdIds ids) {
    _ids = ids;
  }

  /// Suspends every ad request — for a paid tier, or a screen flow where an ad
  /// would be inappropriate. Existing ads are disposed.
  static void setSuspended({required bool suspended}) {
    _suspended = suspended;
    if (suspended) {
      _interstitial?.dispose();
      _interstitial = null;
    }
  }

  static bool get isSuspended => _suspended;

  /// Initialises the SDK behind UMP consent.
  ///
  /// Call it from `main()` **without** awaiting: the first frame must not wait
  /// on a network round trip to Google. It never throws.
  static Future<void> initialize() async {
    if (!isEnabled || _initialised) return;
    _initialised = true;
    try {
      // Consent first: under GDPR an ad may not be requested before the user
      // has been asked. Initialising the SDK is harmless either way; the
      // request that follows is the part that must be gated.
      await AglConsent.gather();
      await MobileAds.instance.initialize();
      if (kDebugMode) {
        // Test-device ids can be supplied at build time so a physical device
        // used for QA always receives test fill, even from a release build:
        //   --dart-define=ADMOB_TEST_DEVICES=ABCD1234,EFGH5678
        const raw = String.fromEnvironment('ADMOB_TEST_DEVICES');
        if (raw.isNotEmpty) {
          await MobileAds.instance.updateRequestConfiguration(
            RequestConfiguration(testDeviceIds: raw.split(',')),
          );
        }
      }
      // Caches the answer for AglConsent.adsAllowed, which is what the
      // synchronous call sites in the apps read.
      if (!await AglConsent.refresh()) return;
      unawaited(_loadInterstitial());
    } catch (error, stack) {
      await AglCrash.recordError(error, stack, reason: 'AdMob initialize');
    }
  }

  static Future<void> _loadInterstitial() async {
    if (!isEnabled || _suspended || _loading || _interstitial != null) return;
    if (!await AglConsent.canRequestAds()) return;
    _loading = true;
    try {
      await InterstitialAd.load(
        adUnitId: _ids!.interstitial,
        request: const AdRequest(),
        adLoadCallback: InterstitialAdLoadCallback(
          onAdLoaded: (ad) {
            _loading = false;
            if (_suspended) {
              ad.dispose();
              return;
            }
            _interstitial = ad;
          },
          onAdFailedToLoad: (error) {
            // No fill is the normal case for a new AdMob app, not a defect.
            // Leave the slot empty and try again at the next transition —
            // which is the backoff: requests are driven by user navigation,
            // never by a timer, so a dead network cannot spin.
            _loading = false;
            _interstitial = null;
            AglLog.write('Interstitial not filled: ${error.code}');
          },
        ),
      );
    } catch (error, stack) {
      _loading = false;
      await AglCrash.recordError(error, stack, reason: 'Interstitial load');
    }
  }

  /// Records a natural transition, and shows an interstitial if one is ready
  /// and the caps allow it.
  ///
  /// Call **after** the navigation has happened, never before — the user
  /// should already be where they asked to be when an ad appears. Never call
  /// it during sign-in, payment, or any flow the user cannot abandon.
  static void onTransition() {
    if (!isEnabled || _suspended) return;
    _transitions++;

    final ad = _interstitial;
    final last = _lastShown;
    final tooSoon = last != null &&
        DateTime.now().difference(last) < minInterstitialInterval;

    if (ad == null || _transitions <= warmupTransitions || tooSoon) {
      unawaited(_loadInterstitial());
      return;
    }

    _interstitial = null;
    _lastShown = DateTime.now();

    ad.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        unawaited(_loadInterstitial());
      },
      onAdFailedToShowFullScreenContent: (ad, error) {
        ad.dispose();
        AglLog.write('Interstitial failed to show: ${error.code}');
        unawaited(_loadInterstitial());
      },
    );

    try {
      ad.show();
    } catch (error, stack) {
      AglCrash.recordError(error, stack, reason: 'Interstitial show');
      ad.dispose();
      unawaited(_loadInterstitial());
    }
  }

  /// Test seam.
  @visibleForTesting
  static void resetForTest() {
    _interstitial?.dispose();
    _interstitial = null;
    _ids = null;
    _initialised = false;
    _loading = false;
    _transitions = 0;
    _lastShown = null;
    _suspended = false;
  }

  @visibleForTesting
  static int get transitionsForTest => _transitions;
}
