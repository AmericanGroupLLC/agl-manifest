#!/usr/bin/env python3
"""Write each app's android/key.properties from the manifest's secrets.

Every app has its **own** upload keystore — 30 of them — because Play binds an
upload key per app and losing one means that app can never be updated again.
So delivery cannot use a single keystore the way a one-app pipeline would.

The keystores arrive as one secret each (`KEYSTORE_<APP>_BASE64`) and their
aliases and passwords as a single JSON secret (`ANDROID_KEYSTORE_CONFIG`). This
decodes the ones needed for the current batch into $RUNNER_TEMP and points each
app's Gradle build at its own.

    python3 scripts/materialise_signing.py --apps all --out "$RUNNER_TEMP"

Writes nothing to the workspace, so a later step cannot pick a keystore up as a
build input or upload it as an artifact.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "apps.json").read_text())


def secret_name(app: str) -> str:
    return "KEYSTORE_" + re.sub(r"[^A-Z0-9]", "_", app.upper()) + "_BASE64"


# Actions only puts a secret in the environment if the workflow names it, and
# there are 34 per-app keystore secrets — one more for every app added. Listing
# them individually meant the list silently fell behind: run 36298643799 passed
# only ANDROID_KEYSTORE_CONFIG, so every app reported "no keystore" and would
# have produced debug-signed bundles that Play rejects at upload.
#
# The workflow hands over `toJSON(secrets)` instead, so a new app needs no
# workflow edit. It arrives as a FILE, not a variable: with all 43 keystores
# present the JSON is a few hundred kilobytes, and putting that in the process
# environment made every shard die before it started with
# "An error occurred trying to start process '/usr/bin/bash' ... Argument list
# too long" (run 36311877819). ALL_SECRETS is still read for small cases, and a
# directly-set variable still wins, so a local run needs nothing but an
# exported KEYSTORE_<APP>_BASE64.
def secret_value(name: str) -> str:
    direct = os.environ.get(name, "").strip()
    if direct:
        return direct
    blob = ""
    path = os.environ.get("ALL_SECRETS_FILE", "").strip()
    if path and pathlib.Path(path).exists():
        blob = pathlib.Path(path).read_text().strip()
    else:
        blob = os.environ.get("ALL_SECRETS", "").strip()
    if not blob:
        return ""
    try:
        return str(json.loads(blob).get(name, "")).strip()
    except json.JSONDecodeError:
        print("::warning::ALL_SECRETS is set but is not JSON; ignoring it")
        return ""


def select(spec: str) -> list[dict]:
    apps = [a for a in MANIFEST["apps"] if a.get("flutter")]
    if spec in ("", "all"):
        return apps
    if spec == "android-deliverable":
        return [a for a in apps if a["deliverable"]["android"]]
    wanted = {s.strip().lower() for s in spec.split(",") if s.strip()}
    return [a for a in apps if a["repo"].lower() in wanted]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", default="all")
    ap.add_argument("--out", required=True, help="a directory outside the workspace")
    args = ap.parse_args()

    raw_config = os.environ.get("ANDROID_KEYSTORE_CONFIG", "").strip()
    if not raw_config:
        print("::error::ANDROID_KEYSTORE_CONFIG is not set — no app can be signed.")
        return 1
    config = json.loads(raw_config)

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    signed = skipped = 0
    for app in select(args.apps):
        repo = app["repo"]
        material = secret_value(secret_name(repo))
        entry = config.get(repo)
        if not material or not entry:
            # An app with no keystore still builds; the artifact is just not
            # uploadable, and the Gradle config says so loudly at build time.
            print(f"{repo:20} no keystore — will build unsigned")
            skipped += 1
            continue

        keystore = out / f"{repo}-upload.jks"
        keystore.write_bytes(base64.b64decode(material))
        keystore.chmod(0o600)

        app_dir = ROOT / "work" / repo
        if app["dir"] != ".":
            app_dir = app_dir / app["dir"]
        properties = app_dir / "android" / "key.properties"
        if not properties.parent.is_dir():
            print(f"{repo:20} no android/ directory — skipped")
            skipped += 1
            continue

        properties.write_text(
            "# Generated for this run only. Never committed.\n"
            f"storeFile={keystore}\n"
            f"storePassword={entry['storePassword']}\n"
            f"keyAlias={entry['alias']}\n"
            f"keyPassword={entry['keyPassword']}\n"
        )
        properties.chmod(0o600)
        signed += 1
        print(f"{repo:20} signing material ready")

    print(f"\n{signed} app(s) ready to sign, {skipped} without a keystore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
