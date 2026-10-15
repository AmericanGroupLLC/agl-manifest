import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'compat.dart';

const _probe = MethodChannel('fln_probe');
final _log = ValueNotifier<List<String>>([]);

Future<void> log(String s) async {
  final line = '${DateTime.now().toIso8601String().substring(11, 23)} $s';
  // ignore: avoid_print
  print('FLNDART $line');
  _log.value = [..._log.value, s];
  await _probe.invokeMethod('log', s);
}

Future<void> runStep(String step) async {
  final sw = Stopwatch()..start();
  await log('STEP $step start');
  Object? r;
  if (step == 'init') {
    r = await flnInit(requestPermission: false);
  } else if (step == 'initperm') {
    r = await flnInit(requestPermission: true);
  } else if (step == 'cancel') {
    await flnCancel(1001);
  } else if (step == 'cancelAll') {
    await flnCancelAll();
  } else if (step == 'schedule') {
    await flnSchedule(1001);
  } else if (step == 'show') {
    await flnShow(1001);
  } else if (step == 'pending') {
    r = await flnPending();
  } else if (step == 'active') {
    r = await flnActive();
  } else if (step == 'wait') {
    await Future<void>.delayed(const Duration(seconds: 2));
  } else if (step.startsWith('n:') || step.startsWith('nb:')) {
    final bg = step.startsWith('nb:');
    final api = step.substring(bg ? 3 : 2);
    r = await _probe.invokeMethod('native', {'api': api, 'bg': bg});
  } else {
    r = 'unknown step';
  }
  await log('STEP $step done ${sw.elapsedMilliseconds}ms -> $r');
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ReproApp());
  WidgetsBinding.instance.addPostFrameCallback((_) async {
    final args = (await _probe.invokeListMethod<String>('args')) ?? [];
    final i = args.indexOf('-steps');
    final steps = i >= 0 && i + 1 < args.length ? args[i + 1].split(',') : <String>[];
    await log('plugin=$flnVersion steps=$steps');
    for (final s in steps) {
      try {
        await runStep(s);
      } catch (e) {
        await log('STEP $s threw $e');
      }
    }
    await log('ALL DONE');
  });
}

class ReproApp extends StatelessWidget {
  const ReproApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        home: Scaffold(
          appBar: AppBar(title: Text('FLN repro $flnVersion')),
          body: ValueListenableBuilder<List<String>>(
            valueListenable: _log,
            builder: (_, l, __) => ListView(
              padding: const EdgeInsets.all(8),
              children: [for (final s in l) Text(s, style: const TextStyle(fontSize: 13))],
            ),
          ),
        ),
      );
}
