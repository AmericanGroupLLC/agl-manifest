import "dart:io";
import "package:args/args.dart";

void main(List<String> argv) {
  final parser = ArgParser()
    ..addCommand("doctor")
    ..addCommand("apps")
    ..addCommand("status")
    ..addCommand("test")
    ..addCommand("build")
    ..addCommand("beta")
    ..addCommand("release")
    ..addCommand("screenshots")
    ..addCommand("visual-test")
    ..addCommand("artifacts")
    ..addCommand("platform");

  ArgResults results;
  try {
    results = parser.parse(argv);
  } catch (e) {
    stderr.writeln(e);
    _printUsage(parser);
    exit(2);
  }

  final cmd = results.command?.name;
  if (cmd == null) {
    _printUsage(parser);
    return;
  }

  switch (cmd) {
    case "doctor":
      _doctor();
      return;
    case "apps":
      _runPython(
        "python3 scripts/resolve_matrix.py --spec all --platform validate --shards 1",
      );
      return;
    default:
      stdout.writeln(
        "Command '$cmd' is scaffolded. Next step is wiring to manifest + Fastlane orchestration.",
      );
  }
}

void _doctor() {
  const checks = ["python3", "bundle", "gh", "flutter", "dart"];
  var failed = false;
  for (final c in checks) {
    final ok = _exists(c);
    stdout.writeln("${ok ? '✓' : '✗'} $c");
    if (!ok) failed = true;
  }
  if (failed) exit(1);
}

bool _exists(String command) {
  final r = Process.runSync("bash", [
    "-lc",
    "command -v $command >/dev/null 2>&1",
  ]);
  return r.exitCode == 0;
}

void _runPython(String command) {
  final r = Process.runSync("bash", ["-lc", command], runInShell: true);
  stdout.write(r.stdout);
  stderr.write(r.stderr);
  exit(r.exitCode);
}

void _printUsage(ArgParser parser) {
  stdout.writeln("Usage: dart run tool/mobile.dart <command>");
  stdout.writeln("Commands:");
  for (final c in parser.commands.keys) {
    stdout.writeln("  $c");
  }
}
