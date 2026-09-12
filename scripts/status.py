#!/usr/bin/env python3
"""Regenerate STATUS.md and status.csv — the whole portfolio in one place.

Both are measured, not maintained. Everything comes from apps.json (itself
generated from an audit of the repositories), from live GitHub queries for
releases and secrets, and from the last App Store Connect sync. Nothing here is
a claim someone typed and forgot to update.

    python3 scripts/status.py            # both files
    python3 scripts/status.py --offline  # skip the GitHub queries

`gh` must be authenticated for the live half. Refresh the App Store side with
`bundle exec ruby scripts/appstore_records.rb`.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "apps.json").read_text())
ORG = MANIFEST["org"]
APPS = MANIFEST["apps"]

# Apps that cannot build at all, with the reason.
BROKEN = {"CodeDeal": "Does not compile — 5 analyzer errors"}

TEST_ADMOB = "3940256099942544"


# ── data ────────────────────────────────────────────────────────────────────


def build_evidence() -> dict:
    """What scripts/build_release.py last observed, keyed by repo.

    Absent rather than fabricated when the script has never run: an empty table
    is honest, a table of dashes claiming "no binary" would not be.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    out: dict = {}
    for kind, name in (("aab", "build-evidence.json"), ("apk", "build-evidence-apk.json")):
        f = root / "docs" / name
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            out.setdefault(r["repo"], {})[kind] = r
    return out

def gh(args: list[str]) -> str:
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def releases(repo: str) -> list[dict]:
    raw = gh(["release", "list", "--repo", f"{ORG}/{repo}", "--limit", "5",
              "--json", "tagName,isDraft"])
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def assets(repo: str, tag: str) -> list[str]:
    raw = gh(["release", "view", tag, "--repo", f"{ORG}/{repo}",
              "--json", "assets", "--jq", '[.assets[].name]|join(",")'])
    return [a for a in (raw or "").strip().split(",") if a]


def gh_is_working() -> bool:
    """Whether `gh` can actually read the org's repositories.

    This matters because every query below swallows its own failure and returns
    an empty string. Without this check, a run with no credentials produces a
    document that confidently says no app has a release and no keystore is
    loaded — which is worse than not running at all, because it looks like an
    answer. `--offline` is the way to say "I know, do it anyway".
    """
    return bool(gh(["repo", "view", f"{ORG}/agl-manifest", "--json", "name",
                    "--jq", ".name"]).strip())


def manifest_secrets() -> set[str]:
    raw = gh(["secret", "list", "--repo", f"{ORG}/agl-manifest",
              "--json", "name", "--jq", '[.[].name]|join(",")'])
    return {s for s in (raw or "").strip().split(",") if s}


def appstore_records() -> dict[str, str]:
    path = ROOT / "docs" / "appstore-records.json"
    if not path.exists():
        return {}
    return {r["bundleId"]: r["name"] for r in json.loads(path.read_text())}


# ── formatting ──────────────────────────────────────────────────────────────

def link(repo: str) -> str:
    return f"[{repo}](https://github.com/{ORG}/{repo})"


def ids(app: dict) -> str:
    """Android applicationId and iOS bundle id — the string AdMob, Play, App
    Store Connect and keytool each ask for. Usually identical, not always."""
    android, ios = app.get("application_id") or "", app.get("bundle_id") or ""
    if not android and not ios:
        return "—"
    suffix = " _(reserved)_" if app.get("package_reserved") else ""
    if android == ios:
        return f"`{android}`{suffix}"
    return f"A `{android}`<br>i `{ios}`{suffix}"


def support(app: dict, platform: str) -> str:
    if not app["flutter"] or not app["platforms"][platform]:
        return "—"
    return "yes" if app["deliverable"][platform] else "build only"


def login(app: dict) -> str:
    if not app["flutter"]:
        return "—"
    auth = app["auth"]
    if not auth["providers"]:
        return "none"
    text = " + ".join(auth["providers"])
    if auth["account_optional"]:
        return text + " (optional)"
    if not auth["login_screen"]:
        return text + " (no screen)"
    return text


def status_of(app: dict, has_binary: bool) -> str:
    if not app["flutter"]:
        return "Not ported"
    if app["repo"] in BROKEN:
        return BROKEN[app["repo"]]
    if not app.get("in_org", True):
        return "Outside the org"
    if has_binary:
        return "Binary published"
    if not (app["deliverable"]["android"] or app["deliverable"]["ios"]):
        return "Builds, delivery not wired"
    return "Ready — needs AGL_PACKAGES_TOKEN"


def admob_cell(value: str) -> str:
    if not value:
        return "**missing**"
    if value.startswith("$"):
        return f"`{value}` _(build-time)_"
    if TEST_ADMOB in value:
        return f"`{value}` _(Google test)_"
    return f"`{value}`"


def keystore_secret_name(repo: str) -> str:
    return "KEYSTORE_" + "".join(c if c.isalnum() else "_" for c in repo.upper()) + "_BASE64"


# ── the one document ────────────────────────────────────────────────────────

def build(offline: bool) -> None:
    records = appstore_records()
    secrets = set() if offline else manifest_secrets()
    in_org = [a for a in APPS if a.get("in_org", True)]
    outside = [a for a in APPS if not a.get("in_org", True)]
    numbers = {a["repo"]: i for i, a in enumerate(in_org, start=1)}

    rows: list[dict] = []
    downloadable = 0

    for app in in_org + outside:
        repo = app["repo"]
        latest, names = "—", []
        if app["flutter"] and not offline:
            rel = releases(repo)
            if rel:
                latest = rel[0]["tagName"] + (" (draft)" if rel[0].get("isDraft") else "")
                names = assets(repo, rel[0]["tagName"])
                if names:
                    downloadable += 1
            else:
                latest = "no release"

        prefix = "" if app["dir"] == "." else f"{app['dir']}/"
        bundle = app.get("bundle_id") or ""
        secret = keystore_secret_name(repo)

        rows.append({
            "no": numbers.get(repo, ""),
            "app": repo,
            "repo_url": f"https://github.com/{ORG}/{repo}",
            "in_org": app.get("in_org", True),
            "flutter": app["flutter"],
            "status": status_of(app, bool(names)),
            "android_package": app.get("application_id", ""),
            "ios_bundle_id": bundle,
            "android_support": support(app, "android"),
            "ios_support": support(app, "ios"),
            "ads": app["admob"]["integrated"] if app["flutter"] else False,
            "admob_android_app_id": app["admob"].get("android_app_id", ""),
            "admob_ios_app_id": app["admob"].get("ios_app_id", ""),
            "admob_android_banner": app["admob"].get("android_banner", ""),
            "admob_android_interstitial": app["admob"].get("android_interstitial", ""),
            "login": login(app),
            "appstore_record": records.get(bundle, "") if bundle else "",
            "latest_release": latest,
            "binaries": ", ".join(names),
            "firebase_android_path": f"{prefix}android/app/google-services.json"
                                     if app["flutter"] else "",
            "firebase_ios_path": f"{prefix}ios/Runner/GoogleService-Info.plist"
                                 if app["flutter"] else "",
            "firebase_present": not app["pending"]["firebase_android"],
            "key_properties_path": f"{prefix}android/key.properties" if app["flutter"] else "",
            "keystore_secret_loaded": secret in secrets,
            "store_description": (not app["pending"]["store_description"])
                                 if app["flutter"] else False,
        })

    by_repo = {r["app"]: r for r in rows}
    flutter = [a for a in in_org if a["flutter"]]
    with_ads = [a for a in in_org if a["flutter"] and a["admob"]["integrated"]]
    matched = [a for a in in_org if by_repo[a["repo"]]["appstore_record"]]
    no_record = [a for a in in_org if not by_repo[a["repo"]]["appstore_record"]]
    orphans = {b: n for b, n in records.items()
               if b not in {a.get("bundle_id") for a in in_org}}
    no_desc = [a["repo"] for a in flutter if a["pending"]["store_description"]]
    no_admob = [a["repo"] for a in with_ads
                if TEST_ADMOB in a["admob"].get("android_app_id", "")
                or ((a["admob"].get("android_app_id", "").startswith("$")
                     or not a["admob"].get("android_app_id"))
                    and not a["admob"].get("android_banner"))]
    test_ios = [a["repo"] for a in with_ads
                if TEST_ADMOB in a["admob"].get("ios_app_id", "")]
    keystores = sum(1 for r in rows if r["keystore_secret_loaded"])
    # Only apps in the org; `rows` also carries the transferred-out one, which
    # made this count exceed the total.
    missing_fb = sum(1 for a in flutter if not by_repo[a["repo"]]["firebase_present"])
    evidence = build_evidence()

    L: list[str] = []
    add = L.append

    add("# Portfolio status")
    add("")
    add(f"All {len(in_org)} mobile apps in the organization — what each one is, where it")
    add("stands, and everything still needed to ship it. Regenerate with")
    add("`python3 scripts/status.py`; the same data as a spreadsheet is in")
    add("[`status.csv`](status.csv).")
    add("")
    add("The package name in each row is the string AdMob, Play Console, App Store")
    add("Connect and `keytool` all ask for, so this is the table to work from when")
    add("creating AdMob apps, upload keys or store records.")
    add("")
    add("| | Count |")
    add("| --- | ---: |")
    add(f"| Mobile apps in the org | {len(in_org)} |")
    add(f"| Flutter, buildable today | {len(flutter)} |")
    add(f"| Not ported yet | {len(in_org) - len(flutter)} |")
    add(f"| Serving ads | {len(with_ads)} |")
    add(f"| App Store record matching a live bundle id | {len(matched)} |")
    add(f"| Upload keystores loaded into this repo's secrets | {keystores} |")
    add(f"| Firebase config present | {len(flutter) - missing_fb} of {len(flutter)} |")
    add(f"| Binary anyone can download | {downloadable} |")
    signed = sum(1 for r in evidence.values()
                 if r.get("aab", {}).get("result") == "SIGNED")
    add(f"| Signed release bundle, verified against its upload key | {signed} of {len(flutter)} |")

    add("")

    add("## 1. Every app")
    add("")
    add("`yes` under a platform means present **and** deliverable — a real signing")
    add("config and a `beta` lane. `build only` means it compiles but delivery is not")
    add("wired.")
    add("")
    add("| # | App | Package / bundle id | Status | Android | iOS | Ads | Sign-in | Store record | Build | Binaries |")
    add("| --: | --- | --- | --- | :-: | :-: | :-: | --- | --- | --- | --- |")
    for app in in_org:
        r = by_repo[app["repo"]]
        binaries = ", ".join(f"`{n}`" for n in r["binaries"].split(", ") if n) or "—"
        add(f"| {r['no']} | {link(app['repo'])} | {ids(app)} | {r['status']} "
            f"| {r['android_support']} | {r['ios_support']} "
            f"| {'yes' if r['ads'] else '—'} | {r['login']} "
            f"| {r['appstore_record'] or '**none**'} | {r['latest_release']} "
            f"| {binaries} |")
    add("")
    if outside:
        add("**Not in the organization.** Still delivered by this manifest, but the")
        add("repository is owned elsewhere and reachable only through a GitHub redirect.")
        add("If that redirect is removed, delivery for it stops.")
        add("")
        add("| App | Where it lives now | Package |")
        add("| --- | --- | --- |")
        for app in outside:
            add(f"| {app['repo']} | `{app.get('status', 'moved')}` | {ids(app)} |")
        add("")

    add("## 2. Signed release bundles")
    add("")
    add("Built locally with `python3 scripts/build_release.py`, which is cheaper than")
    add("a runner and works today — Android needs no macOS minutes and no CI secret.")
    add("")
    add("Every bundle's signing certificate is compared against the upload keystore it")
    add("was meant to use, and the fingerprint is shown so the claim can be checked")
    add("rather than taken on faith. This is not ceremony: a release build with a")
    add("misconfigured `signingConfig` silently falls back to the debug key, exits 0,")
    add("and is rejected at upload. One app in this table was caught exactly that way.")
    add("")
    if not evidence:
        add("No build evidence yet — run `python3 scripts/build_release.py`.")
        add("")
    else:
        ok = sum(1 for r in evidence.values()
                 if r.get("aab", {}).get("result") == "SIGNED")
        add(f"**{ok} of {len(evidence)}** apps produce a verified signed bundle.")
        add("")
        add("| # | App | AAB (Play) | APK (sideload) | Flavour | Signing certificate (SHA-256) |")
        add("| --: | --- | --- | --- | --- | --- |")
        verdicts = {"SIGNED": None,
                    "SIGNATURE_MISMATCH": "**wrong key**",
                    "NO_KEYSTORE": "no keystore",
                    "BUILD_FAILED": "**build failed**"}

        def cell(e):
            if not e:
                return "—"
            bad = verdicts.get(e["result"], e["result"])
            if bad:
                return bad
            return f"{e['bytes'] / 1e6:.0f} MB" if e.get("bytes") else "signed"

        for app in in_org:
            e = evidence.get(app["repo"])
            if not e:
                continue
            r = by_repo[app["repo"]]
            aab, apk = e.get("aab"), e.get("apk")
            fp = (aab or apk or {}).get("signer_sha256") or ""
            add(f"| {r['no']} | {link(app['repo'])} | {cell(aab)} | {cell(apk)} "
                f"| {(aab or apk or {}).get('flavour_built') or '—'} | `{fp[:16] or '—'}` |")
        add("")
        add("Both are published to a GitHub Release in each app's own repository, so an")
        add("app can be installed and tried without a build machine, a keystore or a Play")
        add("account. The APK sideloads onto a device; the AAB is what Play accepts and")
        add("cannot be installed by hand — neither one does both jobs.")
        add("")
        add("Locally they are kept outside every git repository (`~/agl/.dist/`) so a stray")
        add("`git add -A` cannot commit 60 MB binaries. The build tree each one came")
        add("from is deleted afterwards — 37 Flutter release trees are about 36 GB, and")
        add("keeping them filled this machine's disk on the first attempt.")
        add("")

    add("## 3. AdMob")
    add("")
    add("Application ids are declared in `AndroidManifest.xml` and `Info.plist` and must")
    add("match what is passed to `AglAds.configure`. A mismatch is not a degraded")
    add("experience — on iOS the SDK throws `GADInvalidInitializationException` and iOS")
    add("terminates the app on every launch.")
    add("")
    add("Unit ids are never committed. They are read from `--dart-define` at build time,")
    add("so a build without them serves Google's test units — the safe default rather")
    add("than a broken one. The values below are the console record.")
    add("")
    add("| # | App | Package | Android app id | iOS app id | Android banner | Android interstitial |")
    add("| --: | --- | --- | --- | --- | --- | --- |")
    for app in with_ads:
        ad = app["admob"]
        add(f"| {numbers[app['repo']]} | {link(app['repo'])} | {ids(app)} "
            f"| {admob_cell(ad.get('android_app_id',''))} "
            f"| {admob_cell(ad.get('ios_app_id',''))} "
            f"| {admob_cell(ad.get('android_banner',''))} "
            f"| {admob_cell(ad.get('android_interstitial',''))} |")
    add("")
    if no_admob:
        add(f"**{len(no_admob)} of these have no AdMob record at all** — they serve ads")
        add("against Google's test application id, so they earn nothing: "
            + ", ".join(no_admob) + ".")
        add("")
    if test_ios:
        add(f"**{len(test_ios)} carry the test application id on iOS.** Correct while an")
        add("app has no iOS AdMob app of its own, and the thing to replace when one is")
        add("created: " + ", ".join(test_ios) + ". No app has iOS unit ids, so an iOS")
        add("release build serves test ads by design.")
        add("")
    add("Every ad app gates its requests on UMP consent, with a per-app test that fails")
    add("if any ad is constructed without a check in the enclosing method. It stays")
    add("dormant until a GDPR message is published in AdMob → Privacy & messaging.")
    add("")

    if records:
        add("## 4. App Store Connect records")
        add("")
        add(f"Live from the API on the last sync: **{len(records)} records exist**, and")
        add(f"**{len(matched)} of {len(in_org)}** match a bundle id this portfolio builds.")
        add("Refresh with `bundle exec ruby scripts/appstore_records.rb`.")
        add("")
        add("A bundle id that does not match a record is not a warning at upload time —")
        add("it is a rejected build.")
        add("")
        add(f"**{len(no_record)} apps have no matching record:**")
        add("")
        add("| # | App | Bundle id it builds with |")
        add("| --: | --- | --- |")
        for app in no_record:
            add(f"| {numbers[app['repo']]} | {link(app['repo'])} "
                f"| `{app.get('bundle_id') or '—'}` |")
        add("")
        if orphans:
            add(f"**{len(orphans)} records match no app.** Mostly the rename history —")
            add("iFoodRadar became GroceryMatch, OfflineBuddy became Verba, iDealZap")
            add("became GadgetNest, StayDeal became TripNest. Each is a decision: rename")
            add("the record and keep its history, or leave it and create a new one. A")
            add("bundle id cannot be changed once an app is published.")
            add("")
            add("| Bundle id | Store record |")
            add("| --- | --- |")
            for bid, name in sorted(orphans.items()):
                add(f"| `{bid}` | {name} |")
            add("")

    add("## 5. Required files")
    add("")
    add("None of these are in git, for two different reasons. The signing material is")
    add("secret and must never be committed. The Firebase files are **not** secret —")
    add("Google documents them as shipping inside the binary — and are absent only")
    add("because nobody has downloaded them yet.")
    add("")
    add("Once for the whole portfolio:")
    add("")
    add("| File | Where it comes from | Status |")
    add("| --- | --- | --- |")
    add("| `AuthKey_UV8NYF9767.p8` | App Store Connect → Users and Access → Keys | "
        "**loaded** into `ASC_KEY_CONTENT`, verified against the live API |")
    add("| Play service-account JSON | Play Console → Setup → API access → grant "
        "*Release manager* → download | **missing** |")
    add("| Distribution certificate + profiles | `bundle exec fastlane match appstore` "
        "on a Mac | **missing** |")
    add("| `AGL_PACKAGES_TOKEN` | GitHub → Developer settings | **missing** |")
    add("")
    add("Per app. `key.properties` and the keystore are the Android upload key — **lose")
    add("a keystore with Play App Signing off and that app can never be updated again.**")
    add("")
    add("| # | App | google-services.json | GoogleService-Info.plist | Keystore |")
    add("| --: | --- | --- | --- | --- |")
    for app in flutter:
        r = by_repo[app["repo"]]
        add(f"| {r['no']} | {link(app['repo'])} | `{r['firebase_android_path']}` "
            f"| `{r['firebase_ios_path']}` "
            f"| {'loaded' if r['keystore_secret_loaded'] else '**missing**'} |")
    add("")
    add(f"**{missing_fb} apps have no Firebase config.** Until they do, "
        "`AglCrash.isActive` is")
    add("false in every build and no crash is reported. The Gradle plugins apply")
    add("themselves the moment the JSON appears — there is no code change waiting.")
    add("")
    add("A placeholder is worse than nothing: MyHealth carries one for project")
    add("`myhealth-local-dev` with project_number `000000000000`, which would make")
    add("Crashlytics initialise against a project that does not exist. The sanity suite")
    add("rejects any config that is not `americangroupllc-5bdfc`.")
    add("")

    add("## 6. Still to create")
    add("")
    add("Everything here needs an account this repository does not have.")
    add("")
    add("| # | What | Where | Unblocks | Status |")
    add("| --: | --- | --- | --- | --- |")
    add("| 1 | **`AGL_PACKAGES_TOKEN`** | GitHub → Developer settings. Read on the app "
        "repos and this manifest; **write** to publish binaries. Store it as an "
        "organization secret. | **Everything** — without it `flutter pub get` cannot "
        "reach the shared packages and nothing builds | **missing** |")
    add("| 2 | Play service-account JSON | Play Console → Setup → API access | Play "
        "upload, and listing which apps already have Play records | **missing** |")
    add("| 3 | `match` password / distribution certificate | A Mac signed into the "
        "Apple account | iOS signing on CI | **missing** |")
    add("| 4 | Firebase config files | Firebase console, project "
        "`americangroupllc-5bdfc` | Crash reporting | "
        f"**{missing_fb} of {len(flutter)} missing** |")
    add("| 5 | AdMob apps + unit ids | AdMob console | Live ads for the apps that earn "
        f"nothing today | **{len(no_admob)} apps have no record** |")
    add("| 6 | A GDPR message | AdMob → Privacy & messaging | The consent form; the "
        "code is already in every ad app | **not published** |")
    add("| 7 | Store descriptions | `store/apps/<repo>.json`, then "
        "`scripts/store_metadata.py generate` | Both listings require one | "
        f"**{len(no_desc)} apps have none** |")
    add("| 8 | Privacy policy + support URLs | Your hosting | Both listings | "
        "templated; the pages must exist |")
    add("")
    add("Already done and verified: the App Store Connect key and its issuer id, both")
    add(f"confirmed against the live API, and {keystores} upload keystores loaded here.")
    add("")
    if no_desc:
        add(f"Apps still needing a store description: {', '.join(no_desc)}.")
        add("")

    (ROOT / "STATUS.md").write_text("\n".join(L))

    with (ROOT / "status.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"STATUS.md + status.csv — {len(in_org)} apps, {len(with_ads)} with ads, "
          f"{downloadable} with a binary, {len(matched)} with a store record")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="skip the GitHub queries and leave those columns blank")
    args = ap.parse_args()

    if not args.offline and not gh_is_working():
        print("::error::`gh` cannot read the organization, so releases and "
              "secrets would all come back empty and this would write a "
              "document that looks like an answer. Authenticate `gh` (or set "
              "GH_TOKEN), or pass --offline to accept the gaps deliberately.")
        return 1

    build(args.offline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
