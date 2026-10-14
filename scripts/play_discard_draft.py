#!/usr/bin/env python3
"""Discard a DRAFT release from a Play track (never touches a completed/live release).

    python3 scripts/play_discard_draft.py PlantPulse            # production track (default)
    python3 scripts/play_discard_draft.py PlantPulse --track internal --dry-run

Founder-approved use (2026-10-14): PlantPulse's production draft held the retired
smart-home remote build. Refuses if the track holds anything other than drafts.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from play_production_blockers import token, call, API  # noqa: E402
from agl_paths import MANIFEST  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
track = sys.argv[sys.argv.index("--track") + 1] if "--track" in sys.argv else "production"
if track in args: args.remove(track)
dry = "--dry-run" in sys.argv
apps = {a["repo"]: a for a in json.loads((MANIFEST / "apps.json").read_text())["apps"]}
if len(args) != 1 or args[0] not in apps:
    sys.exit("usage: play_discard_draft.py <App> [--track production] [--dry-run]")
pkg = apps[args[0]].get("application_id")
tok = token()
c, edit = call("POST", f"{API}/{pkg}/edits", tok)
if c != 200:
    sys.exit(f"open edit: HTTP {c} {edit}")
eid = edit["id"]
c, t = call("GET", f"{API}/{pkg}/edits/{eid}/tracks/{track}", tok)
rels = t.get("releases", []) if c == 200 else []
print(f"{args[0]} {track} before: {[(r.get('versionCodes'), r.get('status')) for r in rels]}")
if any(r.get("status") != "draft" for r in rels):
    call("DELETE", f"{API}/{pkg}/edits/{eid}", tok)
    sys.exit("refused: the track holds a non-draft release")
if not rels or dry:
    call("DELETE", f"{API}/{pkg}/edits/{eid}", tok)
    print("nothing to do" if not rels else "dry run: would discard the draft(s)")
    sys.exit(0)
c, u = call("PUT", f"{API}/{pkg}/edits/{eid}/tracks/{track}", tok, {"track": track, "releases": []})
if c not in (200, 204):  # Play answers 204 No Content for an emptied track
    call("DELETE", f"{API}/{pkg}/edits/{eid}", tok)
    sys.exit(f"update track: HTTP {c} {u}")
c, cm = call("POST", f"{API}/{pkg}/edits/{eid}:commit", tok)
print(f"commit: HTTP {c}" + ("" if c in (200, 204) else f" {cm}"))
