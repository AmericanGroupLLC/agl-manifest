#!/usr/bin/env python3
"""Rename every app's iOS bundle id and Android application id to
com.americangroupllc.<lowercase repo name>.

Final convention, confirmed 2026-09-15 after two passes went in opposite
directions: com.americangroupllc.<lowercase>, identical on both stores. This
supersedes the com.americangroup.* pass.

    python3 scripts/rename_identifiers.py --dry-run AGCleaner
    python3 scripts/rename_identifiers.py AGCleaner
    python3 scripts/rename_identifiers.py --all --commit

Replaces only the app's own current identifiers (bundle id, application id,
and any camel-case variant) in text files under the app directory, skipping
build output. After the edit it checks that AndroidManifest's main activity
still resolves against the new namespace; a Kotlin file whose package cannot
follow gets the fully qualified class name written into the manifest instead.
Regenerate apps.json afterwards (audit_release_readiness.py + generate_manifest.py).
"""
import json, os, pathlib, re, subprocess, sys

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402
SKIP_DIRS = {"build", ".dart_tool", ".git", "Pods", "node_modules", ".gradle", ".idea", "DerivedData"}
TEXT_EXT = {".gradle", ".kts", ".pbxproj", ".plist", ".xml", ".kt", ".java", ".dart", ".rb", ".md", ".json", ".yaml", ".yml", ".txt", ".entitlements", ".xcconfig", ".sh", ".pro", ".env", ".example", ".swift", ".h", ".m", ".properties", ".xcscheme", ".cfg", ".toml", ""}
apps = json.load(open(M / "apps.json"))["apps"]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
DRY = "--dry-run" in sys.argv; COMMIT = "--commit" in sys.argv
sel = apps if "--all" in sys.argv else [a for a in apps if a["repo"] in args]

def new_id(repo): return "com.americangroupllc." + re.sub(r"[^a-z0-9]", "", repo.lower())

for a in sel:
    repo = a["repo"]; d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    new = new_id(repo)
    olds = {a["bundle_id"], a["application_id"]}
    olds |= {o for o in [a["bundle_id"].lower(), a["application_id"].lower()]}
    olds.discard(new)
    if not olds: print(f"{repo:18} already {new}"); continue
    # longest first so 'com.americangroupllc.x' is replaced before any shorter variant
    pats = sorted(olds, key=len, reverse=True)
    changed = []
    for f in d.rglob("*"):
        if not f.is_file() or any(p in SKIP_DIRS or p.endswith(".bak") or ".bak." in p for p in f.relative_to(d).parts): continue
        if f.suffix not in TEXT_EXT and f.name not in ("Fastfile", "Appfile", "Podfile", "Gemfile"): continue
        try: t = f.read_text()
        except Exception: continue
        n = t
        for o in pats: n = n.replace(o, new)
        if n != t:
            changed.append(str(f.relative_to(d)))
            if not DRY: f.write_text(n)
    # sanity: Android main activity must resolve under the new namespace
    warn = ""
    man = d / "android/app/src/main/AndroidManifest.xml"
    if man.exists() and not DRY:
        mt = man.read_text()
        m = re.search(r'<activity[^>]*android:name="([^"]+)"[^>]*>', mt, re.S)
        if m and m.group(1).startswith("."):
            cls = m.group(1)[1:]
            kt = list((d / "android/app/src/main").rglob(f"{cls}.kt")) + list((d / "android/app/src/main").rglob(f"{cls}.java"))
            pkg = None
            for k in kt:
                pm = re.search(r"^\s*package\s+([\w.]+)", k.read_text(), re.M)
                if pm: pkg = pm.group(1); break
            if pkg and pkg != new:
                mt = mt.replace(f'android:name="{m.group(1)}"', f'android:name="{pkg}.{cls}"'); man.write_text(mt)
                warn = f"manifest activity fully qualified as {pkg}.{cls}"
    # gradle namespace must equal the Kotlin package of MainActivity only when relative names are used; report values
    g = next(iter([p for p in (d / "android/app").glob("build.gradle*")]), None)
    ns = appid = ""
    if g:
        gt = g.read_text(); ns = (re.search(r'namespace\s*=?\s*["\']([^"\']+)', gt) or [None, ""])[1]; appid = (re.search(r'applicationId\s*=?\s*["\']([^"\']+)', gt) or [None, ""])[1]
    pb = d / "ios/Runner.xcodeproj/project.pbxproj"
    ios_ids = sorted(set(re.findall(r"PRODUCT_BUNDLE_IDENTIFIER = ([^;]+);", pb.read_text()))) if pb.exists() else []
    print(f"{repo:18} -> {new:36} files={len(changed):3} appId={appid} ns={ns} ios={ios_ids} {warn}")
    if COMMIT and changed and not DRY:
        r = lambda *c: subprocess.run(c, cwd=ROOT / repo, capture_output=True, text=True)
        r("git", "add", "-A", "--", a["dir"] if a["dir"] != "." else ".")
        # never commit signing churn or pods
        r("git", "reset", "-q", "--", *[p for p in [f"{a['dir']}/ios/Podfile.lock" if a['dir'] != '.' else "ios/Podfile.lock"]])
        r("git", "commit", "-q", "-m", f"Rename identifiers to {new}\n\nBoth stores use com.americangroupllc.<app>, identical on each. This is the\nfinal convention (decision 2026-09-15) and supersedes the com.americangroup.*\npass, whose direction this message used to state backwards. Generated by\nagl-manifest scripts/rename_identifiers_llc.py.")
        br = r("git", "branch", "--show-current").stdout.strip()
        dflt = r("git", "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip().replace("origin/", "") or "main"
        p = r("git", "push", "-q", "origin", br); f2 = r("git", "push", "-q", "origin", f"HEAD:{dflt}")
        if p.returncode or f2.returncode: print(f"    push problem: {p.stderr.strip()[-80:]} {f2.stderr.strip()[-80:]}")
