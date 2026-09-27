#!/usr/bin/env python3
"""Produce signed Android release bundles locally, and prove each one is signed.

Why this exists rather than a CI job: GitHub's macOS minutes are the expensive
resource this programme is trying to avoid, and Android bundles do not need
them. Building here also means a bundle can be produced before the CI
credentials (AGL_PACKAGES_TOKEN and friends) are in place.

Three things about this build machine are load-bearing and were each found the
hard way, so they are set here rather than left to the operator:

1.  The JVM's AF_INET6 connect() is denied with EPERM. A plain
    `java` loopback connect fails; the same connect with
    -Djava.net.preferIPv4Stack=true succeeds. Without it Gradle reports
    "Could not connect to the Gradle daemon" and no build starts at all.

2.  Direct egress is blocked; the machine reaches the internet through a local
    proxy. The shell honours HTTP_PROXY, the JVM does not — it reads only
    the http.proxyHost/proxyPort system properties. Without them dependency
    downloads fail as "Got socket exception ... Operation not permitted".

3.  Both the Gradle *client* and the Gradle *daemon* are separate JVMs and both
    need the above. JAVA_TOOL_OPTIONS is the one channel every JVM picks up,
    including daemons Gradle forks itself. Putting the flags in a project's
    org.gradle.jvmargs does not work: the daemon did not pick them up, and a
    project setting org.gradle.jvmargs also silently replaces the global
    ~/.gradle value rather than merging with it.

None of this is committed to the app repositories, because none of it is true
of the app — it is true of this machine.

Signature verification is not optional here. A release build with a
misconfigured signingConfig falls back to the debug key and still produces a
perfectly valid-looking .aab; Play rejects it on upload, long after the point
where the mistake is cheap to find. So every bundle's certificate fingerprint
is compared against the keystore it was supposed to be signed with, and a
mismatch is a failure.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT, flutter_bin  # noqa: E402

ROOT = _ROOT
MANIFEST = _MANIFEST
AUDIT = MANIFEST / "docs/release-readiness.json"
SECRETS = ROOT / ".secrets"
KEYSTORES = SECRETS / "keystores.json"
FLUTTER = flutter_bin()
def _tool(env: str, local: str, on_path: str) -> str:
    """Pick a build tool: an explicit override, this Mac's install, then PATH.

    The local install is preferred over PATH deliberately. macOS ships a
    /usr/bin/keytool stub that resolves ahead of the real Corretto JDK, so
    taking PATH first would have quietly changed which keytool local builds
    use — and keytool is what decides whether a bundle is declared signed.
    """
    return os.environ.get(env) or (local if pathlib.Path(local).exists() else "") \
        or shutil.which(on_path) or local


KEYTOOL = _tool(
    "AGL_KEYTOOL",
    "/Library/Java/JavaVirtualMachines/amazon-corretto-17.jdk/Contents/Home/bin/keytool",
    "keytool")
EVIDENCE = MANIFEST / "docs/build-evidence.json"

# Bundles are collected here and the build tree is then deleted. A Flutter
# release tree is 0.5–4 GB, so keeping 37 of them needs ~36 GB that this machine
# does not have — a first attempt at the full run died with ENOSPC partway
# through. The tree is entirely regenerable; the .aab is the artefact worth
# keeping, and it is two orders of magnitude smaller.
#
# Deliberately outside every git repository, so a stray `git add -A` cannot
# commit 50 MB binaries.
DIST = ROOT / ".dist"

PROXY = "127.0.0.1:10054"

JAVA_TOOL_OPTIONS = " ".join([
    "-Djava.net.preferIPv4Stack=true",
    f"-Dhttp.proxyHost={PROXY.split(':')[0]}",
    f"-Dhttp.proxyPort={PROXY.split(':')[1]}",
    f"-Dhttps.proxyHost={PROXY.split(':')[0]}",
    f"-Dhttps.proxyPort={PROXY.split(':')[1]}",
    "-Dhttp.nonProxyHosts=localhost|127.0.0.1",
])

# A flavour has to be chosen explicitly. `flutter build appbundle` on a flavoured
# project builds every flavour and then looks for the unflavoured output, so it
# reports "failed to produce an .aab" while the bundles sit on disk. Preferring
# the production flavour by name avoids shipping a staging build to the store.
PROD_FLAVOUR_PREFERENCE = ("prod", "production", "release", "live", "store")


def app_list() -> list[dict]:
    return [a for a in json.loads(AUDIT.read_text()) if a.get("flutter")]


def app_path(app: dict) -> pathlib.Path:
    base = ROOT / app["repo"]
    return base if app["app_dir"] == "." else base / app["app_dir"]


def flavours(app_dir: pathlib.Path) -> list[str]:
    """Product flavour names declared by the Android module, if any."""
    for name in ("app/build.gradle.kts", "app/build.gradle"):
        f = app_dir / "android" / name
        if not f.exists():
            continue
        text = f.read_text(errors="replace")
        m = re.search(r"productFlavors\s*\{", text)
        if not m:
            continue
        # Walk the braces so nested blocks don't end the scan early.
        i = text.index("{", m.start())
        depth, j = 1, i + 1
        while j < len(text) and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        block = text[i + 1:j - 1]
        # Flavour names are the identifiers opening a block at depth 0.
        names, depth = [], 0
        for line in block.splitlines():
            stripped = line.strip()
            if depth == 0:
                fm = re.match(r'(?:create\(")?([A-Za-z][A-Za-z0-9_]*)"?\)?\s*\{', stripped)
                if fm:
                    names.append(fm.group(1))
            depth += line.count("{") - line.count("}")
        return names
    return []


def pick_flavour(names: list[str]) -> str | None:
    if not names:
        return None
    lowered = {n.lower(): n for n in names}
    for pref in PROD_FLAVOUR_PREFERENCE:
        if pref in lowered:
            return lowered[pref]
    return names[-1]


# FashionFactory's published policy promises no signing material on disk inside
# the repository, and test/security/release_config_test.dart enforces it. Its
# Gradle reads the path from the FASHION_FACTORY_KEY_PROPERTIES environment
# variable instead, so writing the file here would sign the bundle *and* break
# the test the policy exists to protect.
ENV_KEY_PROPERTIES = {
    "FashionFactory": "FASHION_FACTORY_KEY_PROPERTIES",
}


def write_key_properties(app_dir: pathlib.Path, entry: dict,
                         repo: str | None = None) -> pathlib.Path | None:
    """Point the Gradle signingConfig at the real upload keystore.

    Written rather than committed: android/key.properties is gitignored in every
    app precisely so the passwords never reach a repository.
    """
    ks = SECRETS / "keystores" / pathlib.Path(entry["keystore"]).name
    if not ks.exists():
        raise FileNotFoundError(ks)
    env_var = ENV_KEY_PROPERTIES.get(repo or "")
    if env_var:
        vault = SECRETS / "keystores" / f"{repo}-key.properties"
        if not vault.exists():
            raise FileNotFoundError(vault)
        os.environ[env_var] = str(vault)
        # Remove any copy an earlier run left in the repo.
        stale = app_dir / "android/key.properties"
        if stale.exists():
            stale.unlink()
        return None
    p = app_dir / "android/key.properties"
    p.write_text(
        f"storeFile={ks}\n"
        f"storePassword={entry['storePassword']}\n"
        f"keyAlias={entry['alias']}\n"
        f"keyPassword={entry['keyPassword']}\n"
    )
    return p


def keystore_fingerprint(entry: dict | None,
                         app_dir: pathlib.Path | None = None) -> str | None:
    """The certificate the app is *supposed* to be signed with.

    With no local registry — every CI run — the answer is in the
    android/key.properties that materialise_signing.py wrote from the secret,
    which names the keystore, its password and the alias. Reading it there
    keeps the comparison honest instead of skipping it, and skipping it is what
    lets a debug-signed bundle reach an upload.
    """
    if entry is None:
        if app_dir is None:
            return None
        props = app_dir / "android/key.properties"
        if not props.exists():
            return None
        kv = {}
        for line in props.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                kv[k.strip()] = v.strip()
        entry = {"keystore": kv.get("storeFile", ""),
                 "storePassword": kv.get("storePassword", ""),
                 "alias": kv.get("keyAlias", "")}
        ks = pathlib.Path(entry["keystore"])
        if not ks.is_absolute():
            ks = app_dir / "android" / ks
    else:
        ks = SECRETS / "keystores" / pathlib.Path(entry["keystore"]).name
    if not ks.exists():
        return None
    out = subprocess.run(
        [KEYTOOL, "-list", "-v", "-keystore", str(ks),
         "-storepass", entry["storePassword"], "-alias", entry["alias"]],
        capture_output=True, text=True,
    ).stdout
    m = re.search(r"SHA256:\s*([0-9A-F:]+)", out)
    return m.group(1).replace(":", "") if m else None


APKSIGNER = _tool(
    "AGL_APKSIGNER",
    "/Users/spatchava/Library/Android/sdk/build-tools/34.0.0/apksigner",
    "apksigner")


def apk_fingerprint(apk: pathlib.Path) -> str | None:
    """SHA-256 of the certificate an APK is signed with.

    Uses apksigner rather than reading META-INF: an APK signed only with the v2
    or v3 scheme keeps its signature in the APK Signing Block, where a plain zip
    read finds nothing and would wrongly report the artefact unsigned.
    """
    out = subprocess.run([APKSIGNER, "verify", "--print-certs", str(apk)],
                         capture_output=True, text=True).stdout
    m = re.search(r"certificate SHA-?256 digest:\s*([0-9a-fA-F]+)", out)
    return m.group(1).upper() if m else None


def bundle_fingerprint(aab: pathlib.Path) -> str | None:
    """SHA-256 of the certificate the bundle is actually signed with."""
    import zipfile
    with zipfile.ZipFile(aab) as z:
        blocks = [n for n in z.namelist()
                  if n.startswith("META-INF/") and n.upper().endswith((".RSA", ".EC", ".DSA"))]
        if not blocks:
            return None
        der = z.read(blocks[0])
    pem = subprocess.run(
        ["openssl", "pkcs7", "-inform", "DER", "-print_certs"],
        input=der, capture_output=True,
    ).stdout
    fp = subprocess.run(
        ["openssl", "x509", "-noout", "-fingerprint", "-sha256"],
        input=pem, capture_output=True,
    ).stdout.decode(errors="replace")
    m = re.search(r"=([0-9A-Fa-f:]+)", fp)
    return m.group(1).replace(":", "").upper() if m else None


def _rel(path: pathlib.Path) -> str:
    """A short path for the evidence file, without assuming a common root.

    Under the CI layout ROOT is <manifest>/work while the evidence lives in
    <manifest>/docs, so relative_to(ROOT) raises rather than shortening:
    ValueError: '.../docs/build-evidence.json' is not in the subpath of
    '.../work'. Only shorten when the path really is under the root.
    """
    for base in (ROOT, MANIFEST):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def build_one(app: dict, entry: dict | None, timeout: int,
              keep_build: bool = False, kind: str = "aab") -> dict:
    d = app_path(app)
    rec: dict = {"repo": app["repo"], "app_dir": app["app_dir"]}

    if entry is None:
        # Two different "no entry" cases. On a runner there is no local
        # .secrets/keystores.json registry at all: materialise_signing.py has
        # already decoded the per-app secret and written android/key.properties,
        # so the app is signable even though the registry says nothing. Treating
        # that as NO_KEYSTORE silently produced debug-signed bundles that Play
        # rejects only at upload, which is the slowest possible way to find out.
        if (d / "android/key.properties").exists():
            rec["signing_source"] = "key.properties from materialise_signing.py"
        else:
            rec["result"] = "NO_KEYSTORE"
            rec["detail"] = "no upload keystore exists for this app yet"
            return rec
    else:
        rec["signing_source"] = "local .secrets/keystores.json"

    try:
        if entry is not None:
            write_key_properties(d, entry, app["repo"])
    except FileNotFoundError as e:
        rec["result"] = "NO_KEYSTORE"
        rec["detail"] = f"keystore file missing: {e}"
        return rec

    names = flavours(d)
    flavour = pick_flavour(names)
    rec["flavours"] = names
    rec["flavour_built"] = flavour

    target = "apk" if kind == "apk" else "appbundle"
    cmd = [str(FLUTTER), "build", target, "--release"]
    if flavour:
        cmd += ["--flavor", flavour]

    env = dict(os.environ, JAVA_TOOL_OPTIONS=JAVA_TOOL_OPTIONS)
    started = time.time()
    proc = subprocess.run(cmd, cwd=d, capture_output=True, text=True, env=env, timeout=timeout)
    rec["seconds"] = round(time.time() - started, 1)

    # Take the path Flutter reports rather than guessing. Modification time is
    # not a usable signal: an incremental build that has nothing to redo leaves
    # a perfectly good bundle untouched, and treating that as failure would
    # discard real artefacts.
    ext = "apk" if kind == "apk" else "aab"
    aab = None
    m = re.search(rf"✓\s*Built\s+(\S+\.{ext})", proc.stdout)
    if m:
        candidate = pathlib.Path(m.group(1))
        aab = candidate if candidate.is_absolute() else d / candidate

    if aab is None or not aab.exists():
        # Flutter mis-reports flavoured builds as failures, so fall back to the
        # expected output directory before believing it.
        outdir = d / ("build/app/outputs/flutter-apk" if kind == "apk"
                      else "build/app/outputs/bundle")
        found = sorted(outdir.rglob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True) \
            if outdir.exists() else []
        if flavour and kind != "apk":
            want = flavour.lower() + "release"
            found = [c for c in found if c.parent.name.lower() == want] or found
        aab = found[0] if found else None

    if aab is None:
        rec["result"] = "BUILD_FAILED"
        # Gradle's own timestamped debug lines drown the message; drop them, and
        # keep stderr too — a fast failure often says nothing at all on stdout.
        tail = [ln for ln in proc.stdout.splitlines() if not re.match(r"^\d{4}-", ln)]
        err = [ln for ln in proc.stderr.splitlines() if not re.match(r"^\d{4}-", ln)]
        rec["detail"] = ("\n".join(tail[-15:]) + "\n--- stderr ---\n" + "\n".join(err[-15:])).strip()
        rec["exit_code"] = proc.returncode
        return rec
    rec["aab"] = _rel(aab)
    rec["bytes"] = aab.stat().st_size
    rec["sha256"] = hashlib.sha256(aab.read_bytes()).hexdigest()

    want_fp = keystore_fingerprint(entry, d)
    got_fp = apk_fingerprint(aab) if kind == "apk" else bundle_fingerprint(aab)
    rec["keystore_sha256"] = want_fp
    rec["signer_sha256"] = got_fp
    if want_fp and got_fp and want_fp == got_fp:
        rec["result"] = "SIGNED"
    else:
        # Most often means the release signingConfig silently fell back to debug.
        rec["result"] = "SIGNATURE_MISMATCH"
        rec["detail"] = "bundle is not signed with this app's upload key"

    # Keep the bundle, drop the tree. Done after verification so a bundle is
    # never preserved without having been checked.
    DIST.mkdir(exist_ok=True)
    kept = DIST / f"{app['repo']}-{aab.name}"
    shutil.copy2(aab, kept)
    rec["artifact"] = _rel(kept)
    if not keep_build:
        build_dir = d / "build"
        # Never delete anything git is tracking. "build" is an output directory
        # by convention, not by guarantee — DriftDate keeps its desktop icons in
        # one — and a cleanup step that eats source files is far worse than a
        # full disk.
        tracked = subprocess.run(
            ["git", "-C", str(ROOT / app["repo"]), "ls-files", "--error-unmatch", "--", str(build_dir)],
            capture_output=True, text=True,
        )
        if tracked.returncode == 0 and tracked.stdout.strip():
            rec["kept_build"] = "contains tracked files"
        else:
            freed = subprocess.run(["du", "-sk", str(build_dir)], capture_output=True, text=True).stdout
            shutil.rmtree(build_dir, ignore_errors=True)
            try:
                rec["freed_mb"] = round(int(freed.split()[0]) / 1024)
            except (ValueError, IndexError):
                pass
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*", help="repo names; default is every Flutter app")
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--kind", choices=("aab", "apk"), default="aab",
                    help="aab for Play upload; apk for sideloading and manual testing")
    ap.add_argument("--keep-build", action="store_true",
                    help="do not delete the build tree afterwards (needs ~1-4 GB per app)")
    args = ap.parse_args()

    # Absent on a runner by design — the keystores live in repository secrets
    # there, not in a file. An empty registry is not an error.
    keystores = json.loads(KEYSTORES.read_text()) if KEYSTORES.exists() else {}
    if not keystores:
        print(f"no local keystore registry at {KEYSTORES}; relying on "
              f"android/key.properties written from secrets")
    apps = app_list()
    if args.apps:
        wanted = set(args.apps)
        apps = [a for a in apps if a["repo"] in wanted]
        missing = wanted - {a["repo"] for a in apps}
        if missing:
            print(f"unknown apps: {', '.join(sorted(missing))}", file=sys.stderr)
            return 2

    # Kept in separate files so building APKs cannot overwrite the record of the
    # bundles that are going to the store.
    evidence_path = EVIDENCE if args.kind == "aab" else EVIDENCE.with_name("build-evidence-apk.json")
    records = {r["repo"]: r for r in json.loads(evidence_path.read_text())} \
        if evidence_path.exists() else {}

    for i, app in enumerate(apps, 1):
        print(f"[{i}/{len(apps)}] {app['repo']} ... ", end="", flush=True)
        try:
            rec = build_one(app, keystores.get(app["repo"]), args.timeout,
                            args.keep_build, args.kind)
        except subprocess.TimeoutExpired:
            rec = {"repo": app["repo"], "app_dir": app["app_dir"],
                   "result": "TIMEOUT", "detail": f"exceeded {args.timeout}s"}
        rec["built_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        records[app["repo"]] = rec
        extra = f" ({rec['seconds']}s)" if rec.get("seconds") else ""
        print(rec["result"] + extra)
        evidence_path.write_text(json.dumps(sorted(records.values(), key=lambda r: r["repo"]), indent=2) + "\n")

    signed = sum(1 for r in records.values() if r.get("result") == "SIGNED")
    print(f"\n{signed} signed {args.kind}(s); evidence in {_rel(evidence_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
