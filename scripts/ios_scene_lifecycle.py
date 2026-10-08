#!/usr/bin/env python3
"""Adopt the UIScene lifecycle so the apps launch on iOS 27.

    python3 scripts/ios_scene_lifecycle.py --check          # report only
    python3 scripts/ios_scene_lifecycle.py --dry-run
    python3 scripts/ios_scene_lifecycle.py                  # every app
    python3 scripts/ios_scene_lifecycle.py daily-pulse

Found 2026-10-08 by launching daily-pulse on an iOS 27.1 simulator: it started,
then died with EXC_BREAKPOINT in

    UIKitCore  _UIApplicationEvaluateRuntimeIssueForNoSceneLifecycleAdoption

Apple announced at WWDC25 that the release after iOS 26 requires the UIScene
lifecycle. That release is out, and 21 of the 43 apps had no
UIApplicationSceneManifest — so every one of them crashes on launch for every
user on iOS 27, including App Review.

Two different states, two fixes:

  - 6 apps already had the modern AppDelegate (FlutterImplicitEngineDelegate)
    and their storyboards in the build; they lacked only the scene manifest.
  - 15 apps had stripped both storyboards out of the Runner target's
    Resources phase — a workaround for a time this machine could not run
    ibtool — and built their window by hand in didFinishLaunching. They also
    ship with no launch screen at all (UILaunchStoryboardName is empty),
    which iOS answers with legacy display handling and which iPad support
    requires. For these the storyboards go back into Resources, the plist
    names them again, and the AppDelegate becomes the standard Flutter
    3.44 shape. App-specific setup that is not window plumbing — Kinnav's
    Google Maps key — is kept.

The target is exactly what AeroSwift already ships and what launches on iOS
27.1: storyboard-backed FlutterViewController, `FlutterSceneDelegate` as the
scene delegate, plugins registered in didInitializeImplicitFlutterEngine.
FlutterSceneDelegate comes from Flutter.framework, so no Swift file is added
and the Xcode project gains only the two standard Resources entries.

A launch is the only proof. This edits; scripts/sim_install.py --ios on an
iOS 27 simulator is what verifies.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import plistlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

SCENE_MANIFEST = {
    "UIApplicationSupportsMultipleScenes": False,
    "UISceneConfigurations": {
        "UIWindowSceneSessionRoleApplication": [{
            "UISceneClassName": "UIWindowScene",
            "UISceneConfigurationName": "flutter",
            "UISceneDelegateClassName": "FlutterSceneDelegate",
            "UISceneStoryboardFile": "Main",
        }],
    },
}

# Flutter's template ids. Every one of these projects still carries the file
# references and variant groups under these ids; only the build-file entries
# and their place in the Resources phase were removed.
STORYBOARDS = [
    # (build-file id, file-ref id, name)
    ("97C146FC1CF9000F007C117D", "97C146FA1CF9000F007C117D", "Main.storyboard"),
    ("97C147011CF9000F007C117D", "97C146FF1CF9000F007C117D", "LaunchScreen.storyboard"),
]
RUNNER_RESOURCES = "97C146EC1CF9000F007C117D"

MODERN_APPDELEGATE = """import Flutter
import UIKit
{extra_imports}
@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {{
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {{
{extra_setup}    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }}

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {{
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
  }}
}}
"""

# Lines that belong to the hand-built window. Anything else inside
# didFinishLaunching is app-specific and is carried over.
WINDOW_PLUMBING = re.compile(
    r"FlutterEngine\(|flutterEngine\.run\(|GeneratedPluginRegistrant|"
    r"FlutterViewController\(|engine: flutterEngine|UIWindow\(|"
    r"rootViewController|makeKeyAndVisible|self\.window = |"
    r"return super\.application|^\s*//")


def app_dir(a) -> pathlib.Path:
    return ROOT / a["repo"] / (a.get("dir") or ".")


def fix_pbxproj(path: pathlib.Path, dry: bool) -> list[str]:
    s = path.read_text()
    done = []
    for bf, ref, name in STORYBOARDS:
        if f"{name} in Resources" in s:
            continue
        if f"{ref} /* {name} */ = {{" not in s:
            raise SystemExit(f"  {path}: no file reference {ref} for {name} — refusing")
        line = (f"\t\t{bf} /* {name} in Resources */ = {{isa = PBXBuildFile; "
                f"fileRef = {ref} /* {name} */; }};\n")
        anchor = "/* Begin PBXBuildFile section */\n"
        assert s.count(anchor) == 1
        s = s.replace(anchor, anchor + line)
        m = re.search(RUNNER_RESOURCES + r" /\* Resources \*/ = \{\s*isa = PBXResourcesBuildPhase;"
                      r"[^}]*?files = \(\n", s)
        if not m:
            raise SystemExit(f"  {path}: Runner Resources phase not found — refusing")
        s = s[:m.end()] + f"\t\t\t\t{bf} /* {name} in Resources */,\n" + s[m.end():]
        done.append(f"{name} back in Resources")
    if done and not dry:
        path.write_text(s)
    return done


SCENE_XML = """\t<key>UIApplicationSceneManifest</key>
\t<dict>
\t\t<key>UIApplicationSupportsMultipleScenes</key>
\t\t<false/>
\t\t<key>UISceneConfigurations</key>
\t\t<dict>
\t\t\t<key>UIWindowSceneSessionRoleApplication</key>
\t\t\t<array>
\t\t\t\t<dict>
\t\t\t\t\t<key>UISceneClassName</key>
\t\t\t\t\t<string>UIWindowScene</string>
\t\t\t\t\t<key>UISceneConfigurationName</key>
\t\t\t\t\t<string>flutter</string>
\t\t\t\t\t<key>UISceneDelegateClassName</key>
\t\t\t\t\t<string>FlutterSceneDelegate</string>
\t\t\t\t\t<key>UISceneStoryboardFile</key>
\t\t\t\t\t<string>Main</string>
\t\t\t\t</dict>
\t\t\t</array>
\t\t</dict>
\t</dict>
"""


def fix_plist(path: pathlib.Path, dry: bool) -> list[str]:
    """Edit Info.plist as text, so comments and formatting survive.

    Round-tripping through plistlib drops XML comments, and these plists use
    comments to record decisions — daily-pulse's explains why its Google
    Sign-In URL scheme is deliberately absent. The result is still parsed to
    prove it is a valid plist with the expected values.
    """
    s = path.read_text()
    info = plistlib.loads(s.encode())
    done = []

    def set_string(text, key, value):
        # Fill an existing empty value, or add the key if it is absent.
        pat = re.compile(r"(<key>" + key + r"</key>\s*)<string>\s*</string>")
        if pat.search(text):
            return pat.sub(r"\g<1><string>" + value + "</string>", text, count=1), True
        if f"<key>{key}</key>" not in text:
            return insert(text, f"\t<key>{key}</key>\n\t<string>{value}</string>\n"), True
        return text, False

    def insert(text, snippet):
        end = text.rstrip().rfind("</dict>")
        assert end > 0 and text.rstrip().endswith("</plist>"), "unexpected plist shape"
        return text[:end] + snippet + text[end:]

    if not info.get("UIApplicationSceneManifest"):
        s = insert(s, SCENE_XML)
        done.append("scene manifest")
    if not info.get("UIMainStoryboardFile"):
        s, ok = set_string(s, "UIMainStoryboardFile", "Main")
        if ok: done.append("UIMainStoryboardFile=Main")
    if not info.get("UILaunchStoryboardName"):
        s, ok = set_string(s, "UILaunchStoryboardName", "LaunchScreen")
        if ok: done.append("UILaunchStoryboardName=LaunchScreen")

    after = plistlib.loads(s.encode())
    assert after.get("UIApplicationSceneManifest") and after.get("UIMainStoryboardFile") == "Main" \
        and after.get("UILaunchStoryboardName") == "LaunchScreen", f"{path}: plist check failed"
    if done and not dry:
        path.write_text(s)
    return done


def fix_appdelegate(path: pathlib.Path, dry: bool) -> list[str]:
    s = path.read_text()
    if "FlutterImplicitEngineDelegate" in s:
        return []
    if "rootViewController" not in s:
        raise SystemExit(f"  {path}: unfamiliar AppDelegate shape — refusing to guess")
    extra_imports = [l for l in s.splitlines()
                     if l.startswith("import ") and l.split()[1] not in ("Flutter", "UIKit")]
    body = s[s.index("didFinishLaunchingWithOptions"):]
    body = body[body.index("{") + 1:]
    depth, out = 1, []
    for ch in body:
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: break
        out.append(ch)
    lines = "".join(out).splitlines()
    # Carry over app-specific statements, with the comment directly above them.
    keep, pending = [], []
    for l in lines:
        st = l.strip()
        if st.startswith("//"):
            pending.append(l)
            continue
        if not st:
            pending = []
            continue
        if WINDOW_PLUMBING.search(l):
            pending = []
            continue
        keep.extend(pending + [l])
        pending = []
    extra_setup = "".join(f"{l}\n" for l in keep)
    if extra_setup:
        extra_setup += "\n"
    new = MODERN_APPDELEGATE.format(
        extra_imports="".join(f"{l}\n" for l in extra_imports),
        extra_setup=extra_setup)
    if not dry:
        path.write_text(new)
    return ["AppDelegate: implicit engine"
            + (f" (kept {len([l for l in keep if not l.strip().startswith('//')])} "
               "app-specific line(s))" if keep else "")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    apps = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        apps = [a for a in apps if a["repo"] in args.apps]

    missing = []
    for a in apps:
        d = app_dir(a) / "ios"
        plist = d / "Runner/Info.plist"
        if not plist.exists():
            continue
        info = plistlib.loads(plist.read_bytes())
        if info.get("UIApplicationSceneManifest"):
            continue
        missing.append(a)
        if args.check:
            print(f"  {a['repo']:16} no UIApplicationSceneManifest — crashes on launch on iOS 27")
            continue
        notes = []
        notes += fix_pbxproj(d / "Runner.xcodeproj/project.pbxproj", args.dry_run)
        notes += fix_plist(plist, args.dry_run)
        notes += fix_appdelegate(d / "Runner/AppDelegate.swift", args.dry_run)
        print(f"  {a['repo']:16} {'would: ' if args.dry_run else ''}{'; '.join(notes)}",
              flush=True)

    print(f"\n  {len(missing)} app(s) without the UIScene lifecycle"
          + ("" if args.check else (" — would fix" if args.dry_run else " — fixed")))
    if args.check:
        return 1 if missing else 0
    if missing and not args.dry_run:
        print("  Verify each with: python3 scripts/sim_install.py <app> --ios  "
              "(on an iOS 27 simulator; a launch is the only proof)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
