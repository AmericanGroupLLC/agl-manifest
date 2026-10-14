/// Shared Google AdMob integration for the American Group LLC portfolio.
///
/// ```dart
/// // main(), before runApp — never awaited on the critical path.
/// AglAds.configure(AglAdIds.fromEnvironment(
///   androidAppId: 'ca-app-pub-…~…',   // must equal AndroidManifest.xml
///   iosAppId: 'ca-app-pub-…~…',       // must equal Info.plist
/// ));
/// unawaited(AglAds.initialize());
///
/// // In a screen, in normal layout flow — never stacked over content.
/// const AglAdBanner(),
///
/// // After a navigation the user asked for, never before it.
/// AglAds.onTransition();
///
/// // Only where it fits the app: a native row in a list or feed …
/// const AglNativeAd(),
///
/// // … or a reward the user chooses ("watch an ad to unlock …").
/// unawaited(AglAds.preloadRewarded());           // when that screen opens
/// await AglAds.showRewarded(onReward: unlock);   // from the button
/// ```
///
/// Three rules this package exists to enforce:
///
/// 1. **Consent gates the request, not just personalisation.** In the EEA, the
///    UK and Switzerland an ad may not be *requested* until the user has been
///    asked. Every load is behind `canRequestAds()`, which fails closed.
/// 2. **Production units only in release builds.** Requesting live ads from a
///    development build is what gets an AdMob account suspended for invalid
///    traffic.
/// 3. **Ads are additive.** A failed load, an empty fill or an SDK that never
///    initialises leaves the app exactly as usable as it was.
library;

export 'src/ad_banner.dart' show AglAdBanner;
export 'src/ad_ids.dart' show AglAdIds;
export 'src/ad_native.dart' show AglNativeAd;
export 'src/ads.dart' show AglAds;
export 'src/consent.dart' show AglConsent;
