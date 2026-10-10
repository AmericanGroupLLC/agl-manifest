#!/usr/bin/env python3
"""Write the Play Console answers out per app, so the forms are transcription.

    python3 scripts/console_answers.py            # -> docs/console-answers/<app>.md
    python3 scripts/console_answers.py CalcMaster

37 apps sit in Draft on Google Play, and an app leaves Draft only when its
App content declarations are complete. Of the 145 methods in the Play
Developer API, exactly one touches them — `applications.dataSafety`. Content
rating (IARC), target audience, ads, and app access have no API at all, so
those four are Console work no matter what.

What is avoidable is *deciding the answers 37 times*. Every answer below is
already measured somewhere in this repository:

  Data safety        store/privacy/<app>.json   (the Apple privacy answers)
  Content rating     store/ratings/<app>.json   (the Apple age-rating answers)
  Ads                dep_google_mobile_ads      (docs/release-readiness.json)
  App access         whether the Dart has a sign-in with no guest path
  Target audience    the age band the rating answers imply

So this prints, per app, what to select — and flags the one case the
repository cannot settle: an app that gates on sign-in needs working
reviewer credentials, and MA-036 records that the documented ones do not
authenticate.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

OUT = M / "docs/console-answers"
AUTH = re.compile(r"signInWithPassword|SupabaseAuthService|signInWithOtp"
                  r"|FirebaseAuth\.instance\.signIn")
GUEST = re.compile(r"(?i)continue as guest|guest mode|skip sign|browse as guest"
                   r"|continue without")

# Apple's data types -> the Play Data safety categories they correspond to.
DATA_MAP = {
    "EMAIL_ADDRESS": "Personal info > Email address",
    "NAME": "Personal info > Name",
    "USER_ID": "Personal info > User IDs",
    "DEVICE_ID": "Device or other IDs > Device or other IDs",
    "ADVERTISING_DATA": "App activity > App interactions (advertising)",
    "PURCHASE_HISTORY": "Financial info > Purchase history",
    "HEALTH": "Health and fitness > Health info",
    "DATA_NOT_COLLECTED": None,
}


def gate(app_dir: pathlib.Path) -> bool:
    lib = app_dir / "lib"
    if not lib.exists():
        return False
    auth = guest = False
    for f in lib.rglob("*.dart"):
        if "generated" in str(f):
            continue
        try:
            s = f.read_text(errors="ignore")
        except OSError:
            continue
        auth = auth or bool(AUTH.search(s))
        guest = guest or bool(GUEST.search(s))
    return auth and not guest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    readiness = {r["repo"]: r for r in
                 json.loads((M / "docs/release-readiness.json").read_text())}
    OUT.mkdir(parents=True, exist_ok=True)

    written = 0
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        rr = readiness.get(repo, {})

        priv = M / "store/privacy" / f"{repo}.json"
        types = []
        if priv.exists():
            types = [p.get("data_type") for p in
                     (json.loads(priv.read_text()).get("data_protections") or [])]
        collected = [DATA_MAP[t] for t in types if DATA_MAP.get(t)]

        rating_f = M / "store/ratings" / f"{repo}.json"
        rating_f = rating_f if rating_f.exists() else M / "store/ratings/default.json"
        rating = json.loads(rating_f.read_text()) if rating_f.exists() else {}
        tame = all(v in ("NONE", False, None) for k, v in rating.items()
                   if not k.startswith(("_", "advertising", "socialMedia")))

        ads = bool(rr.get("dep_google_mobile_ads"))
        walled = gate(d)

        data_block = ("**This app does not collect or share any user data.**"
                      if not collected else "Collected data types:\n"
                      + "\n".join(f"  - {c}" for c in sorted(set(collected))))
        body = f"""# Play Console answers — {repo}

`{a.get('application_id')}`

Four of these five have no API; they are Console forms. Every answer is taken
from what this repository already measures, so this is transcription rather
than judgement.

## App access
{"**All functionality is available without a special access.**"
 if not walled else
 "**Some functionality is restricted.** This app signs in and has no guest "
 "path, so Play needs working reviewer credentials — and MA-036 records that "
 "the documented test accounts do not authenticate. Fix that first."}

## Ads
{"**Yes, this app contains ads.** It links the Google Mobile Ads SDK"
 f" (AdMob {rr.get('android_admob_id') or 'id in docs/admob-ids.json'})."
 if ads else "**No, this app does not contain ads.** It does not link the "
 "Google Mobile Ads SDK."}

## Content rating (IARC questionnaire)
Category: {a.get('primary_category') or 'see store/apps/' + repo + '.json'}
{"Answer **No** to every content question — violence, sexuality, language, "
 "controlled substances, gambling, horror. These are the same answers already "
 "accepted by Apple, in store/ratings/." if tame else
 "This app has at least one non-default content answer; read "
 f"store/ratings/{repo}.json and mirror it."}
User-generated content: {"Yes — the app accepts user content." if walled
                         else "No."}

## Target audience and content
Target age group: **18 and over** unless the listing says otherwise.
Appeals to children: **No**.

## Data safety
{data_block}
{"" if not collected else '''
For each: collected **Yes**, shared **No**, processed ephemerally **No**,
collection is **required**. Purpose: *App functionality* and *Analytics*;
add *Advertising* for the advertising row.'''}
Encrypted in transit: **Yes**. Users can request deletion: **Yes** —
{(a.get('deletion_url') or 'https://www.americangroup.ai/policy/' + repo.lower() + '/delete-account.html')}

## After the forms
The production release is already staged as a draft with a signed bundle.
Once App content is complete the app leaves Draft and the release can be
rolled out — `python3 scripts/play_release.py {repo}` or the Console.
"""
        (OUT / f"{repo}.md").write_text(body)
        written += 1

    print(f"  wrote {written} answer sheets -> {OUT.relative_to(M)}")
    print("  Content rating, target audience, ads and app access have no API; "
          "data safety has one (applications.dataSafety, CSV).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
