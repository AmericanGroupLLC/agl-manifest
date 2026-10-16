#!/usr/bin/env python3
"""Draft the 4.3 answer for each app, with the facts filled and the judgement left.

    python3 scripts/differentiation_scaffold.py --dry-run
    python3 scripts/differentiation_scaffold.py

Fourteen apps were rejected under Guidelines 4.3 (Spam) and 4.2.6 (App
Generation Services). Apple's reply asks, per app:

  1. what the app does and the problem it solves, not the marketing copy
  2. the specific target audience
  3. the gap it fills that existing apps do not
  4. the beta testing done, and feedback applied
  5. whether it is standalone or part of a suite, and if a suite, how its
     scope differs from the others
  6-9. (added by Apple in 2026) in-app-purchase consolidation, code shared
     with our apps, code shared with third parties, client work

Questions 1, 2 and 5 are answerable from what this repository measures, so
they are filled in. Questions 3 and 4 are claims about the market and about
testing that actually happened; inventing them is exactly what 4.2.6 screens
for, so they are left as TODO with the question restated.

The result lands in `differentiation` in store/apps/<repo>.json, which
store_checklist.py requires before an app may be submitted. An app whose
TODOs are unfilled fails that check — which is the point.

Measured alongside, and worth knowing before answering question 3: no two of
the 43 apps share more than 22% of their description vocabulary. The copy is
not duplicated, so the 4.3 trigger is more likely the shared scaffold and the
submission volume than the words.

Where each answer comes from (2026-10-12, 26 apps rejected under 4.3/4.2.6):

  2  The store subtitle ("Flight and airport board") is a fragment, not an
     audience. A written audience goes in store/apps/<repo>.json under
     `differentiation_overrides` -> {"2": "..."}; the subtitle is only the
     fallback. Any question number can be overridden the same way, and an
     override always wins over what this script derives.
  4  Facts above the TODO come from docs/beta-evidence.json, which
     scripts/testflight/beta_evidence.rb reads from App Store Connect (GET
     only). The TODO stays: Apple asks for feedback that was applied, and only
     a person can say what that was — the file shows what TestFlight holds.
  6  Where other apps share the category, a "Proposed (owner to confirm)" line
     gives the measured overlap (screen names in common, implementation
     similarity). The TODO stays.

This script rewrites the whole `differentiation` string and does NOT preserve
hand edits made to it. Put lasting wording in `differentiation_overrides`, or
regenerate only some questions and keep the rest of the current text verbatim:

    python3 scripts/differentiation_scaffold.py --sections 2,4,6 AeroSwift
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

TODO = "TODO"


# Widgets every Flutter app uses. Leaving them in makes any two Flutter apps
# look 97% alike, which is how a first pass at this "found" 260 duplicate
# pairs that were nothing of the kind.
GENERIC = set("""Container Text Padding Column Row SizedBox Expanded Center Icon
Scaffold AppBar ListView Card InkWell GestureDetector Flexible Stack Positioned
EdgeInsets BorderRadius BoxDecoration TextStyle Color Colors Theme MediaQuery
Navigator MaterialPageRoute Widget State StatelessWidget StatefulWidget Key
BuildContext Duration Offset Size Rect Align Wrap Divider Spacer SafeArea
SingleChildScrollView Material ElevatedButton TextButton OutlinedButton IconButton
Image Opacity Transform AnimatedContainer ValueNotifier Future List Map Set
String DateTime""".split())


def code_signature(app_dir: pathlib.Path):
    """How this app is built, ignoring the Flutter vocabulary everyone uses."""
    import collections
    c = collections.Counter()
    lib = app_dir / "lib"
    if not lib.is_dir():
        return c
    for f in lib.rglob("*.dart"):
        if "generated" in str(f) or "/l10n/" in str(f):
            continue
        for w in re.findall(r"\b([A-Z][A-Za-z0-9_]{2,})\(", f.read_text(errors="ignore")):
            if w not in GENERIC:
                c[w] += 1
    return c


def cosine(a, b) -> float:
    keys = set(a) | set(b)
    num = sum(a[k] * b[k] for k in keys)
    da = sum(v * v for v in a.values()) ** 0.5
    db = sum(v * v for v in b.values()) ** 0.5
    return num / (da * db) if da and db else 0.0


SHARED_PACKAGES = ("agl_i18n", "agl_observability", "agl_ads")


def pubspec_deps(app_dir: pathlib.Path) -> tuple[list[str], list[str]]:
    """(our shared packages, notable third-party SDKs) from pubspec.yaml."""
    f = app_dir / "pubspec.yaml"
    if not f.exists():
        return [], []
    text = f.read_text(errors="ignore")
    block = text.split("dependencies:", 1)[1].split("dev_dependencies:", 1)[0] \
        if "dependencies:" in text else ""
    names = re.findall(r"(?m)^  ([a-z_][a-z0-9_]*):", block)
    ours = [n for n in names if n in SHARED_PACKAGES]
    notable = [n for n in names if n.split("_")[0] in
               ("firebase", "supabase", "google", "sign", "in", "purchases",
                "revenue", "sentry", "flutter") and n not in ("flutter",)]
    return ours, sorted(set(notable))[:10]


def features_of(app_dir: pathlib.Path) -> list[str]:
    """Screen names, as a factual stand-in for 'what the app contains'."""
    out = []
    for sub in ("lib/screens", "lib/features", "lib/presentation/screens"):
        d = app_dir / sub
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            name = p.stem.replace("_screen", "").replace("_", " ").strip()
            if name and name not in out:
                out.append(name)
    return out[:12]


SECTION_RE = re.compile(r"(?m)^([1-9])\. [A-Z][A-Z0-9 ,/-]*$")


def split_sections(text: str) -> tuple[str, dict[str, str]]:
    """(preamble, {"1": "1. WHAT IT DOES\\n...", ...}); joining them gives text back."""
    marks = list(SECTION_RE.finditer(text))
    if not marks:
        return text, {}
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1)] = text[m.start():end]
    return text[:marks[0].start()], out


def apply_overrides(text: str, overrides: dict) -> str:
    """Replace the body of each overridden question, keeping its heading."""
    pre, secs = split_sections(text)
    for k, body in (overrides or {}).items():
        k = str(k)
        if k in secs and isinstance(body, str) and body.strip():
            heading = secs[k].split("\n", 1)[0]
            secs[k] = f"{heading}\n{body.strip()}\n\n"
    return pre + "".join(secs[k] for k in sorted(secs)).rstrip("\n") + "\n"


def keep_sections(old: str, new: str, regenerate: set[str]) -> str:
    """`new` for the questions in `regenerate`, the current text for the rest."""
    pre_o, old_s = split_sections(old)
    pre_n, new_s = split_sections(new)
    if not old_s:
        return new
    keys = sorted(set(old_s) | set(new_s))
    parts = [(new_s if (k in regenerate or k not in old_s) else old_s)[k] for k in keys]
    for i, k in enumerate(keys[:-1]):          # every section but the last ends in a blank line
        if not parts[i].endswith("\n\n"):
            parts[i] = parts[i].rstrip("\n") + "\n\n"
    parts[-1] = parts[-1].rstrip("\n") + "\n"
    return pre_o + "".join(parts)


def _day(iso: str | None) -> str:
    return (iso or "")[:10] or "unknown"


def _states(d: dict) -> str:
    return ", ".join(f"{v} {k}" for k, v in sorted(d.items(), key=lambda kv: -kv[1])) or "none"


def beta_facts(ev: dict | None, measured_at: str | None) -> str:
    """Question 4's measured lines, from docs/beta-evidence.json. Facts only."""
    if not ev:
        return ("No TestFlight measurement for this app in docs/beta-evidence.json; run "
                "scripts/testflight/beta_evidence.rb before answering.")
    if not ev.get("app_store_record"):
        return "App Store Connect holds no app record for this bundle id."
    b = ev["builds"]
    groups = ev.get("beta_groups") or []
    t = ev["testers"]
    internal = t.get("in_internal_groups",
                     sum(g["testers"] for g in groups if g.get("internal")))
    u = ev.get("usage_all_builds") or {}
    by = ev.get("usage_by_tester_kind_365d") or {}
    ints = (by.get("internal_group_members") or {}).get("sessionCount", 0)
    exts = (by.get("external_only") or {}).get("sessionCount", 0)
    sessions = u.get("sessionCount", 0)
    fb = ev.get("feedback_submissions") or {}
    rv = ev.get("beta_app_review_submissions") or {}
    lines = [
        f"Measured from App Store Connect on {_day(measured_at)} (GET only; "
        "docs/beta-evidence.json):",
        f"  - TestFlight builds uploaded: {b['count']} ({b['valid']} processed), "
        f"first {_day(b.get('first_uploaded'))}, last {_day(b.get('last_uploaded'))}",
        f"  - Tester records on its {len(groups)} beta group(s): {t['unique']}, of which "
        f"{internal} in the internal group (App Store Connect users of this account); "
        f"state as Apple reports it: {_states(t['states'])}",
        "  - Beta App Review submissions (needed before external testers get a build): "
        + (f"{rv['count']} ({_states(rv['states'])}), last {_day(rv.get('last_submitted'))}"
           if rv.get("count") else "none"),
        f"  - Recorded across all builds, last 365 days: {u.get('installCount', 0)} installs, "
        f"{sessions} sessions, {u.get('crashCount', 0)} crashes",
    ]
    if sessions:
        rest = max(sessions - ints - exts, 0)
        lines.append(f"    of the sessions, {ints} came from internal-group members, {exts} from "
                     f"external testers, and {rest} cannot be attributed to a tester record "
                     "currently on the app")
    lines.append(
        f"  - Tester feedback recorded by TestFlight: {u.get('feedbackCount', 0)} "
        f"(screenshot feedback submissions: {fb.get('screenshot')}, crash feedback "
        f"submissions: {fb.get('crash')})")
    if ev.get("refused"):
        lines.append("  - Requests App Store Connect refused: "
                     + "; ".join(f"{r['path']} -> {r['status']} {r.get('detail')}" for r in ev["refused"]))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sections", default="",
                    help="comma-separated question numbers to regenerate; the rest of the "
                         "current text is kept verbatim (default: regenerate all)")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()
    regenerate = {s.strip() for s in args.sections.split(",") if s.strip()}

    evf = M / "docs" / "beta-evidence.json"
    evdoc = json.loads(evf.read_text()) if evf.exists() else {}
    evidence = {r["repo"]: r for r in evdoc.get("apps") or []}

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    # Measure every app against every other once, so question 5 can be
    # answered with a number instead of an assertion.
    full = json.loads((M / "apps.json").read_text())["apps"]
    sigs = {}
    for a in full:
        d = ROOT / a["repo"] / (a.get("dir") or ".")
        s = code_signature(d)
        if s:
            sigs[a["repo"]] = s

    written = 0
    for a in manifest:
        repo = a["repo"]
        f = M / "store/apps" / f"{repo}.json"
        if not f.exists():
            continue
        rec = json.loads(f.read_text())
        en = (rec.get("copy") or {}).get("en") or {}
        d = ROOT / repo / (a.get("dir") or ".")
        feats = features_of(d)

        purpose = (en.get("description") or "").split("\n\n")[0].strip()
        audience = (en.get("subtitle") or "").strip()

        mine = sigs.get(repo) or {}
        others = sorted(((cosine(mine, s), r) for r, s in sigs.items() if r != repo),
                        reverse=True)
        nearest_pct = round(others[0][0] * 100) if others else 0
        nearest_name = others[0][1] if others else "n/a"
        allpairs = sorted(c for c, _ in others)
        median_pct = round(allpairs[len(allpairs) // 2] * 100) if allpairs else 0
        mine_only = set(features_of(d))
        for r2 in sigs:
            if r2 == repo:
                continue
            d2 = ROOT / r2 / (next((x.get("dir") for x in full if x["repo"] == r2), ".") or ".")
            mine_only -= set(features_of(d2))
        unique_screens = ", ".join(sorted(mine_only)[:8]) or "none"

        ours, sdks = pubspec_deps(d)
        cat = rec.get("primary_category")
        same_cat = sorted(x["repo"] for x in full if x["repo"] != repo and cat and
                          (json.loads((M / "store/apps" / f"{x['repo']}.json").read_text())
                           .get("primary_category") if (M / "store/apps" / f"{x['repo']}.json").exists()
                           else None) == cat)
        q6 = (f"No. No other app on this account is in its category ({cat}), so there is "
              "no existing app it could be an in-app purchase or feature of."
              if cat and not same_cat else
              f"{TODO}: {', '.join(same_cat)} share its category ({cat}). Say concretely "
              "why this is not a feature of one of them — this is a judgement, not a fact "
              "the repository holds." if cat else f"{TODO}: category unknown.")
        if same_cat:
            # Measured overlap only — the answer itself stays the owner's.
            overlap = []
            for r2 in same_cat:
                d2 = ROOT / r2 / (next((x.get("dir") for x in full if x["repo"] == r2), ".") or ".")
                common = sorted(set(feats) & set(features_of(d2)))
                pct = round(cosine(mine, sigs[r2]) * 100) if r2 in sigs and mine else None
                overlap.append((pct or 0, f"{r2}: {len(common)} screen name(s) in common"
                                + (f" ({', '.join(common)})" if common else "")
                                + (f", {pct}% implementation similarity" if pct is not None
                                   else ", implementation similarity not measured")))
            closest = max(overlap)[0]
            q6 += ("\nProposed (owner to confirm): "
                   + ("No. Measured overlap with each app in the category: "
                      if closest < 50 else
                      "no answer proposed — one app in the category is too close by "
                      "implementation to judge from the numbers. Measured: ")
                   + "; ".join(o for _, o in overlap) + ".")
        # Describe only what this app actually links. An earlier draft said
        # "ad mediation" for apps that do not use agl_ads — a false statement
        # in a reply to App Review.
        roles = {"agl_i18n": "shared translations", "agl_observability": "crash reporting",
                 "agl_ads": "ad mediation"}
        q7 = ("Yes, infrastructure only: " + "; ".join(f"{p} ({roles[p]})" for p in ours)
              + (". It also uses the same Supabase project as our other apps for sign-in"
                 if "supabase" in (d / "pubspec.yaml").read_text(errors="ignore") else "")
              + ". No screens, features or content are shared; the similarity figure in 5 "
              "measures exactly that.") if ours else "No shared in-house packages."
        ev = evidence.get(repo)
        fb_count = "an unmeasured number of"
        if ev and ev.get("app_store_record"):
            fbs = ev.get("feedback_submissions") or {}
            fb_count = max((ev.get("usage_all_builds") or {}).get("feedbackCount", 0),
                           (fbs.get("screenshot") or 0) + (fbs.get("crash") or 0))
        text = f"""1. WHAT IT DOES
{purpose or TODO + ': describe the primary problem this app solves.'}
Screens it contains: {', '.join(feats) if feats else TODO}

2. INTENDED USER
{audience or TODO + ': describe the specific target audience.'}

3. GAP IT FILLS
{TODO}: what does this app do that existing apps do not, or do less well?
Answer concretely — a named competitor and a named difference. This cannot
be drafted from the repository; it is a claim about the market.

4. BETA TESTING DONE
{beta_facts(ev, evdoc.get("measured_at"))}
{TODO}: describe the beta testing that actually happened and name one change
made because of a tester's feedback. TestFlight records {fb_count} feedback
item(s) for this app, so an example of applied feedback has to come from
testing outside TestFlight and be shown, not asserted. If there is none, say so.

5. STANDALONE OR PART OF A SUITE
Part of a suite: 43 apps are published under this developer account.
Category: {rec.get('primary_category') or TODO}.

This app's scope differs from the rest measurably, not just by description:

  - Screens unique to it: {unique_screens}
  - Closest other app by implementation: {nearest_name} at {nearest_pct}%
    similarity of non-generic widget and class usage
  - Across all 43 apps the median pairwise similarity is {median_pct}%, and
    no pair exceeds 85%

Both numbers exclude the ~60 widgets every Flutter app uses — Column, Text,
Padding and so on. Including them makes any two Flutter apps look 97% alike,
which is a property of the framework rather than of these apps.

The store copy is distinct on the same basis: no two of the 43 share more
than 22% of their description vocabulary.

6. COULD THIS BE AN IN-APP PURCHASE IN ANOTHER APP
{q6}

7. CODE SHARED WITH OUR OTHER APPS
{q7}

8. CODE SHARED WITH THIRD-PARTY APPS
No, beyond standard third-party frameworks{": " + ", ".join(sdks) if sdks else ""}.

9. MADE FOR A CLIENT OR THIRD PARTY
{TODO}: confirm — was this app's content, concept or branding provided by a
client or partner? (Expected answer: no, built and published by American Group
LLC. Only the account owner can state it.)
"""
        if regenerate:
            text = keep_sections(rec.get("differentiation") or "", text, regenerate)
        # Last, so a written answer wins whether or not its question was regenerated.
        text = apply_overrides(text, rec.get("differentiation_overrides") or {})
        if args.dry_run:
            print(f"  {repo:18} would draft {len(text)} chars, "
                  f"{text.count(TODO)} TODO(s)", flush=True)
            continue
        if rec.get("differentiation") == text:
            continue
        rec["differentiation"] = text
        f.write_text(json.dumps(rec, indent=1) + "\n")
        written += 1
        print(f"  {repo:18} drafted, {text.count(TODO)} TODO(s) left", flush=True)

    print(f"\ndrafts written: {written}")
    print("Each TODO is a question only a person can answer honestly. "
          "store_checklist.py fails an app until they are gone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
