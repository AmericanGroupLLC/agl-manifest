import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';

/// AdMob application and ad-unit identifiers for one app.
///
/// **Where the values come from.** Production units are read from
/// `--dart-define` (or `--dart-define-from-file`) so that no live unit id has
/// to be committed, and a fork or a public mirror of a repository cannot serve
/// ads against an AGL account. A build with no defines serves Google's public
/// test units — the safe default, not a broken one.
///
/// The **application** ids are different: they must be identical to the values
/// in `AndroidManifest.xml` and `Info.plist`, which are committed files, so
/// passing them here is about asserting that they agree, not about secrecy.
/// A mismatch is not a degraded experience — on iOS the SDK throws
/// `GADInvalidInitializationException` and the app is terminated on every
/// launch.
@immutable
class AglAdIds {
  const AglAdIds({
    required this.androidAppId,
    required this.iosAppId,
    this.androidBanner,
    this.androidInterstitial,
    this.iosBanner,
    this.iosInterstitial,
  });

  /// Reads production units from the environment, keeping them out of source.
  ///
  /// Pass them at build time:
  ///
  /// ```sh
  /// flutter build appbundle --release \
  ///   --dart-define=ADMOB_BANNER_ANDROID=ca-app-pub-…/… \
  ///   --dart-define=ADMOB_INTERSTITIAL_ANDROID=ca-app-pub-…/…
  /// # or, better, keep them in a gitignored file:
  /// flutter build ipa --release --dart-define-from-file=env/prod.json
  /// ```
  ///
  /// An id left undefined means "this platform has no live unit yet", and that
  /// platform serves test ads even in release. That is deliberate: an app whose
  /// iOS AdMob app has not been created yet must not report its traffic against
  /// the Android units.
  factory AglAdIds.fromEnvironment({
    required String androidAppId,
    required String iosAppId,
  }) {
    String? env(String key) {
      const values = <String, String>{
        'ADMOB_BANNER_ANDROID':
            String.fromEnvironment('ADMOB_BANNER_ANDROID'),
        'ADMOB_INTERSTITIAL_ANDROID':
            String.fromEnvironment('ADMOB_INTERSTITIAL_ANDROID'),
        'ADMOB_BANNER_IOS': String.fromEnvironment('ADMOB_BANNER_IOS'),
        'ADMOB_INTERSTITIAL_IOS':
            String.fromEnvironment('ADMOB_INTERSTITIAL_IOS'),
      };
      final value = values[key];
      return (value == null || value.isEmpty) ? null : value;
    }

    return AglAdIds(
      androidAppId: androidAppId,
      iosAppId: iosAppId,
      androidBanner: env('ADMOB_BANNER_ANDROID'),
      androidInterstitial: env('ADMOB_INTERSTITIAL_ANDROID'),
      iosBanner: env('ADMOB_BANNER_IOS'),
      iosInterstitial: env('ADMOB_INTERSTITIAL_IOS'),
    );
  }

  final String androidAppId;
  final String iosAppId;
  final String? androidBanner;
  final String? androidInterstitial;
  final String? iosBanner;
  final String? iosInterstitial;

  /// Google's public test application id for iOS. Correct to ship while an app
  /// has no iOS AdMob app of its own — the Android application id is not valid
  /// on iOS and crashes the SDK at launch.
  static const String testIosAppId =
      'ca-app-pub-3940256099942544~1458002511';
  static const String testAndroidAppId =
      'ca-app-pub-3940256099942544~3347511713';

  // https://developers.google.com/admob/android/test-ads
  static const String _testBannerAndroid =
      'ca-app-pub-3940256099942544/6300978111';
  static const String _testInterstitialAndroid =
      'ca-app-pub-3940256099942544/1033173712';
  static const String _testBannerIos =
      'ca-app-pub-3940256099942544/2934735716';
  static const String _testInterstitialIos =
      'ca-app-pub-3940256099942544/4411468910';

  /// True only where the AdMob SDK exists.
  ///
  /// Widget tests run on the host VM, where this is false, so every screen
  /// builds without a plugin channel behind it.
  static bool get isSupported {
    if (kIsWeb) return false;
    try {
      return Platform.isAndroid || Platform.isIOS;
    } catch (_) {
      return false;
    }
  }

  static bool get _isIos {
    if (kIsWeb) return false;
    try {
      return Platform.isIOS;
    } catch (_) {
      return false;
    }
  }

  /// The application id this platform must have declared natively.
  String get appId => _isIos ? iosAppId : androidAppId;

  /// The banner unit to request: production only in a release build that was
  /// given one, Google's test unit in every other case.
  String get banner {
    if (kReleaseMode) {
      final live = _isIos ? iosBanner : androidBanner;
      if (live != null) return live;
    }
    return _isIos ? _testBannerIos : _testBannerAndroid;
  }

  String get interstitial {
    if (kReleaseMode) {
      final live = _isIos ? iosInterstitial : androidInterstitial;
      if (live != null) return live;
    }
    return _isIos ? _testInterstitialIos : _testInterstitialAndroid;
  }

  /// Whether this build will serve real, billable ads.
  ///
  /// Worth showing in a settings or debug row: it is the difference between a
  /// tester seeing house ads and a tester generating invalid traffic.
  bool get servesLiveAds {
    if (!kReleaseMode) return false;
    return (_isIos ? iosBanner : androidBanner) != null ||
        (_isIos ? iosInterstitial : androidInterstitial) != null;
  }
}
