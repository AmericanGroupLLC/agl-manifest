#!/usr/bin/env python3
"""Find every americangroup.ai URL the apps reference, and prove which are real.

The host serves an SPA catch-all: any unknown path returns HTTP 200 with the
marketing homepage. So a 200 means nothing. The only reliable test is to fetch
a deliberately nonexistent path, hash it, and treat any URL with that same hash
as a 404 in disguise.
"""
import hashlib, json, pathlib, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402
URL_RE = re.compile(r"https://(?:www\.)?safecodeg\.com[^\s\"'`)<>\\,\]]*")

HOME_TITLE = b"American Group LLC \xe2\x80\x94 Enterprise Technology & Mobile Apps"

def fetch(url):
    """Return (is_catchall, bytes).

    md5 equality is NOT a reliable test: the catch-all body varies by a byte
    between requests, so a hash comparison silently passes fake pages as real.
    The homepage <title> is stable, so that is what identifies it.
    """
    r = subprocess.run(["curl", "-sL", "--max-time", "45", url],
                       capture_output=True, timeout=90)
    return (HOME_TITLE in r.stdout), len(r.stdout)

assert fetch("https://www.americangroup.ai/ThisPathCannotExist999888")[0], "catch-all probe failed"
print("catch-all identified by homepage <title>\n")

apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
found = {}   # url -> set(repo)
for a in apps:
    repo = a["repo"]
    d = ROOT / repo if a.get("dir", ".") in (".", None) else ROOT / repo / a["dir"]
    for pat in ("lib/**/*.dart", "fastlane/**/*.txt", "distribution/**/*.txt",
                "ios/Runner/Info.plist", "android/app/src/main/AndroidManifest.xml"):
        for p in d.glob(pat):
            if "/build/" in str(p):
                continue
            try:
                for m in URL_RE.findall(p.read_text(errors="ignore")):
                    found.setdefault(m.rstrip('.,);'), set()).add(repo)
            except Exception:
                pass

urls = sorted(found)
print(f"distinct americangroup.ai URLs referenced by apps: {len(urls)}")
with ThreadPoolExecutor(max_workers=8) as ex:
    res = list(ex.map(fetch, urls))

# The site root legitimately IS the homepage, so it hashes the same as the
# catch-all. Flagging it would be a false positive, not a finding.
ROOTS = {"https://www.americangroup.ai", "https://www.americangroup.ai/",
         "https://www.americangroup.ai", "https://www.americangroup.ai/"}

bad = []
for url, (is_ca, n) in zip(urls, res):
    if is_ca and url not in ROOTS:
        bad.append((url, sorted(found[url])))
print(f"\nREAL pages:      {len(urls)-len(bad)}")
print(f"CATCH-ALL (fake): {len(bad)}")
for url, repos in bad:
    print(f"   {url}\n      referenced by: {', '.join(repos)}")
(ROOT / ".dist/url-sweep.json").write_text(json.dumps(
    {"detection": "homepage <title>",
     "fake": [{"url": u, "repos": r} for u, r in bad],
     "checked": len(urls)}, indent=1))
