#!/usr/bin/env python3
"""Measure store-release readiness across every AGL mobile repo.

Counts real signals in each repository — files that exist, plugins that are
applied, keys that are declared — and writes both a JSON record and a Markdown
report. Nothing here is inferred from a spreadsheet or from a previous run.

    python3 scripts/audit_release_readiness.py [--root ~/agl]

Outputs docs/release-readiness.json and docs/RELEASE_READINESS.md.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess

SKIP = {
    "AmericanGroupLLC-Backend",
    "AmericanGroupLLC.github.io",
    "www.safecodeg.com",
    ".github",
    # This repository. It holds the shared packages, so it looks like a Flutter
    # project to find_app_root — but it is the delivery engine, not an app.
    "agl-manifest",
}


def read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def find_app_root(repo: pathlib.Path) -> pathlib.Path | None:
    """The directory holding the Flutter app's pubspec.yaml.

    Most repos have it at the root; a few keep the app in a subdirectory
    (TripNest in mobile/, NexusTransferPay in flutter-mobile-app/).
    """
    if (repo / "pubspec.yaml").exists() and (repo / "lib").is_dir():
        return repo
    best = None
    for candidate in sorted(repo.glob("*/pubspec.yaml")) + sorted(
        repo.glob("*/*/pubspec.yaml")
    ):
        if "/.flutter-sdk/" in str(candidate) or "/build/" in str(candidate):
            continue
        app = candidate.parent
        if not (app / "lib").is_dir():
            continue
        score = len(list((app / "lib").rglob("*.dart")))
        if best is None or score > best[0]:
            best = (score, app)
    return best[1] if best else None


def gradle_files(app: pathlib.Path) -> tuple[str, str, str]:
    android = app / "android"
    app_gradle = ""
    # Groovy first: Gradle resolves build.gradle before build.gradle.kts,
    # so where both exist the Groovy file is the one that runs.
    for name in ("app/build.gradle", "app/build.gradle.kts"):
        if (android / name).exists():
            app_gradle = read(android / name)
            break
    root_gradle = ""
    for name in ("build.gradle.kts", "build.gradle", "settings.gradle.kts", "settings.gradle"):
        root_gradle += read(android / name)
    return app_gradle, root_gradle, read(android / "gradle.properties")


def first(pattern: str, text: str, group: int = 1) -> str | None:
    m = re.search(pattern, text)
    return m.group(group) if m else None


def count_dart_signal(app: pathlib.Path, pattern: re.Pattern) -> int:
    total = 0
    lib = app / "lib"
    if not lib.is_dir():
        return 0
    for dart in lib.rglob("*.dart"):
        if "/l10n/" in str(dart) and dart.name.startswith("app_localizations"):
            continue
        total += len(pattern.findall(read(dart)))
    return total


L10N_CALLSITE = re.compile(r"\bl10n\.|AppLocalizations\.of\(|AglL10n\.of\(")
# `tooltip:` counts: Flutter feeds an IconButton's tooltip straight into the
# semantics tree, so it is what a screen reader announces. Counting only
# Semantics() and semanticLabel understated how many controls are named.
SEMANTICS = re.compile(r"\bSemantics\(|semanticLabel:|tooltip:")


def audit_repo(repo: pathlib.Path) -> dict:
    app = find_app_root(repo)
    out: dict = {"repo": repo.name, "flutter": app is not None}
    if app is None:
        return out
    out["app_dir"] = str(app.relative_to(repo)) or "."

    pubspec = read(app / "pubspec.yaml")
    out["version"] = first(r"(?m)^version:\s*(\S+)", pubspec) or ""
    out["sdk_constraint"] = first(r"(?m)^\s+sdk:\s*['\"]?(\^?>?=?[\d. <>=]+)", pubspec) or ""
    for dep in (
        "firebase_core",
        "firebase_crashlytics",
        "google_mobile_ads",
        "flutter_localizations",
        "agl_i18n",
        "agl_observability",
        "agl_ads",
    ):
        out[f"dep_{dep}"] = bool(re.search(rf"^\s+{dep}\s*:", pubspec, re.M))

    # ── Crash reporting ────────────────────────────────────────────────────
    module = app / "lib" / "core" / "observability" / "crash_reporting.dart"
    main_dart = read(app / "lib" / "main.dart")
    out["crash_module"] = module.exists()
    out["crash_wired_in_main"] = (
        "AglCrash.init" in main_dart or "initCrashReporting" in main_dart
    )
    out["crash_guarded_zone"] = "guardedMain" in main_dart or "runZonedGuarded" in main_dart
    out["firebase_android_config"] = (app / "android" / "app" / "google-services.json").exists()
    out["firebase_ios_config"] = (app / "ios" / "Runner" / "GoogleService-Info.plist").exists()

    app_gradle, root_gradle, gradle_props = gradle_files(app)
    out["gradle_google_services"] = "com.google.gms.google-services" in app_gradle
    out["gradle_crashlytics"] = "com.google.firebase.crashlytics" in app_gradle
    out["application_id"] = first(r'applicationId\s*=?\s*["\']([\w.]+)["\']', app_gradle) or ""
    out["min_sdk"] = first(r"minSdk(?:Version)?\s*=?\s*(\d+|\w+)", app_gradle) or ""
    out["target_sdk"] = first(r"targetSdk(?:Version)?\s*=?\s*(\d+|\w+)", app_gradle) or ""
    out["compile_sdk"] = first(r"compileSdk(?:Version)?\s*=?\s*(\d+|\w+)", app_gradle) or ""
    # A release signing config exists if the build declares one that is not the
    # debug key. The name varies — "release" in most apps, "upload" in
    # VirtuBand — and the material may come from key.properties or from the
    # environment, so neither name nor source can be required.
    out["release_signing"] = bool(
        re.search(r'create\("(?!debug)\w+"\)', app_gradle)
        or re.search(
            r"(?ms)^\s+signingConfigs\s*\{.*?^\s+(?!debug\b)\w+\s*\{.*?keyAlias",
            app_gradle,
        )
    )
    # The failure that actually matters: a release build that always uses the
    # debug key, which Play rejects and which looks like a real build locally.
    release_block = re.search(
        r"(?ms)^\s+release\s*\{(.*?)^\s+\}", app_gradle
    )
    body = release_block.group(1) if release_block else ""
    out["debug_signing_in_release"] = (
        "signingConfig" in body
        and "debug" in body
        and not re.search(r"if\s*\(|\?", body)
    )
    out["minify"] = "isMinifyEnabled = true" in app_gradle or "minifyEnabled true" in app_gradle
    out["proguard_rules"] = (app / "android" / "app" / "proguard-rules.pro").exists()

    manifest = read(app / "android" / "app" / "src" / "main" / "AndroidManifest.xml")
    out["android_admob_id"] = first(
        r'com\.google\.android\.gms\.ads\.APPLICATION_ID"\s*\n?\s*android:value="([^"]+)"',
        manifest,
    ) or ""
    out["android_permissions"] = sorted(
        set(re.findall(r'uses-permission android:name="android\.permission\.([\w.]+)"', manifest))
    )
    out["android_backup_rules"] = "dataExtractionRules" in manifest or "fullBackupContent" in manifest

    # ── iOS ────────────────────────────────────────────────────────────────
    plist = read(app / "ios" / "Runner" / "Info.plist")
    # A comment can sit between the key and its value, and several apps put one
    # there explaining which AdMob app the id belongs to.
    out["ios_admob_id"] = first(
        r"(?s)<key>GADApplicationIdentifier</key>(?:\s|<!--.*?-->)*<string>([^<]*)</string>",
        plist,
    ) or ""
    out["ios_scene_manifest"] = "UIApplicationSceneManifest" in plist
    out["ios_bundle_display_name"] = first(
        r"<key>CFBundleDisplayName</key>\s*<string>([^<]*)</string>", plist
    ) or ""
    out["ios_usage_descriptions"] = sorted(re.findall(r"<key>(NS\w*UsageDescription)</key>", plist))
    out["ios_ats_arbitrary_loads"] = "NSAllowsArbitraryLoads" in plist
    out["ios_privacy_manifest"] = (app / "ios" / "Runner" / "PrivacyInfo.xcprivacy").exists()
    pbxproj = read(app / "ios" / "Runner.xcodeproj" / "project.pbxproj")
    targets = sorted(set(re.findall(r"IPHONEOS_DEPLOYMENT_TARGET = ([\d.]+);", pbxproj)))
    out["ios_deployment_targets"] = targets
    out["ios_bundle_id"] = first(r"PRODUCT_BUNDLE_IDENTIFIER = ([\w.\-]+);", pbxproj) or ""
    podfile = read(app / "ios" / "Podfile")
    out["ios_podfile_platform"] = first(r"platform :ios, '([\d.]+)'", podfile) or ""
    podfile_lock = read(app / "ios" / "Podfile.lock")
    out["ios_pods_installed"] = bool(podfile_lock)
    out["ios_pod_admob"] = "Google-Mobile-Ads-SDK" in podfile_lock
    out["ios_pod_crashlytics"] = "FirebaseCrashlytics" in podfile_lock

    # ── Delivery ───────────────────────────────────────────────────────────
    for name, rel in (
        ("fastlane_appfile", "fastlane/Appfile"),
        ("fastlane_fastfile", "fastlane/Fastfile"),
        ("gemfile", "Gemfile"),
        ("ci_workflow", ".github/workflows/ci.yml"),
        ("release_workflow", ".github/workflows/release.yml"),
    ):
        out[name] = (repo / rel).exists() or (app / rel).exists()
    # The app directory first: four repos keep a second, stale Fastfile at the
    # repo root, and only the one beside pubspec.yaml can actually build.
    fastfile = read(app / "fastlane" / "Fastfile") or read(repo / "fastlane" / "Fastfile")
    out["duplicate_fastfile"] = (
        app != repo
        and (app / "fastlane" / "Fastfile").exists()
        and (repo / "fastlane" / "Fastfile").exists()
    )
    out["fastlane_lanes"] = sorted(set(re.findall(r"^\s*lane :(\w+)", fastfile, re.M)))
    out["fastlane_uploads_dsym"] = "upload_symbols_to_crashlytics" in fastfile
    out["fastlane_uploads_mapping"] = "mapping" in fastfile
    out["store_metadata_dir"] = any(
        (base / "store").is_dir() or (base / "fastlane" / "metadata").is_dir()
        for base in (repo, app)
    )

    # ── i18n ───────────────────────────────────────────────────────────────
    arb = sorted(p.stem.replace("app_", "") for p in (app / "lib" / "l10n").glob("app_*.arb"))
    out["l10n_yaml"] = (app / "l10n.yaml").exists()
    out["arb_locales"] = arb
    out["l10n_callsites"] = count_dart_signal(app, L10N_CALLSITE)
    out["screens"] = len(list((app / "lib").rglob("*screen*.dart")))

    # ── Size and coverage ──────────────────────────────────────────────────
    dart_files = [p for p in (app / "lib").rglob("*.dart")]
    out["lib_files"] = len(dart_files)
    out["lib_loc"] = sum(len(read(p).splitlines()) for p in dart_files)
    out["test_files"] = len(list((app / "test").rglob("*_test.dart"))) if (app / "test").is_dir() else 0
    out["a11y_signals"] = count_dart_signal(app, SEMANTICS)
    out["secrets_in_dart"] = count_dart_signal(
        app, re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]")
    )
    out["print_calls"] = count_dart_signal(app, re.compile(r"(?<![\w.])print\("))

    # ── Capability matrix ──────────────────────────────────────────────────
    # What a store listing has to be able to claim, and what a tester needs to
    # know before opening the app.
    out["platform_android"] = (app / "android").is_dir()
    out["platform_ios"] = (app / "ios").is_dir()

    providers = []
    for dep, label in (
        ("supabase_flutter", "Supabase"),
        ("firebase_auth", "Firebase"),
        ("google_sign_in", "Google"),
        ("sign_in_with_apple", "Apple"),
        ("local_auth", "Biometric"),
    ):
        if re.search(rf"(?m)^\s+{dep}\s*:", pubspec):
            providers.append(label)
    out["auth_providers"] = providers
    # A sign-in screen the user can actually reach, as opposed to a dependency
    # that is declared and never wired up.
    out["has_login_screen"] = bool(
        list((app / "lib").rglob("*login*.dart"))
        or list((app / "lib").rglob("*sign_in*.dart"))
        or list((app / "lib").rglob("*auth*screen*.dart"))
    )
    # Several apps state in the UI that no account is needed; that is a product
    # decision, not a gap.
    out["account_optional"] = bool(
        re.search(r"(?i)continue as guest|no account needed|skip sign|guest mode",
                  "".join(read(p) for p in (app / "lib").rglob("*.dart")))
    )

    out["git_branch"] = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    return out


BLOCKERS = [
    ("release_signing", "no real release signing — a release build is debug-signed"),
    ("crash_wired_in_main", "crash reporting not initialised in main()"),
    ("fastlane_fastfile", "no Fastlane lanes"),
    ("release_workflow", "no release workflow"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(pathlib.Path.home() / "agl"))
    args = parser.parse_args()
    root = pathlib.Path(args.root).expanduser()

    rows = []
    for repo in sorted(root.iterdir()):
        if repo.name.startswith(".") or not repo.is_dir():
            continue
        if repo.name in SKIP or not (repo / ".git").exists():
            continue
        rows.append(audit_repo(repo))

    here = pathlib.Path(__file__).resolve().parent.parent / "docs"
    (here / "release-readiness.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    flutter = [r for r in rows if r.get("flutter")]
    lines = [
        "# Store-release readiness",
        "",
        f"Measured across {len(rows)} repositories "
        f"({len(flutter)} of them Flutter apps) by "
        "`scripts/audit_release_readiness.py`. Raw data: "
        "[`release-readiness.json`](release-readiness.json).",
        "",
        "## Portfolio totals",
        "",
        "| Signal | Apps with it | Apps without |",
        "| --- | ---: | ---: |",
    ]
    signals = [
        ("Release signing config", "release_signing"),
        ("Crashlytics wired in main()", "crash_wired_in_main"),
        ("firebase_crashlytics dependency", "dep_firebase_crashlytics"),
        ("google-services.json", "firebase_android_config"),
        ("GoogleService-Info.plist", "firebase_ios_config"),
        ("google_mobile_ads dependency", "dep_google_mobile_ads"),
        ("Android AdMob app id", "android_admob_id"),
        ("iOS AdMob app id", "ios_admob_id"),
        ("Fastlane Fastfile", "fastlane_fastfile"),
        ("Release workflow", "release_workflow"),
        ("CI workflow", "ci_workflow"),
        ("Store metadata", "store_metadata_dir"),
        ("l10n.yaml", "l10n_yaml"),
        ("iOS privacy manifest", "ios_privacy_manifest"),
    ]
    for label, key in signals:
        have = sum(1 for r in flutter if r.get(key))
        lines.append(f"| {label} | {have} | {len(flutter) - have} |")

    lines += ["", "## Per-app", "", "| App | ver | sign | crash | ads(A/i) | fastlane | CI | locales | l10n calls | tests |", "| --- | --- | :-: | :-: | :-: | :-: | :-: | ---: | ---: | ---: |"]
    tick = lambda b: "yes" if b else "—"
    for r in sorted(flutter, key=lambda r: r["repo"].lower()):
        lines.append(
            "| {repo} | {version} | {sign} | {crash} | {ads} | {fl} | {ci} | {loc} | {calls} | {tests} |".format(
                repo=r["repo"],
                version=r.get("version", ""),
                sign=tick(r.get("release_signing")),
                crash=tick(r.get("crash_wired_in_main")),
                ads="{}/{}".format(
                    "yes" if r.get("android_admob_id") else "—",
                    "yes" if r.get("ios_admob_id") else "—",
                ),
                fl=tick(r.get("fastlane_fastfile")),
                ci=tick(r.get("release_workflow")),
                loc=len(r.get("arb_locales", [])),
                calls=r.get("l10n_callsites", 0),
                tests=r.get("test_files", 0),
            )
        )

    lines += ["", "## Blocking gaps, by app", ""]
    for r in sorted(flutter, key=lambda r: r["repo"].lower()):
        missing = [msg for key, msg in BLOCKERS if not r.get(key)]
        if missing:
            lines.append(f"- **{r['repo']}** — " + "; ".join(missing))
    lines.append("")

    (here / "RELEASE_READINESS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(rows)} repos, {len(flutter)} Flutter apps → docs/RELEASE_READINESS.md")


if __name__ == "__main__":
    main()
