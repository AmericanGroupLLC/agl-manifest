import 'dart:convert';
import 'dart:io';

import 'package:agl_i18n/agl_i18n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Every app in the portfolio depends on this package, so a regression here is
/// a regression in 42 apps at once. These tests are the contract.

Map<String, dynamic> arb(String code) => json.decode(
        File('lib/l10n/agl_$code.arb').readAsStringSync())
    as Map<String, dynamic>;

Widget harness(AglLocaleController controller, {Widget? child}) =>
    ListenableBuilder(
      listenable: controller,
      builder: (context, _) => MaterialApp(
        locale: controller.locale,
        supportedLocales: controller.supportedLocales,
        localizationsDelegates: aglLocalizationsDelegates(null),
        home: child ?? AglLanguageScreen(controller: controller),
      ),
    );

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('the locale set', () {
    test('is the twelve agreed languages, in picker order', () {
      expect(AglLocales.standard.map((l) => l.languageCode).toList(), [
        'en', 'es', 'zh', 'hi', 'fr', 'ar',
        'de', 'ja', 'pt', 'ko', 'it', 'ru',
      ]);
    });

    test('includes a right-to-left language, so RTL bugs surface early', () {
      expect(
          AglLocales.standard
              .any((l) => AglLocales.isRtl(l.languageCode)),
          isTrue);
    });

    test('names every standard language in its own script', () {
      for (final locale in AglLocales.standard) {
        final name = AglLocales.nativeName(locale.languageCode);
        // Falling through to the raw code means a name was never added.
        expect(name, isNot(locale.languageCode),
            reason: 'no native name for ${locale.languageCode}');
      }
    });

    test('an unknown code degrades to the code rather than throwing', () {
      expect(AglLocales.nativeName('xx'), 'xx');
    });

    group('withExtras', () {
      test('appends languages an app adds', () {
        final result = AglLocales.withExtras(
            const [Locale('tr'), Locale('sw')]);
        expect(result.map((l) => l.languageCode),
            containsAll(<String>['tr', 'sw']));
        expect(result.length, AglLocales.standard.length + 2);
      });

      test('never duplicates one already in the standard set', () {
        final result = AglLocales.withExtras(const [Locale('fr')]);
        expect(result.length, AglLocales.standard.length);
      });

      test('never drops a language — adopting this package must not cost '
          'an app a locale it already shipped', () {
        // iMaps ships these three beyond the standard set.
        final result = AglLocales.withExtras(
            const [Locale('tr'), Locale('id'), Locale('sw')]);
        for (final code in ['tr', 'id', 'sw']) {
          expect(result.map((l) => l.languageCode), contains(code));
        }
      });
    });
  });

  group('the controller', () {
    test('defaults to following the device', () {
      expect(AglLocaleController().locale, isNull);
    });

    test('persists a choice and reads it back', () async {
      final a = AglLocaleController();
      await a.setLocale(const Locale('ja'));

      final b = AglLocaleController();
      await b.load();
      expect(b.locale, const Locale('ja'));
    });

    test('clearing the choice goes back to the device', () async {
      final a = AglLocaleController();
      await a.setLocale(const Locale('ja'));
      await a.setLocale(null);

      final b = AglLocaleController();
      await b.load();
      expect(b.locale, isNull);
    });

    test('a stored language this build no longer ships is ignored, '
        'not forced to English', () async {
      SharedPreferences.setMockInitialValues(
          {AglLocaleController.prefsKey: 'sw'});
      final c = AglLocaleController(); // no extras, so Swahili is absent
      await c.load();
      expect(c.locale, isNull);
    });

    test('a stored language an app added as an extra is honoured', () async {
      SharedPreferences.setMockInitialValues(
          {AglLocaleController.prefsKey: 'sw'});
      final c = AglLocaleController(extraLocales: const [Locale('sw')]);
      await c.load();
      expect(c.locale, const Locale('sw'));
    });

    test('notifies listeners on change, and not on a no-op set', () async {
      final c = AglLocaleController();
      var notifications = 0;
      c.addListener(() => notifications++);

      await c.setLocale(const Locale('es'));
      expect(notifications, 1);

      await c.setLocale(const Locale('es'));
      expect(notifications, 1, reason: 'setting the same locale is a no-op');
    });

    testWidgets('isRtl follows the device when no choice is made',
        (tester) async {
      final c = AglLocaleController();
      late BuildContext ctx;
      await tester.pumpWidget(harness(c,
          child: Builder(builder: (context) {
            ctx = context;
            return const SizedBox();
          })));
      // The test binding reports en-US.
      expect(c.isRtl(ctx), isFalse);

      await c.setLocale(const Locale('ar'));
      await tester.pump();
      expect(c.isRtl(ctx), isTrue);
    });
  });

  group('the shared catalogue', () {
    test('every locale carries every key the template defines', () {
      final keys =
          arb('en').keys.where((k) => !k.startsWith('@')).toSet();
      for (final locale in AglLocales.standard) {
        final missing = keys.difference(arb(locale.languageCode).keys.toSet());
        expect(missing, isEmpty,
            reason: 'agl_${locale.languageCode}.arb is missing: '
                '${missing.join(', ')}');
      }
    });

    test('no locale silently repeats the English text', () {
      // Strings that stay identical in every language because they carry a
      // brand name.
      const brandBearing = {
        'authContinueWithGoogle',
        'authContinueWithApple',
      };

      // Genuine cognates and loanwords, listed per language rather than per
      // key so the check stays sharp everywhere else. Each of these is the
      // word a native speaker would actually use — inventing a different one
      // to satisfy a test would make the app worse, not more translated.
      const cognates = <String, Set<String>>{
        'de': {'authName', 'miscVersion'},
        'es': {'miscTotal'},
        'fr': {'navNotifications', 'miscVersion', 'miscTotal'},
        'it': {'navHome', 'navAccount', 'authPassword'},
        'pt': {'miscTotal'},
      };

      final en = arb('en');
      final keys = en.keys.where((k) => !k.startsWith('@')).toSet();

      for (final locale in AglLocales.standard) {
        final code = locale.languageCode;
        if (code == 'en') continue;
        final other = arb(code);
        final allowed = cognates[code] ?? const <String>{};
        final repeated = keys
            .where((k) =>
                !brandBearing.contains(k) &&
                !allowed.contains(k) &&
                other[k] == en[k])
            .toList()
          ..sort();
        expect(repeated, isEmpty,
            reason: 'agl_$code.arb repeats English for: '
                '${repeated.join(', ')}');
      }
    });

    test('every English string has a description for the translator', () {
      final en = arb('en');
      final undocumented = en.keys
          .where((k) => !k.startsWith('@') && k != '@@locale')
          .where((k) {
            final meta = en['@$k'];
            return meta is! Map ||
                (meta['description'] as String?)?.isNotEmpty != true;
          })
          .toList()
        ..sort();
      expect(undocumented, isEmpty);
    });

    test('an ARB file exists for every standard locale, and no orphans', () {
      final onDisk = Directory('lib/l10n')
          .listSync()
          .whereType<File>()
          .where((f) => f.path.endsWith('.arb'))
          .map((f) => f.uri.pathSegments.last
              .replaceFirst('agl_', '')
              .replaceFirst('.arb', ''))
          .toSet();
      expect(onDisk,
          AglLocales.standard.map((l) => l.languageCode).toSet());
    });
  });

  group('the delegates', () {
    test('include the three Flutter globals, so Material widgets translate '
        'too', () {
      final delegates = aglLocalizationsDelegates(null);
      expect(delegates, contains(GlobalMaterialLocalizations.delegate));
      expect(delegates, contains(GlobalWidgetsLocalizations.delegate));
      expect(delegates, contains(GlobalCupertinoLocalizations.delegate));
    });

    test("the app's own delegate comes first, so it can override a shared "
        'string', () {
      final app = AglL10n.delegate;
      expect(aglLocalizationsDelegates(app).first, same(app));
    });

    test('a null app delegate is allowed — some apps have no strings of '
        'their own yet', () {
      expect(aglLocalizationsDelegates(null), isNotEmpty);
    });
  });

  group('the picker', () {
    testWidgets('lists system default plus every supported language',
        (tester) async {
      await tester.pumpWidget(harness(AglLocaleController()));
      await tester.pumpAndSettle();

      expect(find.text('System default'), findsOneWidget);
      for (final locale in AglLocales.standard) {
        final name = AglLocales.nativeName(locale.languageCode);
        await tester.scrollUntilVisible(find.text(name), 100,
            scrollable: find.byType(Scrollable).first);
        expect(find.text(name), findsOneWidget);
      }
    });

    testWidgets('choosing a language re-renders the picker in it',
        (tester) async {
      final c = AglLocaleController();
      await tester.pumpWidget(harness(c));
      await tester.pumpAndSettle();
      expect(find.text('Language'), findsOneWidget);

      await tester.tap(find.text('Español'));
      await tester.pumpAndSettle();

      expect(c.locale, const Locale('es'));
      expect(find.text('Idioma'), findsOneWidget);
      expect(find.text('Language'), findsNothing);
    });

    testWidgets('an Arabic app lays the picker out right to left',
        (tester) async {
      final c = AglLocaleController();
      await c.setLocale(const Locale('ar'));
      await tester.pumpWidget(harness(c));
      await tester.pumpAndSettle();

      expect(find.text('اللغة'), findsWidgets);
      expect(Directionality.of(tester.element(find.text('العربية').first)),
          TextDirection.rtl);
    });

    testWidgets('an English app still shows Arabic right to left',
        (tester) async {
      await tester.pumpWidget(harness(AglLocaleController()));
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(find.text('العربية'), 100,
          scrollable: find.byType(Scrollable).first);
      expect(Directionality.of(tester.element(find.text('العربية'))),
          TextDirection.rtl);
    });
  });

  group('shared strings resolve', () {
    for (final entry in {
      'es': 'Guardar',
      'ja': '保存',
      'ar': 'حفظ',
      'ru': 'Сохранить',
    }.entries) {
      testWidgets('${entry.key} renders its own word for Save',
          (tester) async {
        final l = await AglL10n.delegate.load(Locale(entry.key));
        expect(l.actionSave, entry.value);
      });
    }
  });
}
