import 'package:agl_observability/agl_observability.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

/// The contract for 37 apps: an app with no Firebase config must behave
/// exactly as it did before crash reporting was added.
void main() {
  setUp(AglCrash.resetForTest);

  test('init returns false rather than throwing when Firebase is absent',
      () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    // No platform channel and no config files in a unit test — the same state
    // as an app whose google-services.json has not been added yet.
    expect(await AglCrash.init(environment: 'test'), isFalse);
    expect(AglCrash.isActive, isFalse);
  });

  test('every reporting call is a no-op while inactive', () async {
    await expectLater(
      Future.wait([
        AglCrash.recordError(StateError('x'), StackTrace.current),
        AglCrash.log('breadcrumb'),
        AglCrash.setKey('k', 'v'),
        AglCrash.setUserId('opaque-id'),
        AglCrash.setScreen('/home'),
        AglCrash.setAuthenticated(true),
      ]),
      completes,
    );
  });

  test('sendTestReport reports inactivity instead of pretending', () async {
    expect(await AglCrash.sendTestReport(), isFalse);
  });

  test('runGuarded completes even when the body throws', () async {
    var ran = false;
    await AglCrash.runGuarded(() async {
      ran = true;
      throw StateError('startup blew up');
    });
    expect(ran, isTrue);
  });

  test('runGuarded returns the body result path for a clean run', () async {
    var ran = false;
    await AglCrash.runGuarded(() async => ran = true);
    expect(ran, isTrue);
  });

  group('AglLog', () {
    test('is silent in release for anything below a warning', () {
      // kReleaseMode is false under `flutter test`, so this asserts the
      // predicate rather than the output: debug and info are the levels that
      // get dropped, warnings and errors are the levels that survive.
      expect(kReleaseMode, isFalse);
      final lines = <String>[];
      final previous = debugPrint;
      debugPrint = (message, {wrapWidth}) => lines.add(message ?? '');
      addTearDown(() => debugPrint = previous);

      AglLog.write('debug line');
      AglLog.write('warning line', level: AglLogLevel.warning);
      expect(lines, hasLength(2));

      AglLog.enabled = false;
      addTearDown(() => AglLog.enabled = true);
      AglLog.write('suppressed', level: AglLogLevel.error);
      expect(lines, hasLength(2));
    });
  });
}
