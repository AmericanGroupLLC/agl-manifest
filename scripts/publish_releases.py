#!/usr/bin/env python3
"""Attach each app's signed binaries to a GitHub Release in its own repository.

The point is that someone can install an app and try it without a build
machine, a keystore or a Play account. So each release carries:

  * the **APK**, which can be sideloaded onto a device directly;
  * the **AAB**, which is the artefact Google Play accepts and which cannot be
    installed by hand — both are published because neither one does both jobs.

The release notes record the signing certificate fingerprint. That is what makes
the download checkable: anyone can run `apksigner verify --print-certs` and
confirm the file came from this org's upload key rather than trusting the page
it was downloaded from.

Idempotent. Re-running replaces the assets on an existing tag rather than
failing or creating duplicates, so a rebuilt app can be republished.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT  # noqa: E402

ROOT = _ROOT
MANIFEST = _MANIFEST
ORG = "AmericanGroupLLC"
# Since 2026-10-17 the app repos are archived (read-only) and every app lives in
# the monorepo, so each app's releases go there, tagged <App>/v<version>-android.
RELEASE_REPO = f"{ORG}/agl-monorepo"
AAB_EVIDENCE = MANIFEST / "docs/build-evidence.json"
APK_EVIDENCE = MANIFEST / "docs/build-evidence-apk.json"
AUDIT = MANIFEST / "docs/release-readiness.json"


def load(p: pathlib.Path) -> dict:
    return {r["repo"]: r for r in json.loads(p.read_text())} if p.exists() else {}


def notes(repo: str, version: str, aab: dict | None, apk: dict | None) -> str:
    fp = (apk or aab or {}).get("signer_sha256", "")
    pretty = ":".join(fp[i:i + 2] for i in range(0, len(fp), 2)) if fp else "unknown"
    lines = [
        f"Signed release build of **{repo}**, version `{version}`.",
        "",
        "| File | What it is for |",
        "| --- | --- |",
    ]
    if apk:
        lines.append("| `.apk` | Install straight onto an Android device to try the app. |")
    if aab:
        lines.append("| `.aab` | The format Google Play accepts. It cannot be installed by hand. |")
    lines += [
        "",
        "Both are signed with this app's own upload key. You can check that "
        "rather than take it on trust:",
        "",
        "```",
        "apksigner verify --print-certs <file>.apk",
        "```",
        "",
        f"Expected SHA-256: `{pretty}`",
        "",
        "Built with `agl-manifest/scripts/build_release.py`, which verifies every "
        "artefact's certificate against the keystore it was meant to use before "
        "publishing it — a release build with a broken `signingConfig` otherwise "
        "falls back to the debug key and exits 0.",
    ]
    return "\n".join(lines)


ATTEMPTS = 4


def publish(repo: str, tag: str, version: str,
            assets: list[pathlib.Path], body: str, dry: bool) -> str:
    if dry:
        return f"would publish {tag} with {len(assets)} asset(s)"

    # The release is created empty first, and assets are attached afterwards one
    # at a time. Passing them to `gh release create` looks tidier but is worse
    # here: if any upload fails, gh deletes the release it just made, so a flaky
    # 50 MB upload loses the whole thing and the next run starts over. Creating
    # first makes the operation resumable.
    exists = subprocess.run(["gh", "release", "view", tag, "--repo", RELEASE_REPO],
                            capture_output=True, text=True).returncode == 0
    if not exists:
        r = subprocess.run(["gh", "release", "create", tag,
                            "--repo", RELEASE_REPO,
                            "--title", f"{repo} {version}",
                            "--notes", body], capture_output=True, text=True)
        if r.returncode != 0:
            return "FAILED to create: " + (r.stderr.strip().splitlines() or ["?"])[-1][:140]

    # This machine uploads through a local egress proxy that intermittently
    # corrupts large bodies ("tls: bad record MAC", "http2: client connection
    # lost"). One asset per request and a few attempts is enough to get through;
    # --clobber makes a retry replace a partial rather than collide with it.
    failed = []
    for asset in assets:
        for attempt in range(1, ATTEMPTS + 1):
            r = subprocess.run(["gh", "release", "upload", tag, str(asset),
                                "--repo", RELEASE_REPO, "--clobber"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                break
            if attempt < ATTEMPTS:
                time.sleep(5 * attempt)
        else:
            failed.append(asset.name)

    if failed:
        return f"PARTIAL: {len(assets) - len(failed)}/{len(assets)} uploaded; failed {', '.join(failed)}"
    return "updated" if exists else "created"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would be published without touching GitHub")
    args = ap.parse_args()

    aabs, apks = load(AAB_EVIDENCE), load(APK_EVIDENCE)
    audit = {a["repo"]: a for a in json.loads(AUDIT.read_text())}

    repos = sorted(set(aabs) | set(apks))
    if args.apps:
        repos = [r for r in repos if r in set(args.apps)]

    # Kinnav used to be skipped: its repo sat outside the org behind a redirect.
    # Its releases now go to the monorepo like every other app's.
    skipped: list[str] = []

    created = failed = 0
    for i, repo in enumerate(repos, 1):
        aab, apk = aabs.get(repo), apks.get(repo)
        assets = [ROOT / r["artifact"] for r in (apk, aab)
                  if r and r.get("result") == "SIGNED" and r.get("artifact")
                  and (ROOT / r["artifact"]).exists()]
        if not assets:
            print(f"[{i}/{len(repos)}] {repo}: no verified artefact, skipped")
            continue

        version = (audit.get(repo, {}).get("version") or "0.0.0").split("+")[0]
        tag = f"{repo}/v{version}-android"
        body = notes(repo, version, aab, apk)
        outcome = publish(repo, tag, version, assets, body, args.dry_run)
        print(f"[{i}/{len(repos)}] {repo}: {outcome} ({len(assets)} asset(s))")
        # PARTIAL counts as a failure. A summary reading "0 failed" while an
        # asset is missing from a release is worse than no summary — it is the
        # line someone reads instead of checking.
        if outcome.startswith(("FAILED", "PARTIAL")):
            failed += 1
        else:
            created += 1

    if skipped:
        print(f"\nskipped (outside the organization): {', '.join(skipped)}")
    print(f"{created} published, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
