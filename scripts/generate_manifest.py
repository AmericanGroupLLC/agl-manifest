#!/usr/bin/env python3
"""Build agl-manifest/apps.json from the measured readiness audit.

The manifest is not hand-maintained. It is derived from
docs/release-readiness.json, which is itself measured from the repositories, so
a new app, a moved project directory or a renamed bundle id reaches the
delivery pipeline by re-running the audit rather than by someone remembering.

    python3 scripts/audit_release_readiness.py
    python3 scripts/generate_manifest.py --out ~/agl/agl-manifest/apps.json
"""

from __future__ import annotations

import argparse
import json
import pathlib


def store_eligible(repo):
    """False when store/apps/<repo>.json still carries a `_blocked` marker.

    `_was_blocked_resolved` is a record of a block that was lifted and does not
    count. A repo with no store JSON at all is treated as eligible.
    """
    p = pathlib.Path(__file__).resolve().parent.parent / "store/apps" / f"{repo}.json"
    if not p.exists():
        return True
    try:
        return "_blocked" not in json.loads(p.read_text())
    except Exception:
        return True



BACKEND = pathlib.Path(__file__).resolve().parent.parent
AUDIT = BACKEND / "docs" / "release-readiness.json"
ORG = "AmericanGroupLLC"



# admob-ids.json predates the repo names in a couple of places.
_ADMOB_ALIAS = {"radiotune": "RadioTune", "Uscis-Case": "USCIS Case"}


def _admob(repo: str) -> dict:
    path = BACKEND / "docs" / "admob-ids.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get(repo) or data.get(_ADMOB_ALIAS.get(repo, repo), {})


def _has_description(repo: str) -> bool:
    """Whether this app has English store copy a listing could actually use."""
    path = BACKEND / "store" / "apps" / f"{repo}.json"
    if not path.exists():
        return False
    english = json.loads(path.read_text()).get("copy", {}).get("en", {})
    return bool(english.get("description") or english.get("full_description"))


def _default_branches() -> dict[str, str]:
    """Each repo's default branch, from GitHub rather than from a checkout.

    This used to be `git_branch` — whatever branch the local clone happened to
    be sitting on. That is not what CI should check out, and it broke badly:
    every app was pinned to `production-readiness-2026-09-12`, that branch was
    deleted during the branch consolidation, and the next run died with
    `fatal: Remote branch production-readiness-2026-09-12 not found in
    upstream origin` before a single app was analysed.

    Now that each repo has one branch, the default branch is the answer, and
    asking GitHub means a stale local clone cannot put a dead ref back.
    """
    import subprocess
    try:
        out = subprocess.run(
            ["gh", "repo", "list", ORG, "--limit", "200", "--json",
             "name,defaultBranchRef",
             "--jq", r'.[] | "\(.name)|\(.defaultBranchRef.name)"'],
            capture_output=True, text=True, timeout=120)
        return dict(l.split("|", 1) for l in out.stdout.strip().splitlines() if "|" in l)
    except Exception as e:
        print(f"::warning::could not read default branches from GitHub ({e}); "
              f"falling back to each checkout's current branch")
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = json.loads(AUDIT.read_text())

    # The portfolio is 42 mobile apps, not 37. Six are not Flutter yet and one
    # has been transferred out of the org — they belong in the tables with
    # their real status rather than being silently dropped, because "why is
    # this app missing" is the question a partial list always produces.
    # Package names reserved ahead of the ports. `com.americangroupllc.<app>` is
    # what 31 of the 37 existing apps use, so the six follow it rather than the
    # `com.americangroup.` variant six older apps happen to have.
    #
    # They are reserved deliberately: an AdMob app, a Play record, an App Store
    # record and an upload keystore can all be created from the package name
    # alone, before a line of Flutter exists. Registering them now takes the
    # console work off the critical path of the port — and an id, once
    # published, can never be changed.
    not_flutter = {
        "AeroSwift": ("TypeScript monorepo (npm workspaces): tracking, personal, transit",
                      "com.americangroupllc.aeroswift"),
        "AGStudio": ("React Native — port pending", "com.americangroupllc.agstudio"),
        "ApexMarketWatch": ("not Flutter yet", "com.americangroupllc.apexmarketwatch"),
        "BuddyPlay": ("native Swift + Kotlin — port pending",
                      "com.americangroupllc.buddyplay"),
        "MyCard": ("native Swift + Kotlin + TS — port pending",
                   "com.americangroupllc.mycard"),
        "PlantPulse": ("not Flutter yet", "com.americangroupllc.plantpulse"),
    }
    # Repos that live outside AmericanGroupLLC. Kinnav was here until
    # 2026-09-24, when it was transferred back into the org - verified by
    # `gh repo list AmericanGroupLLC`, which is authoritative;
    # `gh api repos/<org>/<name>` is not, because it follows redirects.
    moved_out: dict[str, str] = {}

    defaults = _default_branches()
    apps = []
    for r in sorted((x for x in rows if x.get("flutter")), key=lambda x: x["repo"].lower()):
        lanes = r.get("fastlane_lanes") or []
        apps.append({
            "repo": r["repo"],
            "url": f"https://github.com/{ORG}/{r['repo']}.git",
            "branch": defaults.get(r["repo"]) or r.get("git_branch") or "main",
            # Eleven apps keep the Flutter project in a subdirectory; every
            # Flutter and Fastlane command has to run from here.
            "dir": r.get("app_dir", "."),
            "application_id": r.get("application_id", ""),
            "bundle_id": r.get("ios_bundle_id", ""),
            "version": r.get("version", ""),
            # What delivery can actually attempt today.
            "deliverable": {
                "android": bool(r.get("release_signing")) and "beta" in lanes,
                "ios": "beta" in lanes,
            },
            # Whether this app should reach a public store at all. Editorial,
            # not technical: an app whose store JSON still carries `_blocked`
            # has been judged unpublishable, and every store script skips it.
            # Nothing is blocked today. portfolio-board was, as AGL's own
            # delivery tracker, but its store JSON now carries
            # `_was_blocked_resolved` rather than `_blocked`, so the portfolio
            # is 43 apps and not 42.
            "store_eligible": store_eligible(r["repo"]),
            "ads": bool(r.get("dep_google_mobile_ads")),
            "platforms": {
                "android": bool(r.get("platform_android")),
                "ios": bool(r.get("platform_ios")),
            },
            "auth": {
                "providers": r.get("auth_providers", []),
                "login_screen": bool(r.get("has_login_screen")),
                "account_optional": bool(r.get("account_optional")),
            },
            # The application ids are what the binary declares; the unit ids
            # come from the console record. A build only serves the live units
            # when they are passed at build time.
            "admob": {
                "integrated": bool(r.get("dep_google_mobile_ads")),
                "android_app_id": r.get("android_admob_id", ""),
                "ios_app_id": r.get("ios_admob_id", ""),
                **{k: v for k, v in _admob(r["repo"]).items()
                   if k in ("android_banner", "android_interstitial",
                            "ios_banner", "ios_interstitial")},
            },
            "needs_private_packages": bool(
                r.get("dep_agl_i18n") or r.get("dep_agl_observability") or r.get("dep_agl_ads")
            ),
            # What is still missing per app, so the manifest can render a
            # pending table without reaching back into this repository.
            "pending": {
                "firebase_android": not r.get("firebase_android_config"),
                "firebase_ios": not r.get("firebase_ios_config"),
                "admob_android_id": bool(r.get("dep_google_mobile_ads"))
                and not r.get("android_admob_id"),
                "admob_ios_id": bool(r.get("dep_google_mobile_ads"))
                and not r.get("ios_admob_id"),
                "store_description": not _has_description(r["repo"]),
            },
        })

    # Skip any repo the audit has already emitted as a Flutter app. This list is
    # hand-maintained, and every entry in it eventually gets ported — at which
    # point leaving it here silently produces a second entry for the same app.
    # That is exactly what happened: apps.json grew to 49 entries for 43 apps and
    # the status tables reported "48 apps" for an org that has 42.
    already = {a["repo"] for a in apps}
    for repo, (why, package) in sorted(not_flutter.items(), key=lambda kv: kv[0].lower()):
        if repo in already:
            continue
        apps.append({
            "repo": repo,
            "url": f"https://github.com/{ORG}/{repo}.git",
            "branch": "main",
            "dir": ".",
            "flutter": False,
            "status": why,
            # Reserved, not yet in a build. Marked so a table can say so.
            "application_id": package,
            "bundle_id": package,
            "package_reserved": True,
            "version": "",
            "deliverable": {"android": False, "ios": False},
            "store_eligible": False,
            "ads": False,
            "needs_private_packages": False,
            "platforms": {"android": False, "ios": False},
            "auth": {"providers": [], "login_screen": False, "account_optional": False},
            "admob": {"integrated": False, "android_app_id": "", "ios_app_id": ""},
            "pending": {
                "firebase_android": True, "firebase_ios": True,
                "admob_android_id": False, "admob_ios_id": False,
                "store_description": True,
            },
        })

    for app in apps:
        app.setdefault("flutter", True)
        if app["repo"] in moved_out:
            app["status"] = moved_out[app["repo"]]
            app["in_org"] = False
        else:
            app["in_org"] = app["repo"] not in moved_out

    manifest = {
        "_comment": (
            "Generated by scripts/generate_manifest.py "
            "from docs/release-readiness.json. Do not edit by hand — re-run the "
            "audit and regenerate."
        ),
        "org": ORG,
        "flutter_version": "3.44.2",
        "apps": apps,
    }
    # Refuse to write a manifest that lists an app twice. Everything downstream
    # counts these rows, so a duplicate does not fail loudly — it just inflates
    # every total in STATUS.md and status.csv, which is harder to notice and
    # harder to trust once noticed.
    seen: dict[str, int] = {}
    for a in apps:
        seen[a["repo"]] = seen.get(a["repo"], 0) + 1
    dupes = sorted(r for r, n in seen.items() if n > 1)
    if dupes:
        raise SystemExit(f"refusing to write: duplicated repos {', '.join(dupes)}")

    out = pathlib.Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(apps)} apps → {out}")


if __name__ == "__main__":
    main()
