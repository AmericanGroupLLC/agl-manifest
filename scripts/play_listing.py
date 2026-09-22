#!/usr/bin/env python3
"""Push each app's store listing and graphics to Google Play.

play_upload.py only ships the binary; a Play entry with no description or
screenshots cannot be promoted past internal testing. This uploads, per app:
title, short and full description, the feature graphic, the 512px icon and
every phone and tablet screenshot the repo holds.

The icon is rendered from the app's own 1024px iOS app icon, because Play wants
exactly 512x512 and the Android launcher icons top out at 192px.

    python3 scripts/play_listing.py --all
    python3 scripts/play_listing.py RideZap
    python3 scripts/play_listing.py --all --audit   # report only, upload nothing
"""
import json, pathlib, subprocess, sys, tempfile, time

ROOT = pathlib.Path("/Users/spatchava/agl"); M = ROOT / "agl-manifest"
OUT = ROOT / ".dist" / "play-listing-results.json"
SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
UPLOAD = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications"
IMAGE_TYPES = ["phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots"]

_tok = {"v": "", "at": 0.0}
def token():
    if time.time() - _tok["at"] > 1500:
        _tok["v"] = subprocess.run(
            [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
             "--scopes=https://www.googleapis.com/auth/androidpublisher"],
            capture_output=True, text=True).stdout.strip()
        _tok["at"] = time.time()
    return _tok["v"]

def call(method, url, body=None, file=None, ctype="application/json"):
    cmd = ["curl", "-s", "--max-time", "900", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", f"Content-Type: {ctype}"]
    if file: cmd += ["--data-binary", f"@{file}"]
    elif body is not None: cmd += ["-d", json.dumps(body)]
    else: cmd += ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out) if out.strip() else {}
    except Exception: return {"error": {"message": out[:200] or "empty response"}}

def fail(d): return d["error"].get("message", "unknown")[:160] if "error" in d else None

def app_dir(a):
    p = ROOT / a["repo"]
    return p if a.get("dir") in (None, ".") else p / a["dir"]

def read(p): return p.read_text().strip() if p.exists() else ""

def icon_512(a, tmp):
    """Play wants exactly 512x512; the iOS 1024 icon is the only clean source."""
    src = sorted(app_dir(a).glob("ios/Runner/Assets.xcassets/AppIcon.appiconset/*1024*.png"))
    if not src: return None
    dst = pathlib.Path(tmp) / f"{a['repo']}-icon512.png"
    r = subprocess.run(["sips", "-z", "512", "512", str(src[0]), "--out", str(dst)],
                       capture_output=True, text=True)
    return dst if r.returncode == 0 and dst.exists() else None

AUDIT = "--audit" in sys.argv
apps = json.load(open(M / "apps.json"))["apps"]
names = [a for a in sys.argv[1:] if not a.startswith("--")]
if names: apps = [a for a in apps if a["repo"] in names]
elif "--all" not in sys.argv: sys.exit("pass --all or one or more app names")

out = json.load(open(OUT)) if OUT.exists() else {}
tmp = tempfile.mkdtemp(prefix="play-listing-")

for a in apps:
    repo, pkg = a["repo"], a["application_id"]
    md = app_dir(a) / "fastlane/metadata/android/en-US"
    img = md / "images"
    title, short, full = read(md / "title.txt"), read(md / "short_description.txt"), read(md / "full_description.txt")
    if not (title and full):
        print(f"{repo:18} no listing copy on disk"); out[repo] = {"status": "no-copy"}; continue

    shots = {t: sorted((img / t).glob("*.png")) for t in IMAGE_TYPES}
    feat = img / "featureGraphic.png"
    if AUDIT:
        print(f"{repo:18} title={len(title)} short={len(short)} full={len(full)} "
              f"feat={feat.exists()} " + " ".join(f"{t}={len(v)}" for t, v in shots.items()))
        continue

    e = call("POST", f"{API}/{pkg}/edits")
    if (m := fail(e)): print(f"{repo:18} open edit: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    eid = e["id"]
    step = "listing"
    r = call("PUT", f"{API}/{pkg}/edits/{eid}/listings/en-US",
             {"language": "en-US", "title": title[:30], "shortDescription": short[:80],
              "fullDescription": full[:4000]})
    if (m := fail(r)): print(f"{repo:18} {step}: {m}"); out[repo] = {"status": "failed", "step": step, "error": m}; continue

    uploaded = {}
    # Replacing the whole image type first keeps re-runs from stacking duplicates.
    def put_images(kind, files):
        if not files: return 0
        call("DELETE", f"{API}/{pkg}/edits/{eid}/listings/en-US/{kind}")
        n = 0
        for f in files:
            u = call("POST", f"{UPLOAD}/{pkg}/edits/{eid}/listings/en-US/{kind}?uploadType=media",
                     file=f, ctype="image/png")
            if fail(u) is None: n += 1
            else: print(f"{repo:18} {kind} {pathlib.Path(f).name}: {fail(u)}")
        return n

    icon = icon_512(a, tmp)
    if icon: uploaded["icon"] = put_images("icon", [icon])
    if feat.exists(): uploaded["featureGraphic"] = put_images("featureGraphic", [feat])
    for t, files in shots.items():
        if files: uploaded[t] = put_images(t, files)

    c = call("POST", f"{API}/{pkg}/edits/{eid}:commit")
    if (m := fail(c)): print(f"{repo:18} commit: {m}"); out[repo] = {"status": "failed", "step": "commit", "error": m}; continue
    out[repo] = {"status": "listed", "package": pkg, "uploaded": uploaded,
                 "at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    print(f"{repo:18} listing updated  " + " ".join(f"{k}={v}" for k, v in uploaded.items()))
    json.dump(out, open(OUT, "w"), indent=1)

if not AUDIT:
    json.dump(out, open(OUT, "w"), indent=1)
    done = sum(1 for v in out.values() if v.get("status") == "listed")
    print(f"\nlistings updated: {done}/{len(out)}  -> {OUT}")
