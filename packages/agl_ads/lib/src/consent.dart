import 'dart:async';

import 'package:agl_observability/agl_observability.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'ad_ids.dart';

/// Google User Messaging Platform consent.
///
/// AdMob policy requires a certified CMP for users in the EEA, the UK and
/// Switzerland: an ad must not be **requested** there until the user has been
/// asked — serving a non-personalised one instead is not sufficient. UMP
/// decides whether a form is required from the user's actual location, so
/// there is no geo-check here; everywhere else it reports "not required" and
/// ads proceed untouched.
///
/// The forms are authored in the AdMob console under **Privacy & messaging**.
/// Until a GDPR message is published there, UMP reports "not required"
/// everywhere and this is a no-op — publishing the message switches it on with
/// no app change and no new build.
abstract final class AglConsent {
  static bool _gathered = false;
  static bool _allowed = false;
  static Future<void>? _inFlight;

  /// The last answer from [canRequestAds], readable synchronously.
  ///
  /// Some ad call sites cannot await — a `build()` method, or a factory that
  /// returns a `BannerAd`. They read this instead.
  ///
  /// It is **false until consent has actually been resolved**, so a sync call
  /// site that runs before [gather] completes declines to request an ad rather
  /// than guessing. That is the right way round: a missed impression costs
  /// pennies, a request without consent is a policy breach. Call [refresh]
  /// once at startup — `AglAds.initialize()` already does.
  static bool get adsAllowed => _allowed;

  /// Requests the consent info and shows the form if UMP says one is required.
  ///
  /// Safe to call repeatedly; the work happens once per launch. Never throws —
  /// a consent failure must not stop the app, and [canRequestAds] stays
  /// authoritative about whether a request may actually go out.
  static Future<void> gather() {
    if (!AglAdIds.isSupported) return Future<void>.value();
    return _inFlight ??= _gather();
  }

  static Future<void> _gather() async {
    final completer = Completer<void>();

    void finish() {
      _gathered = true;
      if (!completer.isCompleted) completer.complete();
    }

    try {
      ConsentInformation.instance.requestConsentInfoUpdate(
        ConsentRequestParameters(),
        () async {
          await ConsentForm.loadAndShowConsentFormIfRequired((formError) {
            if (formError != null) {
              AglLog.write(
                'Consent form: ${formError.errorCode} ${formError.message}',
                level: AglLogLevel.warning,
              );
            }
            finish();
          });
        },
        (formError) {
          // UMP unreachable. canRequestAds() still decides, and it answers
          // false where consent is required but unresolved.
          AglLog.write(
            'Consent info update failed: '
            '${formError.errorCode} ${formError.message}',
            level: AglLogLevel.warning,
          );
          finish();
        },
      );
    } catch (error, stack) {
      AglCrash.recordError(error, stack, reason: 'UMP consent');
      finish();
    }

    // A user who leaves the form open must not wedge ad loading forever.
    return completer.future
        .timeout(const Duration(seconds: 30), onTimeout: finish);
  }

  /// Whether an ad request is permitted right now.
  ///
  /// This is UMP's answer, not ours. Fails **closed**: a lost impression costs
  /// pennies, a request without consent is a policy breach.
  static Future<bool> canRequestAds() async {
    if (!AglAdIds.isSupported) return _allowed = false;
    if (!_gathered) await gather();
    try {
      return _allowed = await ConsentInformation.instance.canRequestAds();
    } catch (error, stack) {
      await AglCrash.recordError(error, stack, reason: 'canRequestAds');
      return _allowed = false;
    }
  }

  /// Resolves consent and caches the answer for [adsAllowed]. Call once at
  /// startup, before anything might build a banner.
  static Future<bool> refresh() => canRequestAds();

  /// Whether to offer a "Privacy options" row in settings.
  ///
  /// Where a GDPR message applies, Google requires an always-available way to
  /// change the choice after the first prompt. Show the row only when this is
  /// true, so users elsewhere are not offered a form that would not open.
  static Future<bool> isPrivacyOptionsRequired() async {
    if (!AglAdIds.isSupported) return false;
    try {
      final status =
          await ConsentInformation.instance.getPrivacyOptionsRequirementStatus();
      return status == PrivacyOptionsRequirementStatus.required;
    } catch (_) {
      return false;
    }
  }

  /// Reopens the consent form so the user can change their choice.
  static Future<void> showPrivacyOptions() async {
    if (!AglAdIds.isSupported) return;
    try {
      await ConsentForm.showPrivacyOptionsForm((formError) {
        if (formError != null) {
          AglLog.write(
            'Privacy options: ${formError.errorCode} ${formError.message}',
            level: AglLogLevel.warning,
          );
        }
      });
    } catch (error, stack) {
      await AglCrash.recordError(error, stack, reason: 'showPrivacyOptions');
    }
  }

  /// Clears the stored consent so the form can be re-tested. Debug only —
  /// calling this in production would re-prompt every user.
  static Future<void> resetForTesting() async {
    if (!AglAdIds.isSupported) return;
    try {
      ConsentInformation.instance.reset();
      _gathered = false;
      _allowed = false;
      _inFlight = null;
    } catch (_) {}
  }
}
