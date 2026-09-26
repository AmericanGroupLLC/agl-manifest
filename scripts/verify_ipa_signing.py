#!/usr/bin/env python3
"""Confirm every shipped IPA is really distribution-signed for the right id."""
import json, pathlib, re, shutil, subprocess, tempfile
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT  # noqa: E402
ROOT=_ROOT; DIST=ROOT/".dist"
apps=[a for a in json.loads((ROOT/"agl-manifest/apps.json").read_text())["apps"] if a.get("flutter")]
bad=[]; ok=0
for a in apps:
    repo=a["repo"]; want=a["bundle_id"]
    ipa=DIST/f"{repo}.ipa"
    if not ipa.exists():
        bad.append((repo,"NO_IPA","")); continue
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["unzip","-qq",str(ipa),"-d",td],capture_output=True)
        apps_dir=list(pathlib.Path(td,"Payload").glob("*.app")) if pathlib.Path(td,"Payload").exists() else []
        if not apps_dir: bad.append((repo,"NO_APP","")); continue
        app=apps_dir[0]
        bid=subprocess.run(["plutil","-extract","CFBundleIdentifier","raw",str(app/"Info.plist")],
                           capture_output=True,text=True).stdout.strip()
        cs=subprocess.run(["codesign","-dvvv",str(app)],capture_output=True,text=True).stderr
        auth=re.search(r"Authority=(.+)",cs)
        ent=subprocess.run(["codesign","-d","--entitlements",":-",str(app)],capture_output=True,text=True).stdout
        gta="get-task-allow" in ent and "<true/>" in ent.split("get-task-allow")[1][:40]
        vr=subprocess.run(["codesign","--verify","--strict",str(app)],capture_output=True,text=True).returncode
        probs=[]
        if bid!=want: probs.append(f"bundle {bid}!={want}")
        if not auth or "Apple Distribution" not in auth.group(1): probs.append("not Apple Distribution")
        if gta: probs.append("get-task-allow=true")
        if vr!=0: probs.append("signature invalid")
        if probs: bad.append((repo,"; ".join(probs),bid))
        else: ok+=1
print(f"IPAs fully valid: {ok}/{len(apps)}")
for r,p,b in bad: print(f"   {r}: {p}")
