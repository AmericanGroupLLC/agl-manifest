# agl_notify

Cancel local notifications without freezing the app on iOS 27.

## Why

flutter_local_notifications' `cancel(id)` calls
`UNUserNotificationCenter.removePendingNotificationRequests(withIdentifiers:)`
on the main thread (17.2.4, 22.3.2 and 23.0.0-dev.4 all do; no release changes
it). On iOS 27.0 that call waits for an answer from SpringBoard's notification
server, and on the simulator that server starts lazily — 7.5 hours after a boot
on the build Mac (2026-10-14 21:00 → 04:34). Until it is up nothing answers and
the app is frozen: Verba never left its launch screen, FashionFactory froze on
the first "Save order". Measured with a minimal app (`/tmp/agl-fln-repro`, see
the ai-office issue): the same direct call returned in 0 ms on the same
simulator once the server was up.

What still answers while the server is down:

| call | iOS 27.0, server not up |
| --- | --- |
| `removePendingNotificationRequests(withIdentifiers:)` (`cancel`) | blocks the calling thread |
| `getPendingNotificationRequests` / `getDeliveredNotifications` | no callback, but the main thread runs |
| `removeAllPending…` / `removeAllDelivered…` (`cancelAll`) | returns at once (6 ms / 21 ms) |
| `removeDeliveredNotifications(withIdentifiers:)` | returns at once (21 ms) |

## What it does

`AglNotify.cancel(ids)` lists what is pending and delivered first (callbacks,
never the main thread) and cancels only ids that are really there. A fresh
install — and any "Save" of a new item — therefore makes no cancel call at all.
If the list does not arrive within `lookupTimeout` (3 s), the cancel is not
dropped: it runs as soon as the list arrives, skipping any id the app has
scheduled again since (`noteScheduled`). On Android it calls the plugin directly.

Limit: a deferred cancel lives in memory. If the app is killed before the system
answers, that cancel is lost; the app's next cancel/reschedule pass covers it.

## Wiring

```yaml
dependencies:
  agl_notify:
    git:
      url: https://github.com/AmericanGroupLLC/agl-manifest.git
      path: packages/agl_notify
      ref: master
```

```dart
final notify = AglNotify(
  pendingIds: () async =>
      [for (final r in await plugin.pendingNotificationRequests()) r.id],
  deliveredIds: () async => [
    for (final n in await plugin.getActiveNotifications())
      if (n.id != null) n.id!,
  ],
  cancelId: (id) => plugin.cancel(id: id), // 17.x: (id) => plugin.cancel(id)
  cancelEverything: plugin.cancelAll,
);

notify.noteScheduled(id); // right before zonedSchedule(id …)
await notify.cancel([id]);
await notify.cancelAll();
```

`scripts/predelivery.py` fails an app that calls the plugin's `cancel(` or
`cancelAll(` anywhere but inside these closures.
