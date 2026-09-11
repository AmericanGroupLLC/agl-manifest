/// Shared crash reporting for the American Group LLC portfolio.
///
/// Firebase project **`americangroupllc-5bdfc`**.
///
/// ```dart
/// Future<void> main() async {
///   await AglCrash.runGuarded(() async {
///     WidgetsFlutterBinding.ensureInitialized();
///     await AglCrash.init(environment: AppEnv.name);
///     runApp(const MyApp());
///   });
/// }
/// ```
///
/// The one rule this package exists to enforce: **crash reporting must never
/// take an app down.** `Firebase.initializeApp()` throws `[core/no-app]` when
/// the config files are absent, and an app whose `main()` dies before
/// `runApp()` launches to a blank window. Every path here is guarded, and an
/// app with no Firebase config runs exactly as before, unreported.
library;

export 'src/crash.dart' show AglCrash;
export 'src/telemetry.dart' show AglLog, AglLogLevel;
