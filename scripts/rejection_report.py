#!/usr/bin/env python3
"""Why each app is not live, what the store asked for, and what is missing.

    python3 scripts/rejection_report.py        # -> docs/REJECTION_ANALYSIS.md + .json

One table, per app, joined from everything already measured:

  Apple   docs/asc-build-state.json  (review state)
          ~/agl/.dist/rejections.json (Resolution Center text)
  Play    docs/play-production-blockers.json, docs/play-app-content-state.json
  Gates   docs/store-checklist-detail.json, docs/api-hosts.json, Info.plist

The rejections fall into two kinds that look alike in App Store Connect and
are nothing alike underneath:

  INFO_NEEDED  Guideline 2.1 "Information Needed — New App Submission",
               sent because the account has "limited App Review history".
               The 2.3.3 / 3.1.1 / 3.2 lines under "Prevent Common Issues"
               are boilerplate advice, not findings. Apple wants a reply with
               a screen recording on a physical device on the latest OS and
               six answers; the answers are in the review notes already.
  SPAM_4_3     Guidelines 4.3 and 4.2.6. Apple asks nine questions and says
               do not resubmit; reply instead.

Every row says what is automatable and what needs a person, and nothing in
it is an estimate: a field it cannot read is reported as unknown.
"""

from __future__ import annotations

import html
import json
import pathlib
import plistlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

OUT_MD = M / "docs/REJECTION_ANALYSIS.md"
OUT_JSON = M / "docs/rejection-analysis.json"


def load(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except Exception:
        return default


def classify(messages: list[str]) -> tuple[str, list[str]]:
    """The most serious finding anywhere in the thread, not in one message.

    A thread holds Apple's messages and our replies, and its order is not
    guaranteed; classifying on messages[-1] alone reported sixteen
    Guideline 5.6 findings as "OTHER", which the summary never printed.
    """
    kinds, gls = set(), set()
    for m in messages:
        head = html.unescape(re.sub(r"<[^>]+>", " ", m))[:300]
        gls |= set(re.findall(r"\b(\d\.\d+(?:\.\d+)?)\b", head))
        if re.search(r"Guidelines?\s+5\.6\b", head):
            kinds.add("CONDUCT_5_6")
        # "Guidelines 4.3 - Spam and 4.2.6" is plural; a pattern that wanted
        # "Guideline " missed all fourteen spam rejections the first time.
        if re.search(r"Guidelines?\s+4\.3", head):
            kinds.add("SPAM_4_3")
        if "Information Needed" in head:
            kinds.add("INFO_NEEDED")
    for k in ("CONDUCT_5_6", "SPAM_4_3", "INFO_NEEDED"):
        if k in kinds:
            return k, sorted(gls)
    if not messages:
        return "NONE", []
    return "OTHER", sorted(gls)


ASKS = {
    "CONDUCT_5_6": "Apple: 'features that appear to have been intentionally hidden "
                   "during the review process'. Not a reply-and-wait finding: repeated "
                   "5.6 findings put the developer account at risk. Remove every "
                   "runtime switch that changes what a reviewer sees (remote config "
                   "feature flags, date or region gates, reviewer detection, hidden "
                   "gestures), then reply describing exactly what changed.",
    "INFO_NEEDED": "Reply in Resolution Center with: (1) a screen recording on a "
                   "physical device running the latest iOS, from launch through "
                   "sign-up, login, account deletion and paid features; (2)-(6) "
                   "purpose, setup/credentials, external services, regional "
                   "differences, regulation.",
    "SPAM_4_3": "Do not resubmit. Reply answering nine questions: what it does, "
                "who for, market gap, beta testing, suite or standalone, could it "
                "be an in-app purchase elsewhere, shared code with your apps, "
                "shared code with third parties, made for a client.",
}


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    asc = {r["repo"]: r for r in (lambda s: s if isinstance(s, list) else s.get("apps", []))(
        load(M / "docs/asc-build-state.json", []))}
    rej = load(DIST / "rejections.json", {})
    play = {r["repo"]: r for r in load(M / "docs/play-production-blockers.json", {}).get("apps", [])}
    content = {r["repo"]: r for r in load(M / "docs/play-app-content-state.json", {}).get("apps", [])}
    gate = load(M / "docs/store-checklist-detail.json", {})
    hosts = load(M / "docs/api-hosts.json", {}).get("apps", {})

    rows = []
    for a in apps:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        rec = load(M / f"store/apps/{repo}.json", {})
        ri = rec.get("review_information") or {}
        apple_state = (asc.get(repo) or {}).get("review_state") or "unknown"
        kind, gl = classify((rej.get(repo) or {}).get("messages") or [])
        if repo not in rej and apple_state == "REJECTED":
            kind = "UNREAD"

        plist = d / "ios/Runner/Info.plist"
        scene = None
        if plist.exists():
            try:
                scene = bool(plistlib.loads(plist.read_bytes()).get("UIApplicationSceneManifest"))
            except Exception:
                scene = False
        fails = [c["check"] for c in gate.get(repo, []) if c.get("state") == "FAIL"]
        dead = sorted((hosts.get(repo) or {}).get("dead", {}))
        diff = rec.get("differentiation") or ""

        auto, human = [], []
        if scene is False:
            auto.append("adopt UIScene (crashes on launch on iOS 27): scripts/ios_scene_lifecycle.py")
        # Only when the scene manifest arrived after the build Apple holds:
        # the 22 apps that always had one need no new upload for this reason.
        if scene is True and apple_state in ("REJECTED", "PREPARE_FOR_SUBMISSION"):
            import datetime, subprocess
            added = subprocess.run(
                ["git", "-C", str(d), "log", "-1", "--format=%ct", "-S",
                 "UIApplicationSceneManifest", "--", "ios/Runner/Info.plist"],
                capture_output=True, text=True).stdout.strip()
            up = (asc.get(repo) or {}).get("uploaded_at") or ""
            try:
                up_ts = datetime.datetime.fromisoformat(up.replace("Z", "+00:00")).timestamp()
            except ValueError:
                up_ts = None
            if added and up_ts and int(added) > up_ts:
                auto.append("upload a new build — the build Apple holds predates the "
                            "iOS 27 launch fix")
        if dead:
            auto.append("calls hosts that do not exist: " + ", ".join(dead))
        if kind == "INFO_NEEDED":
            human.append("screen recording on a physical iPhone on iOS 27 "
                         "(Firebase Test Lab tops out at iOS 26.3)")
            auto.append("post the six answers as a Resolution Center reply (in review notes already)"
                        if ri.get("notes") else "write review notes")
        if kind == "SPAM_4_3":
            todo = diff.count("TODO")
            human.append(f"answer the market-gap and beta-testing questions ({todo} TODO in the draft)"
                         if diff else "differentiation answers not drafted")
            # Only when the draft really lacks questions: this was appended
            # unconditionally and kept reporting 26 drafts as five-question
            # long after all of them carried Apple's nine.
            asked = {n for n in range(1, 10) if re.search(rf"(?m)^{n}\. ", diff)}
            if len(asked) < 9:
                auto.append(f"extend the drafted reply from {len(asked)} to Apple's 9 questions")
        if kind == "CONDUCT_5_6":
            human.append("decide and approve the 5.6 reply after the hidden-feature audit "
                         "(docs/REJECTION_ANALYSIS.md, CONDUCT_5_6)")
        if kind == "UNREAD":
            human.append("rejection text not readable from here (Apple ID web session) — open "
                         "Resolution Center")
        p = play.get(repo) or {}
        if p.get("state") and p.get("state") != "LIVE_PRODUCTION":
            n = (content.get(repo) or {}).get("app_content_need_attention")
            human.append(f"Play Console App content: {n} declaration(s) need attention"
                         if n else f"Play: {p.get('blocker') or p.get('state')}")
        rows.append({
            "repo": repo, "apple": apple_state, "kind": kind, "guidelines": gl,
            "asked": ASKS.get(kind, ""), "play": p.get("state") or "unknown",
            "scene_lifecycle": scene, "dead_hosts": dead, "gate_failures": fails,
            "automatable": auto, "needs_a_person": human,
        })

    OUT_JSON.write_text(json.dumps(rows, indent=1) + "\n")

    def count(f):
        return sum(1 for r in rows if f(r))
    lines = [
        "# Why each app is not live — generated by `scripts/rejection_report.py`",
        "",
        "Regenerate rather than edit. Every cell comes from a measured file; "
        "`unknown` means the source could not be read.",
        "",
        "## The shape of it",
        "",
        f"- Apple: **{count(lambda r: r['apple'] == 'REJECTED')} rejected**, "
        f"{count(lambda r: r['apple'] == 'PREPARE_FOR_SUBMISSION')} preparing, "
        f"{count(lambda r: r['apple'] == 'READY_FOR_SALE')} live.",
        f"  - **{count(lambda r: r['kind'] == 'CONDUCT_5_6')} Developer Code of Conduct (5.6)** — "
        "'features intentionally hidden during review'. The most serious finding: "
        "repeated, it endangers the developer account. Fix before any resubmission.",
        f"  - **{count(lambda r: r['kind'] == 'INFO_NEEDED')} Information Needed (2.1)** — "
        "not a defect finding. Apple wants a physical-device recording on the latest "
        "iOS plus six answers.",
        f"  - **{count(lambda r: r['kind'] == 'SPAM_4_3')} Spam (4.3 / 4.2.6)** — reply to nine "
        "questions; do not resubmit.",
        f"  - **{count(lambda r: r['kind'] == 'UNREAD')} rejected with text not readable here**.",
        f"  - **{count(lambda r: r['kind'] == 'OTHER')} other** (see the per-app table).",
        f"- Play: **{count(lambda r: r['play'] == 'LIVE_PRODUCTION')} live**; the rest wait on "
        "App content declarations, which have no API.",
        f"- iOS 27 launch crash (no UIScene lifecycle): "
        f"**{count(lambda r: r['scene_lifecycle'] is False)}** apps still affected.",
        f"- Calling hosts that do not exist: **{count(lambda r: r['dead_hosts'])}** apps.",
        "",
        "## Per app",
        "",
        "| App | Apple | Rejection | Play | Automatable next | Needs a person |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['repo']} | {r['apple']} | {r['kind']} | {r['play']} | "
            + ("<br>".join(r["automatable"]) or "—") + " | "
            + ("<br>".join(r["needs_a_person"]) or "—") + " |")
    lines += ["", "## What each kind of rejection asks for", ""]
    for k, v in ASKS.items():
        lines.append(f"- **{k}** — {v}")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"  {len(rows)} apps -> {OUT_MD.relative_to(M)} and {OUT_JSON.relative_to(M)}")
    for l in lines[6:16]:
        print("  " + l)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
