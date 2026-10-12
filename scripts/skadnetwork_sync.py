#!/usr/bin/env python3
"""Give every ad-serving app Google's full SKAdNetwork list.

    python3 scripts/skadnetwork_sync.py --dry-run
    python3 scripts/skadnetwork_sync.py            # edits ios/Runner/Info.plist in place

Without these identifiers iOS cannot attribute installs to the ad networks
Google's mediation buys from, which lowers fill and revenue. Several apps
carried a partial hand-copied list (BodyQuest: 13 of 50). The canonical list
is docs/skadnetwork-google.json, fetched from Google's page (its _source).

Only adds missing <dict><key>SKAdNetworkIdentifier</key>…</dict> entries;
never removes one. Apps without google_mobile_ads or agl_ads are skipped.
Edits the XML text rather than re-serialising the plist, so the file's
formatting and comments survive and the diff shows only the additions.
"""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

DRY = "--dry-run" in sys.argv
want = json.loads((M / "docs/skadnetwork-google.json").read_text())["identifiers"]
apps = json.loads((M / "apps.json").read_text())["apps"]
total = 0
for a in apps:
    d = ROOT / a["repo"] / (a["dir"] if a["dir"] != "." else "")
    pub = (d / "pubspec.yaml").read_text() if (d / "pubspec.yaml").exists() else ""
    if not re.search(r"^\s+(google_mobile_ads|agl_ads):", pub, re.M):
        continue
    plist = d / "ios/Runner/Info.plist"
    text = plist.read_text()
    have = set(re.findall(r"<string>([a-z0-9]{10}\.skadnetwork)</string>", text))
    missing = [i for i in want if i not in have]
    if not missing:
        print(f"  {a['repo']:18} complete ({len(have)})"); continue
    entries = "".join(f"\t\t<dict>\n\t\t\t<key>SKAdNetworkIdentifier</key>\n\t\t\t<string>{i}</string>\n\t\t</dict>\n"
                      for i in missing)
    m = re.search(r"(<key>SKAdNetworkItems</key>\s*<array>\s*)", text)
    if m:
        text = text[:m.end()] + entries + text[m.end():]
    else:
        # Before the closing </dict> of the top-level plist dictionary.
        i = text.rindex("</dict>")
        text = text[:i] + f"\t<key>SKAdNetworkItems</key>\n\t<array>\n{entries}\t</array>\n" + text[i:]
    total += len(missing)
    print(f"  {a['repo']:18} {'would add' if DRY else 'added'} {len(missing)} (had {len(have)})")
    if not DRY:
        plist.write_text(text)
print(f"\n  {total} identifier(s) {'missing' if DRY else 'added'}")
