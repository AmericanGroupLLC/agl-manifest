#!/usr/bin/env python3
"""Every store gate, measured where a machine can measure it.

Two different bars are in play and confusing them is how an app gets rejected:

  TESTING     TestFlight beta distribution and Play internal testing.
  PRODUCTION  App Store review and a Play production release.

This reads what the delivery scripts and the two APIs actually reported and
writes docs/store-gates.json, which `scripts/status.py` folds into the
`gate: *` columns of `status.csv`. It used to also render its own markdown
table; that was one of eleven status documents saying overlapping things, so
the table now lives only in the single sheet.

Gates that no API exposes are not measurable here at all — they are written
down by name in docs/MANUAL_ACTIONS.md rather than being quietly omitted.

    bundle exec ruby scripts/testflight/store_gates.rb   # refresh the Apple side
    python3 scripts/store_gates.py                       # -> docs/store-gates.json
"""
import glob, json, pathlib, struct, zipfile

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M, DIST as D  # noqa: E402
def load(p, d=None):
    try: return json.load(open(D / p))
    except Exception: return d if d is not None else {}

apps  = json.load(open(M / "apps.json"))["apps"]
# 42 of the 43 repositories are store candidates; portfolio-board is not.
apps = [a for a in apps if a.get("store_eligible", True)]
asc   = load("asc-gates.json")
tf    = load("testflight-state.json")
play  = load("play-results.json")
rel   = load("play-release-results.json")
lst   = load("play-listing-results.json")
codes = load("play-version-codes.json")

def so_alignment(aab):
    """Play requires 64-bit native libraries built for 16 KB pages."""
    try: z = zipfile.ZipFile(aab)
    except Exception: return None
    worst = None
    for i in z.infolist():
        if not i.filename.endswith(".so"): continue
        if "arm64" not in i.filename and "x86_64" not in i.filename: continue
        data = z.read(i)
        if data[:4] != b"\x7fELF" or data[4] != 2: continue
        phoff = struct.unpack_from("<Q", data, 0x20)[0]
        phent = struct.unpack_from("<H", data, 0x36)[0]
        phnum = struct.unpack_from("<H", data, 0x38)[0]
        for n in range(phnum):
            off = phoff + n * phent
            if struct.unpack_from("<I", data, off)[0] != 1: continue
            a = struct.unpack_from("<Q", data, off + 0x30)[0]
            worst = a if worst is None else min(worst, a)
    return worst

rows = []
for a in sorted(apps, key=lambda x: x["repo"].lower()):
    r = a["repo"]; g = asc.get(r, {}); t = tf.get(r, {}); l = lst.get(r, {}).get("uploaded", {})
    aab = sorted(glob.glob(str(D / f"{r}-*.aab")))
    align = so_alignment(aab[0]) if aab else None
    shots_ios = sum((g.get("screenshot_sets") or {}).values())
    rows.append({
        "app": r,
        "asc_record": bool(g.get("record")),
        "tf_build": g.get("build") or "—",
        "tf_testers": t.get("testers", "—"),
        "tf_review": t.get("review", "—"),
        "ios_meta": all([g.get("subtitle"), g.get("keywords"), g.get("support_url"),
                         g.get("privacy_policy_url"), (g.get("description") or 0) > 100,
                         g.get("primary_category"), g.get("age_rating")]),
        "ios_shots": shots_ios,
        # "Play has a bundle for this package", asked of Play rather than
        # inferred from our own upload log. The log records the LAST attempt,
        # so a later attempt that failed on the upload key overwrote an earlier
        # success — CalcMaster and Kinnav both read as "no Play entry" while
        # serving a live internal release. play-version-codes.json is Play's
        # own bundle list per package, which cannot be wrong that way.
        "play_entry": (codes.get(r, {}).get("state") == "OK"
                       if codes else play.get(r, {}).get("status") == "uploaded"),
        "play_live": rel.get(r, {}).get("status") == "live-internal",
        "play_shots": l.get("phoneScreenshots", 0),
        "play_icon": bool(l.get("icon")),
        "play_feat": bool(l.get("featureGraphic")),
        "align16k": (align or 0) >= 16384 if align is not None else None,
    })

# Refuse to write rather than write blanks that read like answers.
#
# Every input above lives in .dist/, which is a run artefact and does not exist
# on a runner. The housekeeping job regenerated this file there and wrote 43
# rows of False, and status.py folded them in — so status.csv reported 0/43
# App Store Connect records when the real figure was 29/43. A sheet that is
# confidently wrong is worse than one that is missing a column.
_have = [len(x) for x in (asc, tf, play, rel, lst) if x]
if not _have:
    print("::warning::none of the .dist/ inputs exist, so there is nothing "
          "measured to write. Leaving docs/store-gates.json alone — run the "
          "delivery scripts first, or run this where .dist/ lives.")
    raise SystemExit(0)

(M / "docs/store-gates.json").write_text(json.dumps(rows, indent=1) + "\n")
print(f"wrote docs/store-gates.json ({len(rows)} apps) — "
      f"the table itself is the `gate: *` columns of status.csv")
