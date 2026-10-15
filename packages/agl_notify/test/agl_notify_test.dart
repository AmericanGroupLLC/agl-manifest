import 'dart:async';

import 'package:agl_notify/agl_notify.dart';
import 'package:flutter_test/flutter_test.dart';

/// A fake notification centre. [answer] null = the system never answers the
/// look-ups (iOS 27.0 simulator before SpringBoard's notification server is
/// up); a completer lets a test answer later.
class FakeCentre {
  FakeCentre({this.pending = const [], this.delivered = const []});
  List<int> pending;
  List<int> delivered;
  Completer<void>? gate;
  final cancelled = <int>[];
  int cancelAlls = 0;

  AglNotify notify({bool guarded = true}) => AglNotify(
        guarded: guarded,
        lookupTimeout: const Duration(milliseconds: 50),
        pendingIds: () async {
          if (gate != null) await gate!.future;
          return pending;
        },
        deliveredIds: () async {
          if (gate != null) await gate!.future;
          return delivered;
        },
        cancelId: (id) async => cancelled.add(id),
        cancelEverything: () async => cancelAlls++,
      );
}

void main() {
  test('a fresh install has nothing to cancel, so no cancel call is made',
      () async {
    final c = FakeCentre();
    expect(await c.notify().cancel([1001, 1002]),
        AglCancelOutcome.nothingToCancel);
    expect(c.cancelled, isEmpty);
  });

  test('only ids that are pending or delivered are cancelled, once each',
      () async {
    final c = FakeCentre(pending: [7, 2001], delivered: [1002, 2001]);
    expect(await c.notify().cancel([1001, 1002, 2001, 2001]),
        AglCancelOutcome.cancelled);
    expect(c.cancelled, [1002, 2001]);
  });

  test('a reminder for a deleted item still goes when the system answers late',
      () async {
    final c = FakeCentre(pending: [42])..gate = Completer<void>();
    final n = c.notify();
    expect(await n.cancel([42]), AglCancelOutcome.deferred);
    expect(c.cancelled, isEmpty, reason: 'no cancel before the answer');
    expect(n.deferredCount, 1);
    c.gate!.complete();
    await Future<void>.delayed(Duration.zero);
    await Future<void>.delayed(Duration.zero);
    expect(c.cancelled, [42]);
    expect(n.deferredCount, 0);
  });

  test('a deferred cancel does not remove a reminder scheduled again since',
      () async {
    final c = FakeCentre(pending: [42, 43])..gate = Completer<void>();
    final n = c.notify();
    expect(await n.cancel([42, 43]), AglCancelOutcome.deferred);
    n.noteScheduled(42);
    c.gate!.complete();
    await Future<void>.delayed(Duration.zero);
    await Future<void>.delayed(Duration.zero);
    expect(c.cancelled, [43]);
  });

  test('a look-up error means the system answered: cancel directly', () async {
    final n = AglNotify(
      guarded: true,
      pendingIds: () async => throw StateError('boom'),
      deliveredIds: () async => const [],
      cancelId: (id) async => cancelledIds.add(id),
      cancelEverything: () async {},
    );
    expect(await n.cancel([5]), AglCancelOutcome.cancelled);
    expect(cancelledIds, [5]);
  });

  test('unguarded platforms (Android) cancel directly', () async {
    final c = FakeCentre();
    expect(await c.notify(guarded: false).cancel([3, 3, 4]),
        AglCancelOutcome.direct);
    expect(c.cancelled, [3, 4]);
  });

  test('cancelAll goes straight through and never throws', () async {
    final c = FakeCentre();
    await c.notify().cancelAll();
    expect(c.cancelAlls, 1);
    final failing = AglNotify(
      pendingIds: () async => const [],
      deliveredIds: () async => const [],
      cancelId: (_) async {},
      cancelEverything: () async => throw StateError('no'),
    );
    await failing.cancelAll();
  });

  test('a cancel that throws is reported, not rethrown', () async {
    final n = AglNotify(
      guarded: true,
      pendingIds: () async => const [9],
      deliveredIds: () async => const [],
      cancelId: (_) async => throw StateError('platform'),
      cancelEverything: () async {},
    );
    expect(await n.cancel([9]), AglCancelOutcome.cancelled);
  });

  test('idsToCancel keeps wanted order and drops absent ids', () {
    expect(AglNotify.idsToCancel(wanted: [3, 1, 2, 3], present: [2, 3]),
        [3, 2]);
  });
}

final cancelledIds = <int>[];
