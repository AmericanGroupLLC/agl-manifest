#!/usr/bin/env python3
"""Write each app's App Store privacy "nutrition label" JSON from measured facts,
in the shape fastlane's upload_app_privacy_details_to_app_store expects.

    python3 scripts/privacy_details.py            -> store/privacy/<repo>.json

Rules (what actually leaves the device, per the code and its dependencies):
  accounts (Supabase / Sign in with Google or Apple)  -> EMAIL_ADDRESS, NAME, USER_ID  linked, APP_FUNCTIONALITY
  ads (google_mobile_ads)                              -> DEVICE_ID, ADVERTISING_DATA  not linked, THIRD_PARTY_ADVERTISING;
                                                          marked "used to track you" only when the app asks App Tracking Transparency
  health package + account                             -> HEALTH  linked, APP_FUNCTIONALITY
  purchases                                            -> PURCHASE_HISTORY linked (receipts tied to the account/Apple ID)
  everything else (location, camera, mic, photos)      -> stays on device in these apps; not declared
  no account, no ads                                   -> DATA_NOT_COLLECTED
Adjust an app's file by hand if product knows better; the file is what gets uploaded.
"""
import json, pathlib, plistlib, re
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402
OUT = M / "store/privacy"
OUT.mkdir(exist_ok=True)
apps = json.load(open(M / "apps.json"))["apps"]
for a in apps:
    d = ROOT / a["repo"] / (a["dir"] if a["dir"] != "." else "")
    deps = (d / "pubspec.yaml").read_text().split("dev_dependencies")[0]
    dep = lambda k: re.search(rf"^\s+{k}:", deps, re.M) is not None
    pl = plistlib.load(open(d / "ios/Runner/Info.plist", "rb"))
    att = "NSUserTrackingUsageDescription" in pl
    account = dep("supabase_flutter") or dep("google_sign_in") or dep("sign_in_with_apple") or bool(set(a["auth"]["providers"]) & {"Supabase", "Google", "Apple", "Firebase"})
    ads = a["ads"] or dep("google_mobile_ads"); iap = dep("in_app_purchase") or dep("purchases_flutter"); health = dep("health")
    prot = []
    if account:
        for t in ("EMAIL_ADDRESS", "NAME", "USER_ID"):
            prot.append({"data_type": t, "protections": ["DATA_LINKED_TO_YOU"], "purposes": ["APP_FUNCTIONALITY"]})
    if ads:
        p = ["DATA_USED_TO_TRACK_YOU", "DATA_NOT_LINKED_TO_YOU"] if att else ["DATA_NOT_LINKED_TO_YOU"]
        for t in ("DEVICE_ID", "ADVERTISING_DATA"):
            prot.append({"data_type": t, "protections": p, "purposes": ["THIRD_PARTY_ADVERTISING"]})
    if health and account:
        prot.append({"data_type": "HEALTH", "protections": ["DATA_LINKED_TO_YOU"], "purposes": ["APP_FUNCTIONALITY"]})
    if iap and account:
        prot.append({"data_type": "PURCHASE_HISTORY", "protections": ["DATA_LINKED_TO_YOU"], "purposes": ["APP_FUNCTIONALITY"]})
    doc = {"data_protections": prot} if prot else {"data_protections": [{"data_type": "DATA_NOT_COLLECTED"}]}
    doc["_derived_from"] = {"account": account, "ads": ads, "att_prompt": att, "health": health, "iap": iap, "date": "2026-09-14"}
    json.dump(doc, open(OUT / f"{a['repo']}.json", "w"), indent=2)
    print(f"{a['repo']:18} {'NOT_COLLECTED' if not prot else ', '.join(sorted({p['data_type'] for p in prot}))}")
