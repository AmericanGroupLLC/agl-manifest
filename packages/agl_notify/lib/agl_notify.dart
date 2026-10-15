/// Cancelling local notifications without freezing the app.
///
/// Why this exists (measured 2026-10-14/15, iOS 27.0 simulator, see
/// README.md): `UNUserNotificationCenter.removePendingNotificationRequests(
/// withIdentifiers:)` — what flutter_local_notifications' `cancel(id)` calls,
/// on the main thread, in 17.2.4, 22.3.2 and 23.0.0-dev.4 alike — waits for an
/// answer from SpringBoard's notification server. Until that server has
/// started (7.5 hours after a simulator boot on the build Mac) nothing answers,
/// and the app freezes: Verba never left its launch screen, FashionFactory
/// froze on "Save order". The look-ups (`pendingNotificationRequests`,
/// `getActiveNotifications`) answer through completion handlers, so they never
/// hold the main thread, and `cancelAll` returns at once.
///
/// [AglNotify.cancel] therefore asks first and only cancels ids that really
/// are pending or delivered. If the system does not answer within
/// [AglNotify.lookupTimeout], the cancel is not dropped: it runs the moment
/// the answer arrives, unless the app has scheduled that id again meanwhile.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';

/// What [AglNotify.cancel] did.
enum AglCancelOutcome {
  /// Nothing asked for was pending or delivered, so no cancel call was made.
  nothingToCancel,

  /// The ids that were pending or delivered were cancelled.
  cancelled,

  /// The system did not answer in time. The cancel runs as soon as it does.
  deferred,

  /// Not a guarded platform (Android): the plugin's cancel was called directly.
  direct,
}

/// One instance per plugin instance. Pass closures over the app's own
/// `FlutterLocalNotificationsPlugin`, whatever its version:
///
/// ```dart
/// final notify = AglNotify(
///   pendingIds: () async =>
///       [for (final r in await plugin.pendingNotificationRequests()) r.id],
///   deliveredIds: () async => [
///     for (final n in await plugin.getActiveNotifications())
///       if (n.id != null) n.id!,
///   ],
///   cancelId: (id) => plugin.cancel(id: id), // 17.x: plugin.cancel(id)
///   cancelEverything: plugin.cancelAll,
/// );
/// ```
class AglNotify {
  AglNotify({
    required Future<Iterable<int>> Function() pendingIds,
    required Future<Iterable<int>> Function() deliveredIds,
    required Future<void> Function(int id) cancelId,
    required Future<void> Function() cancelEverything,
    this.lookupTimeout = const Duration(seconds: 3),
    bool? guarded,
  })  : _pendingIds = pendingIds,
        _deliveredIds = deliveredIds,
        _cancelId = cancelId,
        _cancelEverything = cancelEverything,
        _guarded = guarded;

  final Future<Iterable<int>> Function() _pendingIds;
  final Future<Iterable<int>> Function() _deliveredIds;
  final Future<void> Function(int id) _cancelId;
  final Future<void> Function() _cancelEverything;
  final bool? _guarded;

  /// How long [cancel] waits for the system to list what is scheduled.
  final Duration lookupTimeout;

  /// Bumped by [noteScheduled]; a deferred cancel skips an id whose number
  /// moved after the cancel was asked for.
  final Map<int, int> _generation = {};

  /// Deferred cancels still waiting for the system, for tests and logs.
  int get deferredCount => _deferred;
  int _deferred = 0;

  /// The cancel-by-id call is only dangerous on Apple platforms.
  bool get guarded =>
      _guarded ??
      (!kIsWeb &&
          (defaultTargetPlatform == TargetPlatform.iOS ||
              defaultTargetPlatform == TargetPlatform.macOS));

  /// Call right before scheduling [id], so a cancel of the previous
  /// notification with that id that is still waiting for the system does not
  /// remove the new one.
  void noteScheduled(int id) {
    _generation[id] = (_generation[id] ?? 0) + 1;
  }

  /// Cancels every id in [ids] that is pending or delivered.
  ///
  /// Never throws: a platform error is reported through [debugPrint] and the
  /// cancel is retried once directly, because the system did answer.
  Future<AglCancelOutcome> cancel(Iterable<int> ids) async {
    final wanted = ids.toSet().toList();
    if (wanted.isEmpty) return AglCancelOutcome.nothingToCancel;
    if (!guarded) {
      for (final id in wanted) {
        await _safely(() => _cancelId(id), 'cancel $id');
      }
      return AglCancelOutcome.direct;
    }
    final asked = {for (final id in wanted) id: _generation[id] ?? 0};
    final lookup = _present();
    final List<int> present;
    try {
      present = await lookup.timeout(lookupTimeout);
    } on TimeoutException {
      _deferred++;
      unawaited(lookup.then((found) async {
        for (final id in idsToCancel(wanted: wanted, present: found)) {
          if ((_generation[id] ?? 0) != asked[id]) continue;
          await _safely(() => _cancelId(id), 'deferred cancel $id');
        }
      }, onError: (Object e) {
        debugPrint('[agl_notify] deferred look-up failed: $e');
      }).whenComplete(() => _deferred--));
      return AglCancelOutcome.deferred;
    } catch (e) {
      // The system answered, with an error: a cancel will not hang now.
      debugPrint('[agl_notify] look-up failed ($e); cancelling directly');
      for (final id in wanted) {
        await _safely(() => _cancelId(id), 'cancel $id');
      }
      return AglCancelOutcome.cancelled;
    }
    final targets = idsToCancel(wanted: wanted, present: present);
    if (targets.isEmpty) return AglCancelOutcome.nothingToCancel;
    for (final id in targets) {
      await _safely(() => _cancelId(id), 'cancel $id');
    }
    return AglCancelOutcome.cancelled;
  }

  /// Cancels everything. On iOS this is `removeAllPendingNotificationRequests`
  /// plus `removeAllDeliveredNotifications`, which do not wait for an answer
  /// (measured: 6 ms and 21 ms with the notification server down).
  Future<void> cancelAll() => _safely(_cancelEverything, 'cancelAll');

  Future<List<int>> _present() async {
    final both = await Future.wait([_pendingIds(), _deliveredIds()]);
    return [...both[0], ...both[1]];
  }

  Future<void> _safely(Future<void> Function() call, String what) async {
    try {
      await call();
    } catch (e) {
      debugPrint('[agl_notify] $what failed: $e');
    }
  }

  /// The ids from [wanted] that are in [present], in [wanted] order, once each.
  @visibleForTesting
  static List<int> idsToCancel({
    required Iterable<int> wanted,
    required Iterable<int> present,
  }) {
    final there = present.toSet();
    final seen = <int>{};
    return [
      for (final id in wanted)
        if (there.contains(id) && seen.add(id)) id,
    ];
  }
}
