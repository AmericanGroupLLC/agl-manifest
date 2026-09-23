/// Shared crash reporting and free-tier telemetry for the American Group LLC
/// portfolio.
///
/// The portfolio is spread over **three** Firebase projects, not one, because
/// a project caps how many apps it will hold: `americangroupllc-5bdfc` (15
/// apps), `americangroupllc-agl2` (15) and `americangroupllc-agl3` (13).
/// Nothing here names a project — each app is bound to its own by the
/// `google-services.json` / `GoogleService-Info.plist` it ships.
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
export 'src/insights.dart' show AglInsights;
export 'src/telemetry.dart' show AglLog, AglLogLevel;
