Uscis-Case M6: launch with Firebase config absent and the network off
Run 2026-10-14, 10:57-11:01 local, by software-developer (repair round).

Device: existing simulator "iPhone 17 Pro Max" C8780642-C06D-40DA-8E81-F6BFAC5F6CF7, iOS 26.4
(booted for this run, shut down afterwards; no simulator was created).
Toolchain: Flutter 3.44.2, Xcode_27.1.0_27A9275_fb.app.
Source: Uscis-Case main at 914e354 plus integration_test/offline_launch_test.dart
(committed afterwards as Uscis-Case b609749).

Why debug, not release: Flutter release (and profile) builds do not run on the iOS
simulator; release mode is device-only. A literal release launch on the simulator is
impossible, so both launches below are simulator debug builds. A physical-device run
stays a human step (spec M6).

1. Offline launch test (offline_launch_test.log, m6_01..m6_03)
   flutter build ios --simulator --debug -t integration_test/offline_launch_test.dart \
     --dart-define=EXPECT_NO_FIREBASE=true --dart-define=M6_HOLD_SECONDS=8
   rm Runner.app/GoogleService-Info.plist ; codesign --force --sign - --preserve-metadata=entitlements Runner.app
   (find Runner.app -name 'GoogleService-Info*' | wc -l  ->  0)
   simctl uninstall / install (fresh install), simctl launch, no flutter tool attached.
   The test boots the real main() with every dart:io HTTP connection refused
   (HttpOverrides: Supabase, Federal Register, anything on HttpClient), then adds a
   receipt and a conditional green card through the real UI.
   Key lines from the log:
     [m6] network probe refused: SocketException: Network is off (M6 offline launch test) (OS Error: Network is unreachable, errno = 51)
     [AGL:warning] Crash reporting inactive - Firebase did not initialise ([core/not-initialized] ...)
     [AGL:warning] Insights inactive - Firebase is not initialised. ...
     [m6] first frame with content after 1026ms
     [m6] AglCrash.isActive=false AglInsights.analyticsActive=false
     [m6] RESULT offline launch passed
     00:57 +2: All tests passed!
   Screens: m6_01_first_screen.png ("What's on your desk?"),
            m6_02_docket_with_data.png (Docket: "Now open" I-751 window for Ana, 52 days left),
            m6_03_case_offline.png (case page: "Needs a connection to federalregister.gov." + Retry).

2. The real app entry point without Firebase config (app_main_no_firebase.log, m6_04)
   flutter build ios --simulator --debug (lib/main.dart), plist removed and re-signed as above,
   fresh install, simctl launch. Log shows the same two "Firebase did not initialise" warnings and
   "Supabase init completed"; screenshot at +12 s shows the first screen; the process was still
   running (launchctl list: pid 40356). Network was NOT cut for this launch.

What "network off" did not cover (honest limits):
 - The simulator shares the Mac's network stack. Turning the Mac's network off would also cut off
   the agent doing the run, so native networking was not disabled. Native SDK traffic (Google
   Mobile Ads / UMP) still reached Google: the log shows the UMP reply "Failed to read publisher's
   account configuration", and m6_03 shows a Google test-mode banner (debug build).
 - Only Dart networking was cut, by HttpOverrides inside the test.
 - iOS 26.4, not iOS 27.0 (the crash device): the only existing iOS 27.0 iPhone simulator that is not
   in use by another session (FDF74304) has never been booted, and a first boot needs disk this
   Mac did not have to spare (about 2.5-4.5 GB free during the run).
