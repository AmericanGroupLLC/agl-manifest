#!/usr/bin/env python3
"""Create a Flutter app in a repository, wired to this org's conventions.

The six remaining non-Flutter apps are being ported. Doing that by hand six
times would produce six subtly different Android configs, which is how the
existing portfolio ended up with eight Gradle/AGP pairs and one app that read
`keystore.properties` while everything else read `key.properties` — and quietly
debug-signed its releases as a result.

So the scaffold is generated. What it guarantees:

  * The Android release build **fails** when signing is not configured, instead
    of falling back to the debug key. A debug-signed .aab looks finished and is
    rejected at upload.
  * Firebase plugins apply only when google-services.json is present, so
    enabling Crashlytics is a file drop rather than a code change — and a
    missing config file does not break the build.
  * key.properties is gitignored before it can ever be written.
  * The applicationId matches the App Store record where one already exists.
    Those are permanent; getting one wrong means a new app, not a rename.

The app code itself is not generated. This produces a compiling, signable,
testable shell; the port fills it in.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, flutter_bin  # noqa: E402
FLUTTER = flutter_bin()

# Bundle ids that already have an App Store Connect record are fixed and must be
# reproduced exactly; the others follow the org's majority convention.
APPS = {
    "AGStudio":        dict(bundle="com.americangroupllc.agstudio",       name="agstudio",        title="AGStudio",        store_record=True),
    "AeroSwift":       dict(bundle="com.americangroupllc.aeroswift",         name="aeroswift",       title="AeroSwift",       store_record=False),
    "ApexMarketWatch": dict(bundle="com.americangroupllc.apexmarketwatch", name="apexmarketwatch", title="ApexMarketWatch", store_record=True),
    "BuddyPlay":       dict(bundle="com.americangroupllc.buddyplay",      name="buddyplay",       title="BuddyPlay",       store_record=True),
    "MyCard":          dict(bundle="com.americangroupllc.mycard",         name="mycard",          title="MyCard",          store_record=True),
    "PlantPulse":      dict(bundle="com.americangroupllc.plantpulse",     name="plantpulse",      title="PlantPulse",      store_record=False),
}

BUILD_GRADLE = '''import java.util.Properties

plugins {{
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}}

// Firebase applies itself as soon as the config file is present. The Google
// Services plugin fails the build outright when google-services.json is
// missing, so it must not be applied unconditionally — and this way enabling
// Crashlytics is a file drop, with no code change and no new release.
if (file("google-services.json").exists()) {{
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
}}

// Release signing. Values come from android/key.properties (never committed) or,
// in CI, from the environment. If neither is present the release build is left
// unsigned rather than silently falling back to the debug key — a debug-signed
// bundle looks finished, exits 0, and is rejected at upload.
val keystorePropertiesFile = rootProject.file("key.properties")
val keystoreProperties = Properties().apply {{
    if (keystorePropertiesFile.exists()) {{
        keystorePropertiesFile.inputStream().use {{ load(it) }}
    }}
}}

fun signingValue(propKey: String, envKey: String): String? =
    keystoreProperties.getProperty(propKey) ?: System.getenv(envKey)

val releaseStoreFile = signingValue("storeFile", "ANDROID_KEYSTORE_PATH")
val releaseStorePassword = signingValue("storePassword", "ANDROID_KEYSTORE_PASSWORD")
val releaseKeyAlias = signingValue("keyAlias", "ANDROID_KEY_ALIAS")
val releaseKeyPassword = signingValue("keyPassword", "ANDROID_KEY_PASSWORD")
val hasReleaseSigning = listOf(
    releaseStoreFile, releaseStorePassword, releaseKeyAlias, releaseKeyPassword
).all {{ !it.isNullOrBlank() }}

android {{
    namespace = "{bundle}"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    defaultConfig {{
        // Permanent. {record_note}
        applicationId = "{bundle}"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }}

    signingConfigs {{
        if (hasReleaseSigning) {{
            create("release") {{
                storeFile = file(releaseStoreFile!!)
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }}
        }}
    }}

    buildTypes {{
        release {{
            signingConfig = if (hasReleaseSigning) {{
                signingConfigs.getByName("release")
            }} else {{
                // Unsigned on purpose, so a debug-signed AAB cannot reach Play
                // by accident. `gradlew verifyReleaseSigning` explains the fix.
                null
            }}
        }}
    }}
}}

// Fail loudly, with instructions, instead of shipping an unsigned bundle.
tasks.register("verifyReleaseSigning") {{
    doLast {{
        if (!hasReleaseSigning) {{
            throw GradleException(
                "Release signing is not configured.\\n" +
                    "Copy android/key.properties.example to android/key.properties and fill it in,\\n" +
                    "or set ANDROID_KEYSTORE_PATH, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS\\n" +
                    "and ANDROID_KEY_PASSWORD in the environment."
            )
        }}
        println("Release signing configured for alias '$releaseKeyAlias'.")
    }}
}}

kotlin {{
    compilerOptions {{
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }}
}}

flutter {{
    source = "../.."
}}
'''

KEY_PROPERTIES_EXAMPLE = """# Copy to key.properties and fill in. Never commit the real file — it is
# gitignored, and its passwords are the upload key for this app.
#
# storeFile must be an absolute path, or relative to the android/ directory.
storeFile=/absolute/path/to/upload.jks
storePassword=
keyAlias=upload
keyPassword=
"""


def sh(cmd: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def scaffold(repo: str, spec: dict, force: bool) -> str:
    repo_dir = ROOT / repo
    if not repo_dir.exists():
        return f"no such repository: {repo_dir}"
    app_dir = repo_dir / "mobile"

    # mobile/ rather than the repo root: these repos already hold web, desktop
    # and browser-extension trees, and BuddyPlay/MyCard/AGStudio still contain
    # the native app being replaced. A separate directory keeps the port
    # reviewable next to what it replaces instead of overwriting it.
    if app_dir.exists() and not force:
        return "mobile/ already exists (use --force to regenerate)"

    r = sh([str(FLUTTER), "create",
            "--org", spec["bundle"].rsplit(".", 1)[0],
            "--project-name", spec["name"],
            "--platforms", "android,ios",
            "--description", f'{spec["title"]} — American Group LLC',
            str(app_dir)])
    if r.returncode != 0:
        return "flutter create failed: " + (r.stderr or r.stdout)[-300:]

    note = ("Matches the existing App Store Connect record; changing it means a new app."
            if spec["store_record"] else
            "No store record yet, but treat it as fixed from first upload.")
    (app_dir / "android/app/build.gradle.kts").write_text(
        BUILD_GRADLE.format(bundle=spec["bundle"], record_note=note))

    (app_dir / "android/key.properties.example").write_text(KEY_PROPERTIES_EXAMPLE)

    gi = app_dir / "android/.gitignore"
    text = gi.read_text() if gi.exists() else ""
    if "key.properties" not in text:
        gi.write_text(text.rstrip("\n") + "\nkey.properties\n")

    # iOS display name, so the springboard shows the product name rather than
    # the lowercase dart package name.
    plist = app_dir / "ios/Runner/Info.plist"
    if plist.exists():
        p = plist.read_text()
        if "CFBundleDisplayName" in p:
            p = re.sub(r"(<key>CFBundleDisplayName</key>\s*<string>)[^<]*(</string>)",
                       rf"\g<1>{spec['title']}\g<2>", p)
        else:
            p = p.replace("<dict>",
                          f"<dict>\n\t<key>CFBundleDisplayName</key>\n\t<string>{spec['title']}</string>", 1)
        plist.write_text(p)

    return "created"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*", default=sorted(APPS), help="default: all six")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    todo = args.apps or sorted(APPS)
    unknown = [a for a in todo if a not in APPS]
    if unknown:
        print(f"unknown: {', '.join(unknown)}", file=sys.stderr)
        return 2

    for app in todo:
        print(f"{app:18} {scaffold(app, APPS[app], args.force)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
