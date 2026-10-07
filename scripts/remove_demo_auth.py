#!/usr/bin/env python3
"""Delete the test-account and demo-mode paths. Real users only.

    python3 scripts/remove_demo_auth.py --dry-run
    python3 scripts/remove_demo_auth.py --verify          # + analyze and test
    python3 scripts/remove_demo_auth.py yourtube --verify

Sixteen apps shipped three things that should never have been in an app at
all, even behind a debug guard:

  1. a "Use test account" button and a "Demo mode (dev) — skip to app"
     shortcut, both compiled out of release but *visible in every screenshot
     capture*, because captures are debug builds (MA-036 symptom 2);
  2. `_isConfiguredTestAccount`, which compares the typed email and password
     against constants baked into the binary and returns "authenticated"
     without ever asking Supabase — a local fake login;
  3. a "local demo session" persisted to SharedPreferences, which survived
     restarts and made the app look signed in when it was not.

All three existed because the documented QA accounts did not work. They do
now — `scripts/supabase_accounts.py` confirmed them against the real project —
so a tester signs in through Supabase like everybody else, and none of this
has a reason to exist.

Removal is structural, not textual. A regex that deletes `if (showDevShortcuts)
...[` up to the next `]` gets the wrong bracket the moment the block contains a
list, and a half-deleted widget tree still analyzes clean often enough to be
dangerous. So this walks the source with a scanner that understands Dart
strings, comments and nesting, and refuses anything it is not certain about
rather than guessing — every refusal is printed.

Nothing is reported as done without `--verify`, which runs `flutter analyze`
and `flutter test` per app. Analyze alone is not enough: it cannot see a null
check that throws at runtime, which is how a previous codemod here passed a
green analyze while breaking 355 tests.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, flutter_sdk  # noqa: E402

# Members whose whole declaration goes, wherever it is declared.
DEAD_MEMBERS = [
    "_isConfiguredTestAccount",
    "signInWithTestAccount",
    "testAccountEnabled",
    "devAccountEnabled",
    "showDevShortcuts",
    "qaEmail", "qaPassword",
    "devEmail", "devPassword",
    "adminEmail", "adminPassword",
]

# NOT removed here, deliberately. `_kDemoKey` / `auth_demo_session` is the
# persisted local session, and it is also how roughly seven widget tests per
# app get past the sign-in wall. Deleting the read without giving the harness
# another way in just breaks the suites. Tracked as phase B.

# Conditions that gate a demo-only widget. A collection-if on one of these is
# removed along with the widget it guards.
GUARD = re.compile(
    r"\b(?:[\w.]*\bshowDevShortcuts|[\w.]*\btestAccountEnabled"
    r"|[\w.]*\bdevAccountEnabled)\b")

OPEN, CLOSE = "([{", ")]}"


def scan(src: str):
    """Yield (index, char, depth, in_code) with strings and comments masked.

    Dart needs real scanning here: `'...'`, `"..."`, `'''...'''`, r-strings,
    `//`, `/* */`, and `$ { }` interpolation all contain brackets that must
    not count towards nesting.
    """
    i, n, depth = 0, len(src), 0
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if two == "//":
            j = src.find("\n", i)
            j = n if j < 0 else j
            yield from ((k, src[k], depth, False) for k in range(i, j))
            i = j
            continue
        if two == "/*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            yield from ((k, src[k], depth, False) for k in range(i, j))
            i = j
            continue
        if c in "'\"":
            triple = src[i:i + 3]
            q = triple if triple in ("'''", '"""') else c
            j = i + len(q)
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src.startswith(q, j):
                    j += len(q)
                    break
                j += 1
            yield from ((k, src[k], depth, False) for k in range(i, min(j, n)))
            i = j
            continue
        if c in OPEN:
            depth += 1
            yield i, c, depth, True
        elif c in CLOSE:
            yield i, c, depth, True
            depth -= 1
        else:
            yield i, c, depth, True
        i += 1


def code_mask(src: str) -> list[bool]:
    m = [False] * len(src)
    for i, _c, _d, live in scan(src):
        if i < len(src):
            m[i] = live
    return m


def match_bracket(src: str, start: int) -> int:
    """Index just past the bracket opened at `start`."""
    want = CLOSE[OPEN.index(src[start])]
    depth = 0
    for i, c, _d, live in scan(src[start:]):
        if not live:
            continue
        if c == src[start]:
            depth += 1
        elif c == want:
            depth -= 1
            if depth == 0:
                return start + i + 1
    return -1


def doc_start(src: str, pos: int) -> int:
    """Walk back over doc comments, annotations and blank-free lines."""
    ls = src.rfind("\n", 0, pos) + 1
    while ls > 0:
        prev_end = ls - 1
        prev_start = src.rfind("\n", 0, prev_end) + 1
        line = src[prev_start:prev_end].strip()
        if line.startswith(("///", "//", "@", "/*", "*", "*/")):
            ls = prev_start
            continue
        break
    return ls


def enclosing(src: str) -> list[str]:
    """For each index, the nearest unclosed opening bracket character.

    This is what tells a *collection-if* inside a `[ ... ]` widget list apart
    from an ordinary `if` statement inside a method body. Without it the
    removal below walks into service code and deletes control flow: the first
    version of this script ate the body of `AppEnv.validate` and truncated
    `signInWithTestAccount` halfway, because `if (!x.testAccountEnabled)` in a
    method looks identical to a collection-if when you only pattern-match text.
    """
    out = [""] * (len(src) + 1)
    stack: list[str] = []
    for i, c, _d, live in scan(src):
        out[i] = stack[-1] if stack else ""
        if not live:
            continue
        if c in OPEN:
            stack.append(c)
        elif c in CLOSE and stack:
            stack.pop()
    return out


def remove_member(src: str, name: str) -> tuple[str, int]:
    """Remove every declaration of `name` (method, getter or field)."""
    removed = 0
    while True:
        mask = code_mask(src)
        hit = None
        for m in re.finditer(rf"\b{re.escape(name)}\b", src):
            i = m.start()
            if not mask[i]:
                continue
            before = src[max(0, i - 1):i]
            if before == ".":
                continue
            # The name must be followed by something that can only follow a
            # declaration. A trailing `,` means it is a *parameter* — which is
            # how `required bool testAccountEnabled,` was once mistaken for a
            # member, taking the whole enclosing method body with it.
            after = src[m.end():].lstrip(" \t\n")
            if not after or after[0] not in "(={;":
                continue
            line_start = src.rfind("\n", 0, i) + 1
            head = src[line_start:i].strip()
            if not head or head.endswith(("return", "=", "&&", "||", "(", ",", "!")):
                continue
            if not re.search(r"\b(static|bool|String|Future|void|int|double|get)\b",
                             head):
                continue
            hit = (line_start, i, m.end())
            break
        if hit is None:
            return src, removed
        line_start, i, end = hit
        # Find the end of the declaration: a body `{...}`, or `=> ...;`, or `;`.
        j = end
        stop = -1
        while j < len(src):
            if src[j] == "{":
                stop = match_bracket(src, j)
                break
            if src[j] == ";":
                stop = j + 1
                break
            if src[j] == "(":
                j = match_bracket(src, j)
                if j < 0:
                    break
                continue
            j += 1
        if stop < 0:
            return src, removed
        s = doc_start(src, line_start)
        # Swallow one trailing newline so no blank hole is left behind.
        while stop < len(src) and src[stop] in " \t":
            stop += 1
        if stop < len(src) and src[stop] == "\n":
            stop += 1
        src = src[:s] + src[stop:]
        removed += 1


def remove_guarded_widgets(src: str) -> tuple[str, int, list[str]]:
    """Remove `if (<demo guard>) <widget>,` in a collection literal."""
    removed, skipped = 0, []
    while True:
        mask = code_mask(src)
        encl = enclosing(src)
        found = None
        for m in re.finditer(r"\bif\s*\(", src):
            i = m.start()
            if not mask[i]:
                continue
            # Only a collection-if, i.e. one sitting directly inside a list
            # literal. An `if` inside a method body is control flow and is
            # none of this function's business.
            if encl[i] != "[":
                continue
            cond_open = src.index("(", i)
            cond_end = match_bracket(src, cond_open)
            if cond_end < 0:
                continue
            cond = src[cond_open:cond_end]
            if not GUARD.search(cond):
                continue
            found = (i, cond_end)
            break
        if found is None:
            return src, removed, skipped
        i, cond_end = found
        j = cond_end
        while j < len(src) and src[j] in " \t\n":
            j += 1
        # `...[ ... ]` or `...<Widget>[ ... ]` spread, or a single expression.
        if src.startswith("...", j):
            k = j + 3
            while k < len(src) and src[k] in " \t":
                k += 1
            if k < len(src) and src[k] == "<":
                k = src.index("[", k)
            if k >= len(src) or src[k] != "[":
                skipped.append(src[i:i + 70].replace("\n", " "))
                src = src[:i] + "/*AGL-SKIP*/" + src[i:]
                continue
            end = match_bracket(src, k)
        else:
            # Expression up to the comma that closes this collection element.
            # Depth-counted, not match_bracket-and-continue: `continue` does
            # not advance the generator past the bracket, so the scan walked
            # straight into the widget's own argument list and stopped at its
            # first comma. That cut `OutlinedButton(` in half and left its
            # `style:` arguments orphaned in the children list.
            end, depth = -1, 0
            for off, c, _d, live in scan(src[j:]):
                if not live:
                    continue
                p = j + off
                if c in OPEN:
                    depth += 1
                elif c in CLOSE:
                    if depth == 0:
                        end = p
                        break
                    depth -= 1
                elif c == "," and depth == 0 and p > j:
                    end = p
                    break
            if end < 0:
                skipped.append(src[i:i + 70].replace("\n", " "))
                src = src[:i] + "/*AGL-SKIP*/" + src[i:]
                continue
        # An `else` branch means this is not a pure demo-only block.
        tail = src[end:end + 40].lstrip(" \t\n,")
        if tail.startswith("else"):
            skipped.append(src[i:i + 70].replace("\n", " "))
            src = src[:i] + "/*AGL-SKIP*/" + src[i:]
            continue
        while end < len(src) and src[end] in " \t":
            end += 1
        if end < len(src) and src[end] == ",":
            end += 1
        while end < len(src) and src[end] in " \t":
            end += 1
        if end < len(src) and src[end] == "\n":
            end += 1
        start = doc_start(src, src.rfind("\n", 0, i) + 1)
        src = src[:start] + src[end:]
        removed += 1


def remove_named(src: str, name: str) -> tuple[str, int]:
    """Remove `required bool name,` declarations and `name: <expr>,` arguments.

    Deleting a member without deleting the places that pass it just moves the
    breakage. Both forms live inside `(` or `{`, never inside `[`.
    """
    removed = 0
    while True:
        mask, encl = code_mask(src), enclosing(src)
        hit = None
        for m in re.finditer(rf"\b{re.escape(name)}\b", src):
            i = m.start()
            if not mask[i] or encl[i] not in "({":
                continue
            if src[max(0, i - 1):i] == ".":
                continue
            after = src[m.end():]
            dpos = max(src.rfind(ch, 0, i) for ch in "({,\n")
            head = src[dpos + 1:i].strip()
            # `}` and `=` cover an optional parameter with a default,
            # `{bool useTestAccount = false}`, which the analyzer otherwise
            # reports as "a value for optional parameter isn't ever given".
            is_param = bool(re.match(r"^(required\s+)?[\w<>?,\s]*$", head)) and \
                after.lstrip(" \t")[:1] in (",", ")", "}", "=")
            is_arg = after.lstrip(" \t")[:1] == ":" and not head.endswith(("?", ":"))
            if not (is_param or is_arg):
                continue
            hit = (i, m.end(), is_arg)
            break
        if hit is None:
            return src, removed
        i, end, is_arg = hit
        if is_arg:
            j = src.index(":", end) + 1
            stop, depth = -1, 0
            for off, c, _d, live in scan(src[j:]):
                if not live:
                    continue
                p = j + off
                if c in OPEN:
                    depth += 1
                elif c in CLOSE:
                    if depth == 0:
                        stop = p
                        break
                    depth -= 1
                elif c == "," and depth == 0:
                    stop = p + 1
                    break
            if stop < 0:
                return src, removed
        else:
            stop = end
            while stop < len(src) and src[stop] in " \t":
                stop += 1
            if stop < len(src) and src[stop] == "=":
                depth = 0
                for off, c, _d, live in scan(src[stop:]):
                    if not live:
                        continue
                    if c in OPEN:
                        depth += 1
                    elif c in CLOSE:
                        if depth == 0:
                            stop += off
                            break
                        depth -= 1
                    elif c == "," and depth == 0:
                        stop += off
                        break
            while stop < len(src) and src[stop] in " \t":
                stop += 1
            if stop < len(src) and src[stop] == ",":
                stop += 1
        dpos = max(src.rfind(ch, 0, i) for ch in "({,\n")
        line_start = src.rfind("\n", 0, i) + 1
        if not is_arg and src[line_start:i].strip() and dpos > line_start:
            line_start = dpos + 1
        # For a parameter the line prefix is only modifiers and the type —
        # `required bool ` — and must go with the name, or the signature is
        # left as `required bool ,` which still parses far enough to confuse.
        start = line_start if (not is_arg or not src[line_start:i].strip()) else i
        while stop < len(src) and src[stop] in " \t":
            stop += 1
        if stop < len(src) and src[stop] == "\n" and start == line_start:
            stop += 1
        src = src[:start] + src[stop:]
        # Dropping the last named parameter leaves `_submit({})`, which Dart
        # rejects outright: "Named parameter lists cannot be empty."
        src = re.sub(r",\s*\{\s*\}\s*\)", ")", src)
        src = re.sub(r"\(\s*\{\s*\}\s*\)", "()", src)
        removed += 1


DEAD_NAME = re.compile(
    r"\b(?:_isConfiguredTestAccount|signInWithTestAccount|testAccountEnabled"
    r"|devAccountEnabled|showDevShortcuts|useTestAccount"
    r"|qaEmail|qaPassword|devEmail|devPassword|adminEmail|adminPassword)\b")


def has_dead(src: str, a: int, b: int, mask: list[bool]) -> bool:
    """A dead symbol mentioned in *code* between a and b — not in a string.

    Without the mask this matched the regex literal inside the test "no
    committed source ships a literal test credential", whose whole point is
    to name `qaPassword` and friends, and deleted the guard in every app.
    """
    return any(mask[a + m.start()] for m in DEAD_NAME.finditer(src[a:b]))


def top_level_split(cond: str, op: str) -> bool:
    """True when `op` appears directly inside `cond`'s outer parentheses."""
    depth = 0
    for i, c, _d, live in scan(cond):
        if not live:
            continue
        if c in OPEN:
            depth += 1
        elif c in CLOSE:
            depth -= 1
        elif depth == 1 and cond.startswith(op, i):
            return True
    return False


def fold_dead_conditionals(src: str) -> tuple[str, int, list[str]]:
    """Constant-fold `if`s whose condition is now statically known.

    Every removed symbol is false by construction — the accounts no longer
    exist in the binary — so `if (… && testAccountEnabled)` is dead and
    `if (!_isConfiguredTestAccount(…))` is always taken. Folding says that
    once, instead of each call site guessing. A condition this cannot decide
    (a top-level `||`) is left alone and reported.
    """
    folded, skipped = 0, []
    while True:
        mask, encl = code_mask(src), enclosing(src)
        hit = None
        for m in re.finditer(r"\bif\s*\(", src):
            i = m.start()
            if not mask[i] or encl[i] != "{":
                continue
            o = src.index("(", i)
            e = match_bracket(src, o)
            if e < 0 or not has_dead(src, o, e, mask):
                continue
            hit = (i, o, e)
            break
        if hit is None:
            return src, folded, skipped
        i, o, e = hit
        cond = src[o:e]
        inner = cond[1:-1].strip()
        if top_level_split(cond, "||"):
            skipped.append(f"cannot fold (top-level ||): {inner[:70]}")
            src = src[:i] + "/*AGL-SKIP*/" + src[i:]
            continue
        truth = bool(re.match(r"^!\s*[\w.]*(?:" + DEAD_NAME.pattern[2:-2] + r")",
                              inner)) and not top_level_split(cond, "&&")

        def branch(at):
            while at < len(src) and src[at] in " \t\n":
                at += 1
            if at < len(src) and src[at] == "{":
                end = match_bracket(src, at)
                return at, end, src[at + 1:end - 1]
            end = src.find(";", at) + 1
            return at, end, src[at:end]

        tb_s, tb_e, tbody = branch(e)
        rest = src[tb_e:]
        eb_e, ebody = tb_e, None
        mm = re.match(r"\s*else\b", rest)
        if mm:
            eb_s, eb_e, ebody = branch(tb_e + mm.end())
        keep = tbody if truth else ebody
        line_start = src.rfind("\n", 0, i) + 1
        indent = src[line_start:i]
        if keep is None:
            new = ""
            stop = eb_e
            while stop < len(src) and src[stop] in " \t":
                stop += 1
            if stop < len(src) and src[stop] == "\n":
                stop += 1
            src = src[:line_start] + src[stop:]
        else:
            # Re-indent by shifting, not by flattening: `ln.strip()` collapsed
            # every nested line onto the `if`'s own column and turned a
            # readable method into a staircase.
            lines = keep.strip("\n").split("\n")
            base = min((len(l) - len(l.lstrip()) for l in lines if l.strip()),
                       default=0)
            body = "\n".join(
                (indent + l[base:].rstrip()) if l.strip() else ""
                for l in lines)
            src = src[:line_start] + body + "\n" + src[eb_e:].lstrip(" \t")
        folded += 1


def strip_unreachable(src: str) -> tuple[str, int]:
    """Delete statements that follow a `return` or `throw` in the same block.

    Folding `if (!dead) { return msg; }` to `return msg;` is correct and leaves
    the rest of the method stranded behind it. Dart calls that `dead_code`, a
    *warning* — and `--no-fatal-infos` still fails on warnings, so this is not
    cosmetic.
    """
    n = 0
    while True:
        mask, encl = code_mask(src), enclosing(src)
        cut = None
        for m in re.finditer(r"(?m)^[ \t]*(return\b[^\n]*?|throw\b[^\n]*?);",
                             src):
            end = m.end()
            if not mask[m.start()] or encl[m.start()] != "{":
                continue
            rest = src[end:]
            after = rest.lstrip(" \t\n")
            if not after or after.startswith(("}", "case ", "default:")):
                continue
            # Everything up to the end of this block is unreachable.
            depth_close = -1
            for off, c, _d, live in scan(rest):
                if live and c == "}" and enclosing(rest)[off] == "":
                    depth_close = off
                    break
            if depth_close <= 0:
                continue
            cut = (end, end + depth_close)
            break
        if cut is None:
            return src, n
        a, b = cut
        src = src[:a] + "\n" + src[b:]
        n += 1


def remove_dead_statements(src: str) -> tuple[str, int]:
    """Drop whole statements that exist only to service a removed symbol.

    Deliberately narrow: a single line, at statement level, that is a bare
    call — `await prefs.remove(_kDemoKey);`. Anything with an assignment is
    left for the dangling report, because dropping it could change what a
    live variable holds.
    """
    n = 0
    while True:
        mask, encl = code_mask(src), enclosing(src)
        cut = None
        # `[^;()]` matches newlines too, so this once swallowed the whole
        # multi-line `AppEnv.validate(...)` startup check — a production
        # guard — because one of its named arguments mentioned a dead symbol.
        # Single line only, and the call must be the entire statement.
        for m in re.finditer(r"(?m)^[ \t]*(?:await\s+)?[\w.]+\([^;()\n]*\);[ \t]*$",
                             src):
            if not mask[m.start()] or encl[m.start()] != "{":
                continue
            if not has_dead(src, m.start(), m.end(), mask):
                continue
            cut = (m.start(), m.end())
            break
        if cut is None:
            return src, n
        a, b = cut
        while b < len(src) and src[b] in " \t":
            b += 1
        if b < len(src) and src[b] == "\n":
            b += 1
        src = src[:a] + src[b:]
        n += 1


def remove_dead_tests(src: str) -> tuple[str, int]:
    """Remove `test(...)` / `testWidgets(...)` cases for behaviour that is gone.

    A test that asserts `signInWithTestAccount` throws is not a regression
    guard once the method does not exist — it is a compile error.
    """
    n = 0
    while True:
        mask = code_mask(src)
        cut = None
        for m in re.finditer(r"\b(?:testWidgets|test)\s*\(", src):
            i = m.start()
            if not mask[i]:
                continue
            o = src.index("(", i)
            e = match_bracket(src, o)
            if e < 0 or not has_dead(src, o, e, mask):
                continue
            end = e
            while end < len(src) and src[end] in " \t":
                end += 1
            if end < len(src) and src[end] == ";":
                end += 1
            cut = (doc_start(src, src.rfind("\n", 0, i) + 1), end)
            break
        if cut is None:
            return src, n
        a, b = cut
        while b < len(src) and src[b] in " \t":
            b += 1
        if b < len(src) and src[b] == "\n":
            b += 1
        src = src[:a] + src[b:]
        n += 1


def dangling(d: pathlib.Path, names: list[str]) -> list[str]:
    """References to symbols that no longer exist — the work left for a human."""
    out = []
    roots = [d / "lib"] + [d / t for t in ("test", "integration_test")
                           if (d / t).is_dir()]
    for f in sorted(x for r in roots for x in r.rglob("*.dart")):
        if "/generated/" in str(f):
            continue
        src = f.read_text(errors="ignore")
        mask = code_mask(src)
        for n in names:
            for m in re.finditer(rf"\b{re.escape(n)}\b", src):
                if not mask[m.start()]:
                    continue
                line = src[src.rfind("\n", 0, m.start()) + 1:
                           src.find("\n", m.start())].strip()
                out.append(f"{f.relative_to(d)}: {line[:100]}")
    return out


def balanced(src: str) -> bool:
    """Every bracket opened is closed by its own kind.

    A cheap invariant that catches the whole class of bug this script kept
    producing: a removal that cuts through the middle of a widget leaves the
    file unbalanced long before it leaves it unparseable, and Dart's own
    analyzer is too slow to run after every single edit.
    """
    stack = []
    for _i, c, _d, live in scan(src):
        if not live:
            continue
        if c in OPEN:
            stack.append(c)
        elif c in CLOSE:
            if not stack or CLOSE[OPEN.index(stack.pop())] != c:
                return False
    return not stack


ANALYZE = re.compile(
    r"(?:warning|info|error)\s+•\s+(?P<msg>.+?)\s+•\s+(?P<file>[^ ]+):"
    r"(?P<line>\d+):(?P<col>\d+)\s+•\s+(?P<code>[\w_]+)")


# `flutter analyze` and the Dart *compiler* disagree on error format. Analyze
# prints `error • message • file:line:col • code`; the compiler (what
# `flutter test` surfaces) prints `file:line:col: Error: message`. The repair
# pass reads analyze, so it must use the analyze shape — matching only the
# compiler shape is why it silently repaired nothing.
MISSING_CODES = {"undefined_getter", "undefined_method", "undefined_identifier",
                 "undefined_setter", "undefined_named_parameter"}
MISSING_MSG = re.compile(r"(?:Member not found|isn't defined|Undefined name)")


def enclosing_member(src: str, line_no: int) -> str | None:
    """Name of the class member containing a given 1-based line.

    Several apps wrap the shared constants in their own accessor —
    `static String get testPassword => SupabaseConfig.qaPassword;` — so
    deleting `qaPassword` leaves a member whose only purpose was to expose it.
    The analyzer points at the reference; this finds what to delete.
    """
    starts = [0]
    for ln in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(ln))
    if line_no > len(starts) - 1:
        return None
    pos = starts[line_no - 1]
    best = None
    for m in re.finditer(
            r"(?m)^  (?:static\s+)?(?:final\s+)?[\w<>?\[\], ]+?\b"
            r"(?:get\s+)?(?P<name>_?\w+)\s*(?:\(|=>|=|;)", src):
        if m.start() <= pos:
            best = m.group("name")
        else:
            break
    return best


def repair_missing(d: pathlib.Path, flutter: str, rounds: int = 5) -> list[str]:
    """Delete members left dangling by the removal, as the analyzer finds them.

    Several apps wrap the shared constants in their own accessor —
    `static String get testPassword => SupabaseConfig.qaPassword;` — so
    removing `qaPassword` strands a member whose only purpose was to expose
    it. The analyzer points at the reference; this deletes its owner, and
    repeats, because one removal stranded the next.
    """
    done = []
    for _ in range(rounds):
        out = subprocess.run([flutter, "analyze", "--no-fatal-infos"], cwd=d,
                             capture_output=True, text=True, timeout=1800)
        if out.returncode == 0:
            return done
        did = False
        seen = set()
        for m in ANALYZE.finditer(out.stdout + out.stderr):
            if m["code"] not in MISSING_CODES and not MISSING_MSG.search(m["msg"]):
                continue
            if not DEAD_NAME.search(m["msg"]):
                continue
            f = pathlib.Path(m["file"])
            if not f.is_absolute():
                f = d / f
            if not f.exists() or f in seen:
                continue
            src = f.read_text()
            owner = enclosing_member(src, int(m["line"]))
            if not owner:
                continue
            new, n = remove_member(src, owner)
            if not n or not balanced(new):
                continue
            f.write_text(new)
            done.append(f"{f.name}: removed {owner}")
            seen.add(f)
            did = True
        if not did:
            return done
    return done


def tidy(d: pathlib.Path, flutter: str, rounds: int = 3) -> list[str]:
    """Clear the leftovers, using the analyzer as the oracle rather than a guess.

    Removing a member leaves its import unused and its optional parameter
    never-passed. Both are *warnings*, and `--no-fatal-infos` still fails on
    warnings, so the codemod is not finished until they are gone. Asking the
    analyzer where they are beats pattern-matching for them.
    """
    fixed = []
    for _ in range(rounds):
        out = subprocess.run([flutter, "analyze", "--no-fatal-infos"], cwd=d,
                             capture_output=True, text=True, timeout=1800)
        if out.returncode == 0:
            return fixed
        did = False
        for m in ANALYZE.finditer(out.stdout):
            f = pathlib.Path(m["file"])
            if not f.is_absolute():
                f = d / f
            if not f.exists():
                continue
            code, ln = m["code"], int(m["line"])
            src = f.read_text()
            lines = src.splitlines(keepends=True)
            if ln > len(lines):
                continue
            if code == "unused_import":
                del lines[ln - 1]
            elif code == "unused_local_variable" and \
                    lines[ln - 1].rstrip().endswith(";"):
                del lines[ln - 1]
            elif "optional parameter" in m["msg"]:
                name = re.search(r"'([^']+)'", m["msg"])
                if not name:
                    continue
                new, n = remove_named(src, name.group(1))
                if not n or not balanced(new):
                    continue
                f.write_text(new)
                fixed.append(f"{f.name}: dropped parameter {name.group(1)}")
                did = True
                continue
            else:
                continue
            new = "".join(lines)
            if not balanced(new):
                continue
            f.write_text(new)
            fixed.append(f"{f.name}:{ln} {code}")
            did = True
        if not did:
            return fixed
    return fixed


def sh(args, cwd, timeout=1800):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-repair", action="store_true",
                    help="skip the analyzer-driven dangling-member repair; it "
                         "picks the member to delete by heuristic and has been "
                         "seen to choose a local variable")
    ap.add_argument("--revert-on-fail", action="store_true",
                    help="git-restore lib/, test/ and integration_test/ for any "
                         "app still failing after verification, so a run never "
                         "leaves an app half-converted")
    ap.add_argument("--verify-dirty", action="store_true",
                    help="repair, tidy and test every app whose lib/ or test/ "
                         "differs from git — not only the ones changed in "
                         "this run, which is what a re-run would otherwise miss")
    ap.add_argument("--verify", action="store_true",
                    help="run flutter analyze and flutter test per changed app")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    flutter = str(flutter_sdk() / "bin" / "flutter")

    report, touched = {}, []
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        lib = d / "lib"
        if not lib.is_dir():
            continue
        widgets = members = 0
        skipped: list[str] = []
        files: list[str] = []
        roots = [lib] + [d / t for t in ("test", "integration_test")
                         if (d / t).is_dir()]
        for f in sorted(x for r in roots for x in r.rglob("*.dart")):
            if "/generated/" in str(f):
                continue
            src = orig = f.read_text(errors="ignore")
            src, w, sk = remove_guarded_widgets(src)
            src = src.replace("/*AGL-SKIP*/", "")
            for name in DEAD_MEMBERS:
                src, c = remove_member(src, name)
                members += c
            src, fc, fsk = fold_dead_conditionals(src)
            src = src.replace("/*AGL-SKIP*/", "")
            src, uc = strip_unreachable(src)
            src, dc = remove_dead_statements(src)
            src, tc = remove_dead_tests(src)
            members += fc + uc + dc + tc
            sk += fsk
            for name in DEAD_MEMBERS + ["useTestAccount"]:
                src, c = remove_named(src, name)
                members += c
            widgets += w
            skipped += [f"{f.relative_to(d)}: {s}" for s in sk]
            if src != orig:
                if not balanced(src):
                    skipped.append(
                        f"{f.relative_to(d)}: edit left brackets unbalanced, "
                        "file left untouched")
                    continue
                files.append(str(f.relative_to(d)))
                if not args.dry_run:
                    f.write_text(src)
        if widgets or members:
            left = [] if args.dry_run else dangling(d, DEAD_MEMBERS)
            report[repo] = {"widgets": widgets, "members": members,
                            "files": files, "skipped": skipped,
                            "dangling": left}
            touched.append((repo, d))
            print(f"  {repo:16} {widgets} widget block(s), {members} member(s), "
                  f"{len(files)} file(s)"
                  + (f"  [{len(skipped)} SKIPPED]" if skipped else "")
                  + (f"  [{len(left)} dangling]" if left else ""), flush=True)
            for s in skipped:
                print(f"      skipped, needs a human: {s}", flush=True)
            for s in left[:6]:
                print(f"      still references a removed symbol: {s}", flush=True)

    print(f"\n  {'would change' if args.dry_run else 'changed'} {len(report)} app(s)")

    if args.verify_dirty and not args.dry_run:
        for a in manifest:
            d = ROOT / a["repo"] / (a.get("dir") or ".")
            if not (d / "pubspec.yaml").exists():
                continue
            git = subprocess.run(
                ["git", "-C", str(ROOT / a["repo"]), "status", "--porcelain",
                 "--", "lib", "test", "integration_test"],
                capture_output=True, text=True)
            if git.stdout.strip() and (a["repo"], d) not in touched:
                touched.append((a["repo"], d))
        print(f"\n  verifying {len(touched)} app(s) that differ from git")
        args.verify = True

    if args.verify and not args.dry_run:
        print("\n  verifying (analyze, then test) — a codemod is not done "
              "until the tests say so:")
        bad = []
        for repo, d in touched:
            if not args.no_repair:
                for note in repair_missing(d, flutter):
                    print(f"   {repo:16} repaired {note}", flush=True)
            for note in tidy(d, flutter):
                print(f"   {repo:16} tidied {note}", flush=True)
            an = sh([flutter, "analyze", "--no-fatal-infos"], d)
            te = sh([flutter, "test"], d)
            ok = an.returncode == 0 and te.returncode == 0
            print(f"   {repo:16} analyze {'ok' if an.returncode == 0 else 'FAIL'}"
                  f"   test {'ok' if te.returncode == 0 else 'FAIL'}", flush=True)
            if not ok:
                bad.append(repo)
                tail = (an.stdout + an.stderr + te.stdout + te.stderr).strip()
                for line in tail.splitlines()[-8:]:
                    print(f"      {line[:150]}", flush=True)
        if bad and args.revert_on_fail:
            for repo in bad:
                a = next(x for x in manifest if x["repo"] == repo)
                subprocess.run(
                    ["git", "-C", str(ROOT / repo), "checkout", "--",
                     "lib", "test", "integration_test"],
                    capture_output=True, text=True)
                print(f"   {repo:16} REVERTED — left for manual conversion",
                      flush=True)
        report["_verify"] = {"failed": bad, "reverted": bool(args.revert_on_fail)}
        print(f"\n  {len(touched) - len(bad)}/{len(touched)} app(s) green")
        if bad:
            print(f"  FAILING: {', '.join(bad)}")

    out = M / "docs/demo-auth-removal.json"
    if not args.dry_run:
        out.write_text(json.dumps(report, indent=1) + "\n")
        print(f"  -> {out.relative_to(M)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
