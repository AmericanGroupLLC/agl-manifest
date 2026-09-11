import 'package:agl_ads/agl_ads.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const _androidAppId = 'ca-app-pub-8528784688453695~8044208178';
const _iosAppId = AglAdIds.testIosAppId;

void main() {
  setUp(AglAds.resetForTest);

  group('unit selection', () {
    test('a build with no defines serves Google test units', () {
      final ids = AglAdIds.fromEnvironment(
        androidAppId: _androidAppId,
        iosAppId: _iosAppId,
      );
      // Under `flutter test` this is the host VM: not release, no defines.
      expect(ids.banner, startsWith('ca-app-pub-3940256099942544/'));
      expect(ids.interstitial, startsWith('ca-app-pub-3940256099942544/'));
      expect(ids.servesLiveAds, isFalse);
    });

    test('production units are never served outside a release build', () {
      const ids = AglAdIds(
        androidAppId: _androidAppId,
        iosAppId: _iosAppId,
        androidBanner: 'ca-app-pub-8528784688453695/3721819782',
        androidInterstitial: 'ca-app-pub-8528784688453695/5528514029',
      );
      expect(ids.banner, isNot(contains('8528784688453695')),
          reason: 'a debug build must not request billable ads');
      expect(ids.servesLiveAds, isFalse);
    });

    test('a platform with no live unit keeps test units', () {
      const ids = AglAdIds(
        androidAppId: _androidAppId,
        iosAppId: _iosAppId,
        androidBanner: 'ca-app-pub-8528784688453695/3721819782',
        // iOS deliberately left unset: no iOS AdMob app yet.
      );
      expect(ids.iosBanner, isNull);
    });

    test('the iOS app id is never the Android one', () {
      const ids = AglAdIds(androidAppId: _androidAppId, iosAppId: _iosAppId);
      expect(ids.iosAppId, isNot(ids.androidAppId),
          reason: 'the Android application id crashes the SDK on iOS');
      expect(ids.androidAppId, startsWith('ca-app-pub-'));
      expect(ids.iosAppId, startsWith('ca-app-pub-'));
      expect(ids.androidAppId, contains('~'));
      expect(ids.iosAppId, contains('~'));
    });
  });

  group('AglAds', () {
    test('is disabled until configured', () {
      expect(AglAds.isEnabled, isFalse);
      expect(AglAds.ids, isNull);
    });

    test('initialize and onTransition are no-ops off-device', () async {
      AglAds.configure(
        AglAdIds.fromEnvironment(
          androidAppId: _androidAppId,
          iosAppId: _iosAppId,
        ),
      );
      // isSupported is false on the host VM, so this must return without
      // touching a plugin channel.
      await expectLater(AglAds.initialize(), completes);
      AglAds.onTransition();
      expect(AglAds.transitionsForTest, 0);
    });

    test('suspending disposes and blocks further requests', () {
      AglAds.configure(
        const AglAdIds(androidAppId: _androidAppId, iosAppId: _iosAppId),
      );
      AglAds.setSuspended(suspended: true);
      expect(AglAds.isSuspended, isTrue);
      AglAds.onTransition();
      expect(AglAds.transitionsForTest, 0);
    });
  });

  group('AglConsent', () {
    test('fails closed when the SDK is absent', () async {
      expect(await AglConsent.canRequestAds(), isFalse);
      expect(await AglConsent.isPrivacyOptionsRequired(), isFalse);
    });

    test('the synchronous answer starts false and never guesses', () async {
      // A sync call site that runs before consent resolves must decline. This
      // is what stops a banner built during the first frame from requesting an
      // ad in the EEA before the form has been shown.
      expect(AglConsent.adsAllowed, isFalse);
      await AglConsent.refresh();
      expect(AglConsent.adsAllowed, isFalse,
          reason: 'no SDK here, so the cached answer must stay false');
    });
  });

  testWidgets('the banner takes no space until an ad fills', (tester) async {
    AglAds.configure(
      const AglAdIds(androidAppId: _androidAppId, iosAppId: _iosAppId),
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Column(children: [Text('content'), AglAdBanner()]),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('content'), findsOneWidget);
    expect(tester.getSize(find.byType(AglAdBanner)).height, 0,
        reason: 'an unfilled banner must not reserve a gap');
    expect(tester.takeException(), isNull);
  });
}
