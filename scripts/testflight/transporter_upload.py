#!/usr/bin/env python3
"""Upload each app's IPA to App Store Connect with Apple's Transporter.

    source scripts/testflight/env.sh
    python3 scripts/testflight/transporter_upload.py            # every app with an IPA
    python3 scripts/testflight/transporter_upload.py CalcMaster
    python3 scripts/testflight/transporter_upload.py --dry-run

Why this exists, and the one thing that makes it work:

Transporter appeared to be broken on this Mac. Every invocation answered

    ERROR: Could not download Defaults.properties (launcher)

and it was written off as an incomplete install — 72 MB, with
Contents/itms/lib holding only osgibootstrapper.jar. That was wrong. The file
is perfectly reachable:

    curl https://contentdelivery.itunes.apple.com/transporter/Defaults.properties
    200

It is the same JVM-proxy problem CLAUDE.md already documents for Gradle: this
machine's direct egress is blocked and everything goes through 127.0.0.1:10054.
curl honours HTTP_PROXY; a JVM does not — it reads only the http.proxyHost /
https.proxyHost system properties. Setting HTTP_PROXY, HTTPS_PROXY,
TRANSPORTER_JAVA_OPTS or JVM_OPTIONS all changed nothing, because the launcher
forwards **-D arguments** to the JVM and nothing else.

With them passed as arguments it works, and `-m upload` returned
"1 package was uploaded successfully" for CalcMaster.

`-m verify` is not useful here: it expects an .itmsp *directory* and answers
"is NOT a directory" for an .ipa. Upload is the only mode that takes one.

-numStreams 1 is load-bearing. By default Transporter opens four parallel
streams, and through this machine's proxy 16 of 43 uploads died with

    Upload Failed: (... part: 4) ([1/3] will retry):
    java.net.SocketException: Connection reset / Broken pipe
    javax.net.ssl.SSLException: Received fatal alert

after exhausting all three retries. One stream uploads the same files without
a single failure. (-t DAV, the other obvious lever, is refused: "The DAV
transport is obsolete, and is no longer supported.")
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from agl_paths import MANIFEST, DIST, ROOT  # noqa: E402

IT = pathlib.Path("/Applications/Transporter.app/Contents/itms/bin/iTMSTransporter")

# Passed as arguments, not environment. See the module docstring.
PROXY = [
    "-Dhttp.proxyHost=127.0.0.1", "-Dhttp.proxyPort=10054",
    "-Dhttps.proxyHost=127.0.0.1", "-Dhttps.proxyPort=10054",
    "-Dhttp.nonProxyHosts=localhost|127.0.0.1",
    "-Djava.net.preferIPv4Stack=true",
]


def stage_fresh(apps: list[str]) -> None:
    """Build each app and put *that* IPA where this script uploads from.

    The previous IPA is moved to <DIST>/ipa-previous/ rather than deleted.
    An app whose build fails keeps nothing staged, so it cannot fall back to
    an old binary.
    """
    import shutil
    manifest = {a["repo"]: a for a in json.loads((MANIFEST / "apps.json").read_text())["apps"]}
    prev = DIST / "ipa-previous"
    prev.mkdir(parents=True, exist_ok=True)
    here = pathlib.Path(__file__).resolve().parent
    for repo in apps:
        a = manifest[repo]
        app_dir = ROOT / repo / (a.get("dir") or ".")
        staged = DIST / f"{repo}.ipa"
        if staged.exists():
            shutil.move(str(staged), str(prev / f"{repo}.ipa"))
        r = subprocess.run([sys.executable, str(here / "build_only.py"), repo],
                           capture_output=True, text=True, timeout=3600)
        line = (r.stdout.strip().splitlines() or [""])[-1]
        ipas = sorted((app_dir / "build/ios/ipa").glob("*.ipa"), key=lambda q: q.stat().st_mtime)
        if r.returncode != 0 or " OK " not in f" {line} " or not ipas:
            print(f"  {repo:18} BUILD FAILED — nothing staged: {line[:120]}", flush=True)
            continue
        shutil.copy(ipas[-1], staged)
        print(f"  {repo:18} built and staged {staged.name}", flush=True)


def ipa_blocker(ipa: pathlib.Path) -> str | None:
    """Why this IPA must not be uploaded, or None."""
    import plistlib, zipfile
    try:
        with zipfile.ZipFile(ipa) as z:
            name = next(n for n in z.namelist()
                        if n.startswith("Payload/") and n.endswith(".app/Info.plist")
                        and n.count("/") == 2)
            info = plistlib.loads(z.read(name))
    except (StopIteration, zipfile.BadZipFile, KeyError, plistlib.InvalidFileException) as e:
        return f"cannot read the app's Info.plist ({type(e).__name__})"
    if not info.get("UIApplicationSceneManifest"):
        return (f"build {info.get('CFBundleVersion')} has no UIApplicationSceneManifest — "
                "it crashes on launch on iOS 27; rebuild from the fixed source")
    # The purpose strings Apple's ITMS-90683 scan will demand of this binary.
    from privacy_scan import scan
    _info, missing = scan(ipa)
    if missing:
        return ("missing purpose string(s) Apple will flag (ITMS-90683): "
                + ", ".join(f"{k} — binary references {api}" for k, api in missing))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--build", action="store_true",
                    help="build a fresh signed IPA for each named app first (build_only.py) "
                         "and stage exactly that file, setting the previous one aside")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()
    if args.build:
        if not args.apps:
            raise SystemExit("  --build needs app names")
        stage_fresh(args.apps)

    if not IT.exists():
        raise SystemExit(f"Transporter not found at {IT}")
    for var in ("ASC_KEY_ID", "ASC_ISSUER_ID"):
        if not os.environ.get(var):
            raise SystemExit(f"{var} not set — source scripts/testflight/env.sh")

    # Transporter reads the .p8 from here, not from ASC_KEY_PATH.
    keys = pathlib.Path.home() / ".appstoreconnect/private_keys"
    keys.mkdir(parents=True, exist_ok=True)
    src = pathlib.Path(os.environ.get("ASC_KEY_PATH", ""))
    if src.is_file() and not (keys / src.name).exists():
        (keys / src.name).write_bytes(src.read_bytes())

    manifest = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    out, ok, failed, missing = {}, 0, 0, 0
    for a in manifest:
        repo = a["repo"]
        ipa = DIST / f"{repo}.ipa"
        if not ipa.exists():
            out[repo] = {"status": "no-ipa"}
            print(f"  {repo:18} no IPA in {DIST}", flush=True)
            missing += 1
            continue
        # Refuse a binary that crashes on launch on iOS 27. On 2026-10-08 the
        # IPA sitting here for BodyQuest was the 29 September build (build 3)
        # with no UIApplicationSceneManifest, while the fixed build was in
        # the app's build/ folder; uploading by filename would have shipped
        # the crash again. Read the plist inside the binary, not the repo.
        why = ipa_blocker(ipa)
        if why:
            out[repo] = {"status": "refused", "detail": why}
            print(f"  {repo:18} REFUSED: {why}", flush=True)
            failed += 1
            continue
        if args.dry_run:
            print(f"  {repo:18} would upload {ipa.name} "
                  f"({ipa.stat().st_size // 1048576} MB)", flush=True)
            continue

        # Up to three attempts. Even on one stream the upload is flaky
        # through this proxy — NexusTransferPay failed twice and then
        # uploaded on the next attempt with no change at all. Transporter's
        # own per-part retries do not cover a whole-session reset.
        t0 = time.time()
        blob, attempts = "", 0
        for attempt in range(1, 4):
            attempts = attempt
            r = subprocess.run(
                [str(IT), *PROXY, "-m", "upload", "-assetFile", str(ipa),
                 "-apiKey", os.environ["ASC_KEY_ID"],
                 "-apiIssuer", os.environ["ASC_ISSUER_ID"], "-numStreams", "1"],
                capture_output=True, text=True, timeout=3600)
            blob = (r.stdout or "") + (r.stderr or "")
            if "uploaded successfully" in blob or "redundant" in blob.lower():
                break
            if attempt < 3:
                time.sleep(15)
        took = round(time.time() - t0)

        if "uploaded successfully" in blob:
            out[repo] = {"status": "uploaded", "seconds": took, "attempts": attempts}
            ok += 1
            print(f"  {repo:18} uploaded ({took}s"
                  f"{', attempt ' + str(attempts) if attempts > 1 else ''})", flush=True)
        else:
            # Apple's own wording is far more useful than the exit code, and
            # a redundant-binary refusal is a success for our purposes: the
            # build is already there.
            why = ""
            for line in blob.splitlines():
                if "ERROR" in line or "error" in line.lower():
                    why = line.strip()[-220:]
                    break
            redundant = "redundant" in blob.lower() or "already been used" in blob.lower()
            out[repo] = {"status": "already-uploaded" if redundant else "failed",
                         "detail": why, "seconds": took}
            if redundant:
                ok += 1
                print(f"  {repo:18} already on App Store Connect ({took}s)", flush=True)
            else:
                failed += 1
                print(f"  {repo:18} FAILED {why[:120]} ({took}s)", flush=True)

    dest = DIST / "transporter-upload.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nuploaded or already present {ok}, failed {failed}, no IPA {missing}")
    print(f"-> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
