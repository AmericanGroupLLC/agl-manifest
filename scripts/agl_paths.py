"""Where things are, resolved rather than assumed.

Forty-six scripts opened with

    ROOT = pathlib.Path("/Users/spatchava/agl")

which is correct on one laptop and wrong everywhere else. Twelve of them are
called by `ship.yml`, so the first CI run of the pipeline died with

    FileNotFoundError: '/Users/spatchava/agl/agl-manifest/apps.json'

Import from here instead:

    from agl_paths import MANIFEST, ROOT, DIST

MANIFEST is this repository. ROOT is the directory that *contains the app
repositories*, which is not the same place in both worlds:

  * locally the apps sit beside the manifest, so ROOT is its parent;
  * in CI `scripts/checkout.py` clones them into `<manifest>/work`, so that is
    ROOT.

`work/` existing is what distinguishes the two, and AGL_ROOT overrides both for
anyone with a different layout.
"""

from __future__ import annotations

import json
import os
import shutil
import pathlib

# scripts/agl_paths.py -> scripts -> the manifest
MANIFEST = pathlib.Path(__file__).resolve().parent.parent


# A stray `work/` left behind by an earlier checkout is not a CI layout, and
# treating it as one made store_checklist.py report 0 apps on this machine.
# So look for the apps themselves: work/ counts only when it actually holds
# app repositories, which is what checkout.py puts there.
def _looks_like_a_checkout(d: pathlib.Path) -> bool:
    if not d.is_dir():
        return False
    try:
        names = {p.name for p in d.iterdir() if p.is_dir()}
    except OSError:
        return False
    apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    # Two, not one. One was tried and is wrong here: this machine has a
    # leftover agl-manifest/work/GadgetNest from an old experiment, and a
    # one-repo threshold made every local script resolve ROOT to work/.
    #
    # The heuristic cannot be right for both that and a single-app CI run, so
    # CI does not rely on it: ship.yml exports AGL_ROOT after checkout, which
    # takes precedence over everything below.
    return sum(1 for a in apps if a["repo"] in names) >= 2


def _root() -> pathlib.Path:
    override = os.environ.get("AGL_ROOT")
    if override:
        return pathlib.Path(override)
    work = MANIFEST / "work"
    return work if _looks_like_a_checkout(work) else MANIFEST.parent


ROOT = _root()

# Run artefacts: logs, evidence JSON, built binaries. Never committed.
DIST = pathlib.Path(os.environ.get("AGL_DIST") or (ROOT / ".dist"))


def app_dir(app: dict) -> pathlib.Path:
    """Where one app's Flutter project lives, honouring its `dir` in apps.json."""
    sub = app.get("dir") or "."
    base = ROOT / app["repo"]
    return base if sub == "." else base / sub


def play_key() -> pathlib.Path:
    """The Google Play service-account JSON.

    On this laptop it is a file under `.secrets/`. On a runner it is a secret
    that some step has just written to a temporary path, so the path is not
    predictable and must be passed in. A run on 2026-09-26 failed the
    version-code preflight for exactly this reason: ship.yml wrote the key to
    `$RUNNER_TEMP/secrets/play.json` while the script went on reading
    `ROOT/.secrets/play-publisher-agl.json`, and the only symptom was
    `no Play token:` followed by a truncated ENOENT.
    """
    override = os.environ.get("PLAY_SERVICE_ACCOUNT")
    return pathlib.Path(override) if override else ROOT / ".secrets/play-publisher-agl.json"


def flutter_sdk() -> pathlib.Path:
    """The Flutter SDK to build with.

    This machine pins 3.44.2 at <root>/.flutter-sdk and must keep using it —
    the one on PATH is a different version. A runner has no such directory:
    the setup action installs the SDK and exports FLUTTER_ROOT. Checking the
    pinned copy first keeps local behaviour identical, and falling back to
    FLUTTER_ROOT is what lets the ship pipeline build at all. Without this,
    build_release.py died on the runner with
    `FileNotFoundError: .../work/.flutter-sdk/bin/flutter`.
    """
    override = os.environ.get("AGL_FLUTTER_SDK")
    if override:
        return pathlib.Path(override)
    pinned = ROOT / ".flutter-sdk"
    if (pinned / "bin" / "flutter").exists():
        return pinned
    root = os.environ.get("FLUTTER_ROOT")
    if root and (pathlib.Path(root) / "bin" / "flutter").exists():
        return pathlib.Path(root)
    found = shutil.which("flutter")
    if found:
        return pathlib.Path(found).resolve().parent.parent
    return pinned


def flutter_bin() -> pathlib.Path:
    return flutter_sdk() / "bin" / "flutter"
