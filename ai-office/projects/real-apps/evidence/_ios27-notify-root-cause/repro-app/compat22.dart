import 'package:flutter_local_notifications/flutter_local_notifications.dart';

const flnVersion = '22.3.2';
final _p = FlutterLocalNotificationsPlugin();
const _d = NotificationDetails(iOS: DarwinNotificationDetails());

Future<bool?> flnInit({required bool requestPermission}) => _p.initialize(
      settings: InitializationSettings(
        iOS: DarwinInitializationSettings(
          requestAlertPermission: requestPermission,
          requestBadgePermission: requestPermission,
          requestSoundPermission: requestPermission,
        ),
      ),
    );
Future<void> flnCancel(int id) => _p.cancel(id: id);
Future<void> flnCancelAll() => _p.cancelAll();
Future<void> flnSchedule(int id) => _p.periodicallyShow(
    id: id,
    title: 'Repro',
    body: 'periodic',
    repeatInterval: RepeatInterval.daily,
    notificationDetails: _d,
    androidScheduleMode: AndroidScheduleMode.inexact);
Future<void> flnShow(int id) =>
    _p.show(id: id, title: 'Repro', body: 'shown', notificationDetails: _d);
Future<List<int>> flnPending() async =>
    [for (final r in await _p.pendingNotificationRequests()) r.id];
Future<List<int?>> flnActive() async =>
    [for (final n in await _p.getActiveNotifications()) n.id];
