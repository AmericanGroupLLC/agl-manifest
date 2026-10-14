import 'package:agl_observability/agl_observability.dart';
import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'ads.dart';
import 'consent.dart';

/// A native ad drawn by Google's built-in template, as one item in a list or
/// feed. Occupies **no space** until it fills, like [AglAdBanner].
///
/// The template ([NativeTemplateStyle]) needs no `NativeAdFactory` on the
/// Android or iOS side, so an app adds this widget and nothing else. Google's
/// template carries the "Ad" attribution badge the native-ads policy requires.
///
/// Place it as a distinct row between content items — at most one per screen
/// of content — never styled to pass as an app item, and never in a `Stack`.
class AglNativeAd extends StatefulWidget {
  const AglNativeAd({super.key, this.medium = false});

  /// The medium template (media view, about 320dp tall) instead of the small
  /// one (a row about 90-120dp tall).
  final bool medium;

  @override
  State<AglNativeAd> createState() => _AglNativeAdState();
}

class _AglNativeAdState extends State<AglNativeAd> {
  NativeAd? _ad;
  bool _loaded = false;
  bool _requested = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // The template colours come from the theme, so this cannot run in
    // initState. The flag makes it once per state.
    if (!_requested) {
      _requested = true;
      _load();
    }
  }

  Future<void> _load() async {
    final ids = AglAds.ids;
    if (ids == null || !AglAds.isEnabled || AglAds.isSuspended) return;
    if (!await AglConsent.canRequestAds()) return;
    if (!mounted) return;

    final scheme = Theme.of(context).colorScheme;
    try {
      final ad = NativeAd(
        adUnitId: ids.native,
        request: const AdRequest(),
        nativeTemplateStyle: NativeTemplateStyle(
          templateType: widget.medium ? TemplateType.medium : TemplateType.small,
          mainBackgroundColor: scheme.surface,
          cornerRadius: 12,
          callToActionTextStyle: NativeTemplateTextStyle(
            textColor: scheme.onPrimary,
            backgroundColor: scheme.primary,
          ),
          primaryTextStyle: NativeTemplateTextStyle(textColor: scheme.onSurface),
          secondaryTextStyle:
              NativeTemplateTextStyle(textColor: scheme.onSurfaceVariant),
          tertiaryTextStyle:
              NativeTemplateTextStyle(textColor: scheme.onSurfaceVariant),
        ),
        listener: NativeAdListener(
          onAdLoaded: (ad) {
            if (!mounted) {
              ad.dispose();
              return;
            }
            setState(() => _loaded = true);
          },
          onAdFailedToLoad: (ad, error) {
            ad.dispose();
            AglLog.write('Native not filled: ${error.code}');
            if (!mounted) return;
            setState(() {
              _ad = null;
              _loaded = false;
            });
          },
        ),
      );
      if (!mounted) {
        ad.dispose();
        return;
      }
      _ad = ad;
      await ad.load();
    } catch (error, stack) {
      await AglCrash.recordError(error, stack, reason: 'Native load');
    }
  }

  @override
  void dispose() {
    _ad?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ad = _ad;
    if (ad == null || !_loaded) return const SizedBox.shrink();
    // Google's documented bounds for each template.
    final constraints = widget.medium
        ? const BoxConstraints(
            minWidth: 320, minHeight: 320, maxWidth: 400, maxHeight: 400)
        : const BoxConstraints(
            minWidth: 320, minHeight: 90, maxWidth: 400, maxHeight: 200);
    return Semantics(
      label: 'Advertisement',
      container: true,
      child: Center(
        child: ConstrainedBox(
          constraints: constraints,
          child: AdWidget(ad: ad),
        ),
      ),
    );
  }
}
