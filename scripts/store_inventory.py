#!/usr/bin/env python3
"""Reconcile the 43-app manifest against what each store actually holds.

"Is every app in both stores?" is not answerable from either console's app
count, because both accounts carry records that are not part of the portfolio —
abandoned experiments, a record renamed to free a name, and on Play the
deleted `com.americangroup.*` originals. This asks each store, per bundle id
and per package name, and prints the three sets that matter: present, missing,
and extra.

    python3 scripts/store_inventory.py            # -> docs/store-inventory.json

Apple is read with the App Store Connect API key; Play has no "list my apps"
endpoint, so each package is probed by opening an edit, which 404s for a
package the account does not hold (and for one it has deleted).
"""
import json, pathlib, subprocess, sys, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST  # noqa: E402

SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
PLAY = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
OUT = MANIFEST / "docs" / "store-inventory.json"

# Packages the Play account holds that are not in the manifest. Kept here so the
# script reports them rather than silently calling the portfolio complete; the
# API cannot enumerate an account's apps. com.americangroupllc.GroceryMatch was
# on this list until 2026-10-04, when the app was recased onto that record.
PLAY_KNOWN_EXTRA = [
    "com.americangroupllc.Mykarma",
    "com.americangroupllc.careerupgradeai",
    "com.americangroupllc.dealzap",
    "com.americangroup.ratiotune",         # the pre-rename original
]


def play_token():
    r = subprocess.run(
        [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
         "--scopes=https://www.googleapis.com/auth/androidpublisher"],
        capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise RuntimeError(r.stderr[-300:])
    return r.stdout.strip()


def play_holds(pkg, tok):
    req = urllib.request.Request(f"{PLAY}/{pkg}/edits", method="POST",
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Length": "0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False


def apple_bundle_ids():
    """Every bundle id with an App Store Connect record, via spaceship."""
    script = (
        'require "spaceship"; require "json"; '
        'Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create('
        'key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), '
        'filepath: ENV.fetch("ASC_KEY_PATH")); '
        'print JSON.dump(Spaceship::ConnectAPI::App.all.map(&:bundle_id))')
    # The `bundle` on PATH is macOS's Ruby 2.6 and cannot load the gems; the
    # rbenv shim is the one with spaceship. Prefer it when it exists.
    shim = pathlib.Path.home() / ".rbenv/shims/bundle"
    bundle = str(shim) if shim.exists() else "bundle"
    r = subprocess.run([bundle, "exec", "ruby", "-e", script], cwd=str(MANIFEST),
                       capture_output=True, text=True, timeout=600)
    if not r.stdout.strip():
        raise RuntimeError(r.stderr[-400:])
    return json.loads(r.stdout)


def main():
    apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    tok = play_token()

    apple = set(apple_bundle_ids())
    rows = []
    for a in apps:
        pkg = a.get("application_id") or a["bundle_id"]
        rows.append({
            "repo": a["repo"],
            "bundle_id": a["bundle_id"],
            "package": pkg,
            "apple": a["bundle_id"] in apple,
            "play": play_holds(pkg, tok),
        })

    apple_missing = [r["repo"] for r in rows if not r["apple"]]
    play_missing = [r["repo"] for r in rows if not r["play"]]
    apple_extra = sorted(apple - {a["bundle_id"] for a in apps})
    play_extra = [p for p in PLAY_KNOWN_EXTRA if play_holds(p, tok)]

    out = {
        "manifest_apps": len(apps),
        "apple": {"present": len(apps) - len(apple_missing),
                  "missing": apple_missing, "extra_records": apple_extra},
        "play": {"present": len(apps) - len(play_missing),
                 "missing": play_missing, "extra_records": play_extra},
        "apps": rows,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"manifest apps : {len(apps)}")
    print(f"App Store     : {out['apple']['present']}/{len(apps)}  "
          f"missing={apple_missing or 'none'}")
    print(f"               extra records not in the manifest: {apple_extra or 'none'}")
    print(f"Google Play   : {out['play']['present']}/{len(apps)}  "
          f"missing={play_missing or 'none'}")
    print(f"               extra records not in the manifest: {play_extra or 'none'}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
