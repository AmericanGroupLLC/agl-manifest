#!/usr/bin/env python3
"""Mock App Review and mock Play review: every rule in store/policy/catalogue.json, per app.

    python3 scripts/store_policy_audit.py            # all 43 apps
    python3 scripts/store_policy_audit.py Kinnav MyHealth

For each app this

  1. detects the features the CURRENT source has (accounts, third-party
     sign-in, UGC, location, ads, IAP, ...), each with file:line evidence;
  2. decides which catalogue rules apply (a rule applies when any of its
     feature tags is detected, or it says "all");
  3. runs every automated check it can, reusing the measured results other
     scripts already write (docs/apple-requirements.json,
     docs/store-checklist-detail.json, docs/store-gates.json, docs/api-hosts.json,
     the staged IPA via testflight/privacy_scan.py) plus new detectors
     (merged Android permissions vs use, targetSdk, platform mentions, beta
     wording, remote switches, Sign in with Apple, affiliate disclosure,
     in-app privacy link, push prompt at launch, review prompts, required-reason
     APIs vs PrivacyInfo.xcprivacy, SDK privacy manifests);
  4. writes docs/store-policy/<App>.json and .md, and docs/STORE_POLICY.md.

States: PASS (evidence shown), FAIL (evidence shown), HUMAN (a person must
look — the exact thing is named), FOUNDER (a founder-only Console/ASC action),
n-a (the rule does not apply; the reason is shown). Nothing is PASS without
evidence. Exit status 1 when any applicable rule FAILs.

The catalogue was written from knowledge, not from the live guideline text
(its `_about` says so); a PASS here means "passes our reading of the rule".
predelivery.py check 2.8 reads docs/store-policy/<App>.json and re-runs this
for the app when the file is stale (audit_for_gate()).
"""

from __future__ import annotations

import collections
import datetime
import json
import os
import pathlib
import plistlib
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "testflight"))
from agl_paths import ROOT, MANIFEST as M, DIST, flutter_sdk  # noqa: E402
import apple_requirements as AR  # noqa: E402
import store_checklist as SC  # noqa: E402
import privacy_scan as PS  # noqa: E402

PASS, FAIL, HUMAN, FOUNDER, NA = "PASS", "FAIL", "HUMAN", "FOUNDER", "n-a"
STATES = (FAIL, HUMAN, FOUNDER, PASS, NA)

# Google Play's target API level for new apps and app updates. From 31 Aug 2025
# Play required API 35; the yearly step to API 36 (Android 16) was expected for
# 31 Aug 2026. VERIFY against
# https://developer.android.com/google/play/requirements/target-sdk before
# relying on it — written without web access.
PLAY_TARGET_SDK_REQUIRED = 36

CATALOGUE = M / "store/policy/catalogue.json"
OUT = M / "docs/store-policy"
SUMMARY = M / "docs/STORE_POLICY.md"
PUB_CACHE = pathlib.Path(os.environ.get("PUB_CACHE") or pathlib.Path.home() / ".pub-cache")

# Owner roles (ai-office/.claude/agents/).
DEV, PRIV, SEC, COMP, CREAT, ASO = ("software-developer", "privacy-engineer", "appsec-engineer",
                                    "store-compliance", "store-creative", "aso-specialist")
HYG, AAR, PPA, FND, BE, PM = ("code-hygiene", "apple-review-auditor", "play-policy-auditor",
                              "founder", "backend-supabase", "product-manager")

MAX_EV = 6  # evidence lines kept per finding (the count is always reported)


def load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text())
    except Exception:
        return default


def read(p: pathlib.Path) -> str:
    try:
        return p.read_text(errors="ignore")
    except OSError:
        return ""


def mtime(p: pathlib.Path) -> str | None:
    try:
        return datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")
    except OSError:
        return None


def cap(ev: list[str], n: int = MAX_EV) -> list[str]:
    ev = list(dict.fromkeys(ev))
    return ev[:n] + ([f"... and {len(ev) - n} more"] if len(ev) > n else [])


# ------------------------------------------------------------------ Dart reading

def strip_comment(line: str) -> str:
    """The line without a trailing // comment (quotes respected, so URLs survive)."""
    q, i, n = None, 0, len(line)
    while i < n:
        c = line[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == "/" and line.startswith("//", i):
            return line[:i]
        i += 1
    return line


def code_lines(src: str) -> list[tuple[int, str]]:
    """(line number, code) with comments removed; import/export/part lines kept."""
    out, block = [], False
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw
        if block:
            if "*/" not in line:
                continue
            line, block = line.split("*/", 1)[1], False
        s = line.strip()
        if s.startswith("/*") and "*/" not in s:
            block = True
            continue
        if s.startswith(("//", "*", "/*")):
            continue
        line = strip_comment(line)
        if line.strip():
            out.append((n, line))
    return out


STR_LIT = re.compile(r"""r?'((?:[^'\\\n]|\\.)*)'|r?"((?:[^"\\\n]|\\.)*)\"""")
DIRECTIVE = re.compile(r"^\s*(import|export|part|library)\b")


def literals(line: str) -> list[str]:
    if DIRECTIVE.match(line):
        return []
    return [a or b for a, b in STR_LIT.findall(line)]


def without_literals(line: str) -> str:
    return STR_LIT.sub("''", line)


def skip_string(s: str, i: int) -> int:
    """Index just past the string literal starting at s[i]."""
    q = s[i:i + 3] if s[i:i + 3] in ("'''", '"""') else s[i]
    j, n = i + len(q), len(s)
    while j < n:
        if s[j] == "\\":
            j += 2
            continue
        if s.startswith(q, j):
            return j + len(q)
        if len(q) == 1 and s[j] == "\n":
            return j + 1
        j += 1
    return n


def match_close(s: str, i: int) -> int:
    """Index of the bracket that closes the one at s[i]; strings and comments skipped."""
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            i = skip_string(s, i)
            continue
        if c == "/" and s.startswith("//", i):
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "/" and s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def arg_end(s: str, i: int, stops: str = ",)]}") -> int:
    """End of the expression starting at i: the first stop character at depth 0."""
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            i = skip_string(s, i)
            continue
        if c in "({[":
            depth += 1
        elif c in ")}]":
            if depth == 0:
                return i
            depth -= 1
        elif depth == 0 and c in stops:
            return i
        i += 1
    return n


# ------------------------------------------------------------------ the app

def direct_deps(pubspec: str) -> set[str]:
    deps, keep = set(), False
    for line in pubspec.splitlines():
        if re.match(r"^dependencies:", line):
            keep = True
            continue
        if re.match(r"^[A-Za-z_]", line):
            keep = False
        m = re.match(r"^  ([a-z_0-9]+)\s*:", line)
        if keep and m:
            deps.add(m.group(1))
    return deps


def parse_lock(text: str) -> dict[str, dict]:
    pkgs, cur, sub = {}, None, None
    for line in text.splitlines():
        m = re.match(r"^  ([A-Za-z_0-9]+):\s*$", line)
        if m:
            cur = pkgs.setdefault(m.group(1), {})
            sub = None
            continue
        if cur is None:
            continue
        m = re.match(r"^    ([\w-]+):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip().strip('"')
            if k == "description" and not v:
                sub = cur.setdefault("description", {})
            else:
                cur[k], sub = v, None
            continue
        m = re.match(r"^      ([\w-]+):\s*(.*)$", line)
        if m and sub is not None:
            sub[m.group(1)] = m.group(2).strip().strip('"')
    return pkgs


class App:
    def __init__(self, a: dict):
        self.a, self.repo = a, a["repo"]
        self.repo_dir = ROOT / self.repo
        self.d = SC.app_dir(a)
        self.dart = {f: s for f, s in AR._dart(self.d).items()
                     if not f.name.startswith("app_localizations")}
        self.lines = {f: code_lines(s) for f, s in self.dart.items()}
        self.pubspec = read(self.d / "pubspec.yaml")
        self.deps = direct_deps(self.pubspec)
        self.lock = parse_lock(read(self.d / "pubspec.lock"))
        try:
            self.info = plistlib.loads((self.d / "ios/Runner/Info.plist").read_bytes())
        except Exception:
            self.info = {}
        self.ent = "".join(read(p) for p in (self.d / "ios/Runner").glob("*.entitlements"))
        self.rec = load(M / f"store/apps/{self.repo}.json", {})
        self.ipa = DIST / f"{self.repo}.ipa"
        self._zip_names = None
        self._bins = None
        self._ipa_info = None
        self._android = None
        self._arb = None
        self._graph = None

    # -- paths and grep
    def rel(self, f: pathlib.Path) -> str:
        try:
            return str(f.relative_to(self.repo_dir))
        except ValueError:
            return str(f)

    def where(self, f, n, text="") -> str:
        t = text.strip()
        return f"{self.rel(f)}:{n}" + (f" `{t[:90]}`" if t else "")

    def grep(self, pat, *, no_literals=False, flags=0) -> list[tuple[pathlib.Path, int, str]]:
        rx = re.compile(pat, flags) if isinstance(pat, str) else pat
        out = []
        for f, lines in self.lines.items():
            for n, line in lines:
                if rx.search(without_literals(line) if no_literals else line):
                    out.append((f, n, line))
        return out

    def ev(self, hits) -> list[str]:
        return [self.where(f, n, l) for f, n, l in hits]

    def uses(self, pkg: str) -> list[tuple[pathlib.Path, int, str]]:
        return self.grep(rf"""['"]package:{re.escape(pkg)}/""")

    # -- UI strings: Dart literals and the English ARB values
    def arb(self) -> list[tuple[pathlib.Path, int, str, str]]:
        if self._arb is None:
            self._arb = []
            l10n = read(self.d / "l10n.yaml")
            m = re.search(r"(?m)^arb-dir:\s*(\S+)", l10n)
            arb_dir = self.d / (m.group(1) if m else "lib/l10n")
            m = re.search(r"(?m)^template-arb-file:\s*(\S+)", l10n)
            files = [arb_dir / m.group(1)] if m else sorted(arb_dir.glob("*_en.arb"))
            for f in files:
                if not f.exists():
                    continue
                text = read(f)
                data = load(f, {})
                lines = text.splitlines()
                for k, v in data.items():
                    if k.startswith("@") or not isinstance(v, str):
                        continue
                    n = next((i for i, l in enumerate(lines, 1) if f'"{k}"' in l), 0)
                    self._arb.append((f, n, k, v))
        return self._arb

    def ui_strings(self):
        """[(where, text, file, line, arb_key|None)]"""
        out = []
        for f, lines in self.lines.items():
            for n, line in lines:
                for lit in literals(line):
                    out.append((self.where(f, n, line), lit, f, n, None))
        for f, n, k, v in self.arb():
            out.append((f"{self.rel(f)}:{n} ({k})", v, f, n, k))
        return out

    def ios_metadata(self):
        """[(where, text)] customer-visible iOS listing text."""
        out = []
        en = (self.rec.get("copy") or {}).get("en") or {}
        for k in ("name", "subtitle", "description", "keywords", "promotional_text", "release_notes"):
            if en.get(k):
                out.append((f"store/apps/{self.repo}.json copy.en.{k}", en[k]))
        md = self.d / "fastlane/metadata"
        if md.is_dir():
            for f in sorted(md.rglob("*.txt")):
                parts = f.relative_to(md).parts
                if parts[0] in ("android", "review_information") or f.name.endswith(("_url.txt",)):
                    continue
                out.append((self.rel(f), read(f)))
        return out

    # -- the staged IPA
    def zip_names(self) -> list[str]:
        if self._zip_names is None:
            self._zip_names = []
            if self.ipa.exists():
                try:
                    with zipfile.ZipFile(self.ipa) as z:
                        self._zip_names = z.namelist()
                except Exception:
                    pass
        return self._zip_names

    def bins(self) -> dict[str, bytes]:
        """Every Mach-O in the .app: the executable, frameworks and extensions."""
        if self._bins is None:
            self._bins = {}
            if self.ipa.exists():
                rx = re.compile(r"Payload/[^/]+\.app/(Frameworks/[^/]+\.framework/[^/.]+|"
                                r"PlugIns/[^/]+\.appex/[^/.]+|[^/.]+)$")
                with zipfile.ZipFile(self.ipa) as z:
                    for n in z.namelist():
                        if rx.match(n):
                            data = z.read(n)
                            if data[:4] in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xcf"):
                                self._bins[n] = data
        return self._bins

    def ipa_info(self) -> dict:
        if self._ipa_info is None:
            self._ipa_info = {}
            n = next((x for x in self.zip_names() if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", x)), None)
            if n:
                with zipfile.ZipFile(self.ipa) as z:
                    self._ipa_info = plistlib.loads(z.read(n))
        return self._ipa_info

    def ipa_label(self) -> str:
        if not self.ipa.exists():
            return "no staged IPA"
        return f"{self.ipa.name} build {self.ipa_info().get('CFBundleVersion')} ({mtime(self.ipa)})"

    def last_commit(self) -> int | None:
        rel = "." if self.d == self.repo_dir else str(self.d.relative_to(self.repo_dir))
        try:
            out = subprocess.run(["git", "-C", str(self.repo_dir), "log", "-1", "--format=%ct", "--", rel],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
            return int(out) if out.isdigit() else None
        except Exception:
            return None

    # -- Android: release manifests + every plugin manifest pubspec.lock pulls in
    def android(self) -> dict:
        """{'perms': {name: {'sources': [...], 'max_sdk': int|None}}, 'removed': {...},
            'services': [(source, attrs)], 'unresolved': [pkg], 'plugins_read': n}"""
        if self._android is not None:
            return self._android
        perms: dict[str, dict] = {}
        removed: dict[str, str] = {}
        services, unresolved, read_n = [], [], 0

        def take(text: str, source: str, own: bool):
            text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
            for m in re.finditer(r"<uses-permission(?:-sdk-23)?\b([^>]*)>", text, re.S):
                at = dict(re.findall(r'([\w:]+)\s*=\s*"([^"]*)"', m.group(1)))
                name = at.get("android:name", "")
                short = name.rsplit(".", 1)[-1] if name.startswith("android.permission.") else name
                if own and at.get("tools:node") == "remove":
                    removed[short] = source
                    continue
                e = perms.setdefault(short, {"sources": [], "max_sdk": None})
                e["sources"].append(source)
                if at.get("android:maxSdkVersion", "").isdigit():
                    e["max_sdk"] = int(at["android:maxSdkVersion"])
            for m in re.finditer(r"<service\b([^>]*)>", text, re.S):
                services.append((source, dict(re.findall(r'([\w:]+)\s*=\s*"([^"]*)"', m.group(1)))))

        src = self.d / "android/app/src"
        for f in sorted(src.glob("*/AndroidManifest.xml")) if src.is_dir() else []:
            if f.parent.name in ("debug", "profile", "test", "androidTest"):
                continue
            take(read(f), self.rel(f), True)
        for name, p in sorted(self.lock.items()):
            if p.get("dependency") == "direct dev" or p.get("source") == "sdk":
                continue
            desc = p.get("description") if isinstance(p.get("description"), dict) else {}
            pkg_dir = None
            if p.get("source") == "hosted":
                pkg_dir = PUB_CACHE / "hosted/pub.dev" / f"{name}-{p.get('version')}"
            elif p.get("source") == "git":
                base = (desc.get("url") or "").rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
                pkg_dir = PUB_CACHE / "git" / f"{base}-{desc.get('resolved-ref')}" / (desc.get("path") or ".")
            elif p.get("source") == "path":
                pkg_dir = (self.d / (desc.get("path") or "")).resolve()
            if pkg_dir is None:
                continue
            if not pkg_dir.is_dir():
                unresolved.append(f"{name} {p.get('version')}")
                continue
            mf = pkg_dir / "android/src/main/AndroidManifest.xml"
            if mf.exists():
                read_n += 1
                take(read(mf), f"plugin {name} {p.get('version')}", False)
        for short in removed:
            perms.pop(short, None)
        self._android = {"perms": perms, "removed": removed, "services": services,
                         "unresolved": unresolved, "plugins_read": read_n}
        return self._android

    def perm_ev(self, name: str) -> str:
        e = self.android()["perms"].get(name)
        return f"{name} (from {', '.join(e['sources'][:3])})" if e else name


def flutter_default_target_sdk() -> tuple[int | None, str]:
    f = flutter_sdk() / "packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt"
    m = re.search(r"val targetSdkVersion: Int = (\d+)", read(f))
    return (int(m.group(1)) if m else None), str(f)


def target_sdk(app: App) -> tuple[int | None, str]:
    for g in ("android/app/build.gradle.kts", "android/app/build.gradle"):
        p = app.d / g
        if not p.exists():
            continue
        for n, line in enumerate(read(p).splitlines(), 1):
            m = re.match(r"\s*targetSdk(?:Version)?\s*(?:=|\s)\s*(.+?)\s*$", strip_comment(line))
            if not m:
                continue
            val = m.group(1).strip().strip('"')
            where = f"{app.rel(p)}:{n} `{line.strip()}`"
            if val.isdigit():
                return int(val), where
            if "flutter.targetSdkVersion" in val:
                v, src = flutter_default_target_sdk()
                return v, f"{where} -> Flutter SDK default {v} ({src})"
            return None, f"{where} (not a literal; cannot resolve)"
    return None, "no targetSdk line in android/app/build.gradle(.kts)"


# ------------------------------------------------------------------ Dart call graph
# Used to decide whether a permission prompt runs at launch: main() and the
# first screen's lifecycle methods, without a user action. Calls inside on*
# callbacks and inside route builders are masked (they need a tap / navigation).

NOT_DEF = {"if", "for", "while", "switch", "catch", "return", "super", "this", "assert", "await",
           "throw", "new", "on", "when", "print", "setState", "with", "rethrow", "yield", "else",
           "do", "try", "sizeof"}
ROUTE_CTORS = {"GoRoute", "ShellRoute", "StatefulShellRoute", "MaterialPageRoute", "CupertinoPageRoute",
               "PageRouteBuilder", "StatefulShellBranch", "showDialog", "showModalBottomSheet",
               "showCupertinoModalPopup", "showGeneralDialog", "showBottomSheet"}
AUTO_METHODS = {"build", "initState", "didChangeDependencies", "createState"}
IDENT_CALL = re.compile(r"(?<![\w$])([A-Za-z_]\w*)\s*(?:<[^<>()]*>)?\s*\(")
ARG_NAME = re.compile(r"([A-Za-z_]\w*)\s*:(?!:)")
COMMON = {"add", "map", "then", "call", "toString", "where", "forEach", "of", "read", "watch", "get",
          "set", "put", "remove", "contains", "join", "listen", "cancel", "dispose", "init", "copyWith"}


def mask_callbacks(s: str) -> str:
    out, stack, i, n = list(s), [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            i = skip_string(s, i)
            continue
        if c == "(":
            m = re.search(r"([A-Za-z_]\w*)\s*(?:<[^<>()]*>)?\s*$", s[max(0, i - 80):i])
            stack.append(m.group(1) if m else "")
            i += 1
            continue
        if c == ")":
            if stack:
                stack.pop()
            i += 1
            continue
        if (c.isalpha() or c == "_") and (i == 0 or not (s[i - 1].isalnum() or s[i - 1] in "_.$")):
            m = ARG_NAME.match(s, i)
            if m:
                name, top = m.group(1), (stack[-1] if stack else "")
                if re.match(r"on[A-Z]", name) or name in ("routes", "onGenerateRoute", "redirect") or \
                        (name in ("builder", "pageBuilder") and top in ROUTE_CTORS):
                    j = arg_end(s, m.end())
                    for k in range(m.end(), j):
                        if out[k] != "\n":
                            out[k] = " "
                    i = j
                    continue
                i = m.end()
                continue
            m = re.match(r"\w+", s[i:])
            i += len(m.group(0)) if m else 1
            continue
        i += 1
    return "".join(out)


class Graph:
    def __init__(self, app: App):
        self.app = app
        self.defs = []          # dict(name, cls, file, start, end, line, body_masked)
        self.classes = {}       # name -> (file, start, end)
        self.masked = {}        # file -> masked text
        self.text = {}
        for f, src in app.dart.items():
            self.text[f] = src
            masked = mask_callbacks(src)
            self.masked[f] = masked
            spans = []
            for m in re.finditer(r"\b(?:class|mixin|extension)\s+(\w+)[^{;()]*\{", src):
                b = m.end() - 1
                spans.append((m.group(1), m.start(), match_close(src, b)))
                self.classes.setdefault(m.group(1), (f, m.start(), spans[-1][2]))
            for m in IDENT_CALL.finditer(src):
                name = m.group(1)
                if name in NOT_DEF:
                    continue
                ls = src.rfind("\n", 0, m.start()) + 1
                prefix = src[ls:m.start()]
                if re.search(r"[=,(:?!&|+\-*/]\s*$|\breturn\b|\bawait\b|\.\s*$", prefix):
                    continue
                if prefix.strip() and not re.fullmatch(r"\s*(?:@\w+\s+)*(?:(?:static|external|factory|"
                                                       r"abstract|late|covariant)\s+)*[\w<>?,\[\]\s]*\s",
                                                       prefix):
                    continue
                op = m.end() - 1
                close = match_close(src, op)
                k = close + 1
                mm = re.match(r"\s*(?:async\*?|sync\*)?\s*(\{|=>)", src[k:])
                if not mm:
                    continue
                bstart = k + mm.start(1)
                bend = match_close(src, bstart) if mm.group(1) == "{" else arg_end(src, bstart + 2, ";")
                cls = None
                for cname, cs, ce in spans:
                    if cs < m.start() < ce and (cls is None or cs > cls[1]):
                        cls = (cname, cs)
                self.defs.append({"name": name, "cls": cls[0] if cls else None, "file": f, "start": m.start(),
                                  "end": bend, "line": src.count("\n", 0, m.start()) + 1})
        self.by_name = collections.defaultdict(list)
        self.by_cls = collections.defaultdict(lambda: collections.defaultdict(list))
        for i, d in enumerate(self.defs):
            self.by_name[d["name"]].append(i)
            if d["cls"]:
                self.by_cls[d["cls"]][d["name"]].append(i)

    def var_types(self, text: str) -> dict[str, str]:
        """Variable -> class, from declarations in text (`Foo x = ...`, `final x = Foo(...)`)."""
        out = {}
        for m in re.finditer(r"\b([A-Z]\w*)(?:<[^<>]*>)?\??\s+(_?[a-z]\w*)\s*[=;]", text):
            if m.group(1) in self.classes:
                out.setdefault(m.group(2), m.group(1))
        for m in re.finditer(r"\b(?:final|var|late|const)\s+(_?[a-z]\w*)\s*=\s*(?:await\s+)?(?:const\s+)?"
                             r"([A-Z]\w*)\s*(?:\.\s*instance\b|\.\s*[a-z]\w*\s*\(|\()", text):
            if m.group(2) in self.classes:
                out.setdefault(m.group(1), m.group(2))
        return out

    def auto(self, cls: str) -> list[int]:
        out = []
        for nm, idx in self.by_cls.get(cls, {}).items():
            if nm in AUTO_METHODS or nm == cls:
                out += idx
        return out

    def edges(self, i: int):
        d = self.defs[i]
        body = self.masked[d["file"]][d["start"]:d["end"] + 1]
        src = self.text[d["file"]]
        types = self.var_types(src[d["start"]:d["end"] + 1])
        if d["cls"] and d["cls"] in self.classes:
            cf, cs, ce = self.classes[d["cls"]]
            if cf == d["file"]:
                for k, v in self.var_types(src[cs:ce + 1]).items():
                    types.setdefault(k, v)
        for m in IDENT_CALL.finditer(body):
            name = m.group(1)
            if name in NOT_DEF or (name == d["name"] and m.start() < 3):
                continue
            pos = d["start"] + m.start()
            line = src.count("\n", 0, pos) + 1
            j = pos - 1
            while j >= 0 and src[j] in " \t\n":
                j -= 1
            if j >= 0 and src[j] == ".":
                k = j - 1
                while k >= 0 and src[k] in " \t\n":
                    k -= 1
                rm = re.search(r"([A-Za-z_]\w*)$", src[max(0, k - 60):k + 1])
                recv = rm.group(1) if rm else ""
                if recv == "instance":
                    rm2 = re.search(r"([A-Za-z_]\w*)\s*\.\s*instance$", src[max(0, k - 80):k + 1])
                    recv = rm2.group(1) if rm2 else recv
                recv = types.get(recv, recv)
                if recv[:1].isupper() and recv in self.classes:
                    # a method of that class, else a named constructor (Foo.bar())
                    tg = self.by_cls[recv].get(name) or self.auto(recv)
                    for t in tg:
                        yield t, True, line
                elif name not in COMMON and name not in AUTO_METHODS:
                    for t in self.by_name.get(name, []):
                        yield t, False, line
                continue
            if name[:1].isupper():
                if name in self.classes:
                    for t in self.auto(name):
                        yield t, True, line
                continue
            same = self.by_cls[d["cls"]].get(name) if d["cls"] else None
            if same:
                for t in same:
                    yield t, True, line
                continue
            top = [t for t in self.by_name.get(name, []) if self.defs[t]["cls"] is None]
            for t in top:
                yield t, len(top) == 1, line

    def roots(self) -> list[tuple[int, str]]:
        r = [(i, "main()") for i, d in enumerate(self.defs) if d["name"] == "main" and d["cls"] is None]
        pat = re.compile(r"""GoRoute\(\s*path:\s*['"]/['"].{0,400}?(?:builder|pageBuilder):.{0,200}?=>\s*"""
                         r"""(?:const\s+)?(?:\w+\()?\s*(?:child:\s*)?(?:const\s+)?([A-Z]\w*)\(""", re.S)
        pat2 = re.compile(r"""['"]/['"]\s*:\s*\([^)]*\)\s*=>\s*(?:const\s+)?([A-Z]\w*)\(""")
        for f, src in self.text.items():
            for m in list(pat.finditer(src)) + list(pat2.finditer(src)):
                for t in self.auto(m.group(1)):
                    r.append((t, f"initial route '/' -> {m.group(1)}"))
        return r

    def reach(self, max_depth: int = 10, roots=None) -> dict[int, tuple[bool, list[str]]]:
        """def index -> (certain, chain)"""
        best: dict[int, tuple[bool, list[str]]] = {}
        frontier = []
        for i, why in (self.roots() if roots is None else roots):
            d = self.defs[i]
            best[i] = (True, [f"{why}: {self.app.rel(d['file'])}:{d['line']} {d['cls'] or ''}.{d['name']}"])
            frontier.append(i)
        for _ in range(max_depth):
            nxt = []
            for i in frontier:
                cert, chain = best[i]
                for t, c, line in self.edges(i):
                    c2 = cert and c
                    old = best.get(t)
                    if old is None or (c2 and not old[0]):
                        d = self.defs[t]
                        best[t] = (c2, chain + [f"-> {self.app.rel(self.defs[i]['file'])}:{line} calls "
                                                f"{d['cls'] + '.' if d['cls'] else ''}{d['name']} "
                                                f"({self.app.rel(d['file'])}:{d['line']})"])
                        nxt.append(t)
            frontier = nxt
        return best

    def enclosing(self, f, pos) -> int | None:
        cand = [i for i, d in enumerate(self.defs) if d["file"] == f and d["start"] <= pos <= d["end"]]
        return max(cand, key=lambda i: self.defs[i]["start"]) if cand else None


def graph(app: App) -> Graph:
    if app._graph is None:
        app._graph = Graph(app)
    return app._graph


# ------------------------------------------------------------------ feature detection

SENSITIVE_PERMS = {
    # permission -> regex of code that really uses it
    "CAMERA": r"package:camera/|ImageSource\.camera|package:mobile_scanner/|MobileScanner\(|CameraController\(",
    "RECORD_AUDIO": r"package:record/|package:speech_to_text/|package:noise_meter/|AudioRecorder\(|SpeechToText\(|NoiseMeter\(",
    "ACCESS_FINE_LOCATION": r"Geolocator\.|package:location/|package:geolocator/",
    "ACCESS_COARSE_LOCATION": r"Geolocator\.|package:location/|package:geolocator/",
    "ACCESS_BACKGROUND_LOCATION": r"allowBackgroundLocationUpdates:\s*true|package:background_location/|"
                                  r"package:flutter_background_geolocation/|enableBackgroundMode\(\s*enable:\s*true",
    "ACCESS_MEDIA_LOCATION": r"package:photo_manager/|PhotoManager\.|package:exif/",
    "READ_CONTACTS": r"FlutterContacts\.|package:flutter_contacts/|package:contacts_service/|ContactsService\.",
    "WRITE_CONTACTS": r"FlutterContacts\.|package:flutter_contacts/|package:contacts_service/|ContactsService\.",
    "GET_ACCOUNTS": r"(?!)",
    "READ_CALENDAR": r"package:device_calendar/|DeviceCalendarPlugin|package:add_2_calendar/",
    "WRITE_CALENDAR": r"package:device_calendar/|DeviceCalendarPlugin|package:add_2_calendar/",
    "READ_MEDIA_IMAGES": r"PhotoManager\.|package:photo_manager/",
    "READ_MEDIA_VIDEO": r"PhotoManager\.|package:photo_manager/",
    "READ_MEDIA_VISUAL_USER_SELECTED": r"PhotoManager\.|package:photo_manager/",
    "READ_MEDIA_AUDIO": r"package:on_audio_query|OnAudioQuery",
    "READ_EXTERNAL_STORAGE": r"PhotoManager\.|package:photo_manager/|Permission\.storage|getExternalStorageDirectory",
    "WRITE_EXTERNAL_STORAGE": r"PhotoManager\.|package:photo_manager/|Permission\.storage|getExternalStorageDirectory|package:gal/|Gal\.put",
    "POST_NOTIFICATIONS": r"package:flutter_local_notifications/|package:firebase_messaging/|FlutterLocalNotificationsPlugin|"
                          r"package:flutter_foreground_task/|package:audio_service/|package:just_audio_background/",
    "BLUETOOTH": r"package:flutter_blue_plus/|FlutterBluePlus\.|package:flutter_reactive_ble/",
    "BLUETOOTH_ADMIN": r"package:flutter_blue_plus/|FlutterBluePlus\.|package:flutter_reactive_ble/",
    "BLUETOOTH_SCAN": r"package:flutter_blue_plus/|FlutterBluePlus\.|package:flutter_reactive_ble/",
    "BLUETOOTH_CONNECT": r"package:flutter_blue_plus/|FlutterBluePlus\.|package:flutter_reactive_ble/",
    "BLUETOOTH_ADVERTISE": r"package:flutter_blue_plus/|FlutterBluePlus\.|package:flutter_reactive_ble/",
    "NEARBY_WIFI_DEVICES": r"package:network_info_plus/|NetworkInfo\(|package:wifi_scan/",
    "ACTIVITY_RECOGNITION": r"package:pedometer/|Pedometer\.|package:health/|package:activity_recognition",
    "BODY_SENSORS": r"package:health/",
    "READ_PHONE_STATE": r"package:phone_state|package:telephony/",
    "READ_PHONE_NUMBERS": r"package:telephony/",
    "CALL_PHONE": r"FlutterPhoneDirectCaller|package:flutter_phone_direct_caller/",
    "SCHEDULE_EXACT_ALARM": r"AndroidScheduleMode\.(exact|alarmClock)|exactAllowWhileIdle|AndroidAlarmManager\.",
    "USE_EXACT_ALARM": r"AndroidScheduleMode\.(exact|alarmClock)|exactAllowWhileIdle|AndroidAlarmManager\.",
    "USE_FULL_SCREEN_INTENT": r"fullScreenIntent:\s*true",
    "SYSTEM_ALERT_WINDOW": r"package:flutter_overlay_window|SystemAlertWindow",
    "USE_BIOMETRIC": r"package:local_auth/|LocalAuthentication\(",
    "USE_FINGERPRINT": r"package:local_auth/|LocalAuthentication\(",
    "MANAGE_EXTERNAL_STORAGE": r"(?!)", "QUERY_ALL_PACKAGES": r"(?!)", "REQUEST_INSTALL_PACKAGES": r"(?!)",
    "READ_SMS": r"(?!)", "SEND_SMS": r"(?!)", "RECEIVE_SMS": r"(?!)", "RECEIVE_MMS": r"(?!)",
    "RECEIVE_WAP_PUSH": r"(?!)", "READ_CALL_LOG": r"(?!)", "WRITE_CALL_LOG": r"(?!)",
    "PROCESS_OUTGOING_CALLS": r"(?!)",
}
FGS_USE = (r"package:flutter_foreground_task/|FlutterForegroundTask\.|package:audio_service/|AudioService\.init|"
           r"package:just_audio_background/|JustAudioBackground\.init|package:flutter_background_service/|"
           r"ForegroundNotificationConfig\(|foregroundNotificationConfig:")
SMS_CALL = {"READ_SMS", "SEND_SMS", "RECEIVE_SMS", "RECEIVE_MMS", "RECEIVE_WAP_PUSH", "READ_CALL_LOG",
            "WRITE_CALL_LOG", "PROCESS_OUTGOING_CALLS"}
LEGACY_STORAGE = {"READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"}

THIRD_PARTY_LOGIN = (r"GoogleSignIn(\.instance|\s*\()|OAuthProvider\.(google|facebook|github|twitter|azure|"
                     r"discord|linkedin_oidc|linkedin|spotify|kakao|slack|twitch|gitlab|bitbucket|notion|zoom)\b|"
                     r"FacebookAuth\.|GoogleAuthProvider\.credential|package:google_sign_in/|package:flutter_facebook_auth/")
SIWA = r"SignInWithApple\.|OAuthProvider\.apple\b|AppleAuthProvider|package:sign_in_with_apple/"
BG_LOCATION_CODE = SENSITIVE_PERMS["ACCESS_BACKGROUND_LOCATION"]
AI_HOSTS = (r"api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|api\.mistral\.ai|"
            r"api\.groq\.com|api-inference\.huggingface\.co|openrouter\.ai|pollinations\.ai|api\.replicate\.com|"
            r"api\.stability\.ai|api\.cohere\.ai|api\.together\.xyz|api\.deepseek\.com")
AI_CODE = (r"package:(google_generative_ai|dart_openai|langchain\w*|firebase_ai|firebase_vertexai|"
           r"anthropic_sdk_dart|openai_dart|llama_cpp_dart|fllama)/|\bllama_(model|context|decode|tokenize)\w*|"
           r"""functions\.invoke\(\s*['"](?:[\w-]*[-_])?(ai|llm|gpt|chat|assistant|generate|summari[sz]e)"""
           r"""(?:[-_][\w-]*)?['"]""")
AFF_URL = (r"amazon\.[a-z.]+/[^'\"]*[?&]tag=|amzn\.to/|tp\.st/|tp\.media|travelpayouts|linksynergy\.com|"
           r"awin1\.com|prf\.hn|anrdoezrs\.net|jdoqocy\.com|tkqlhce\.com|dpbolvw\.net|kqzyfj\.com|"
           r"shareasale\.com|sjv\.io|pxf\.io|go\.skimresources\.com|viglink\.com|rover\.ebay\.com|"
           r"ebay\.[a-z.]+/[^'\"]*campid=|booking\.com/[^'\"]*[?&]aid=|expedia\.[a-z.]+/[^'\"]*(affcid|camref)=|"
           r"[?&](aff_?id|affiliate_?id|affcid|camref|irclickid)=")
AFF_DISCLOSURE = (r"(?i)\baffiliate (link|links|commission|partner|partners|programme|program|disclosure)|"
                  r"\bwe (may )?earn\b|\bearns? (a|an) (small )?commission|\bcommission (on|from|if|when)\b|"
                  r"\bpaid links?\b|\bsponsored links?\b|as an amazon associate|\bmay receive (a )?commission")
FLAG_PKGS = ("firebase_remote_config", "launchdarkly_flutter_client_sdk", "flagsmith", "flagsmith_flutter_core",
             "unleash_proxy_client_flutter", "growthbook_sdk_flutter", "statsig", "configcat_client",
             "optimizely_flutter_sdk", "split_flutter", "devcycle_flutter_client_sdk")
DYNAMIC_CODE_PKGS = ("shorebird_code_push", "flutter_eval", "dart_eval", "hetu_script", "flutter_js",
                     "flutter_qjs", "js_interpreter")
REPORT_CTRL = AR.REPORT


def affiliate_sites(app: App) -> list[tuple[pathlib.Path, int, str]]:
    """Affiliate link forms in literals, plus affiliate identifiers in files that open a URL.

    An `AffiliatePartner` model nobody renders (iMaps) is not an affiliate link."""
    rx = re.compile(AFF_URL)
    sites = [(f, n, l) for f, lines in app.lines.items() for n, l in lines if any(rx.search(t) for t in literals(l))]
    opener = re.compile(r"launchUrl|launchUrlString|\blaunch\(|Uri\.(parse|https?)\(|WebView")
    for f, n, l in app.grep(r"(?i)affiliate", no_literals=True):
        if opener.search(app.dart.get(f, "")) and re.search(r"https?://", app.dart.get(f, "")):
            sites.append((f, n, l))
    return sites


def detect(app: App) -> tuple[dict[str, list[str]], dict]:
    """({tag: [evidence]}, extras). Every tag carries file:line or the artefact it came from."""
    f: dict[str, list[str]] = {}
    extra: dict = {}

    def add(tag, ev):
        if ev:
            f.setdefault(tag, []).extend(ev)

    and_ = app.android()
    perms = and_["perms"]
    cat = app.rec.get("primary_category") or ""
    cat_ev = f"store/apps/{app.repo}.json primary_category={cat}"
    strings = app.ui_strings()

    def strhits(pat, flags=0, arb=True):
        rx = re.compile(pat, flags)
        return [w for w, t, *_rest in strings if rx.search(t) and (arb or _rest[2] is None)]

    add("accounts", app.ev(app.grep(AR.SIGN_UP)))
    add("sign_in_third_party", app.ev(app.grep(THIRD_PARTY_LOGIN)))
    extra["sign_in_with_apple"] = app.ev(app.grep(SIWA))
    add("ugc", app.ev(app.grep(AR.UGC)))
    add("location", app.ev(app.grep(r"Geolocator\.(getCurrentPosition|getPositionStream|requestPermission|"
                                    r"getLastKnownPosition|checkPermission)|package:location/|Location\(\)\.getLocation")))
    bg = app.ev(app.grep(BG_LOCATION_CODE))
    if "ACCESS_BACKGROUND_LOCATION" in perms:
        bg.append(app.perm_ev("ACCESS_BACKGROUND_LOCATION"))
    if "location" in (app.info.get("UIBackgroundModes") or []):
        bg.append("ios/Runner/Info.plist UIBackgroundModes contains location")
    add("background_location", bg)
    hl = app.ev(app.uses("health")) + (["ios/Runner/*.entitlements: com.apple.developer.healthkit"]
                                       if "com.apple.developer.healthkit" in app.ent else [])
    if cat in ("HEALTH_AND_FITNESS", "MEDICAL"):
        hl.append(cat_ev)
    add("health", hl)
    if cat == "FINANCE":
        add("finance", [cat_ev])
    add("crypto", strhits(r"(?i)\b(bitcoin|ethereum|cryptocurrenc(y|ies)|crypto ?wallet|dogecoin|solana)\b") +
        strhits(r"api\.coingecko\.com|api\.binance\.com|api\.coinbase\.com|api\.kraken\.com"))
    kids = []
    ca = read(M / f"docs/console-answers/{app.repo}.md")
    if re.search(r"Appeals to children:\s*\*\*Yes", ca):
        kids.append(f"docs/console-answers/{app.repo}.md: appeals to children = Yes")
    m = re.search(r"Target age group:\s*\*\*([^*]+)\*\*", ca)
    if m and re.search(r"\b([0-9]|1[0-2])\b", m.group(1)) and "18" not in m.group(1):
        kids.append(f"docs/console-answers/{app.repo}.md: target age group {m.group(1)}")
    if cat == "KIDS" or (app.rec.get("kids_category") or load(M / f"store/ratings/{app.repo}.json", {}).get("kidsAgeBand")):
        kids.append(cat_ev + " / kids age band recorded")
    add("kids", kids)
    add("ads", app.ev(app.grep(r"AglAds\.(configure|initialize)|AglAdBanner\b|\bBannerAd\(|InterstitialAd\.load|"
                               r"RewardedAd\.load|RewardedInterstitialAd\.load|NativeAd\(|AppOpenAd\.load")))
    iap = app.grep(AR.IAP_CODE)
    add("iap", app.ev(iap))
    iap_files = {x[0] for x in iap}
    subs = [x for x in app.grep(r"(?i)subscri|monthly|annual|yearly|auto-?renew") if x[0] in iap_files]
    add("subscriptions", app.ev(subs) + app.ev(app.uses("purchases_flutter")))
    add("webview", app.ev(app.grep(r"package:webview_flutter/|WebViewWidget\(|WebViewController\(|"
                                   r"package:flutter_inappwebview/|InAppWebView\(")))
    add("camera", app.ev(app.grep(SENSITIVE_PERMS["CAMERA"])))
    add("microphone", app.ev(app.grep(SENSITIVE_PERMS["RECORD_AUDIO"])))
    ph = app.ev(app.grep(r"ImageSource\.gallery|\bpickImage\(|pickMultiImage|pickMedia\(|PhotoManager\.|"
                         r"package:photo_manager/|\bGal\.put|package:gal/|ImageGallerySaver"))
    ph += [app.perm_ev(p) for p in ("READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO") if p in perms]
    add("photos", ph)
    add("contacts", app.ev(app.grep(r"FlutterContacts\.|package:flutter_contacts/|ContactsService\.|"
                                    r"FlutterNativeContactPicker|package:flutter_native_contact_picker/")))
    add("bluetooth", app.ev(app.grep(SENSITIVE_PERMS["BLUETOOTH_SCAN"])) +
        [app.perm_ev(p) for p in ("BLUETOOTH_SCAN", "BLUETOOTH_CONNECT", "BLUETOOTH_ADVERTISE") if p in perms])
    push = app.ev(app.grep(r"package:firebase_messaging/|FirebaseMessaging\.instance|package:onesignal_flutter/|"
                           r"OneSignal\.(initialize|Notifications)"))
    local = app.ev(app.grep(r"FlutterLocalNotificationsPlugin\s*\("))
    add("push", push + [e + " (local notifications)" for e in local])
    fd = [f"ios/Runner/Info.plist {k}" for k in ("CFBundleDocumentTypes", "UIFileSharingEnabled",
                                                 "LSSupportsOpeningDocumentsInPlace", "UISupportsDocumentBrowser")
          if k in app.info]
    fd += app.ev(app.grep(r"package:file_picker/|FilePicker\.platform|package:file_selector/|\bopenFile\(\s*acceptedTypeGroups"))
    add("file_documents", fd)
    if app.info.get("UIBackgroundModes"):
        add("background_modes", [f"ios/Runner/Info.plist UIBackgroundModes = {app.info['UIBackgroundModes']}"])
    ext = []
    ios = app.d / "ios"
    for p in sorted(ios.iterdir()) if ios.is_dir() else []:
        if p.is_dir() and p.name not in ("Runner", "Pods", "Flutter", "RunnerTests", ".symlinks", "build") \
                and not p.name.endswith((".xcodeproj", ".xcworkspace")) and (p / "Info.plist").exists():
            ext.append(f"{app.rel(p)}/Info.plist (extension target)")
    if "com.apple.product-type.app-extension" in read(ios / "Runner.xcodeproj/project.pbxproj"):
        ext.append("ios/Runner.xcodeproj: com.apple.product-type.app-extension")
    ext += [f"{app.ipa.name}: {n}" for n in app.zip_names() if re.search(r"\.app/PlugIns/[^/]+\.appex/$", n)]
    add("extensions", ext)
    vpn = []
    if app.ipa.exists():
        vpn = [f"{app.ipa.name}: {h}" for h in PS.vpn_scan(app.ipa)]
    if "com.apple.developer.networking.networkextension" in app.ent:
        vpn.append("ios/Runner/*.entitlements: networkextension")
    add("vpn_networkext", vpn)
    add("ai_generated", strhits(AI_HOSTS, arb=False) + app.ev(app.grep(AI_CODE)))
    add("affiliate_links", app.ev(affiliate_sites(app)))
    nw = strhits(r"^https?://[^'\" ]*(/rss\b|\brss\.|\bfeeds?\.|/feeds?/?$|\.rss\b|/feed/)", arb=False)
    if cat == "NEWS":
        nw.append(cat_ev)
    add("news", nw)
    en = (app.rec.get("copy") or {}).get("en") or {}
    copy_text = " ".join(str(en.get(k) or "") for k in ("name", "subtitle", "description", "full_description"))
    if re.search(r"(?i)\bdating\b|\bdates? nearby\b|\bmatch(es)? near(by)?\b", copy_text):
        add("dating", [f"store/apps/{app.repo}.json copy.en mentions dating"])
    add("emergency_safety", strhits(r"^tel:(911|112|999|000)\b|^(911|112)$", arb=False) +
        strhits(r"(?i)\b(emergency services|call 911|emergency call|emergency number|\bSOS\b)"))
    add("streaming_media", app.ev(app.grep(r"package:(just_audio|audio_service|video_player|chewie|"
                                           r"youtube_player_flutter|youtube_player_iframe|better_player|media_kit)/|"
                                           r"\bUrlSource\(")))
    gov = strhits(r"\b(USCIS|IRS|DMV|FAA|NOAA|Social Security Administration|Department of (State|Homeland Security|"
                  r"Motor Vehicles))\b") + strhits(r"^https?://([\w-]+\.)+gov(/|$)", arb=False)
    gov += [w for w, t in app.ios_metadata() if re.search(r"\b(USCIS|IRS|DMV|FAA)\b", t)]
    add("government_topic", gov)
    # Play's declaration is driven by the FOREGROUND_SERVICE* permissions; a typed
    # <service> a plugin declares (geolocator's) cannot start without them.
    add("foreground_service", [app.perm_ev(p) for p in perms if p.startswith("FOREGROUND_SERVICE")])
    add("exact_alarms", [app.perm_ev(p) for p in ("SCHEDULE_EXACT_ALARM", "USE_EXACT_ALARM") if p in perms])
    add("sms_call_log", [app.perm_ev(p) for p in sorted(SMS_CALL & set(perms))])
    add("gambling", strhits(r"(?i)\b(casino|sportsbook|slot machines?|place (a|your) bets?|wager(ing)?|jackpot|"
                            r"lottery|sweepstakes)\b"))
    add("external_purchase_links", strhits(r"checkout\.stripe\.com|buy\.stripe\.com|paypal\.com/(checkout|cgi-bin/webscr|"
                                           r"donate)|paypal\.me/|gumroad\.com|patreon\.com|ko-fi\.com|buymeacoffee\.com",
                                           arb=False) +
        app.ev(app.uses("flutter_stripe")) + app.ev(app.grep(r"package:flutter_paypal")))
    return {k: list(dict.fromkeys(v)) for k, v in f.items()}, extra


# ------------------------------------------------------------------ reused results

_CACHE: dict = {}


def _doc(name: str):
    if name not in _CACHE:
        p = M / name
        _CACHE[name] = (load(p, None), mtime(p))
    return _CACHE[name]


AR_NAMES = {r["id"]: f"Apple {r['guideline']}: {r['name']}" for r in AR.REQUIREMENTS}
NORM = {"PASS": PASS, "FAIL": FAIL, "HUMAN": HUMAN, "n/a": NA}


def ar_row(app: App, rid: str):
    """(state, evidence) from docs/apple-requirements.json, or None."""
    data, when = _doc("docs/apple-requirements.json")
    for r in (data or {}).get(app.repo, []):
        if r["check"] == AR_NAMES[rid]:
            return NORM.get(r["state"], HUMAN), f"docs/apple-requirements.json ({when}) {rid}: {r['detail']}"
    return None


def sc_row(app: App, name: str):
    data, when = _doc("docs/store-checklist-detail.json")
    for r in (data or {}).get(app.repo, []):
        if r["check"] == name:
            return NORM.get(r["state"], HUMAN), f"docs/store-checklist-detail.json ({when}) '{name}': {r['state']} {r['detail']}".rstrip()
    return None


def from_ar(rid, owner=DEV):
    def check(app, feats):
        row = ar_row(app, rid)
        if row is None:
            return HUMAN, [f"{app.repo} not in docs/apple-requirements.json — run scripts/apple_requirements.py"], owner
        return row[0], [row[1]], owner
    return check


def from_sc(name, owner=COMP):
    def check(app, feats):
        row = sc_row(app, name)
        if row is None:
            return HUMAN, [f"'{name}' not measured for {app.repo} — run scripts/store_checklist.py"], owner
        return row[0], [row[1]], owner
    return check


def worst(*states):
    for s in (FAIL, HUMAN, FOUNDER, PASS, NA):
        if s in states:
            return s
    return HUMAN


def platform_conditional(app: App, f: pathlib.Path, n: int) -> bool:
    if "android" in app.rel(f).lower():
        return True
    lines = dict(app.lines.get(f, []))
    window = " ".join(lines.get(i, "") for i in range(n - 6, n + 7))
    return bool(re.search(r"Platform\.is(Android|IOS)|TargetPlatform\.(android|iOS)|defaultTargetPlatform|"
                          r"\bisAndroid\b|\bisIOS\b|\bisCupertino\b|Platform\.operatingSystem|kIsWeb", window))


def arb_usage(app: App, key: str):
    return app.grep(rf"\.{re.escape(key)}\b")


def ui_hits(app: App, pat: str, flags=0):
    """(unconditional, conditional) UI-string hits; ARB values judged by where their key is used."""
    rx = re.compile(pat, flags)
    hard, cond = [], []
    for w, t, f, n, key in app.ui_strings():
        if not rx.search(t):
            continue
        if key is None:
            (cond if platform_conditional(app, f, n) else hard).append(w)
            continue
        uses = arb_usage(app, key)
        if not uses:
            cond.append(w + " (key unused)")
        elif all(platform_conditional(app, uf, un) for uf, un, _ in uses):
            cond.append(w + " (used only in platform branches)")
        else:
            hard.append(w + " used at " + ", ".join(app.where(uf, un) for uf, un, _ in uses[:2]))
    return hard, cond


# ------------------------------------------------------------------ checks (store, ref) -> fn(app, feats)

def c_fake_data(app, feats):
    fa = load(DIST / "fake-data-audit.json", {}).get(app.repo)
    if fa is None:
        return HUMAN, ["no no-fake-data checker exists in agl-manifest/scripts; read every screen for invented data"], DEV
    return HUMAN, [f"{DIST}/fake-data-audit.json ({mtime(DIST / 'fake-data-audit.json')}, older than current code): "
                   f"{len(fa.get('findings') or [])} release-visible fake-data site(s) then; re-read every screen"], DEV


SECRET = (r"\bsk-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|"
          r"c2VydmljZV9yb2xl|\bsk_live_[0-9a-zA-Z]{20,}|\bghp_[A-Za-z0-9]{30,}|\bxox[bp]-[A-Za-z0-9-]{20,}")


def c_data_security(app, feats):
    hits = [w for w, t, f, n, k in app.ui_strings() if k is None and re.search(SECRET, t)]
    if hits:
        return FAIL, ["secret-looking literal(s) in lib/: " + "; ".join(cap(hits))], SEC
    return HUMAN, ["no secret keys (sk-/sk_live_/AKIA/service_role JWT/private key/ghp_/xox) in lib/ literals",
                   "not verified: how session tokens and personal data are stored and sent — appsec review"], SEC


def c_info_needed(app, feats):
    a = sc_row(app, "Demo account when the app gates on sign-in")
    b = sc_row(app, "Review notes answer Apple's 7 items")
    if not a or not b:
        return HUMAN, ["store-checklist rows missing — run scripts/store_checklist.py"], COMP
    live = SC.login_gate(app.d)
    demo = ((app.rec.get("review_information") or {}).get("demo_account_name") or "")
    ev = [a[1], b[1], f"live: store_checklist.login_gate()={live}, demo_account_name={'set' if demo else 'empty'}"]
    st = worst(a[0], b[0], FAIL if (live and not demo) else PASS)
    return st, ev, COMP


BETA_STRONG = (r"(?i)\b(coming soon|beta (version|build|release|feature|testing|tester|program)|public beta|open beta|"
               r"in beta|early access|developer preview|preview (version|build|release)|sneak preview|"
               r"(page|screen|feature|section|app) (is )?(still )?under construction|demo (mode|version)|"
               r"trial version)\b|\(beta\)")


def meta_hits(app: App, pat: str) -> list[str]:
    """iOS listing text matching pat, each with the words around the match."""
    out = []
    for w, t in app.ios_metadata():
        for m in re.finditer(pat, t):
            out.append(f"iOS metadata {w}: '...{t[max(0, m.start() - 40):m.end() + 30].strip()}...'".replace("\n", " "))
    return out


def c_beta(app, feats):
    hard, cond = ui_hits(app, BETA_STRONG)
    hard += meta_hits(app, BETA_STRONG)
    labels = [w for w, t, f, n, k in app.ui_strings() if t.strip() in ("Beta", "BETA")]
    soft = [w for w, t, f, n, k in app.ui_strings()
            if re.search(r"(?i)\bbeta\b", t) and not re.search(BETA_STRONG, t) and t.strip() not in ("Beta", "BETA")]
    if hard or labels:
        return FAIL, cap(hard + [w + " (Beta badge)" for w in labels]), DEV
    if cond or soft:
        return HUMAN, ["wording to read in context (may be a metric, e.g. stock beta): " + "; ".join(cap(cond + soft))], DEV
    return PASS, ["no beta/coming-soon/preview/demo-mode wording in lib/ strings, the English ARB or iOS metadata"], DEV


def deep_link_only_routes(app: App) -> list[str]:
    out = []
    allcode = "\n".join(l for lines in app.lines.values() for _, l in lines)
    for f, lines in app.lines.items():
        for n, line in lines:
            for m in re.finditer(r"""GoRoute\(\s*path:\s*['"](/[A-Za-z0-9_/-]+)['"]""", line):
                p = m.group(1)
                if len(re.findall(re.escape(f"'{p}") + "|" + re.escape(f'"{p}'), allcode)) <= 1:
                    window = " ".join(l for i, l in lines if n <= i <= n + 3)
                    nm = re.search(r"""name:\s*['"]([\w-]+)['"]""", window)
                    if not nm or len(re.findall(rf"""['"]{re.escape(nm.group(1))}['"]""", allcode)) <= 1:
                        out.append(app.where(f, n, line) + " (path never navigated to)")
    return out


def c_hidden_features(app, feats):
    fails, human, ok = [], [], []
    for pkg in FLAG_PKGS:
        if pkg in app.lock:
            u = app.uses(pkg)
            (fails if u else human).append(f"{pkg} " + (f"used at {', '.join(app.ev(u)[:2])}" if u else
                                                       "in pubspec.lock but not imported — remove it"))
    ph = app.grep(r"\b(isFeatureEnabled|getFeatureFlag(Payload)?|reloadFeatureFlags)\s*\(")
    if ph:
        fails.append("feature-flag calls: " + ", ".join(app.ev(ph)[:3]))
    tbl = app.grep(r"""from\(\s*['"](feature_flags|remote_config|flags|feature_toggles)['"]\s*\)""")
    if tbl:
        fails.append("server-side switch table read: " + ", ".join(app.ev(tbl)[:3]))
    rev = app.grep(r"(?i)\b(is_?)?app_?review(er)?_?mode\b|\bisReviewer\b|\bisAppReview\b|\breviewer_?mode\b|"
                   r"\bapple_?reviewer\b", no_literals=True)
    if rev:
        fails.append("reviewer detection: " + ", ".join(app.ev(rev)[:3]))
    dt = app.grep(r"DateTime\.now\(\)\.(isAfter|isBefore)\(\s*DateTime\(\s*20\d\d")
    if dt:
        human.append("date-gated behaviour (check it is not a post-review switch): " + ", ".join(app.ev(dt)[:3]))
    dl = deep_link_only_routes(app)
    if dl:
        human.append("routes no code navigates to (deep-link-only or dead): " + "; ".join(cap(dl, 4)))
    ok.append(f"checked: {len(FLAG_PKGS)} remote-config/flag SDKs in pubspec.lock, PostHog flag calls, "
              "switch tables, reviewer detection, date gates, GoRoute paths")
    if fails:
        return FAIL, fails + human, HYG
    if human:
        return HUMAN, human, HYG
    return PASS, ok, HYG


def c_preview(app, feats):
    row = sc_row(app, "App preview video")
    if row and row[0] == PASS:
        return HUMAN, [row[1], "watch the preview: footage must be captured from the app itself"], CREAT
    return NA, [(row[1] if row else "no app preview video found in the repo") + " — rule applies only when a preview exists"], CREAT


BRANDS = ["Google", "Amazon", "Apple", "iPhone", "iPad", "Uber", "Lyft", "Instagram", "WhatsApp", "TikTok",
          "YouTube", "Netflix", "Spotify", "Grammarly", "Duolingo", "DoorDash", "Airbnb", "Expedia", "Booking.com",
          "Zillow", "Robinhood", "Venmo", "PayPal", "Tinder", "Bumble", "Strava", "Fitbit", "MyFitnessPal", "Waze",
          "Snapchat", "Facebook", "Twitter", "Pinterest", "Reddit", "ChatGPT", "OpenAI", "Canva", "Photoshop",
          "Lightroom", "Shazam", "SoundCloud", "Pandora", "Audible", "Kindle", "Walmart", "Costco", "Instacart",
          "Grubhub", "Yelp", "Tripadvisor", "Kayak", "Skyscanner", "Coinbase", "Binance", "Cash App", "Revolut",
          "Flightradar24", "FlightAware", "Headspace", "Peloton", "Garmin", "Noom", "Uber Eats", "Ticketmaster",
          "Eventbrite", "Etsy", "eBay", "Shopify", "Gmail", "Outlook", "Telegram", "Discord"]


def brand_hits(text: str) -> list[str]:
    return [b for b in BRANDS if re.search(rf"(?i)(?<![\w]){re.escape(b)}(?![\w])", text)]


def c_name_keywords(app, feats):
    en = (app.rec.get("copy") or {}).get("en") or {}
    probs, ev = [], []
    for nm in ("App Store name", "App Store keywords (<=100)"):
        r = sc_row(app, nm)
        if r:
            ev.append(r[1])
            if r[0] == FAIL:
                probs.append(r[1])
    for k, lim in (("name", 30), ("subtitle", 30)):
        v = en.get(k) or ""
        if len(v) > lim:
            probs.append(f"{k} is {len(v)} chars (> {lim}): '{v}'")
    for k in ("name", "subtitle", "keywords"):
        b = brand_hits(en.get(k) or "")
        if b:
            probs.append(f"store/apps/{app.repo}.json copy.en.{k} names another company's brand: {', '.join(b)}")
    if probs:
        return FAIL, probs, ASO
    return HUMAN, ev + [f"no brand from a {len(BRANDS)}-name list in name/subtitle/keywords; the list is partial — "
                        "a person checks keywords for competitor and trademark terms"], ASO


PLATFORM_WORDS = r"\bAndroid\b|(?i:\bgoogle play\b|\bplay store\b|play\.google\.com)"


# Proper names that contain a platform word but are not about the platform.
PLATFORM_NAMES = r"Android (Authority|Police|Central)"


def c_third_party_platforms(app, feats):
    rx = re.compile(PLATFORM_WORDS)
    hard, soft = [], []
    for w, t, f, n, key in app.ui_strings():
        if not rx.search(t):
            continue
        if key is None:
            line = dict(app.lines.get(f, [])).get(n, "")
            if re.search(r"(?i)user-agent", line):
                continue                                  # an HTTP header, not UI
            if " " not in t.strip() or re.search(PLATFORM_NAMES, t):
                soft.append(w)                            # a URL/domain/identifier or a proper name
            elif platform_conditional(app, f, n):
                soft.append(w + " (platform branch)")
            else:
                hard.append(w)
            continue
        uses = arb_usage(app, key)
        if not uses or all(platform_conditional(app, uf, un) for uf, un, _ in uses):
            soft.append(w + (" (key unused)" if not uses else " (used only in platform branches)"))
        else:
            hard.append(w + " used at " + ", ".join(app.where(uf, un) for uf, un, _ in uses[:2]))
    meta = meta_hits(app, PLATFORM_WORDS)
    if hard or meta:
        return FAIL, cap(meta + hard) + (["to confirm: " + "; ".join(cap(soft, 3))] if soft else []), \
            (COMP if meta and not hard else DEV)
    if soft:
        return HUMAN, ["confirm iOS never shows these (URLs, identifiers, proper names, platform branches): "
                       + "; ".join(cap(soft))], DEV
    return PASS, ["no 'Android'/'Google Play'/'Play Store'/play.google.com in iOS metadata, lib/ strings or the English ARB"], DEV


BG_MODE_USE = {
    "audio": r"package:(just_audio_background|audio_service|just_audio|audioplayers|flutter_tts)/|AudioService\.init|JustAudioBackground\.init",
    "location": BG_LOCATION_CODE,
    "fetch": r"package:(workmanager|background_fetch)/|Workmanager\(\)|BackgroundFetch\.",
    "processing": r"package:(workmanager|background_fetch)/|Workmanager\(\)|BackgroundFetch\.",
    "remote-notification": r"package:(firebase_messaging|onesignal_flutter)/",
    "voip": r"package:(flutter_callkit_incoming|callkeep)/",
    "bluetooth-central": SENSITIVE_PERMS["BLUETOOTH_SCAN"],
    "bluetooth-peripheral": SENSITIVE_PERMS["BLUETOOTH_SCAN"],
}


def c_background_modes(app, feats):
    modes = app.info.get("UIBackgroundModes") or []
    bad, ok, unk = [], [], []
    for mode in modes:
        pat = BG_MODE_USE.get(mode)
        if pat is None:
            unk.append(mode)
            continue
        h = app.grep(pat)
        (ok if h else bad).append(f"{mode}: " + (app.ev(h)[0] if h else "no code that runs in this mode"))
    if bad:
        return FAIL, [f"ios/Runner/Info.plist UIBackgroundModes {modes}"] + bad + ok, DEV
    if unk:
        return HUMAN, ok + [f"modes with no detector: {unk}"], DEV
    return PASS, [f"UIBackgroundModes {modes}, each used: "] + ok, DEV


def c_power(app, feats):
    st, ev, _ = c_background_modes(app, feats) if app.info.get("UIBackgroundModes") else (PASS, ["no UIBackgroundModes"], DEV)
    if st == FAIL:
        return FAIL, ev, DEV
    return HUMAN, ev + ["battery/heat under normal use needs a person on a device"], AAR


def ipa_needed(app):
    return (HUMAN, [f"no staged IPA at {app.ipa} — build one (scripts/build_ipa.py) to check the binary"], SEC)


def c_private_api(app, feats):
    if not app.ipa.exists():
        return ipa_needed(app)
    needles = [b"/System/Library/PrivateFrameworks/", b"LSApplicationWorkspace", b"UIGetScreenImage",
               b"MGCopyAnswer", b"libMobileGestalt"]
    hits = [f"{n.rsplit('/', 1)[-1]}: {x.decode()}" for n, data in app.bins().items() for x in needles if x in data]
    if hits:
        return FAIL, [app.ipa_label()] + cap(hits), SEC
    return PASS, [f"{app.ipa_label()}: {len(app.bins())} Mach-O(s); no PrivateFrameworks link, LSApplicationWorkspace, "
                  "UIGetScreenImage or MobileGestalt (scope: these markers only)"], SEC


def c_dynamic_code(app, feats):
    found = [p for p in DYNAMIC_CODE_PKGS if p in app.lock]
    if found:
        return FAIL, [f"pubspec.lock contains code-loading package(s): {', '.join(found)}"], SEC
    return PASS, [f"none of {', '.join(DYNAMIC_CODE_PKGS)} in pubspec.lock ({len(app.lock)} packages)"], SEC


def c_webkit(app, feats):
    used = [p for p in ("webview_flutter", "flutter_inappwebview") if app.uses(p)]
    if used:
        return PASS, [f"{', '.join(used)} renders with WKWebView on iOS"] + feats.get("webview", [])[:2], DEV
    return HUMAN, ["web view found but not via webview_flutter/flutter_inappwebview: " + "; ".join(feats.get("webview", [])[:3])], DEV


def c_ads_extensions(app, feats):
    if not app.ipa.exists():
        return ipa_needed(app)
    bad = [n for n, data in app.bins().items() if ".appex/" in n and b"GoogleMobileAds" in data]
    if bad:
        return FAIL, ["ads SDK inside an app extension: " + ", ".join(bad)], DEV
    return HUMAN, [f"{app.ipa_label()}: no app extension links GoogleMobileAds",
                   "packages/agl_ads caps interstitials (3 min, 2 warm-up transitions); a person checks placement and close buttons"], AAR


def c_iap(app, feats):
    row = ar_row(app, "iap-2.1b")
    ext = feats.get("external_purchase_links", [])
    st = row[0] if row else HUMAN
    ev = [row[1] if row else "not in docs/apple-requirements.json"]
    if ext:
        return worst(st, HUMAN), ev + ["external payment path present — confirm it sells physical goods/services only: "
                                       + "; ".join(ext[:3])], DEV
    return st, ev + ["no Stripe/PayPal/Gumroad/Patreon checkout in lib/"], DEV


def c_subscriptions_restore(app, feats):
    h = app.grep(r"restorePurchases\s*\(|Purchases\.restorePurchases|restoreTransactions")
    if not h:
        return FAIL, ["sells a subscription but nothing calls restorePurchases()"] + feats.get("subscriptions", [])[:2], DEV
    return HUMAN, ["restore present: " + ", ".join(app.ev(h)[:2]),
                   "a person checks price/term/auto-renew disclosure and the EULA/privacy links on the paywall"], COMP


def c_affiliate(app, feats):
    sites = affiliate_sites(app)
    site_files = {f for f, _, _ in sites}
    disc_files = {}
    for w, t, f, n, key in app.ui_strings():
        if " " in t and re.search(AFF_DISCLOSURE, t):
            if key is None:
                disc_files.setdefault(f, w)
            else:
                for uf, un, _ in arb_usage(app, key):
                    disc_files.setdefault(uf, f"{w} used at {app.where(uf, un)}")
    if not disc_files:
        return FAIL, ["affiliate links with no disclosure text anywhere in lib/ or the English ARB: "
                      + "; ".join(cap(app.ev(sites), 4))], DEV
    g = graph(app)
    names_in = collections.defaultdict(set)
    for dd in g.defs:
        if dd["cls"] is None:
            names_in[dd["file"]].add(dd["name"])
    for c, (cf, _, _) in g.classes.items():
        names_in[cf].add(c)

    def near(sf):
        if sf in disc_files:
            return disc_files[sf]
        for df, w in disc_files.items():
            dsrc = app.dart.get(df, "")
            if any(re.search(rf"\b{re.escape(nm)}\b", dsrc) for nm in names_in[sf]):
                return w + f" (renders {app.rel(sf)})"
            ssrc = app.dart.get(sf, "")
            if any(re.search(rf"\b{re.escape(nm)}\b", ssrc) for nm in names_in[df]):
                return w + f" (embedded by {app.rel(sf)})"
        return None
    far = [app.rel(sf) for sf in sorted(site_files) if not near(sf)]
    ev = [f"{len(sites)} affiliate site(s) in {len(site_files)} file(s)",
          "disclosure: " + "; ".join(cap(list(disc_files.values()), 3))]
    if far:
        return HUMAN, ev + ["no disclosure in or next to: " + ", ".join(far[:5])], DEV
    return PASS, ev, DEV


def c_real_apps(app, feats):
    p = M / f"ai-office/projects/real-apps/continue/{app.repo}.json"
    d = load(p, None)
    if d is None:
        return HUMAN, ["no Real Apps QA record (ai-office/projects/real-apps/continue/) — qa-reviewer has not checked it"], PM
    v = d.get("last_verdict")
    ev = [f"{p.relative_to(M)} ({mtime(p)}): last QA verdict '{v}', {len(d.get('must_fix') or [])} must-fix item(s)"]
    if v == "pass":
        return PASS, ev, PM
    if v == "fail":
        return FAIL, ev + [str(x)[:160] for x in (d.get("must_fix") or [])[:2]], PM
    return HUMAN, ev + [str(x)[:160] for x in (d.get("must_fix") or [])[:2]], PM


def retire_recommended(app):
    txt = read(M / "ai-office/projects/real-apps/overlap.md")
    return app.repo in set(re.findall(r"\b([A-Za-z][\w-]+) is retired", txt))


def c_spam(app, feats, apple: bool = True):
    holds = load(M / "docs/store-holds.json", {})
    h = holds.get(app.repo) if apple else None
    dif = sc_row(app, "4.3 differentiation statement")
    qa = c_real_apps(app, feats)
    ev = ([f"docs/store-holds.json: Apple hold {h['guideline']} ({h.get('why')}), seen {h.get('seen')}"] if h else []) + \
         ([dif[1]] if dif else []) + qa[1][:1]
    if retire_recommended(app):
        return FOUNDER, ev + ["ai-office/projects/real-apps/overlap.md recommends retiring/merging this app — founder decision"], FND
    if (dif and dif[0] == FAIL) or (h and h.get("guideline") in ("4.2.6", "4.3", "4.3(a)") and qa[0] != PASS):
        return FAIL, ev, PM
    return HUMAN, ev + ["duplication is judged against the whole portfolio; a person reads the overlap analysis"], PM


def c_spam_google(app, feats):
    """Play has no differentiation statement; judged on the product (Real Apps QA) and the overlap analysis."""
    qa = c_real_apps(app, feats)
    if retire_recommended(app):
        return FOUNDER, qa[1][:1] + ["ai-office/projects/real-apps/overlap.md recommends retiring/merging this app — founder decision"], FND
    if qa[0] == FAIL:
        return FAIL, qa[1], PM
    return HUMAN, qa[1] + ["a person checks minimum functionality and duplication against our other listings"], PM


NOTIF_REQ = (r"requestNotificationsPermission\s*\(|IOSFlutterLocalNotificationsPlugin|FirebaseMessaging\.instance\."
             r"requestPermission|messaging\.requestPermission|Permission\.notification\.request|"
             r"OneSignal\.Notifications\.requestPermission")


def notification_request_sites(app: App) -> list[tuple[pathlib.Path, int, int, str]]:
    """[(file, line, pos, why)] where a notification permission prompt can start."""
    out = []
    for f, src in app.dart.items():
        for m in re.finditer(NOTIF_REQ, src):
            if m.group(0) == "IOSFlutterLocalNotificationsPlugin":
                # resolvePlatformSpecificImplementation<IOS...>()?.requestPermissions(...)
                tail = src[m.end():m.end() + 160]
                if ".requestPermissions(" not in tail:
                    continue
            out.append((f, src.count("\n", 0, m.start()) + 1, m.start(), m.group(0)))
        for m in re.finditer(r"\b(DarwinInitializationSettings|IOSInitializationSettings)\s*\(", src):
            close = match_close(src, m.end() - 1)
            args = src[m.end():close]
            if not re.search(r"requestAlertPermission:\s*false", args):
                out.append((f, src.count("\n", 0, m.start()) + 1, m.start(),
                            "DarwinInitializationSettings without requestAlertPermission: false (initialize() prompts)"))
    # comments are not code
    keep = []
    for f, n, pos, why in out:
        if any(ln == n for ln, _ in app.lines.get(f, [])):
            keep.append((f, n, pos, why))
    return keep


def c_push_at_launch(app, feats):
    sites = notification_request_sites(app)
    if not sites:
        return PASS, ["no notification-permission request in lib/ (requestPermission/requestNotificationsPermission/"
                      "default DarwinInitializationSettings)"], DEV
    g = graph(app)
    reach = g.reach()
    fails, human, ok = [], [], []
    for f, n, pos, why in sites:
        if not g.masked[f][pos:pos + 5].strip():
            ok.append(f"{app.rel(f)}:{n} inside a user-action callback")
            continue
        i = g.enclosing(f, pos)
        if i is None:
            human.append(f"{app.rel(f)}:{n} {why} (enclosing function not parsed)")
            continue
        d = g.defs[i]
        r = reach.get(i)
        label = f"{app.rel(f)}:{n} {why} in {d['cls'] + '.' if d['cls'] else ''}{d['name']}"
        if r and r[0]:
            fails.append(label + " — runs at launch: " + " ".join(r[1]))
        elif r:
            human.append(label + " — may run at launch (call path through an untyped receiver): " + " ".join(r[1][-3:]))
        else:
            opened = None
            for cls in sorted(g.classes):
                init = [(t, f"{cls}.initState") for t in g.by_cls[cls].get("initState", [])]
                if init:
                    rr = g.reach(6, init).get(i)
                    if rr and rr[0]:
                        opened = (cls, rr[1])
                        break
            if opened:
                human.append(label + f" — prompts as soon as {opened[0]} opens, without a tap: " + " ".join(opened[1]) +
                             f" — check whether {opened[0]} is the first screen")
            else:
                ok.append(label + " — not reached from main() or any screen's initState without a user action")
    if fails:
        return FAIL, fails + human, DEV
    if human:
        return HUMAN, human + ok, DEV
    return PASS, ok + ["heuristic call graph (10 hops; on*-callbacks and route builders count as user actions)"], DEV


def c_ai(app, feats):
    return HUMAN, ["AI output: a person checks it is labelled as AI-generated and moderated"] + feats["ai_generated"][:3], AAR


def c_siwa(app, feats):
    siwa = feats.get("_siwa", [])
    third = feats.get("sign_in_third_party", [])
    if not siwa:
        return FAIL, ["third-party login offered with no Sign in with Apple: " + "; ".join(third[:3])], DEV
    if "com.apple.developer.applesignin" not in app.ent:
        return FAIL, ["Sign in with Apple in code (" + siwa[0] + ") but ios/Runner/*.entitlements lacks "
                      "com.apple.developer.applesignin — it fails on iOS"], DEV
    return PASS, ["third-party: " + third[0], "Sign in with Apple: " + siwa[0],
                  "entitlement com.apple.developer.applesignin present"], DEV


def privacy_link(app):
    url = app.grep(r"""['"][^'"]*(privacy|/policy/)[^'"]*['"]""")
    url = [x for x in url if re.search(r"""['"](https?://|/)[^'"]*(privacy|policy)""", x[2], re.I)]
    if url:
        return app.ev(url)
    files = {}
    for w, t, f, n, key in app.ui_strings():
        if re.search(r"(?i)^\s*(privacy policy|privacy notice|privacy)\s*$", t):
            for uf in ([f] if key is None else [u[0] for u in arb_usage(app, key)]):
                files.setdefault(uf, w)
    for f in app.grep(r"\bmiscPrivacyPolicy\b"):
        files.setdefault(f[0], app.where(f[0], f[1], f[2]))
    out = []
    for f, w in files.items():
        if re.search(r"launchUrl|launchUrlString|\blaunch\(|WebView|openUrl|_open\w*\(", app.dart.get(f, "")):
            out.append(f"{w} (label + link opener in {app.rel(f)})")
    return out


def c_privacy_policy(app, feats):
    page = sc_row(app, "Privacy & support URLs serve the right page")
    link = privacy_link(app)
    ev = [page[1] if page else "policy page not measured (scripts/verify_policy_urls.py + store_checklist.py)"]
    pd = load(M / f"docs/predelivery/{app.repo}.json", {})
    row = next((r for r in pd.get("rows", []) if r.get("id") == "2.5"), None)
    if row:
        ev.append(f"docs/predelivery/{app.repo}.json 2.5: {row['state']} {row['evidence']}")
    if not link:
        return FAIL, ev + ["no in-app privacy-policy link in lib/ (no privacy URL literal, no 'Privacy' label next to a link opener)"], DEV
    ev.append("in-app link: " + "; ".join(link[:2]))
    if not page:
        return HUMAN, ev, COMP
    return (FAIL if page[0] == FAIL else page[0] if page[0] != NA else HUMAN), ev, (COMP if page[0] == FAIL else DEV)


def c_purpose_wording(app, feats):
    row = ar_row(app, "purpose-strings-90683")
    keys = {k: v for k, v in app.info.items() if k.endswith("UsageDescription")}
    ev = [row[1] if row else "not in docs/apple-requirements.json"]
    if row and row[0] == FAIL:
        return FAIL, ev, PRIV
    return HUMAN, ev + [f"read each purpose string ({len(keys)}): " + "; ".join(f"{k}='{str(v)[:60]}'" for k, v in list(keys.items())[:4])], PRIV


def c_minimisation(app, feats):
    if not app.ipa.exists():
        return ipa_needed(app)
    found = set()
    # Beyond privacy_scan.RULES (which lists what makes a key REQUIRED), other
    # APIs that legitimately use a key, so a declared key is not called unused.
    also = [(b"AVAudioEngine", ["NSMicrophoneUsageDescription"]), (b"recordPermission", ["NSMicrophoneUsageDescription"]),
            (b"AVAudioApplication", ["NSMicrophoneUsageDescription"]),
            (b"PHAssetChangeRequest", ["NSPhotoLibraryAddUsageDescription"]),
            (b"PHAssetCreationRequest", ["NSPhotoLibraryAddUsageDescription"])]
    for data in app.bins().values():
        for needle, ks in list(PS.RULES) + also:
            if needle in data:
                found.update(ks)
    judged = {k for _, ks in PS.RULES for k in ks}
    info = app.ipa_info()
    extra = sorted(k for k in info if k in judged and k not in found)
    if extra:
        return FAIL, [f"{app.ipa_label()} declares purpose string(s) for APIs no binary in it references: {', '.join(extra)}"], PRIV
    return PASS, [f"{app.ipa_label()}: every judged purpose string is backed by an API in the binary "
                  f"({len([k for k in info if k in judged])} declared)"], PRIV


def c_ads_consent(app, feats):
    att = ar_row(app, "att-2.1")
    ev = [att[1] if att else "att-2.1 not measured"]
    agl = app.grep(r"AglAds\.initialize\s*\(")
    ump = app.grep(r"ConsentInformation\.instance|ConsentForm\.|AglConsent\.gather\s*\(")
    if agl:
        ev.append("UMP consent gathered before ads by AglAds.initialize() (packages/agl_ads/lib/src/ads.dart): "
                  + app.ev(agl)[0])
    elif ump:
        ev.append("UMP consent calls: " + app.ev(ump)[0])
    else:
        return FAIL, ev + ["ads with no UMP consent flow (no AglAds.initialize(), no ConsentInformation)"], DEV
    return worst(att[0] if att else HUMAN, PASS), ev, DEV


def c_location(app, feats):
    pl = app.info.get("NSLocationWhenInUseUsageDescription")
    always_req = app.grep(r"requestAlwaysAuthorization|Permission\.locationAlways\.request")
    bg = feats.get("background_location", [])
    ev = []
    if not pl:
        return FAIL, ["uses location but ios/Runner/Info.plist has no NSLocationWhenInUseUsageDescription"] + feats["location"][:2], PRIV
    ev.append(f"NSLocationWhenInUseUsageDescription='{str(pl)[:80]}'")
    if always_req and not any("Info.plist" not in b for b in bg):
        return FAIL, ev + ["asks for Always location with no background location use: " + ", ".join(app.ev(always_req)[:2])], DEV
    ev.append("no Always-location request" if not always_req else "Always requested and background use present")
    return PASS, ev, PRIV


def c_5_6(app, feats):
    st, ev, _ = c_hidden_features(app, feats)
    h = load(M / "docs/store-holds.json", {}).get(app.repo)
    if st == FAIL:
        return FAIL, ev, HYG
    if h and h.get("guideline", "").startswith("5.6"):
        return FOUNDER, [f"docs/store-holds.json: 5.6 hold seen {h.get('seen')} — MA-043, account holder replies"] + ev[:1], FND
    return st, ev, HYG


def c_review_prompts(app, feats):
    inc = ui_hits(app, r"(?i)(rate|review)[^.]{0,40}\b(to (unlock|get|earn|receive)|for (free|a reward|coins|points|"
                       r"premium))|\b(unlock|reward|coins|points|premium)\b[^.]{0,40}\b(rat(e|ing)|review) (us|the app|this app)")
    custom = ui_hits(app, r"(?i)\b(enjoying|like|love) (the|this|our) app\b|\brate (us|this app|our app)\b|"
                          r"leave (us )?a (5[- ]star|review)|\bfive stars?\b")
    gate = [f for f in app.dart if re.search(r"RatingBar|flutter_rating_bar", app.dart[f])
            and re.search(r"itms-apps://|action=write-review|apps\.apple\.com", app.dart[f])]
    native = app.grep(r"InAppReview\.instance|requestReview\s*\(")
    if inc[0] or inc[1]:
        return FAIL, ["review incentive wording: " + "; ".join(cap(inc[0] + inc[1], 4))], DEV
    if custom[0] or custom[1] or gate:
        return HUMAN, ["custom review prompt — must hand off to the system prompt and never filter by rating: "
                       + "; ".join(cap(custom[0] + custom[1] + [app.rel(f) + " (rating widget + store link)" for f in gate], 4))], DEV
    return PASS, ["no custom rating prompt, incentive or rating gate in lib/ strings"
                  + (f"; system prompt via in_app_review at {app.ev(native)[0]}" if native else "")], DEV


REQUIRED_REASON = {
    "NSPrivacyAccessedAPICategoryFileTimestamp": [
        b"\x00_stat\x00", b"\x00_fstat\x00", b"\x00_lstat\x00", b"\x00_fstatat\x00", b"\x00_getattrlist\x00",
        b"\x00_fgetattrlist\x00", b"\x00_getattrlistbulk\x00", b"\x00_getattrlistat\x00", b"NSFileCreationDate",
        b"NSFileModificationDate", b"NSURLContentModificationDateKey", b"NSURLCreationDateKey"],
    "NSPrivacyAccessedAPICategorySystemBootTime": [b"\x00_mach_absolute_time\x00", b"systemUptime"],
    "NSPrivacyAccessedAPICategoryDiskSpace": [
        b"\x00_statfs\x00", b"\x00_fstatfs\x00", b"\x00_statvfs\x00", b"\x00_fstatvfs\x00", b"NSFileSystemFreeSize",
        b"NSFileSystemSize", b"NSURLVolumeAvailableCapacityKey", b"NSURLVolumeAvailableCapacityForImportantUsageKey",
        b"NSURLVolumeAvailableCapacityForOpportunisticUsageKey", b"NSURLVolumeTotalCapacityKey"],
    "NSPrivacyAccessedAPICategoryActiveKeyboards": [b"activeInputModes"],
    "NSPrivacyAccessedAPICategoryUserDefaults": [b"NSUserDefaults"],
}


def ipa_manifests(app) -> dict[str, set[str]]:
    """{owner ('app' or 'Frameworks/X.framework'): declared categories} from every PrivacyInfo.xcprivacy."""
    out = collections.defaultdict(set)
    with zipfile.ZipFile(app.ipa) as z:
        for n in z.namelist():
            if not n.endswith("PrivacyInfo.xcprivacy"):
                continue
            m = re.search(r"\.app/(Frameworks/[^/]+\.framework)/", n)
            owner = m.group(1) if m else "app"
            try:
                pl = plistlib.loads(z.read(n))
            except Exception:
                continue
            for t in pl.get("NSPrivacyAccessedAPITypes") or []:
                out[owner].add(t.get("NSPrivacyAccessedAPIType"))
            out.setdefault(owner, set())
    return out


def c_required_reason(app, feats):
    if not app.ipa.exists():
        src = app.d / "ios/Runner/PrivacyInfo.xcprivacy"
        return HUMAN, [f"no staged IPA; source manifest {'present' if src.exists() else 'MISSING'} — "
                       "build an IPA to compare declarations with the binary"], PRIV
    decl = ipa_manifests(app)
    missing = []
    for n, data in app.bins().items():
        m = re.search(r"(Frameworks/[^/]+\.framework)/", n)
        owner = m.group(1) if m else "app"
        have = decl.get(owner, set()) | decl.get("app", set())
        for cat, needles in REQUIRED_REASON.items():
            hit = next((x for x in needles if x in data), None)
            if hit and cat not in have:
                missing.append(f"{n.rsplit('/', 1)[-1]}: {cat.replace('NSPrivacyAccessedAPICategory', '')} "
                               f"({hit.strip(chr(0).encode()).decode()})")
    if missing:
        return FAIL, [f"{app.ipa_label()}: required-reason API used with no declaration in its own or the app's "
                      "PrivacyInfo.xcprivacy (ITMS-91053):"] + cap(missing, 8), PRIV
    return PASS, [f"{app.ipa_label()}: every required-reason API in {len(app.bins())} Mach-O(s) is declared "
                  f"(app manifest: {sorted(c.replace('NSPrivacyAccessedAPICategory', '') for c in decl.get('app', set()))})"], PRIV


# Apple's "commonly used third-party SDKs" that must ship a privacy manifest
# (and a signature). Written from knowledge of Apple's list — verify against
# developer.apple.com/support/third-party-SDK-requirements.
APPLE_SDK_LIST = {
    "Abseil", "AFNetworking", "Alamofire", "AppAuth", "BoringSSL", "openssl_grpc", "Capacitor", "Charts",
    "connectivity_plus", "Cordova", "device_info_plus", "DKImagePickerController", "DKPhotoGallery", "FBAEMKit",
    "FBLPromises", "FBSDKCoreKit", "FBSDKCoreKit_Basics", "FBSDKLoginKit", "FBSDKShareKit", "file_picker",
    "FirebaseABTesting", "FirebaseAuth", "FirebaseCore", "FirebaseCoreDiagnostics", "FirebaseCoreExtension",
    "FirebaseCoreInternal", "FirebaseCrashlytics", "FirebaseDynamicLinks", "FirebaseFirestore",
    "FirebaseInstallations", "FirebaseMessaging", "FirebaseRemoteConfig", "Flutter", "flutter_inappwebview",
    "flutter_local_notifications", "fluttertoast", "FMDB", "geolocator_apple", "GoogleDataTransport",
    "GoogleSignIn", "GoogleToolboxForMac", "GoogleUtilities", "grpcpp", "GTMAppAuth", "GTMSessionFetcher",
    "hermes", "image_picker_ios", "IQKeyboardManager", "IQKeyboardManagerSwift", "Kingfisher", "leveldb",
    "Lottie", "MBProgressHUD", "nanopb", "OneSignal", "OneSignalCore", "OneSignalExtension", "OneSignalOutcomes",
    "OpenSSL", "OrderedSet", "package_info", "package_info_plus", "path_provider", "path_provider_ios",
    "Promises", "Protobuf", "Reachability", "RealmSwift", "RxCocoa", "RxRelay", "RxSwift", "SDWebImage",
    "share_plus", "shared_preferences_ios", "SnapKit", "sqflite", "Starscream", "SVProgressHUD", "SwiftyGif",
    "SwiftyJSON", "Toast", "UnityFramework", "url_launcher", "url_launcher_ios", "video_player_avfoundation",
    "wakelock", "webview_flutter_wkwebview",
}


def c_sdk_manifests(app, feats):
    if not app.ipa.exists():
        return HUMAN, [f"no staged IPA at {app.ipa}"], PRIV
    names = app.zip_names()
    fws = sorted({m.group(1) for n in names for m in [re.search(r"\.app/Frameworks/([^/]+)\.framework/", n)] if m})
    listed = [f for f in fws if f in APPLE_SDK_LIST]
    missing = [f for f in listed if not any(re.search(rf"\.app/Frameworks/{re.escape(f)}\.framework/.*PrivacyInfo\.xcprivacy$", n)
                                            for n in names)]
    if missing:
        return FAIL, [f"{app.ipa_label()}: listed SDK framework(s) without a PrivacyInfo.xcprivacy (ITMS-91061): {', '.join(missing)}"], PRIV
    return PASS, [f"{app.ipa_label()}: {len(listed)} of {len(fws)} frameworks are on Apple's SDK list; each carries a "
                  f"privacy manifest ({', '.join(listed[:8])}{'...' if len(listed) > 8 else ''})",
                  "not checked: SDK signatures"], PRIV


# ------------------------------------------------------------------ Google checks

def c_target_sdk(app, feats):
    v, where = target_sdk(app)
    if v is None:
        return HUMAN, [where], DEV
    ev = [f"targetSdk {v}: {where}", f"Play requires >= {PLAY_TARGET_SDK_REQUIRED} (PLAY_TARGET_SDK_REQUIRED — verify)"]
    return (PASS if v >= PLAY_TARGET_SDK_REQUIRED else FAIL), ev, DEV


def c_16k(app, feats):
    rows, when = _doc("docs/store-gates.json")
    r = next((x for x in rows or [] if x.get("app") == app.repo), None)
    if not r or r.get("align16k") is None:
        return HUMAN, [f"align16k not measured for {app.repo} in docs/store-gates.json"], DEV
    return (PASS if r["align16k"] else FAIL), [f"docs/store-gates.json ({when}) align16k={r['align16k']}"], DEV


def c_data_safety(app, feats):
    p = M / f"docs/console-answers/{app.repo}.md"
    if not p.exists() or "## Data safety" not in read(p):
        return FAIL, [f"{p.relative_to(M)} has no Data safety answers — scripts/console_answers.py"], PPA
    return FOUNDER, [f"answers prepared in {p.relative_to(M)} ({mtime(p)}); the Console form is a founder action"], FND


def c_account_deletion_google(app, feats):
    a = sc_row(app, "Account-deletion page (if accounts)")
    b = ar_row(app, "account-deletion-5.1.1v")
    ev = [x[1] for x in (a, b) if x]
    sts = [x[0] for x in (a, b) if x]
    if not sts:
        return HUMAN, ["neither the deletion page nor in-app deletion is measured"], BE
    st = worst(*sts) if FAIL in sts or HUMAN in sts else (PASS if PASS in sts else HUMAN)
    if a and a[0] == NA and FAIL not in sts:
        st = HUMAN
        ev.append("store_checklist decides 'accounts' from apps.json auth providers, which is older than the code")
    return st, ev, BE


def c_permissions(app, feats):
    a = app.android()
    perms = a["perms"]
    unused, used = [], []
    for p, e in sorted(perms.items()):
        pat = SENSITIVE_PERMS.get(p) or (FGS_USE if p.startswith("FOREGROUND_SERVICE") else None)
        if pat is None:
            continue
        if p in LEGACY_STORAGE and e["max_sdk"] and e["max_sdk"] <= 32:
            continue
        h = app.grep(pat)
        (used if h else unused).append(f"{app.perm_ev(p)}" + (f" — used at {app.ev(h)[0]}" if h else " — no code uses it"))
    ev = [f"merged release permissions: source manifests + {a['plugins_read']} plugin manifest(s) from pubspec.lock"
          + (f"; removed with tools:node=remove: {', '.join(a['removed'])}" if a["removed"] else "")]
    if a["unresolved"]:
        ev.append(f"not in ~/.pub-cache (run flutter pub get): {', '.join(a['unresolved'][:6])}")
    if unused:
        return FAIL, ev + unused + used[:3], DEV
    if a["unresolved"]:
        return HUMAN, ev + used, DEV
    return PASS, ev + (used or ["no sensitive permission declared"]), DEV


def perm_rule(names, owner=DEV, label=""):
    def check(app, feats):
        perms = app.android()["perms"]
        hit = [app.perm_ev(n) for n in names if n in perms]
        if hit:
            return FAIL, [f"declared in the merged manifest: {', '.join(hit)}" + (f" — {label}" if label else "")], owner
        return PASS, [f"none of {', '.join(names)} in the merged release manifest "
                      f"(source + {app.android()['plugins_read']} plugin manifests)"], owner
    return check


def c_bg_location_google(app, feats):
    perms = app.android()["perms"]
    code = app.grep(BG_LOCATION_CODE)
    if "ACCESS_BACKGROUND_LOCATION" in perms and not code:
        return FAIL, [app.perm_ev("ACCESS_BACKGROUND_LOCATION") + " with no background location code"], DEV
    if "ACCESS_BACKGROUND_LOCATION" in perms:
        return FOUNDER, ["background location used: " + app.ev(code)[0],
                         "Play Console background-location declaration + video is a founder action"], FND
    return PASS, ["no ACCESS_BACKGROUND_LOCATION in the merged manifest"] + feats.get("background_location", [])[:2], DEV


def c_photos_google(app, feats):
    perms = app.android()["perms"]
    media = [p for p in ("READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO") if p in perms]
    core = app.grep(r"PhotoManager\.|package:photo_manager/")
    if media and not core:
        return FAIL, [", ".join(app.perm_ev(p) for p in media) + " but the app only picks media (use the photo picker)"], DEV
    if media:
        return FOUNDER, ["broad media access is core (" + app.ev(core)[0] + ")",
                         "Play Console photo/video permissions declaration is a founder action"], FND
    return PASS, ["no READ_MEDIA_IMAGES/READ_MEDIA_VIDEO; media chosen via the system picker"] + feats.get("photos", [])[:1], DEV


def c_fgs(app, feats):
    a = app.android()
    perms = a["perms"]
    typed = [p for p in perms if p.startswith("FOREGROUND_SERVICE_")]
    svc = [(s, at) for s, at in a["services"] if at.get("android:foregroundServiceType")]
    if "FOREGROUND_SERVICE" in perms and not typed:
        return FAIL, [app.perm_ev("FOREGROUND_SERVICE") + " without any FOREGROUND_SERVICE_<TYPE> permission (Android 14)"], DEV
    if not app.grep(FGS_USE):
        return FAIL, ["foreground-service permissions with no code that starts one: " + ", ".join(app.perm_ev(p) for p in perms if p.startswith("FOREGROUND_SERVICE"))], DEV
    return FOUNDER, [f"types: {', '.join(typed)}; services: " + ", ".join(f"{at.get('android:name')}={at['android:foregroundServiceType']}" for _, at in svc[:3]),
                     "Play Console foreground-service declaration is a founder action"], FND


def c_exact_alarm(app, feats):
    perms = app.android()["perms"]
    use = app.grep(SENSITIVE_PERMS["SCHEDULE_EXACT_ALARM"])
    if "USE_EXACT_ALARM" in perms:
        return FAIL, [app.perm_ev("USE_EXACT_ALARM") + " is reserved for alarm-clock/calendar apps"], DEV
    if not use:
        return FAIL, [app.perm_ev("SCHEDULE_EXACT_ALARM") + " but nothing schedules an exact alarm"], DEV
    return PASS, [app.perm_ev("SCHEDULE_EXACT_ALARM") + " used at " + app.ev(use)[0]], DEV


def c_accessibility(app, feats):
    a = app.android()
    bad = [f"{s}: {at.get('android:name')}" for s, at in a["services"]
           if "BIND_ACCESSIBILITY_SERVICE" in at.get("android:permission", "")]
    if bad:
        return FAIL, ["AccessibilityService declared: " + ", ".join(bad)], DEV
    return PASS, [f"no service bound to BIND_ACCESSIBILITY_SERVICE in source or {a['plugins_read']} plugin manifests"], DEV


def c_families(app, feats):
    ev = ["Target audience form is a founder action (answers in docs/console-answers)"]
    if "kids" in feats and "ads" in feats and not app.grep(r"tagForChildDirectedTreatment|TagForChildDirectedTreatment"):
        return FAIL, ["child audience detected and ads without child-directed treatment"] + feats["kids"][:1], DEV
    return FOUNDER, ev, FND


def c_metadata_google(app, feats):
    en = (app.rec.get("copy") or {}).get("en") or {}
    probs, ev = [], []
    for nm in ("Play title", "Play short description (<=80)", "Full description"):
        r = sc_row(app, nm)
        if r:
            ev.append(r[1])
            if r[0] == FAIL:
                probs.append(r[1])
    title = en.get("title") or en.get("name") or ""
    full = en.get("full_description") or en.get("description") or ""
    if len(title) > 30:
        probs.append(f"Play title {len(title)} chars (> 30)")
    if len(full) > 4000:
        probs.append(f"full description {len(full)} chars (> 4000)")
    b = brand_hits(title)
    if b:
        probs.append(f"title names another brand: {', '.join(b)}")
    if probs:
        return FAIL, probs, ASO
    return HUMAN, ev + ["a person checks the listing for keyword stuffing, ranking claims and emoji/caps misuse"], ASO


def c_impersonation(app, feats):
    en = (app.rec.get("copy") or {}).get("en") or {}
    b = brand_hits(" ".join([en.get("name") or "", en.get("title") or ""]))
    if b:
        return FAIL, [f"store name uses another company's brand: {', '.join(b)}"], ASO
    return HUMAN, ["no listed brand in the store name; a person checks icon/name similarity to other apps"], AAR


def c_deceptive(app, feats):
    st, ev, _ = c_hidden_features(app, feats)
    if st == FAIL:
        return FAIL, ev, HYG
    return HUMAN, c_fake_data(app, feats)[1] + ev[:1], DEV


def c_malware(app, feats):
    st, ev, _ = c_dynamic_code(app, feats)
    perms = app.android()["perms"]
    if st == FAIL or "REQUEST_INSTALL_PACKAGES" in perms:
        return FAIL, ev + ([app.perm_ev("REQUEST_INSTALL_PACKAGES")] if "REQUEST_INSTALL_PACKAGES" in perms else []), SEC
    return HUMAN, ev + ["no REQUEST_INSTALL_PACKAGES", "undisclosed data collection is judged against the Data safety form (privacy-engineer)"], SEC


def c_ai_google(app, feats):
    rep = app.grep(REPORT_CTRL)
    if not rep:
        return FAIL, ["AI-generated output with no report/flag control in lib/"] + feats["ai_generated"][:2], DEV
    return HUMAN, ["report control: " + app.ev(rep)[0], "a person checks it sits on the AI output"], DEV


def c_payments_google(app, feats):
    billing = [p for p in ("in_app_purchase", "purchases_flutter") if app.uses(p)]
    if feats.get("external_purchase_links"):
        return HUMAN, ["external payment present — digital goods must use Play Billing: " + "; ".join(feats["external_purchase_links"][:2])], DEV
    if billing:
        return PASS, [f"Play Billing via {', '.join(billing)}"], DEV
    return HUMAN, ["sells in-app but neither in_app_purchase nor purchases_flutter is imported"], DEV


def c_dating(app, feats):
    gate = [w for w, t, *_ in app.ui_strings() if re.search(r"(?i)\b18\+|\bat least 18\b|\b18 or older\b|date of birth|birth ?date", t)]
    gate += app.ev(app.grep(r"\bdateOfBirth\b|\bbirthDate\b|\bageGate\b"))
    if not gate:
        return FAIL, ["dating app with no age gate (18+/date of birth) in lib/"], DEV
    return HUMAN, ["age gate: " + gate[0], "a person checks it blocks under-18s and that safety tools exist"], DEV


def c_government(app, feats):
    rx = r"(?i)not (affiliated|endorsed|associated|connected) with|\bunofficial\b|independent (app|tool)"
    hits = [w for w, t, *_ in app.ui_strings() if re.search(rx, t)] + \
           [w for w, t in app.ios_metadata() if re.search(rx, t)]
    agency = r"\b(USCIS|IRS|DMV|FAA|NOAA|Social Security Administration)\b"
    in_listing = [w for w, t in app.ios_metadata() if re.search(agency, t)]
    if not hits and in_listing:
        return FAIL, ["the listing presents government information (" + "; ".join(meta_hits(app, agency)[:2]) +
                      ") with no 'not affiliated with' statement in the app or listing"], COMP
    if not hits:
        return HUMAN, ["government data/agency in the app (" + "; ".join(feats["government_topic"][:2]) +
                       ") — decide whether it provides government information; if so add a source + "
                       "'not affiliated with' statement to the listing"], COMP
    return HUMAN, ["non-affiliation statement: " + "; ".join(hits[:2]), "a person checks it is prominent and the data source is named"], COMP


def c_contact(app, feats):
    d = load(DIST / "play-gap-audit.json", {}).get(app.repo)
    if d is None:
        return HUMAN, [f"{app.repo} not in {DIST}/play-gap-audit.json — run scripts/play_gap_audit.py"], COMP
    gaps = [g for g in d.get("gaps", []) if g.startswith("contact")]
    ev = [f"{DIST}/play-gap-audit.json ({mtime(DIST / 'play-gap-audit.json')}): gaps {d.get('gaps') or 'none'}"]
    return (FAIL if gaps else PASS), ev, COMP


def c_dev_info(app, feats):
    return from_sc("Privacy & support URLs serve the right page", COMP)(app, feats)


CHECKS = {
    ("apple", "1.1.6"): c_fake_data,
    ("apple", "1.2"): from_ar("ugc-1.2"),
    ("apple", "1.5"): c_dev_info,
    ("apple", "1.6"): c_data_security,
    ("apple", "2.1(a)"): from_ar("launch-2.1a", "qa-reviewer"),
    ("apple", "2.1(b)"): from_ar("iap-2.1b"),
    ("apple", "2.1"): c_info_needed,
    ("apple", "2.2"): c_beta,
    ("apple", "2.3.1"): c_hidden_features,
    ("apple", "2.3.3"): from_ar("screenshots-2.3.3", CREAT),
    ("apple", "2.3.4"): c_preview,
    ("apple", "2.3.6"): from_sc("Apple age rating answered"),
    ("apple", "2.3.7"): c_name_keywords,
    ("apple", "2.3.10"): c_third_party_platforms,
    ("apple", "2.4.1"): from_ar("launch-2.1a", "qa-reviewer"),
    ("apple", "2.4.2"): c_power,
    ("apple", "2.5.1"): c_private_api,
    ("apple", "2.5.2"): c_dynamic_code,
    ("apple", "2.5.4"): c_background_modes,
    ("apple", "2.5.6"): c_webkit,
    ("apple", "2.5.15"): from_ar("upload-scan-plist"),
    ("apple", "2.5.18"): c_ads_extensions,
    ("apple", "3.1.1"): c_iap,
    ("apple", "3.1.2"): c_subscriptions_restore,
    ("apple", "3.2.1"): c_affiliate,
    ("apple", "4.2"): c_real_apps,
    ("apple", "4.2.6"): c_spam,
    ("apple", "4.3(a)"): c_spam,
    ("apple", "4.5.4"): c_push_at_launch,
    ("apple", "4.7"): c_ai,
    ("apple", "4.8"): c_siwa,
    ("apple", "5.1.1(i)"): c_privacy_policy,
    ("apple", "5.1.1(ii)"): c_purpose_wording,
    ("apple", "5.1.1(iii)"): c_minimisation,
    ("apple", "5.1.1(v)"): from_ar("account-deletion-5.1.1v", BE),
    ("apple", "5.1.2"): c_ads_consent,
    ("apple", "5.1.5"): c_location,
    ("apple", "5.4"): from_ar("vpn-notes", COMP),
    ("apple", "5.6"): c_5_6,
    ("apple", "5.6.1"): c_review_prompts,
    ("apple", "ITMS-91053"): c_required_reason,
    ("apple", "ITMS-91061"): c_sdk_manifests,
    ("apple", "ITMS-90683"): from_ar("purpose-strings-90683", PRIV),
    ("apple", "Export compliance"): from_sc("Export compliance answered"),
    ("google", "Target API"): c_target_sdk,
    ("google", "16 KB pages"): c_16k,
    ("google", "App bundle"): from_sc("Android .aab signed with this app's upload key", "release-manager"),
    ("google", "Data safety"): c_data_safety,
    ("google", "User Data"): c_privacy_policy,
    ("google", "Account deletion"): c_account_deletion_google,
    ("google", "Permissions"): c_permissions,
    ("google", "Location"): c_bg_location_google,
    ("google", "Photo/video"): c_photos_google,
    ("google", "Foreground services"): c_fgs,
    ("google", "Exact alarms"): c_exact_alarm,
    ("google", "SMS/Call log"): perm_rule(sorted(SMS_CALL), label="restricted to default SMS/phone handlers"),
    ("google", "All files"): perm_rule(["MANAGE_EXTERNAL_STORAGE"]),
    ("google", "Package visibility"): perm_rule(["QUERY_ALL_PACKAGES"]),
    ("google", "Accessibility"): c_accessibility,
    ("google", "Install packages"): perm_rule(["REQUEST_INSTALL_PACKAGES"]),
    ("google", "Families"): c_families,
    ("google", "Metadata"): c_metadata_google,
    ("google", "Impersonation"): c_impersonation,
    ("google", "Spam"): c_spam_google,
    ("google", "Deceptive behavior"): c_deceptive,
    ("google", "Malware/MUwS"): c_malware,
    ("google", "UGC"): from_ar("ugc-1.2"),
    ("google", "AI-generated content"): c_ai_google,
    ("google", "Payments"): c_payments_google,
    ("google", "Dating"): c_dating,
    ("google", "Government"): c_government,
    ("google", "Contact details"): c_contact,
}

# Owners for rules that fall through to HUMAN/FOUNDER by their catalogue text.
DEFAULT_OWNER = {"apple": AAR, "google": PPA}


# ------------------------------------------------------------------ evaluation

def catalogue() -> dict:
    return json.loads(CATALOGUE.read_text())


def fallback(rule: dict):
    chk = rule["check"].strip()
    owner = DEFAULT_OWNER[rule["store"]]
    if chk.lower().startswith("n/a"):
        return NA, [f"catalogue: {chk}"], owner
    if chk.lower().startswith("founder"):
        return FOUNDER, [chk.split(":", 1)[-1].strip()], FND
    if chk.lower().startswith("human"):
        return HUMAN, [chk.split(":", 1)[-1].strip() if ":" in chk else f"a person reviews: {rule['title']}"], owner
    return HUMAN, [f"no automated check for '{chk}' — a person verifies: {rule['rule'][:160]}"], owner


def applies(rule: dict, feats: dict) -> tuple[bool, list[str]]:
    a = rule["applies"].strip()
    if a == "all":
        return True, ["all apps"]
    if a == "none":
        return False, []
    tags = [t.strip() for t in a.split("|")]
    hit = [t for t in tags if feats.get(t)]
    return bool(hit), hit


# Judged on the staged IPA alone; a finding on a build older than the source is not
# a finding about the current app, so it is reported for a person instead.
BINARY_RULES = {("apple", "2.5.1"), ("apple", "5.1.1(iii)"), ("apple", "ITMS-91053"), ("apple", "ITMS-91061"),
                ("apple", "2.5.18")}


def audit(a: dict) -> dict:
    app = App(a)
    feats, extra = detect(app)
    feats_all = dict(feats, _siwa=extra.get("sign_in_with_apple", []))
    cat = catalogue()
    lc0 = app.last_commit()
    ipa_stale = bool(app.ipa.exists() and lc0 and app.ipa.stat().st_mtime < lc0)
    rows = []
    for rule in cat["rules"]:
        ok, why = applies(rule, feats)
        if not ok:
            tags = rule["applies"]
            rows.append({**{k: rule[k] for k in ("store", "ref", "title", "check")}, "applies": False,
                         "applies_because": [], "state": NA,
                         "evidence": ["catalogue marks it not applicable" if tags == "none" else
                                      f"not applicable: none of [{tags}] detected in the current source"],
                         "owner": DEFAULT_OWNER[rule["store"]]})
            continue
        fn = CHECKS.get((rule["store"], rule["ref"]))
        try:
            st, ev, owner = fn(app, feats_all) if fn else fallback(rule)
        except Exception as e:  # a broken check must show, not pass
            st, ev, owner = FAIL, [f"check errored: {type(e).__name__}: {e}"], DEV
        if fn and rule["check"].lower().startswith("founder") and st == PASS:
            st = FOUNDER
        if st == FAIL and (rule["store"], rule["ref"]) in BINARY_RULES and ipa_stale:
            st = HUMAN
            ev = ["the staged IPA predates the last source commit — rebuild (scripts/build_ipa.py) and re-run; "
                  "on the staged build:"] + list(ev)
        rows.append({**{k: rule[k] for k in ("store", "ref", "title", "check")}, "applies": True,
                     "applies_because": why if why != ["all apps"] else ["all"],
                     "state": st, "evidence": [str(e) for e in ev], "owner": FND if st == FOUNDER else owner})
    counts = collections.Counter(r["state"] for r in rows)
    lc = app.last_commit()
    now = datetime.datetime.now()
    return {
        "app": app.repo,
        "generated_at": now.isoformat(timespec="seconds"),
        "generated_epoch": int(now.timestamp()),
        "catalogue_about": cat.get("_about"),
        "app_dir": app.rel(app.d) if app.d != app.repo_dir else ".",
        "source_commit_time": datetime.datetime.fromtimestamp(lc).isoformat(timespec="minutes") if lc else None,
        "ipa": app.ipa_label() + (" — OLDER than the last source commit; binary checks describe that build"
                                  if app.ipa.exists() and lc and app.ipa.stat().st_mtime < lc else ""),
        "target_sdk_required": PLAY_TARGET_SDK_REQUIRED,
        "features": {k: {"count": len(v), "evidence": cap(v)} for k, v in sorted(feats.items())},
        "sign_in_with_apple": cap(extra.get("sign_in_with_apple", [])),
        "android_permissions": sorted(app.android()["perms"]),
        "summary": {s: counts.get(s, 0) for s in STATES},
        "failing": [f"{r['store']} {r['ref']}" for r in rows if r["state"] == FAIL],
        "rules": rows,
    }


def md_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def render(res: dict) -> str:
    s = res["summary"]
    out = [f"# Store policy audit — {res['app']}", "",
           f"Generated by `scripts/store_policy_audit.py` at {res['generated_at']} — do not edit. "
           f"Rules: `store/policy/catalogue.json` (written from knowledge; verify against the official text).", "",
           f"**{s[FAIL]} FAIL · {s[HUMAN]} HUMAN · {s[FOUNDER]} FOUNDER · {s[PASS]} PASS · {s[NA]} n-a** "
           f"— submit-ready: **{'no' if s[FAIL] or s[HUMAN] or s[FOUNDER] else 'yes'}** "
           "(every applicable rule PASS; HUMAN and FOUNDER items are open until a person signs them off).", "",
           f"- App dir: `{res['app_dir']}` · last source commit {res['source_commit_time']}",
           f"- IPA: {res['ipa']}",
           f"- Play target API required: {res['target_sdk_required']} (constant; verify)", ""]
    if res["failing"]:
        out += ["## Failing", ""]
        for r in res["rules"]:
            if r["state"] == FAIL:
                out.append(f"- **{r['store']} {r['ref']} — {r['title']}** (owner: {r['owner']})")
                out += [f"  - {e}" for e in r["evidence"]]
        out.append("")
    out += ["## Features detected", "", "| Tag | Count | Evidence |", "| --- | --- | --- |"]
    for k, v in res["features"].items():
        out.append(f"| {k} | {v['count']} | {md_cell('; '.join(v['evidence'][:3]))} |")
    out.append(f"| (Sign in with Apple) | {len(res['sign_in_with_apple'])} | {md_cell('; '.join(res['sign_in_with_apple'][:2]))} |")
    out += ["", f"Merged Android permissions: {', '.join(res['android_permissions']) or 'none'}", ""]
    for store, title in (("apple", "Apple App Review"), ("google", "Google Play")):
        out += [f"## {title}", "", "| Ref | Rule | Applies | State | Owner | Evidence |", "| --- | --- | --- | --- | --- | --- |"]
        for r in res["rules"]:
            if r["store"] != store:
                continue
            ap = ("yes: " + ", ".join(r["applies_because"])) if r["applies"] else "no"
            out.append(f"| {md_cell(r['ref'])} | {md_cell(r['title'])} | {md_cell(ap)} | {r['state']} | {r['owner']} | "
                       f"{md_cell('; '.join(r['evidence']))} |")
        out.append("")
    return "\n".join(out)


def write(res: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{res['app']}.json").write_text(json.dumps(res, indent=1) + "\n")
    (OUT / f"{res['app']}.md").write_text(render(res))


def write_summary() -> dict:
    results = [load(p, None) for p in sorted(OUT.glob("*.json"))]
    results = [r for r in results if r]
    tot = collections.Counter()
    failing = collections.defaultdict(list)
    for r in results:
        tot.update(r["summary"])
        for x in r["rules"]:
            if x["state"] == FAIL:
                failing[(x["store"], x["ref"], x["title"])].append(r["app"])
    cat = catalogue()
    lines = ["# Store policy audit — all apps", "",
             "Generated by `python3 scripts/store_policy_audit.py` — do not edit. Each app: "
             "`docs/store-policy/<App>.md`. Rules: `store/policy/catalogue.json` "
             f"({len(cat['rules'])} rules). Caveat from the catalogue: _{cat.get('_about')}_", "",
             f"**{len(results)} apps · {tot[FAIL]} FAIL · {tot[HUMAN]} HUMAN · {tot[FOUNDER]} FOUNDER · "
             f"{tot[PASS]} PASS · {tot[NA]} n-a.** An app is submit-ready only with 0 FAIL and every HUMAN/FOUNDER "
             "item signed off. predelivery.py check 2.8 blocks TestFlight delivery on any FAIL.", "",
             "## Top failing rules", "", "| Store | Ref | Rule | Apps failing | Apps |", "| --- | --- | --- | --- | --- |"]
    for (store, ref, title), apps in sorted(failing.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| {store} | {md_cell(ref)} | {md_cell(title)} | {len(apps)} | {', '.join(apps)} |")
    lines += ["", "## Per app", "", "| App | FAIL | HUMAN | FOUNDER | PASS | n-a | Failing refs | Generated |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in sorted(results, key=lambda r: (-r["summary"][FAIL], r["app"].lower())):
        s = r["summary"]
        lines.append(f"| [{r['app']}](store-policy/{r['app']}.md) | {s[FAIL]} | {s[HUMAN]} | {s[FOUNDER]} | {s[PASS]} | "
                     f"{s[NA]} | {md_cell(', '.join(r['failing']))} | {r['generated_at']} |")
    lines.append("")
    SUMMARY.write_text("\n".join(lines))
    return {"apps": len(results), "totals": dict(tot), "failing": failing}


# ------------------------------------------------------------------ the gate (predelivery 2.8)

INPUTS = ["store/policy/catalogue.json", "scripts/store_policy_audit.py", "docs/apple-requirements.json",
          "docs/store-checklist-detail.json", "docs/store-gates.json", "docs/store-holds.json"]


def is_stale(a: dict, res: dict | None) -> str | None:
    """Why docs/store-policy/<App>.json no longer describes the app, or None."""
    if not res:
        return "no audit on file"
    t = res.get("generated_epoch") or 0
    repo = a["repo"]
    for rel in INPUTS + [f"store/apps/{repo}.json"]:
        p = M / rel
        if p.exists() and p.stat().st_mtime > t:
            return f"{rel} changed after the audit"
    ipa = DIST / f"{repo}.ipa"
    if ipa.exists() and ipa.stat().st_mtime > t:
        return "the IPA is newer than the audit"
    app = App.__new__(App)
    app.repo, app.repo_dir, app.d = repo, ROOT / repo, SC.app_dir(a)
    lc = App.last_commit(app)
    if lc and lc > t:
        return "the app has a commit newer than the audit"
    rel = "." if app.d == app.repo_dir else str(app.d.relative_to(app.repo_dir))
    try:
        dirty = subprocess.run(["git", "-C", str(app.repo_dir), "status", "--porcelain", "--", rel],
                               capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        dirty = ""
    if dirty:
        newest = 0.0
        for line in dirty.splitlines():
            p = app.repo_dir / line[3:].strip().strip('"').split(" -> ")[-1]
            if p.exists():
                newest = max(newest, p.stat().st_mtime)
        if newest > t:
            return "uncommitted app changes newer than the audit"
    return None


def audit_for_gate(a: dict) -> dict:
    """The current audit for one apps.json entry; re-runs (and rewrites the docs) when stale."""
    f = OUT / f"{a['repo']}.json"
    res = load(f, None)
    why = is_stale(a, res)
    if why:
        res = audit(a)
        res["rerun_reason"] = why
        write(res)
        write_summary()
    return res


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    only = sys.argv[1:]
    if only:
        unknown = set(only) - {x["repo"] for x in apps}
        if unknown:
            print(f"  not in apps.json: {', '.join(sorted(unknown))}")
            return 2
        apps = [x for x in apps if x["repo"] in only]
    any_fail = False
    for a in apps:
        res = audit(a)
        write(res)
        s = res["summary"]
        any_fail = any_fail or bool(s[FAIL])
        print(f"  {a['repo']:18} FAIL {s[FAIL]:2}  HUMAN {s[HUMAN]:2}  FOUNDER {s[FOUNDER]:2}  PASS {s[PASS]:2}  "
              f"n-a {s[NA]:2}  {', '.join(res['failing'])}")
    summ = write_summary()
    t = summ["totals"]
    print(f"\n  {len(apps)} app(s) audited; docs/STORE_POLICY.md covers {summ['apps']}: "
          f"{t.get(FAIL, 0)} FAIL, {t.get(HUMAN, 0)} HUMAN, {t.get(FOUNDER, 0)} FOUNDER, {t.get(PASS, 0)} PASS, "
          f"{t.get(NA, 0)} n-a  -> docs/store-policy/, docs/STORE_POLICY.md")
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
