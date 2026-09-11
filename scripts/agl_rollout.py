#!/usr/bin/env python3
"""Apply the AGL production pack to the mobile repos.

Idempotent: every step checks for its own marker first, so re-running is safe
and a partially-applied repo is completed rather than corrupted. Nothing is
committed — inspect, verify with the Flutter SDK, then commit.

    python3 scripts/agl_rollout.py --steps crashlytics --only daily-pulse
    python3 scripts/agl_rollout.py --steps crashlytics,fastlane_symbols --all
    python3 scripts/agl_rollout.py --list

Steps
  crashlytics      agl_observability dependency, guarded main(), Gradle plugins
                   that apply themselves once google-services.json exists
  fastlane_symbols dSYM upload to Crashlytics, mapping upload to Play
  privacy_manifest ios/Runner/PrivacyInfo.xcprivacy for the required-reason APIs
  signing          release signingConfig reading android/key.properties
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

BACKEND = pathlib.Path(__file__).resolve().parent.parent
AUDIT = BACKEND / "docs" / "release-readiness.json"

GIT_DEP = """  agl_observability:
    git:
      url: https://github.com/AmericanGroupLLC/agl-manifest.git
      path: packages/agl_observability
      ref: master
"""

# Applied after the plugins block. Conditional on purpose: the Google Services
# plugin fails the build outright when google-services.json is absent, so an
# unconditional `plugins { id(...) }` would break every app that does not have
# its Firebase config yet — which today is all of them. Written this way, the
# only step left for whoever has console access is to drop the file in.
GRADLE_KTS_APPLY = """
// Firebase applies itself as soon as the config file is present. The Google
// Services plugin fails the build outright when google-services.json is
// missing, so it must not be applied unconditionally — and this way enabling
// Crashlytics is a file drop, with no code change and no new release.
// The Crashlytics plugin uploads the R8 mapping file for every release build,
// which is what makes an obfuscated stack trace readable in the console.
if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
}
"""

GRADLE_GROOVY_APPLY = """
// Firebase applies itself as soon as the config file is present. See the note
// in the Kotlin-DSL apps: applying these without google-services.json fails
// the build, so enabling Crashlytics stays a file drop.
if (file("google-services.json").exists()) {
    apply plugin: 'com.google.gms.google-services'
    apply plugin: 'com.google.firebase.crashlytics'
}
"""

SETTINGS_PLUGINS = """    id("com.google.gms.google-services") version "4.4.2" apply false
    id("com.google.firebase.crashlytics") version "3.0.2" apply false
"""

PRIVACY_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<!--
  Required-reason API declarations. Apple rejects a submission that uses one of
  these APIs without a reason code, and several are reached through Flutter
  itself rather than through anything this app wrote:

    CA92.1  UserDefaults          — shared_preferences, and Flutter's own state
    35F9.1  file timestamp        — the Dart VM and any caching plugin
    C617.1  disk space            — image and HTTP caches
    3B52.1  system boot time      — used for monotonic timing

  Add an NSPrivacyCollectedDataTypes entry for anything the app actually sends
  off the device; an empty array is a claim that it sends nothing.
-->
<plist version="1.0">
<dict>
	<key>NSPrivacyTracking</key>
	<false/>
	<key>NSPrivacyTrackingDomains</key>
	<array/>
	<key>NSPrivacyCollectedDataTypes</key>
	<array/>
	<key>NSPrivacyAccessedAPITypes</key>
	<array>
		<dict>
			<key>NSPrivacyAccessedAPIType</key>
			<string>NSPrivacyAccessedAPICategoryUserDefaults</string>
			<key>NSPrivacyAccessedAPITypeReasons</key>
			<array>
				<string>CA92.1</string>
			</array>
		</dict>
		<dict>
			<key>NSPrivacyAccessedAPIType</key>
			<string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
			<key>NSPrivacyAccessedAPITypeReasons</key>
			<array>
				<string>C617.1</string>
			</array>
		</dict>
		<dict>
			<key>NSPrivacyAccessedAPIType</key>
			<string>NSPrivacyAccessedAPICategoryDiskSpace</string>
			<key>NSPrivacyAccessedAPITypeReasons</key>
			<array>
				<string>E174.1</string>
			</array>
		</dict>
		<dict>
			<key>NSPrivacyAccessedAPIType</key>
			<string>NSPrivacyAccessedAPICategorySystemBootTime</string>
			<key>NSPrivacyAccessedAPITypeReasons</key>
			<array>
				<string>35F9.1</string>
			</array>
		</dict>
	</array>
</dict>
</plist>
"""

DSYM_LANE = '''
  desc "Upload iOS dSYMs to Crashlytics so release crashes are readable"
  lane :upload_dsyms do |options|
    plist = File.expand_path("../ios/Runner/GoogleService-Info.plist", __dir__)
    unless File.exist?(plist)
      UI.important("No GoogleService-Info.plist — skipping dSYM upload.")
      next
    end

    # An .ipa built locally carries its dSYMs; a TestFlight build has them
    # regenerated by Apple's bitcode-free recompile, so fetch those instead
    # when a build has already been processed.
    path = options[:dsym_path]
    if path.nil?
      archive = Dir[File.expand_path("../build/ios/archive/*.xcarchive", __dir__)].max_by { |f| File.mtime(f) }
      path = File.join(archive, "dSYMs") if archive
    end

    if path.nil? || !File.exist?(path)
      UI.important("No dSYMs found at #{path.inspect} — nothing to upload.")
      next
    end

    upload_symbols_to_crashlytics(
      dsym_path: path,
      gsp_path: plist,
      # The binary ships inside the Crashlytics pod once Firebase is installed.
      binary_path: Dir[File.expand_path("../ios/Pods/FirebaseCrashlytics/upload-symbols", __dir__)].first
    )
  end
'''


def read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Result:
    def __init__(self, repo: str):
        self.repo = repo
        self.done: list[str] = []
        self.skipped: list[str] = []
        self.manual: list[str] = []

    def __str__(self) -> str:
        bits = []
        if self.done:
            bits.append("applied " + ", ".join(self.done))
        if self.skipped:
            bits.append("already " + ", ".join(self.skipped))
        if self.manual:
            bits.append("MANUAL " + "; ".join(self.manual))
        return f"{self.repo:22} {' | '.join(bits) or 'nothing to do'}"


# ── crashlytics ────────────────────────────────────────────────────────────


def step_crashlytics(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    pubspec_path = app / "pubspec.yaml"
    pubspec = read(pubspec_path)
    if "agl_observability" in pubspec:
        r.skipped.append("dep")
    else:
        # Straight after `dependencies:`. Anchoring on the flutter SDK entry
        # instead looks tidier but breaks on the five shell apps, which carry a
        # comment between `flutter:` and its `sdk:` line.
        anchor = re.search(r"(?m)^dependencies:\n", pubspec)
        if not anchor:
            r.manual.append("pubspec: no `dependencies:` block")
        else:
            at = anchor.end()
            pubspec = pubspec[:at] + GIT_DEP + pubspec[at:]
            write(pubspec_path, pubspec)
            r.done.append("dep")

    main_path = app / "lib" / "main.dart"
    main = read(main_path)
    if "AglCrash" in main:
        r.skipped.append("main")
    elif "WidgetsFlutterBinding.ensureInitialized();" not in main:
        # An expression-bodied `void main() => runApp(...)` has nowhere to
        # await from. Give it a body; the binding has to be initialised before
        # any plugin call anyway.
        shorthand = re.search(
            r"(?m)^void main\(\) => runApp\((?P<arg>[^;]+)\);$", main
        )
        if not shorthand:
            r.manual.append("main.dart: no ensureInitialized() anchor")
        else:
            main = (
                main[: shorthand.start()]
                + "Future<void> main() async {\n"
                + "  WidgetsFlutterBinding.ensureInitialized();\n"
                + f"  runApp({shorthand.group('arg')});\n"
                + "}"
                + main[shorthand.end() :]
            )
            write(main_path, main)
            # Re-enter with the anchor now present.
            step_crashlytics(app, repo, r)
            return
    else:
        if "import 'package:agl_observability/agl_observability.dart';" not in main:
            # After the last dart: import, before the first package: one —
            # `directives_ordering` fails the analyzer otherwise.
            dart_imports = list(re.finditer(r"(?m)^import 'dart:[^']+';\n", main))
            if dart_imports:
                at = dart_imports[-1].end()
                prefix = "\n"
            else:
                first_import = re.search(r"(?m)^import ", main)
                at = first_import.start() if first_import else 0
                prefix = ""
            main = (
                main[:at]
                + prefix
                + "import 'package:agl_observability/agl_observability.dart';\n"
                + main[at:]
            )

        wiring = (
            "WidgetsFlutterBinding.ensureInitialized();\n"
            "  // Crash reporting, before anything that could fail. Inactive and\n"
            "  // harmless until the Firebase config files are added.\n"
            f"  await AglCrash.init(appName: '{repo.name}');"
        )
        if "ErrorReporter.install()" in main:
            # This app already funnels errors through its own ErrorReporter,
            # whose sink is a documented no-op. Point that sink at Crashlytics
            # rather than installing a second set of framework handlers.
            wiring += (
                "\n  ErrorReporter.sink = (error, stack, {context}) =>\n"
                "      AglCrash.recordError(error, stack, reason: context);"
            )
        main = main.replace(
            "WidgetsFlutterBinding.ensureInitialized();", wiring, 1
        )
        # The init is awaited, so whichever function holds the anchor has to be
        # async. Six apps declared a plain `void main() {`.
        if re.search(r"(?m)^void main\(\) \{", main) and "await AglCrash" in main:
            head = main[: main.index("await AglCrash")]
            if re.search(r"(?ms)^void main\(\) \{(?!.*\basync\b).*", head):
                main = re.sub(
                    r"(?m)^void main\(\) \{", "Future<void> main() async {", main, count=1
                )
        write(main_path, main)
        r.done.append("main")


    _gradle_firebase(app, r)


def _gradle_firebase(app: pathlib.Path, r: Result) -> None:
    android = app / "android"
    app_kts = android / "app" / "build.gradle.kts"
    app_groovy = android / "app" / "build.gradle"
    settings_kts = android / "settings.gradle.kts"
    settings_groovy = android / "settings.gradle"

    if app_kts.exists():
        text = read(app_kts)
        if "com.google.gms.google-services" in text:
            r.skipped.append("gradle")
        else:
            plugins = re.search(r"(?ms)^plugins\s*\{.*?^\}\n", text)
            if not plugins:
                r.manual.append("build.gradle.kts: no plugins block")
            else:
                text = text[: plugins.end()] + GRADLE_KTS_APPLY + text[plugins.end() :]
                write(app_kts, text)
                r.done.append("gradle")
        _settings_plugins(settings_kts, r, kts=True)
    elif app_groovy.exists():
        text = read(app_groovy)
        if "com.google.gms.google-services" in text:
            r.skipped.append("gradle")
        else:
            write(app_groovy, text.rstrip() + "\n" + GRADLE_GROOVY_APPLY)
            r.done.append("gradle")
        _settings_plugins(settings_groovy, r, kts=False)
    else:
        r.manual.append("no android/app/build.gradle[.kts]")


def _settings_plugins(settings: pathlib.Path, r: Result, *, kts: bool) -> None:
    text = read(settings)
    if not text:
        r.manual.append(f"missing {settings.name}")
        return
    if "com.google.gms.google-services" in text:
        return
    block = re.search(r"(?ms)^plugins\s*\{\n(.*?)^\}", text)
    if not block:
        r.manual.append(f"{settings.name}: no plugins block for the classpath")
        return
    lines = SETTINGS_PLUGINS if kts else SETTINGS_PLUGINS.replace('id("', "id '").replace(
        '") version "', "' version '"
    ).replace('" apply false', "' apply false")
    # Appended, not prepended: dev.flutter.flutter-plugin-loader has to stay
    # the first entry, since it is what puts the Flutter tooling on the path.
    at = block.end(1)
    write(settings, text[:at] + lines + text[at:])
    r.done.append("settings")


# ── fastlane ───────────────────────────────────────────────────────────────


def step_fastlane_symbols(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    # The app directory first. Four repos carry a second, stale Fastfile at the
    # repo root; the lanes shell out with `cd ..` relative to the fastlane
    # directory, so only the one beside pubspec.yaml can actually build.
    for base in (app, repo):
        fastfile = base / "fastlane" / "Fastfile"
        if fastfile.exists():
            break
    else:
        r.manual.append("no fastlane/Fastfile")
        return
    if base is app and (repo / "fastlane" / "Fastfile").exists() and repo != app:
        r.manual.append(
            "a second Fastfile at the repo root shadows this one when fastlane "
            "is run from there — delete it"
        )

    text = read(fastfile)
    changed = False

    if "upload_symbols_to_crashlytics" in text:
        r.skipped.append("dsym")
    else:
        # Insert the lane at the end of the iOS platform block.
        ios = re.search(r"(?ms)^platform :ios do\n.*?^end\n", text)
        if not ios:
            r.manual.append("Fastfile: no `platform :ios` block")
        else:
            end = ios.end() - len("end\n")
            text = text[:end] + DSYM_LANE + text[end:]
            changed = True
            r.done.append("dsym")

    # Call it from the iOS build lane, which beta and release both go through.
    # The dSYMs exist from that point on: `flutter build ipa` leaves them in
    # build/ios/archive/Runner.xcarchive.
    if not re.search(r"(?m)^\s+upload_dsyms\s*$", text):
        # Some apps build a flavour: `build ipa --release --flavor prod`.
        new_text, count = re.subn(
            r'(\n\s+flutter_sh\("build ipa --release[^"]*"\)\n)',
            r"\1    upload_dsyms\n",
            text,
        )
        if count:
            text = new_text
            changed = True
            r.done.append("dsym-call")
        else:
            r.manual.append("Fastfile: no ios build lane to call upload_dsyms from")

    if "mapping_paths" in text:
        r.skipped.append("mapping")
    else:
        # supply accepts the R8 mapping alongside the AAB; without it a Play
        # pre-launch crash report is unreadable.
        mapping = (
            '      mapping_paths: Dir[File.expand_path("../build/app/outputs/mapping/release/mapping.txt", __dir__)],\n'
        )
        new_text, count = re.subn(
            r"(\n\s+aab: AAB_PATH,\n)", r"\1" + mapping, text
        )
        if count:
            text = new_text
            changed = True
            r.done.append("mapping")
        else:
            r.manual.append("Fastfile: no `aab: AAB_PATH` to attach a mapping to")

    if changed:
        write(fastfile, text)


# ── privacy manifest ───────────────────────────────────────────────────────


def step_privacy_manifest(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    target = app / "ios" / "Runner" / "PrivacyInfo.xcprivacy"
    if target.exists():
        r.skipped.append("privacy")
        return
    if not (app / "ios" / "Runner").is_dir():
        r.manual.append("no ios/Runner")
        return
    write(target, PRIVACY_MANIFEST)
    r.done.append("privacy")
    pbxproj = app / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    if "PrivacyInfo.xcprivacy" not in read(pbxproj):
        r.manual.append(
            "PrivacyInfo.xcprivacy written but not in the Xcode project — "
            "add it to Runner's Copy Bundle Resources"
        )



CI_TEMPLATE = """name: CI — {name}

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

env:
  FLUTTER_VERSION: '{flutter}'

jobs:
  analyze-and-test:
    name: Analyze and test
    runs-on: ubuntu-latest
{defaults}    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{{{ env.FLUTTER_VERSION }}}}
          channel: stable
          cache: true

      # Always before analyze: without it a healthy app emits bogus
      # "Method not found" errors from a stale package_config.json.
      - name: Resolve dependencies
        run: flutter pub get

      - name: Analyze
        run: flutter analyze

      - name: Test
        run: flutter test --reporter expanded

  build-android:
    name: Build Android release bundle
    runs-on: ubuntu-latest
    needs: analyze-and-test
{defaults}    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{{{ env.FLUTTER_VERSION }}}}
          channel: stable
          cache: true

      - run: flutter pub get

      # Unsigned unless key.properties is present, which it is not in CI. The
      # bundle proves the release build compiles and that R8 does not strip
      # something it needs; it is not uploadable.
      - name: Build appbundle
        run: flutter build appbundle --release

      - uses: actions/upload-artifact@v4
        with:
          name: {slug}-appbundle
          path: {path_prefix}build/app/outputs/bundle/release/*.aab
          retention-days: 14
          if-no-files-found: error

  build-ios:
    name: Build iOS (no codesign)
    runs-on: macos-latest
    needs: analyze-and-test
{defaults}    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{{{ env.FLUTTER_VERSION }}}}
          channel: stable
          cache: true

      - run: flutter pub get

      # --no-codesign: signing needs the Apple certificates, which CI does not
      # hold. This still catches a broken Xcode project or Info.plist.
      - name: Build iOS
        run: flutter build ios --release --no-codesign
"""

RELEASE_TEMPLATE = """name: Release — {name}

# Manual delivery through Fastlane. Every credential is a repository secret;
# the lanes fail loudly when one is missing. The `release` lane runs in the
# `production` GitHub environment, so it waits for a reviewer if that
# environment has required reviewers configured — which is the approval gate
# before anything reaches a public store listing.
on:
  workflow_dispatch:
    inputs:
      platform:
        description: Platform to deliver
        required: true
        default: android
        type: choice
        options: [android, ios]
      lane:
        description: beta (TestFlight / Play internal), release (store draft), metadata (listing only)
        required: true
        default: beta
        type: choice
        options: [beta, release, metadata]

jobs:
  deliver:
    runs-on: ${{{{ inputs.platform == 'ios' && 'macos-latest' || 'ubuntu-latest' }}}}
    environment: ${{{{ inputs.lane == 'release' && 'production' || '' }}}}
{defaults}    steps:
      - uses: actions/checkout@v4

      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: "3.2"
          bundler-cache: true
          working-directory: {bundler_dir}

      - uses: subosito/flutter-action@v2
        with:
          channel: stable
          cache: true

      - run: flutter pub get

      - name: Decode Android upload keystore
        if: inputs.platform == 'android'
        run: echo "${{{{ secrets.ANDROID_KEYSTORE_BASE64 }}}}" | base64 -d > "$RUNNER_TEMP/upload.jks"

      - name: Write Play service account
        if: inputs.platform == 'android'
        run: echo '${{{{ secrets.PLAY_SERVICE_ACCOUNT_JSON }}}}' > "$RUNNER_TEMP/play.json"

      - name: Fastlane ${{{{ inputs.platform }}}} ${{{{ inputs.lane }}}}
        env:
          # iOS — App Store Connect API key
          ASC_KEY_ID: ${{{{ secrets.ASC_KEY_ID }}}}
          ASC_ISSUER_ID: ${{{{ secrets.ASC_ISSUER_ID }}}}
          ASC_KEY_CONTENT: ${{{{ secrets.ASC_KEY_CONTENT }}}}
          # iOS — match (optional; Xcode automatic signing is used when unset)
          MATCH_GIT_URL: ${{{{ secrets.MATCH_GIT_URL }}}}
          MATCH_PASSWORD: ${{{{ secrets.MATCH_PASSWORD }}}}
          MATCH_GIT_BASIC_AUTHORIZATION: ${{{{ secrets.MATCH_GIT_BASIC_AUTHORIZATION }}}}
          # Android
          PLAY_JSON_KEY_FILE: ${{{{ runner.temp }}}}/play.json
          ANDROID_KEYSTORE_PATH: ${{{{ runner.temp }}}}/upload.jks
          ANDROID_KEYSTORE_PASSWORD: ${{{{ secrets.ANDROID_KEYSTORE_PASSWORD }}}}
          ANDROID_KEY_ALIAS: ${{{{ secrets.ANDROID_KEY_ALIAS }}}}
          ANDROID_KEY_PASSWORD: ${{{{ secrets.ANDROID_KEY_PASSWORD }}}}
        run: bundle exec fastlane ${{{{ inputs.platform }}}} ${{{{ inputs.lane }}}}

      # Kept for 90 days so a crash reported weeks after a release can still be
      # symbolicated by hand if the automatic upload failed.
      - uses: actions/upload-artifact@v4
        if: always() && inputs.platform == 'android'
        with:
          name: {slug}-mapping
          path: {path_prefix}build/app/outputs/mapping/release/mapping.txt
          retention-days: 90
          if-no-files-found: ignore
"""

LEGACY_MARKERS = ("eas ", "eas-", "expo", "jest", "yarn ", "npm ci")


def step_workflows(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    rel = "" if app == repo else f"{app.relative_to(repo)}/"
    defaults = "" if not rel else (
        "    defaults:\n      run:\n        working-directory: "
        f"{rel.rstrip('/')}\n"
    )
    slug = repo.name.lower().replace(" ", "-")
    fields = dict(
        name=repo.name,
        flutter="3.44.2",
        defaults=defaults,
        slug=slug,
        path_prefix=rel,
        bundler_dir=rel.rstrip("/") or ".",
    )
    wf = repo / ".github" / "workflows"

    for filename, template in (("ci.yml", CI_TEMPLATE), ("release.yml", RELEASE_TEMPLATE)):
        path = wf / filename
        text = read(path)
        if not text:
            write(path, template.format(**fields))
            r.done.append(f"{filename}:new")
            continue

        lowered = text.lower()
        if "flutter" not in lowered and any(m in lowered for m in LEGACY_MARKERS):
            # An Expo/Jest workflow left over from before the port. It cannot
            # pass or fail meaningfully against a Flutter tree.
            write(path, template.format(**fields))
            r.done.append(f"{filename}:replaced-legacy")
            continue

        if rel and "working-directory" not in text:
            # Every job needs it: the Flutter project is not at the repo root,
            # so `flutter pub get` at the default working directory finds no
            # pubspec.yaml and the whole workflow fails on its first step.
            patched, count = re.subn(
                r"(?m)^(    runs-on: .*\n)",
                r"\1" + defaults.replace("\\n", "\n"),
                text,
            )
            # `defaults.run` covers `run:` steps only, not action inputs, so
            # ruby/setup-ruby still looks for the Gemfile at the repo root
            # unless it is told otherwise.
            patched = patched.replace(
                "          bundler-cache: true\n",
                "          bundler-cache: true\n"
                f"          working-directory: {rel.rstrip('/')}\n",
            )
            if count:
                write(path, patched)
                r.done.append(f"{filename}:working-dir")
            else:
                r.manual.append(f"{filename}: no runs-on to anchor working-directory to")
        else:
            r.skipped.append(filename)


GITIGNORE_BLOCK = """
# ── Signing and delivery secrets — never commit ──────────────────────────────
# An upload keystore in git is unrecoverable: the key is public from the moment
# it is pushed, and with Play App Signing off the listing can never be updated
# again. The Firebase config files are deliberately NOT here — Google documents
# them as non-secret, they ship inside the binary anyway, and CI needs them in
# the checkout for the Crashlytics Gradle plugin to apply and upload a mapping.
**/key.properties
*.jks
*.keystore
*.p8
*.p12
*.mobileprovision
*.cer
**/fastlane/play-service-account.json
**/fastlane/*.json.enc
env/*.json
!env/*.example.json
!env/example.json
"""


def step_gitignore(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    path = repo / ".gitignore"
    text = read(path)
    if "Signing and delivery secrets" in text:
        r.skipped.append("gitignore")
        return
    write(path, (text.rstrip() + "\n" if text else "") + GITIGNORE_BLOCK)
    r.done.append("gitignore")
    # A file already tracked is not un-tracked by .gitignore.
    tracked = subprocess.run(
        ["git", "-C", str(repo), "ls-files",
         "*.jks", "*.keystore", "*.p8", "*.p12", "*key.properties"],
        capture_output=True, text=True,
    ).stdout.split()
    if tracked:
        r.manual.append(
            "already tracked despite the ignore: " + ", ".join(tracked[:5])
        )


# firebase_core 4.x declares a minimum of iOS 15.0. Adding crash reporting to an
# app still targeting 13.0 or 14.0 does not fail at analyze or test — it fails
# at `pod install`, which is only reached on an iOS build:
#
#   Error: The plugin "firebase_core" requires a higher minimum iOS deployment
#   version than your application is targeting.
#
# iOS 15 shipped in 2021 and is below Apple's current floor for new submissions,
# so this costs no user that a store would still accept.
IOS_MIN = "15.0"


def step_ios_deployment_target(app: pathlib.Path, repo: pathlib.Path, r: Result) -> None:
    def too_low(value: str) -> bool:
        try:
            major, _, minor = value.partition(".")
            return (int(major), int(minor or 0)) < (15, 0)
        except ValueError:
            return False

    podfile = app / "ios" / "Podfile"
    if podfile.exists():
        text = read(podfile)
        original = text
        m = re.search(r"^platform :ios, '([\d.]+)'", text, re.M)
        if m and too_low(m.group(1)):
            text = text[: m.start()] + f"platform :ios, '{IOS_MIN}'" + text[m.end():]
        elif not m:
            # Flutter's template ships the line commented out.
            commented = re.search(r"(?m)^# platform :ios, '[\d.]+'\n", text)
            insert_at = commented.end() if commented else 0
            text = text[:insert_at] + f"platform :ios, '{IOS_MIN}'\n" + text[insert_at:]
        # A post_install hook that pins an older target overrides everything.
        text = re.sub(
            r"(IPHONEOS_DEPLOYMENT_TARGET'\] = ')(1[0-4](?:\.\d+)?)(')",
            lambda mm: mm.group(1) + IOS_MIN + mm.group(3),
            text,
        )
        if text != original:
            write(podfile, text)
            r.done.append("podfile-ios")
        else:
            r.skipped.append("podfile-ios")

    pbxproj = app / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    text = read(pbxproj)
    if text:
        new_text = re.sub(
            r"IPHONEOS_DEPLOYMENT_TARGET = (1[0-4](?:\.\d+)?);",
            f"IPHONEOS_DEPLOYMENT_TARGET = {IOS_MIN};",
            text,
        )
        if new_text != text:
            write(pbxproj, new_text)
            r.done.append("pbxproj-ios")
        else:
            r.skipped.append("pbxproj-ios")

STEPS = {
    "crashlytics": step_crashlytics,
    "fastlane_symbols": step_fastlane_symbols,
    "privacy_manifest": step_privacy_manifest,
    "workflows": step_workflows,
    "gitignore": step_gitignore,
    "ios_deployment_target": step_ios_deployment_target,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(pathlib.Path.home() / "agl"))
    parser.add_argument("--steps", default="crashlytics")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.root).expanduser()
    audit = json.loads(read(AUDIT) or "[]")
    apps = [a for a in audit if a.get("flutter")]

    if args.list:
        for a in apps:
            print(f"{a['repo']:22} {a['app_dir']}")
        return 0

    if args.only:
        apps = [a for a in apps if a["repo"] in args.only]
    elif not args.all:
        print("Pass --all or --only <repo>", file=sys.stderr)
        return 2

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        print(f"Unknown step(s): {unknown}. Known: {list(STEPS)}", file=sys.stderr)
        return 2

    for a in apps:
        repo = root / a["repo"]
        app = repo if a["app_dir"] == "." else repo / a["app_dir"]
        result = Result(a["repo"])
        for step in steps:
            STEPS[step](app, repo, result)
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
