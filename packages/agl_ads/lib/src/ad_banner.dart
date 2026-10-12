import 'package:agl_observability/agl_observability.dart';
import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'ad_ids.dart';
import 'ads.dart';
import 'consent.dart';

/// Standard banner height. Google returns a creative at or under this.
const int _maxHeight = 50;

/// An adaptive banner that occupies **no space at all** until it fills.
///
/// Sized with [AdSize.getInlineAdaptiveBannerAdSize], which asks Google for the
/// best ad it has at no more than [_maxHeight] — so the slot adapts to the
/// device while staying near the standard 50dp banner. The anchored adaptive
/// sizes return up to 100dp, which takes far too much of a phone screen.
///
/// The height is never guessed: once the ad loads, [BannerAd.getPlatformAdSize]
/// reports what Google actually returned and the container is sized to exactly
/// that, so the creative is never stretched or letterboxed.
///
/// Because it is zero-height until it fills, it must sit in normal layout flow
/// — a `Column` child, or `bottomNavigationBar` — and never in a `Stack` over
/// content, which is both a policy risk and the usual cause of accidental
/// clicks.
class AglAdBanner extends StatefulWidget {
  const AglAdBanner({super.key, this.maxHeight = _maxHeight});

  final int maxHeight;

  @override
  State<AglAdBanner> createState() => _AglAdBannerState();
}

class _AglAdBannerState extends State<AglAdBanner> {
  BannerAd? _ad;
  AdSize? _loadedSize;
  bool _requested = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Adaptive sizing needs the screen width, so this cannot run in initState.
    // The flag makes it once per state, not once per dependency change.
    if (!_requested) {
      _requested = true;
      _load();
    }
  }

  Future<void> _load() async {
    final ids = AglAds.ids;
    // isEnabled also covers store-screenshot builds (SCREENSHOT=true).
    if (ids == null || !AglAds.isEnabled || AglAds.isSuspended) return;
    // Consent gates the request itself, not just personalisation.
    if (!await AglConsent.canRequestAds()) return;
    if (!mounted) return;

    final width = MediaQuery.sizeOf(context).width.truncate();
    try {
      final ad = BannerAd(
        adUnitId: ids.banner,
        size: AdSize.getInlineAdaptiveBannerAdSize(width, widget.maxHeight),
        request: const AdRequest(),
        listener: BannerAdListener(
          onAdLoaded: (ad) async {
            final size = await (ad as BannerAd).getPlatformAdSize();
            // The widget can be disposed while Google is answering. Setting
            // state here would throw, and keeping the ad would leak it.
            if (!mounted) {
              ad.dispose();
              return;
            }
            setState(() => _loadedSize = size);
          },
          onAdFailedToLoad: (ad, error) {
            ad.dispose();
            AglLog.write('Banner not filled: ${error.code}');
            if (!mounted) return;
            setState(() {
              _ad = null;
              _loadedSize = null;
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
      await AglCrash.recordError(error, stack, reason: 'Banner load');
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
    final size = _loadedSize;
    if (ad == null || size == null) return const SizedBox.shrink();

    final theme = Theme.of(context);
    return Semantics(
      label: 'Advertisement',
      container: true,
      child: Container(
        width: double.infinity,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          border: Border(
            top: BorderSide(color: theme.dividerColor),
          ),
        ),
        child: SizedBox(
          width: size.width.toDouble(),
          height: size.height.toDouble(),
          child: AdWidget(ad: ad),
        ),
      ),
    );
  }
}
