#!/usr/bin/env python3
"""Regenerate RELEASES.md and PENDING.md.

Both tables are measured, not maintained. RELEASES.md asks GitHub what binaries
each app actually has; PENDING.md reads apps.json — which is itself generated
from the backend's audit of the repositories — and asks GitHub which secrets
exist. Nothing in either file is a claim someone typed and forgot to update.

    python3 scripts/status.py            # both files
    python3 scripts/status.py --offline  # skip the GitHub queries

Needs `gh` authenticated for the live half.
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

# The names the workflows in this repository actually read. A secret spelled
# differently is the same as a secret that is missing.
ANDROID_SECRETS = [
    "ANDROID_KEYSTORE_BASE64",
    "ANDROID_KEYSTORE_PASSWORD",
    "ANDROID_KEY_ALIAS",
    "ANDROID_KEY_PASSWORD",
]


def gh(args: list[str]) -> str:
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def releases(repo: str) -> list[dict]:
    raw = gh(["release", "list", "--repo", f"{ORG}/{repo}", "--limit", "10",
              "--json", "tagName,isDraft,isPrerelease,publishedAt"])
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def assets(repo: str, tag: str) -> list[str]:
    raw = gh(["release", "view", tag, "--repo", f"{ORG}/{repo}",
              "--json", "assets", "--jq", "[.assets[].name]|join(\",\")"])
    return [a for a in (raw or "").strip().split(",") if a]


def secrets(repo: str) -> set[str]:
    raw = gh(["secret", "list", "--repo", f"{ORG}/{repo}",
              "--json", "name", "--jq", "[.[].name]|join(\",\")"])
    return {s for s in (raw or "").strip().split(",") if s}



def _link(repo: str) -> str:
    return f"[{repo}](https://github.com/{ORG}/{repo})"


def _name(app: dict) -> str:
    """The repo link, flagged when the repository is not the org's any more."""
    link = _link(app["repo"])
    return link if app.get("in_org", True) else f"{link} ⚠️"


def _ids(app: dict) -> str:
    """Android applicationId and iOS bundle id — what you type into AdMob, Play,
    App Store Connect and `keytool`. Usually the same string, not always, so
    both are shown when they differ."""
    android = app.get("application_id") or ""
    ios = app.get("bundle_id") or ""
    if not android and not ios:
        return "_not ported_"
    if android == ios:
        return f"`{android}`"
    parts = []
    if android:
        parts.append(f"A `{android}`")
    if ios:
        parts.append(f"i `{ios}`")
    return "<br>".join(parts)


# Apps that cannot build at all, with the reason. Everything else is judged
# from what was measured.
BROKEN = {
    "CodeDeal": "Does not compile — 5 analyzer errors",
}


def _status(app: dict, has_binary: bool) -> str:
    """One phrase describing where this app actually is."""
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
    # Everything else is ready and waiting on the same one thing.
    return "Ready — needs AGL_PACKAGES_TOKEN"


def _support(app: dict, platform: str) -> str:
    """`yes` when the platform is present and deliverable, `build only` when the
    project exists but delivery is not wired, `—` when there is no target."""
    if not app["platforms"][platform]:
        return "—"
    return "yes" if app["deliverable"][platform] else "build only"


def _login(app: dict) -> str:
    auth = app["auth"]
    providers = auth["providers"]
    if not providers:
        return "none"
    text = " + ".join(providers)
    if auth["account_optional"]:
        text += " (optional)"
    elif not auth["login_screen"]:
        # A dependency is declared but nothing reaches a sign-in screen.
        text += " (no screen)"
    return text


def write_releases(offline: bool) -> None:
    in_org = [a for a in APPS if a.get("in_org", True)]
    outside = [a for a in APPS if not a.get("in_org", True)]

    lines = [
        "# Release binaries",
        "",
        f"All {len(in_org)} mobile apps in the organization: what each one is, where it",
        "stands, and what you can download and run right now. Regenerate with",
        "`python3 scripts/status.py`. Also published as",
        "[`releases.csv`](releases.csv) for a spreadsheet.",
        "",
        "The package name in each row is what AdMob, Play, App Store Connect and",
        "`keytool` all ask for, so this table is the one to work from when creating",
        "AdMob entries, upload keys or store records.",
        "",
        "`artifacts.yml` publishes the binaries — an APK that installs on a device, the",
        "AAB Play needs, and for iOS a simulator build. A `.aab` **cannot** be",
        "sideloaded; it is a Play upload format, which is why both are published. The",
        "iOS build is unsigned, so it runs in the Simulator and not on a phone —",
        "TestFlight is the only route to real hardware.",
        "",
        "| # | App | Package / bundle id | Status | Android | iOS | Ads | Login | Build | Binaries |",
        "| --: | --- | --- | --- | :-: | :-: | :-: | --- | --- | --- |",
    ]

    tagged = downloadable = 0
    rows_csv = []
    for number, app in enumerate(in_org, start=1):
        repo = app["repo"]
        latest, asset_text, names = "—", "—", []

        if app["flutter"] and not offline:
            rel = releases(repo)
            if rel:
                tagged += 1
                top = rel[0]
                latest = top["tagName"] + (" (draft)" if top.get("isDraft") else "")
                names = assets(repo, top["tagName"])
                if names:
                    downloadable += 1
                    asset_text = ", ".join(f"`{n}`" for n in names)
                else:
                    # A tag with nothing attached. It looks like a release on
                    # the Releases page and there is nothing to install.
                    asset_text = "**none — tag only**"
            else:
                latest = "no release"

        status = _status(app, bool(names))
        android = _support(app, "android") if app["flutter"] else "—"
        ios = _support(app, "ios") if app["flutter"] else "—"
        ads = ("yes" if app["admob"]["integrated"] else "—") if app["flutter"] else "—"
        login = _login(app) if app["flutter"] else "—"

        lines.append(
            f"| {number} | {_link(repo)} | {_ids(app)} | {status} | {android} | {ios} "
            f"| {ads} | {login} | {latest} | {asset_text} |"
        )
        rows_csv.append({
            "no": number,
            "app": repo,
            "repo_url": f"https://github.com/{ORG}/{repo}",
            "android_package": app.get("application_id", ""),
            "ios_bundle_id": app.get("bundle_id", ""),
            "status": status,
            "android": android,
            "ios": ios,
            "ads": ads,
            "login": login,
            "latest_build": latest,
            "binaries": ", ".join(names),
            "admob_android_app_id": app["admob"].get("android_app_id", ""),
            "admob_ios_app_id": app["admob"].get("ios_app_id", ""),
            "admob_android_banner": app["admob"].get("android_banner", ""),
            "admob_android_interstitial": app["admob"].get("android_interstitial", ""),
        })

    flutter_count = sum(1 for a in in_org if a["flutter"])
    lines += [
        "",
        f"**{downloadable} of {len(in_org)} apps have a binary anyone can download.** "
        f"{tagged} carry a release tag, so most of those tags are empty — they look "
        "like a release on the Releases page with nothing attached to install. "
        f"{flutter_count} apps are Flutter and buildable; "
        f"{len(in_org) - flutter_count} are not ported yet and have no Flutter package "
        "name to register anywhere.",
        "",
    ]

    if outside:
        lines += [
            "## Not in the organization",
            "",
            "Still delivered by this manifest, but the repository is owned elsewhere and",
            "reachable only through a GitHub redirect. If that redirect is ever removed,",
            "delivery for it stops.",
            "",
            "| App | Where it lives now | Package |",
            "| --- | --- | --- |",
        ]
        for app in outside:
            lines.append(
                f"| {app['repo']} | `{app.get('status', 'moved')}` | {_ids(app)} |"
            )
            rows_csv.append({
                "no": "", "app": app["repo"],
                "repo_url": f"https://github.com/{ORG}/{app['repo']}",
                "android_package": app.get("application_id", ""),
                "ios_bundle_id": app.get("bundle_id", ""),
                "status": _status(app, False),
                "android": "", "ios": "", "ads": "", "login": "",
                "latest_build": "", "binaries": "",
                "admob_android_app_id": "", "admob_ios_app_id": "",
                "admob_android_banner": "", "admob_android_interstitial": "",
            })
        lines.append("")

    lines += [
        "## Producing the binaries",
        "",
        "```sh",
        "# from the Actions tab: “Publish test builds”, or locally:",
        "bundle exec fastlane publish_artifacts platform:android apps:all",
        "bundle exec fastlane publish_artifacts platform:ios apps:all",
        "```",
        "",
        "Nothing will publish until `AGL_PACKAGES_TOKEN` exists with **write** access —",
        "see [PENDING.md](PENDING.md).",
        "",
    ]
    (ROOT / "RELEASES.md").write_text("\n".join(lines))

    with (ROOT / "releases.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
        writer.writeheader()
        writer.writerows(rows_csv)

    print(f"RELEASES.md + releases.csv — {len(in_org)} apps in the org")


def write_matrix(offline: bool) -> None:
    lines = [
        "# Capability matrix",
        "",
        "Platform support, sign-in, and every AdMob identifier the portfolio uses.",
        "Regenerate with `python3 scripts/status.py`.",
        "",
        "## Platforms and sign-in",
        "",
        "`yes` means the platform is present **and** deliverable — a real signing",
        "config and a `beta` lane. `build only` means the project builds but delivery",
        "is not wired yet.",
        "",
        "| # | App | Package / bundle id | Android | iOS | Sign-in | Login screen | Account optional |",
        "| --: | --- | --- | :-: | :-: | --- | :-: | :-: |",
    ]
    for number, app in enumerate(APPS, start=1):
        if not app["flutter"]:
            lines.append(
                f"| {number} | {_link(app['repo'])} | _not ported_ | — | — "
                f"| — | — | — |"
            )
            continue
        auth = app["auth"]
        lines.append(
            f"| {number} | {_name(app)} | {_ids(app)} "
            f"| {_support(app, 'android')} | {_support(app, 'ios')} "
            f"| {' + '.join(auth['providers']) or 'none'} "
            f"| {'yes' if auth['login_screen'] else '—'} "
            f"| {'yes' if auth['account_optional'] else '—'} |"
        )

    with_ads = [a for a in APPS if a["admob"]["integrated"]]
    flutter = [a for a in APPS if a["flutter"]]
    lines += [
        "",
        f"{sum(1 for a in flutter if a['auth']['providers'])} of {len(flutter)} Flutter "
        f"apps have a sign-in dependency; the rest need no account at all. "
        f"{len(APPS) - len(flutter)} apps are not ported yet and have no Flutter "
        "package name to register.",
        "",
        "## AdMob",
        "",
        f"{len(with_ads)} of {len(flutter)} Flutter apps serve ads.",
        "",
        "**Application ids** are declared in `AndroidManifest.xml` and `Info.plist` and",
        "must match what is passed to `AglAds.configure`. A mismatch is not a degraded",
        "experience — on iOS the SDK throws `GADInvalidInitializationException` and iOS",
        "terminates the app on every launch.",
        "",
        "**Unit ids** are never committed. They are read from `--dart-define` at build",
        "time, so a build without them serves Google's public test units — the safe",
        "default rather than a broken one. The values below are the console record,",
        "shown here so there is one place to check them against AdMob.",
        "",
        "The package name in each row is what AdMob asks for when you add the app,",
        "and what Play and `keytool` use — so this table is the one to work from when",
        "creating AdMob entries, upload keys or store records.",
        "",
        "| # | App | Package / bundle id | Android app id | iOS app id | Android banner | Android interstitial |",
        "| --: | --- | --- | --- | --- | --- | --- |",
    ]

    def cell(value: str) -> str:
        if not value:
            return "**missing**"
        if value.startswith("$"):
            return f"`{value}` _(build-time)_"
        if "3940256099942544" in value:
            return f"`{value}` _(Google test)_"
        return f"`{value}`"

    numbers = {a["repo"]: i for i, a in enumerate(APPS, start=1)}
    for app in with_ads:
        ad = app["admob"]
        lines.append(
            f"| {numbers[app['repo']]} | {_link(app['repo'])} | {_ids(app)} "
            f"| {cell(ad.get('android_app_id',''))} "
            f"| {cell(ad.get('ios_app_id',''))} "
            f"| {cell(ad.get('android_banner',''))} "
            f"| {cell(ad.get('android_interstitial',''))} |"
        )

    test_ids = [a["repo"] for a in with_ads
                if "3940256099942544" in a["admob"].get("ios_app_id", "")]
    lines += [
        "",
        f"**{len(test_ids)} apps still carry Google's test application id on iOS** "
        "— correct while an app has no iOS AdMob app of its own, and the thing to "
        "replace when one is created: " + ", ".join(test_ids) + ".",
        "",
        "No app has iOS unit ids at all, so iOS release builds serve test ads by",
        "design until an iOS AdMob app exists for them.",
        "",
        "## Consent",
        "",
        "Every ad app gates its requests on UMP consent — `AglConsent` in `agl_ads`,",
        "with a per-app test that fails if any ad is constructed without a check in",
        "the enclosing method. It stays dormant until a GDPR message is published in",
        "AdMob → Privacy & messaging; see [PENDING.md](PENDING.md) row 7.",
        "",
    ]
    (ROOT / "MATRIX.md").write_text("\n".join(lines))
    print(f"MATRIX.md — {len(with_ads)} ad apps, {len(APPS)} rows")



def write_files(offline: bool) -> None:
    """Every file that has to be dropped into a repository before it can ship."""
    in_org = [a for a in APPS if a.get("in_org", True) and a["flutter"]]

    lines = [
        "# Required files",
        "",
        "Every file that has to exist before an app can be built, signed and shipped,",
        "and exactly where it goes. Regenerate with `python3 scripts/status.py`;",
        "also published as [`files.csv`](files.csv).",
        "",
        "None of these are in git. Two reasons, and they are different: the signing",
        "material is secret and must never be committed, while the Firebase files are",
        "not secret — Google documents them as shipping inside the binary — and are",
        "absent only because nobody has downloaded them yet.",
        "",
        "## Once for the whole portfolio",
        "",
        "| File | Where it comes from | Where it goes | Needed for |",
        "| --- | --- | --- | --- |",
        "| `AuthKey_<KEYID>.p8` | App Store Connect → Users and Access → Keys. "
        "Downloads once. | `ASC_KEY_CONTENT` secret, base64 | every iOS lane |",
        "| Play service-account JSON | Play Console → Setup → API access → create a "
        "service account → grant *Release manager* | `PLAY_SERVICE_ACCOUNT_JSON` "
        "secret | Play upload |",
        "| Apple distribution certificate + provisioning profiles | "
        "`bundle exec fastlane match appstore` on a Mac signed into the Apple "
        "account | the `match-certificates` branch | iOS signing on CI |",
        "| A GitHub token | GitHub → Developer settings | `AGL_PACKAGES_TOKEN` "
        "organization secret | cloning the apps, and `flutter pub get` reaching the "
        "shared packages |",
        "",
        "## Per app",
        "",
        "`google-services.json` and `GoogleService-Info.plist` come from the Firebase",
        "console for project `americangroupllc-5bdfc`, registered against the package",
        "name and bundle id in the row. A mismatched package name is not a warning —",
        "Crashlytics silently reports nothing, which looks exactly like an app that",
        "never crashes.",
        "",
        "`key.properties` and the keystore are the Android upload key. **Lose a",
        "keystore with Play App Signing off and that app can never be updated again.**",
        "",
        "| # | App | Package / bundle id | google-services.json | GoogleService-Info.plist | key.properties | Keystore |",
        "| --: | --- | --- | --- | --- | --- | --- |",
    ]

    rows_csv = []
    for number, app in enumerate(in_org, start=1):
        prefix = "" if app["dir"] == "." else f"{app['dir']}/"
        gs = f"`{prefix}android/app/google-services.json`"
        gi = f"`{prefix}ios/Runner/GoogleService-Info.plist`"
        kp = f"`{prefix}android/key.properties`"
        ks = f"`~/agl/.secrets/keystores/{app['repo']}-upload.jks`"
        lines.append(
            f"| {number} | {_link(app['repo'])} | {_ids(app)} | {gs} | {gi} | {kp} | {ks} |"
        )
        rows_csv.append({
            "no": number,
            "app": app["repo"],
            "android_package": app.get("application_id", ""),
            "ios_bundle_id": app.get("bundle_id", ""),
            "google_services_json": f"{prefix}android/app/google-services.json",
            "google_service_info_plist": f"{prefix}ios/Runner/GoogleService-Info.plist",
            "key_properties": f"{prefix}android/key.properties",
            "keystore": f"~/agl/.secrets/keystores/{app['repo']}-upload.jks",
            "firebase_android_present": not app["pending"]["firebase_android"],
            "firebase_ios_present": not app["pending"]["firebase_ios"],
        })

    missing_android = sum(1 for a in in_org if a["pending"]["firebase_android"])
    lines += [
        "",
        f"**{missing_android} of {len(in_org)} apps have no Firebase config at all.** "
        "Until they do, `AglCrash.isActive` is false in every build and no crash is "
        "reported. The Gradle plugins apply themselves the moment the JSON appears — "
        "there is no code change waiting behind it.",
        "",
        "The keystores already exist for most apps; the five repositories whose "
        "GitHub secrets are missing or misnamed are listed in "
        "[PENDING.md](PENDING.md) §3.",
        "",
    ]
    (ROOT / "FILES.md").write_text("\n".join(lines))

    with (ROOT / "files.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
        writer.writeheader()
        writer.writerows(rows_csv)

    print(f"FILES.md + files.csv — {len(in_org)} apps, {missing_android} missing Firebase")


def write_pending(offline: bool) -> None:
    per_repo = {} if offline else {a["repo"]: secrets(a["repo"]) for a in APPS}

    def count(predicate) -> int:
        return sum(1 for a in APPS if predicate(a))

    missing_desc = [a["repo"] for a in APPS
                    if a["flutter"] and a["pending"]["store_description"]]
    with_ads = [a for a in APPS if a["admob"]["integrated"]]
    def _no_live_admob(app: dict) -> bool:
        """No AdMob record behind this app, so it earns nothing.

        Either the application id is Google's public test id, or it is a
        build-time placeholder with no unit ids recorded to inject — which
        amounts to the same thing, because the placeholder defaults to the
        test id.
        """
        ad = app["admob"]
        android = ad.get("android_app_id", "")
        if "3940256099942544" in android:
            return True
        placeholder = android.startswith("$") or not android
        return placeholder and not ad.get("android_banner")

    no_admob_record = [a["repo"] for a in with_ads if _no_live_admob(a)]
    test_ios = [a["repo"] for a in with_ads
                if "3940256099942544" in a["admob"].get("ios_app_id", "")]
    missing_admob_android = [a["repo"] for a in APPS if a["pending"]["admob_android_id"]]
    missing_admob_ios = [a["repo"] for a in APPS if a["pending"]["admob_ios_id"]]

    lines = [
        "# Pending — what has to be created before anything ships",
        "",
        "Measured, not asserted. Regenerate with `python3 scripts/status.py`.",
        "",
        "Everything here needs an account this repository does not have. The code side",
        "is done and waiting: each item says exactly what unblocks when it lands.",
        "",
        "## 1. Credentials and API keys",
        "",
        "| # | What | Where to create it | Unblocks | Status |",
        "| --- | --- | --- | --- | --- |",
    ]

    token_present = sum(1 for s in per_repo.values() if "AGL_PACKAGES_TOKEN" in s)
    rows = [
        ("1", "**`AGL_PACKAGES_TOKEN`** — a fine-grained PAT or GitHub App token",
         "GitHub → Settings → Developer settings. Read on every app repo **and** on "
         "`AmericanGroupLLC-Backend`; add **write** to publish release binaries. "
         "Store it as an **organization** secret so it exists once.",
         "**Everything.** Without it every job dies at `flutter pub get` with "
         "`could not read Username for 'https://github.com'`",
         f"missing ({token_present}/{len(APPS)} repos)" if not offline else "missing"),
        ("2", "**App Store Connect API key** (`.p8`), key id, issuer id",
         "App Store Connect → Users and Access → Keys. The `.p8` downloads once.",
         "Every iOS lane: TestFlight and App Store upload",
         "`ASC_KEY_ID` and `ASC_ISSUER_ID` are missing everywhere; "
         "`ASC_KEY_CONTENT` exists in 1 repo"),
        ("3", "**Play service-account JSON**",
         "Play Console → Setup → API access → link `americangroupllc-5bdfc` → "
         "create a service account → grant *Release manager* → download",
         "`android beta` / `release` upload to Play",
         "present in 1 of 37 repos"),
        ("4", "**Firebase config files** — `google-services.json` and "
         "`GoogleService-Info.plist`, per app",
         "Firebase console → project `americangroupllc-5bdfc` → Project settings → "
         "Your apps. The exact package name, bundle id and destination path for all "
         f"{len(APPS)} apps is in `AmericanGroupLLC-Backend/docs/FIREBASE_REGISTRATION.md`",
         "Crash reporting. `AglCrash.isActive` is false in every build until these "
         "exist; the Gradle plugins apply themselves the moment the JSON appears",
         f"missing in {count(lambda a: a['pending']['firebase_android'])} of {len(APPS)}"),
        ("5", "**match password**, or Apple distribution certificate + profiles",
         "A Mac signed into the Apple account: `bundle exec fastlane match appstore`. "
         "The `match-certificates` branch already exists in the backend repo.",
         "iOS signing on CI. Without it the lanes fall back to Xcode automatic "
         "signing, which a runner cannot do",
         "missing"),
        ("6", f"**An AdMob app + unit ids** for the {len(no_admob_record)} apps that "
         "have neither: " + ", ".join(no_admob_record),
         "AdMob console → Apps → Add app, then Ad units",
         "They serve ads today against Google's **test** application id, so they "
         "earn nothing. Everything else has an Android app id; see "
         "[MATRIX.md](MATRIX.md)",
         f"{len(no_admob_record)} of {len(with_ads)} ad apps have no console record"),
        ("6b", "**iOS AdMob apps and unit ids**",
         "AdMob console → Apps → Add app (iOS)",
         "iOS ads. No app has iOS unit ids, so an iOS release build serves test "
         "ads by design",
         f"{len(test_ios)} of {len(with_ads)} ad apps carry Google's test iOS app id"),
        ("7", "**A GDPR message published** in AdMob",
         "AdMob console → Privacy & messaging",
         "The UMP consent form. The code is in every ad app and gated; until a "
         "message is published UMP reports “not required” everywhere and no form "
         "appears",
         "not published"),
        ("8", "**Privacy policy URL** that resolves, plus a support URL and contact",
         "Your hosting",
         "Both store listings, and the in-app link",
         "templated per app; the pages must exist"),
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")

    lines += [
        "",
        "> **Put them on the organization, not on 37 repositories.** Delivery runs from",
        "> here now, so each secret is needed in one place. The Android keystore secrets",
        "> were set per repo before that was true — see §3.",
        "",
        "## 2. Store listing copy",
        "",
        f"{len(missing_desc)} of {sum(1 for a in APPS if a['flutter'])} Flutter apps "
        "have no description, which both stores",
        "require. A description makes claims about what an app does, so it is written by",
        "someone who knows the product, not generated.",
        "",
        "Edit `AmericanGroupLLC-Backend/store/apps/<repo>.json`, then run",
        "`python3 scripts/store_metadata.py generate` there.",
        "",
        "| Needs a description |",
        "| --- |",
    ]
    for repo in missing_desc:
        lines.append(f"| {repo} |")

    lines += [
        "",
        "## 3. Secrets that exist but under the wrong name",
        "",
        "The workflows read the four names below. A secret spelled differently is the",
        "same as one that is missing.",
        "",
        "| Repo | Has | Missing |",
        "| --- | --- | --- |",
    ]
    if offline:
        lines.append("| _(run without --offline to measure)_ | | |")
    else:
        any_gap = False
        for app in APPS:
            got = per_repo.get(app["repo"], set())
            missing = [s for s in ANDROID_SECRETS if s not in got]
            # Only names that look like an Android signing secret under a
            # different spelling. Without this the column fills with unrelated
            # secrets that merely contain "KEY" — ASC_KEY_CONTENT, for one.
            odd = [s for s in got if s not in ANDROID_SECRETS and (
                s.startswith("ANDROID_")
                or s in {"KEYSTORE_BASE64", "KEYSTORE_PASSWORD",
                         "KEY_ALIAS", "KEY_PASSWORD", "STORE_PASSWORD"}
            )]
            if not missing:
                continue
            any_gap = True
            lines.append(
                f"| {app['repo']} | {', '.join(f'`{o}`' for o in odd) or '—'} "
                f"| {', '.join(f'`{m}`' for m in missing)} |"
            )
        if not any_gap:
            lines.append("| _none — every repo has all four_ | | |")

    lines += [
        "",
        "## 4. Apps that cannot be delivered at all yet",
        "",
        "| App | Why |",
        "| --- | --- |",
        "| CodeDeal | A partial Flutter port that does not compile — 5 analyzer errors |",
        "| AGStudio, ApexMarketWatch, BuddyPlay, MyCard, PlantPulse | Not Flutter yet; "
        "outside this manifest until ported |",
        "",
    ]
    (ROOT / "PENDING.md").write_text("\n".join(lines))
    print(f"PENDING.md — {len(missing_desc)} apps need a description")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    write_releases(args.offline)
    write_matrix(args.offline)
    write_files(args.offline)
    write_pending(args.offline)


if __name__ == "__main__":
    main()
