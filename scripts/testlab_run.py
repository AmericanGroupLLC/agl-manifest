#!/usr/bin/env python3
"""Run every app on real hardware in Firebase Test Lab, and keep the video.

    python3 scripts/testlab_run.py --list-devices
    python3 scripts/testlab_run.py CalcMaster
    python3 scripts/testlab_run.py --all --skip-build

Two things this answers that a simulator cannot.

**Guideline 2.1.** Apple has asked, for twelve apps, for "a screen recording
of the app running on a physical device". `docs/MANUAL_ACTIONS.md` recorded
that as human-only work. It is not: Test Lab's device catalog is real
hardware, `--record-video` records it, and the result is an mp4 per device.

**The claim that an app works.** Everything so far has been an emulator or a
simulator on this laptop. A Robo test is an automated crawl — it needs no test
code at all — so it exercises the shipped APK on a real phone and fails loudly
on a crash the simulator never saw.

Robo rather than instrumentation on purpose: `integration_test` would need an
androidTest APK per app, and the crawl is what produces a watchable video of
someone using the app, which is what App Review asked for.

Results land in `~/agl/.dist/testlab/<app>/` and the evidence JSON in
`docs/testlab-results.json`. Nothing here invents a pass: an app with no APK
is reported as not run, and a crawl that crashes is reported as failed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST, flutter_sdk  # noqa: E402

OUT = DIST / "testlab"
# A real phone, and a tablet for the second form factor. Both are checked
# against the live catalog before use — Test Lab retires models, and a stale
# id fails the whole run with a message about an unknown device.
DEFAULT_PHONE = ("Frogger", "36")          # Nothing Phone (4a), physical
FALLBACK_PHONE = ("CPH2449", "34")         # OnePlus 11 5G, physical
TABLET = ("AndroidTablet270dpi.arm", "34")  # virtual; no physical tablet offered


def sh(args, timeout=3600, cwd=None):
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)


def catalog() -> dict[str, set[str]]:
    r = sh(["gcloud", "firebase", "test", "android", "models", "list",
            "--format=value(id,supportedVersionIds.list())"], timeout=600)
    out: dict[str, set[str]] = {}
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out[parts[0]] = {v.strip() for v in parts[1].split(",") if v.strip()}
    return out


def pick(cat: dict[str, set[str]]) -> list[tuple[str, str]]:
    want = []
    for model, ver in (DEFAULT_PHONE, FALLBACK_PHONE):
        if ver in cat.get(model, set()):
            want.append((model, ver))
            break
    if not want:                       # catalog moved under us
        for model, vers in sorted(cat.items()):
            if vers:
                want.append((model, sorted(vers)[-1]))
                break
    if TABLET[1] in cat.get(TABLET[0], set()):
        want.append(TABLET)
    return want


def apk_for(d: pathlib.Path) -> pathlib.Path | None:
    """Newest debug APK already built for this app."""
    cands = list(d.glob("build/app/outputs/flutter-apk/*.apk"))
    cands += list(d.glob("build/app/outputs/apk/**/*.apk"))
    cands = [c for c in cands if c.stat().st_size > 1_000_000]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--timeout", default="4m")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    cat = catalog()
    if not cat:
        raise SystemExit("  could not read the Test Lab catalog — is gcloud "
                         "authenticated and a project set?")
    devices = pick(cat)
    if args.list_devices:
        for m, v in devices:
            print(f"  {m:28} api {v}")
        return 0

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    elif not args.all:
        raise SystemExit("  name an app or pass --all")

    flutter = str(flutter_sdk() / "bin" / "flutter")
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}

    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        if not (d / "pubspec.yaml").exists():
            continue

        apk = apk_for(d)
        if apk is None and not args.skip_build:
            b = sh([flutter, "build", "apk", "--debug"], cwd=d, timeout=3600)
            if b.returncode != 0:
                results[repo] = {"state": "BUILD_FAILED",
                                 "detail": (b.stderr or b.stdout)[-300:]}
                print(f"  {repo:16} build failed", flush=True)
                continue
            apk = apk_for(d)
        if apk is None:
            results[repo] = {"state": "NO_APK"}
            print(f"  {repo:16} no apk, not run", flush=True)
            continue

        dest = OUT / repo
        dest.mkdir(parents=True, exist_ok=True)
        cmd = ["gcloud", "firebase", "test", "android", "run",
               "--type", "robo", "--app", str(apk),
               "--timeout", args.timeout, "--record-video",
               "--format", "json"]
        for m, v in devices:
            cmd += ["--device",
                    f"model={m},version={v},locale=en,orientation=portrait"]

        r = sh(cmd, timeout=5400)
        blob = (r.stdout or "") + (r.stderr or "")
        # gcloud prints the browser URL and the raw results bucket on stderr.
        url = re.search(r"https://console\.firebase\.google\.com/\S+", blob)
        gcs = re.search(r"gs://[^\s\]]+", blob)
        ok = r.returncode == 0
        rec = {"state": "PASSED" if ok else "FAILED",
               "apk": str(apk.relative_to(d)),
               "devices": [f"{m}/api{v}" for m, v in devices],
               "console": url.group(0) if url else None,
               "bucket": gcs.group(0) if gcs else None}

        # The video is the deliverable for Guideline 2.1, so fetch it rather
        # than linking to a console page a reviewer cannot open.
        if gcs:
            g = sh(["gsutil", "-m", "cp", "-r", gcs.group(0), str(dest)],
                   timeout=1800)
            vids = sorted(dest.rglob("*.mp4"))
            rec["videos"] = [str(v.relative_to(DIST)) for v in vids]
            if not vids:
                rec["video_note"] = (g.stderr or "")[-200:]
        results[repo] = rec
        print(f"  {repo:16} {rec['state']:7} "
              f"{len(rec.get('videos') or [])} video(s)", flush=True)

    f = M / "docs/testlab-results.json"
    f.write_text(json.dumps(results, indent=1) + "\n")
    passed = sum(1 for v in results.values() if v.get("state") == "PASSED")
    vids = sum(len(v.get("videos") or []) for v in results.values())
    print(f"\n  {passed}/{len(results)} passed on real hardware, "
          f"{vids} video(s) captured")
    print(f"  -> {f.relative_to(M)}  and  {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
