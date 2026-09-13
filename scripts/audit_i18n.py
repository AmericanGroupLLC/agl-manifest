#!/usr/bin/env python3
"""Measure how localized each app actually is — not how localized it claims to be.

`audit_release_readiness.py` already records `arb_locales` and `l10n_callsites`.
That pair turned out not to be enough: an app can declare twelve locales, ship
twelve complete ARB catalogues, and still open in English on a Spanish phone,
because

  * no screen ever reads a localized string, or
  * `MaterialApp.locale` is pinned to a fixed `Locale`, which overrides the
    device language outright.

This script measures both, plus the size of the remaining job (how much
user-visible copy is still a Dart string literal), and writes
`docs/i18n-audit.json`. `docs/I18N.md` is written from that file.

    python3 scripts/audit_i18n.py                 # -> docs/i18n-audit.json
    python3 scripts/audit_i18n.py --print         # also dump a table to stdout

Nothing here writes to an app repository.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIRROR = ROOT.parent

# The standard set, read from the package rather than repeated here.
AGL_LOCALES_DART = ROOT / "packages" / "agl_i18n" / "lib" / "src" / "agl_locales.dart"


def read(p: pathlib.Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def first(pattern: str, text: str, group: int = 1) -> str | None:
    m = re.search(pattern, text)
    return m.group(group) if m else None


def standard_locales() -> list[str]:
    """Parse `AglLocales.standard` out of the package source."""
    src = read(AGL_LOCALES_DART)
    m = re.search(r"standard\s*=\s*<Locale>\[(.*?)\];", src, re.S)
    return re.findall(r"Locale\('([a-zA-Z-]+)'", m.group(1)) if m else []


# ── Dart source scanning ──────────────────────────────────────────────────────

GENERATED = re.compile(r"(?:^|/)(?:l10n|generated)/|_localizations(?:_\w+)?\.dart$")

L10N_CALLSITE = re.compile(
    r"\bl10n\.|\bAppLocalizations\.of\(|\bAglL10n\.of\(|\bS\.of\(|\bcontext\.l10n\b"
)

# Five apps read localized strings through a one-line alias getter:
#
#     AppLocalizations get t => AppLocalizations.of(context)!;
#     ...
#     Text(t.emptyState)
#
# Counting only `AppLocalizations.of(` scored AGCleaner at 3 call sites when it
# has 25. The alias name has to be discovered per app and added to the pattern.
# The body must actually resolve a localization. Accepting the return type
# alone matched `S get state => _state;` in BuddyPlay — an unrelated generic —
# and inflated that app from 0 call sites to 852.
ALIAS_GETTER = re.compile(
    r"\b(?:AppLocalizations|AglL10n)\??\s+get\s+(\w+)\s*=>\s*[^;]*\.of\(\s*context"
)


def callsite_pattern(app: pathlib.Path) -> re.Pattern:
    aliases: set[str] = set()
    for f in dart_files(app):
        aliases.update(ALIAS_GETTER.findall(read(f)))
    aliases.discard("l10n")  # already in the base pattern
    if not aliases:
        return L10N_CALLSITE
    extra = "|".join(rf"\b{re.escape(a)}\.[A-Za-z_]" for a in sorted(aliases))
    return re.compile(L10N_CALLSITE.pattern + "|" + extra)

# String literals in positions Flutter renders to a human. Deliberately a
# whitelist of parameters: `'foo'` in a Map key or a route name is not copy, and
# counting it would make every app look worse than it is.
UI_STRING = re.compile(
    r"""(?x)
    (?:
        \b(?:Text|SelectableText|TextSpan)\s*\(\s*
      | \b(?:hintText|labelText|helperText|errorText|counterText|prefixText
           |suffixText|semanticLabel|semanticsLabel|tooltip|labelName)\s*:\s*
      | \b(?:title|subtitle|label|message|description|placeholder|heading
           |buttonText|confirmText|cancelText)\s*:\s*
    )
    (?P<q>'|")(?P<s>(?:\\.|(?!(?P=q))[^\\\n])*)(?P=q)
    """
)

# Literals that are not copy even in a copy position.
NOT_COPY = re.compile(
    r"""(?x)
    ^\s*$
  | ^[^A-Za-z]*$                      # digits, punctuation, spacing
  | ^/                                # route names, paths
  | ://                               # urls
  | \.(?:png|jpg|jpeg|svg|json|ttf|otf|webp|gif|mp3|mp4|riv|lottie)$
  | ^[a-z0-9_]+$                      # single lower_snake token: keys, ids
  | ^[A-Z0-9_]{2,}$                   # SCREAMING_CASE constants
  | ^\$\{?\w+\}?$                     # a bare interpolation
  | ^(?:[yMdHhms]{1,4}[/:.\- ]?)+$    # date/time format patterns
    """
)

# A `locale:` argument that hard-codes a language.
PINNED_LITERAL = re.compile(r"^(?:const\s+)?Locale(?:\.fromSubtags)?\s*\(")

# Anything that asks the platform what language the phone is in. An app whose
# own string layer is keyed off a private `language` preference is only honest
# if something seeds that preference from here on first launch.
DEVICE_LOCALE = re.compile(
    r"platformDispatcher\.locales?\b|window\.locales?\b|Platform\.localeName|"
    r"\bdeviceLocale\b|Localizations\.localeOf"
)

# `String _language = 'en';`, `LanguageCode _language = LanguageCode.en;`,
# `_locale = storage.getString(...) ?? 'en';`
ENGLISH_DEFAULT = re.compile(
    r"""(?x)
    \b(?:String|LanguageCode|var|final)\s+_?(?:language|locale|localeCode|lang)\w*
        \s*=\s*(?:'(?P<a>[a-z]{2})'|LanguageCode\.(?P<b>\w+))
  | \b_?(?:language|locale|localeCode|lang)\w*\s*=\s*[^;\n]*\?\?\s*'(?P<c>[a-z]{2})'
    """
)


def dart_files(app: pathlib.Path, skip_generated: bool = True) -> list[pathlib.Path]:
    lib = app / "lib"
    if not lib.is_dir():
        return []
    out = []
    for p in sorted(lib.rglob("*.dart")):
        rel = str(p.relative_to(lib))
        if skip_generated and GENERATED.search(rel):
            continue
        out.append(p)
    return out


# A file that builds widgets. The denominator for "how much of the UI is
# translated". `*screen*.dart` was the obvious choice and is wrong: seven apps
# in this portfolio put their whole UI in `main.dart`, which made them score
# 0/0 and look finished.
BUILDS_WIDGETS = re.compile(r"Widget\s+build\s*\(\s*BuildContext")

# A hand-rolled translation table: a Dart map of locale -> strings, which is
# what most of these apps had before `agl_i18n` existed. Detected so that an
# app translating through its own module is not scored as untranslated — and,
# just as important, so a module that nothing imports shows up as dead.
OWN_I18N_TABLE = re.compile(
    # `Map<String, Map<String, String>>`, but also `Map<DiningLocale, ...>`:
    # GroceryMatch keys its table by an enum, and keying by the locale type
    # rather than by a string is common enough that requiring `String` missed
    # a whole six-language catalogue.
    r"Map<\w+,\s*Map<\w+,\s*String>>|Map<\w+,\s*[A-Z]\w*Strings>|"
    r"Map<\w+,\s*AppStrings>|static\s+\w+\s+of\(BuildContext"
)


def uncommented(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$|(?<![:'\"])//[^\n]*", "", text)


def ui_files(app: pathlib.Path) -> list[pathlib.Path]:
    return [f for f in dart_files(app) if BUILDS_WIDGETS.search(read(f))]


def own_i18n_modules(app: pathlib.Path) -> list[pathlib.Path]:
    """App-local translation modules (not gen-l10n, not agl_i18n)."""
    lib = app / "lib"
    if not lib.is_dir():
        return []
    out = []
    for p in sorted(lib.rglob("*.dart")):
        rel = str(p.relative_to(lib))
        if "/generated/" in rel or rel.startswith("generated/"):
            continue
        if not re.search(
            r"(?:^|/)(?:i18n|l10n)/|strings?\.dart$|translations?\.dart$|i18n\.dart$|l10n\.dart$",
            rel,
        ):
            continue
        if OWN_I18N_TABLE.search(read(p)):
            out.append(p)
    return out


# Language codes used as keys in a hand-rolled table. Measured separately from
# `supportedLocales` because the two disagree: MyHealth declares twelve locales
# in Dart, in Info.plist and in resConfigs, and its string table has three.
OWN_LANG_KEY = re.compile(r"(?m)^\s*'([a-z]{2})'\s*:|\b[A-Z]\w*(?:Code|Locale)\.([a-z]{2})\b")


def own_i18n_languages(modules: list[pathlib.Path]) -> list[str]:
    codes: set[str] = set()
    seen: set[pathlib.Path] = set()
    for mod in modules:
        for p in [mod] + sorted(mod.parent.rglob("*.dart")):
            if p in seen:
                continue
            seen.add(p)
            for a, b in OWN_LANG_KEY.findall(read(p)):
                codes.add(a or b)
    codes.discard("ok")  # a `'ok': ...` entry is a message key, not a language
    return sorted(codes)


def importers_of(app: pathlib.Path, module: pathlib.Path) -> set[pathlib.Path]:
    """Files that import `module`, by package: or relative path."""
    lib = app / "lib"
    pkg = first(r"(?m)^name:\s*(\S+)", read(app / "pubspec.yaml")) or ""
    rel = module.relative_to(lib).as_posix()
    stem = module.name
    hits = set()
    for f in dart_files(app):
        if f == module:
            continue
        text = read(f)
        for m in re.finditer(r"""(?m)^\s*import\s+['"]([^'"]+)['"]""", text):
            spec = m.group(1)
            if spec == f"package:{pkg}/{rel}":
                hits.add(f)
                break
            if not spec.startswith(("package:", "dart:")):
                try:
                    if (f.parent / spec).resolve() == module.resolve():
                        hits.add(f)
                        break
                except OSError:
                    pass
            elif spec.endswith("/" + stem) and spec.startswith(f"package:{pkg}/"):
                hits.add(f)
                break
    return hits


def balanced(text: str, open_at: int) -> str:
    """Return the substring from the '(' at `open_at` to its matching ')'.

    Paren-counting only, but skipping string literals and comments, which is
    what makes it survive `Text('(')` and `// )`.
    """
    depth = 0
    i = open_at
    n = len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            quote = c
            triple = text.startswith(quote * 3, i)
            i += 3 if triple else 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if triple and text.startswith(quote * 3, i):
                    i += 3
                    break
                if not triple and text[i] == quote:
                    i += 1
                    break
                if not triple and text[i] == "\n":
                    break
                i += 1
            continue
        if text.startswith("//", i):
            i = text.find("\n", i)
            if i < 0:
                break
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i)
            i = (j + 2) if j >= 0 else n
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1]
        i += 1
    return text[open_at:]


def top_level_arg(args: str, name: str) -> str | None:
    """Value of a named argument at depth 1 of a constructor's argument list."""
    depth = 0
    i = 0
    n = len(args)
    pat = re.compile(rf"\b{name}\s*:")
    while i < n:
        c = args[i]
        if c in "'\"":
            quote = c
            triple = args.startswith(quote * 3, i)
            i += 3 if triple else 1
            while i < n:
                if args[i] == "\\":
                    i += 2
                    continue
                if triple and args.startswith(quote * 3, i):
                    i += 3
                    break
                if not triple and args[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if args.startswith("//", i):
            j = args.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "([{":
            depth += 1
            i += 1
            continue
        if c in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 1:
            m = pat.match(args, i)
            if m:
                return _arg_value(args, m.end())
        i += 1
    return None


def _arg_value(args: str, start: int) -> str:
    """Text from `start` up to the comma that ends this argument."""
    depth = 0
    i = start
    n = len(args)
    while i < n:
        c = args[i]
        if c in "'\"":
            quote = c
            i += 1
            while i < n:
                if args[i] == "\\":
                    i += 2
                    continue
                if args[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if args.startswith("//", i):
            j = args.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif c == "," and depth == 0:
            break
        i += 1
    return args[start:i].strip()


APP_CTOR = re.compile(r"\b(MaterialApp|CupertinoApp|WidgetsApp)(?:\.router)?\s*\(")


def find_app_widget(app: pathlib.Path) -> tuple[pathlib.Path, str] | None:
    """The MaterialApp/CupertinoApp argument list that owns `supportedLocales`.

    Falls back to the first app constructor found, so an app with no
    localization at all still reports its `locale:` argument.
    """
    fallback = None
    for f in dart_files(app):
        text = read(f)
        for m in APP_CTOR.finditer(text):
            args = balanced(text, m.end() - 1)
            if "supportedLocales" in args:
                return f, args
            if fallback is None:
                fallback = (f, args)
    return fallback


def resolve_locale_count(app: pathlib.Path, expr: str | None, arb: list[str]) -> tuple[int, str]:
    """How many locales the app actually declares, and where the number came from."""
    std = len(standard_locales())
    if expr is None:
        return 0, "none"
    flat = " ".join(expr.split())
    if "AglLocales.standard" in flat:
        return std, "AglLocales.standard"
    if "withExtras" in flat:
        extras = re.findall(r"Locale\('([a-zA-Z-]+)'", flat)
        return std + len(extras), "AglLocales.withExtras"
    if "supportedLocales" in flat and re.search(r"\b(?:localeController|locale|lp|controller)\b", flat):
        # AglLocaleController.supportedLocales — standard plus constructor extras.
        extras = set()
        for f in dart_files(app):
            for m in re.finditer(r"AglLocaleController\s*\(([^;]*?)\)\s*;", read(f), re.S):
                extras.update(re.findall(r"Locale\('([a-zA-Z-]+)'", m.group(1)))
        return std + len(extras), "AglLocaleController.supportedLocales"
    if "AppLocalizations.supportedLocales" in flat:
        if arb:
            return len(arb), "AppLocalizations.supportedLocales (ARB count)"
        n = hand_rolled_locale_count(app)
        return n, "AppLocalizations.supportedLocales (hand-rolled)"
    literal = re.findall(r"Locale\(\s*'([a-zA-Z-]+)'", flat)
    if literal:
        return len(set(literal)), "literal list"
    # An identifier, possibly with `.map(...)` or a comprehension over it.
    # Resolve it to its definition anywhere in lib/ — including lib/l10n/,
    # which the call-site scan skips but which is exactly where an app that
    # hand-rolled its own i18n keeps the list.
    ident = re.match(r"([A-Za-z_]\w*)", flat)
    if ident:
        n, where = resolve_list_symbol(app, ident.group(1))
        if n:
            return n, where
    if arb:
        return len(arb), "ARB count (expression unresolved)"
    return 0, f"unresolved: {flat[:40]}"


def resolve_list_symbol(app: pathlib.Path, name: str) -> tuple[int, str]:
    """Size of a top-level list literal called `name`, wherever it is declared.

    Counts `Locale('xx')` entries, bare `'xx'` locale-code strings, and
    `Something('xx', ...)` records — `appSupportedLocales` in iMeasure is a
    comprehension over a list of `LanguageInfo`, not of `Locale`.
    """
    decl = re.compile(
        rf"(?m)^\s*(?:const\s+|final\s+)?[\w<>?, ]*\b{re.escape(name)}\s*(?:=|=>)\s*"
        rf"(?:const\s*)?<?[\w<>?, ]*>?\s*\[",
    )
    for f in dart_files(app, skip_generated=False):
        text = read(f)
        m = decl.search(text)
        if not m:
            continue
        body = balanced_bracket(text, text.index("[", m.end() - 1))
        codes = set(re.findall(r"Locale\(\s*'([a-zA-Z-]+)'", body))
        if codes:
            return len(codes), f"{name} in {f.name}"
        codes = set(re.findall(r"\w+\(\s*'([a-z]{2}(?:-[A-Za-z]+)?)'", body))
        if codes:
            return len(codes), f"{name} in {f.name}"
        codes = set(re.findall(r"'([a-z]{2}(?:-[A-Za-z]+)?)'", body))
        if codes:
            return len(codes), f"{name} in {f.name}"
        # A comprehension: `[for (final l in kLanguages) Locale(l.code)]`.
        inner = re.search(r"\bin\s+(\w+)\)", body)
        if inner and inner.group(1) != name:
            return resolve_list_symbol(app, inner.group(1))
    return 0, ""


def balanced_bracket(text: str, open_at: int) -> str:
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1]
    return text[open_at:]


def hand_rolled_locale_count(app: pathlib.Path) -> int:
    """Largest `supportedLocales` list literal in the app, generated files included.

    An app with a hand-written `AppLocalizations` keeps its list inside that
    class, which the call-site scan deliberately skips.
    """
    best = 0
    for f in dart_files(app, skip_generated=False):
        text = read(f)
        for m in re.finditer(r"supportedLocales\s*=\s*(?:const\s*)?<?[\w<>, ]*>?\s*\[(.*?)\]", text, re.S):
            best = max(best, len(set(re.findall(r"Locale\(\s*'([a-zA-Z-]+)'", m.group(1)))))
    return best


# ── Where does MaterialApp.locale actually come from? ─────────────────────────
#
# This is the measurement the whole file exists for, and it is the one a regex
# gets wrong. `locale: settings.locale` is correct in AGStudio (the getter
# returns null until the user picks) and wrong in DriftDate (the getter is
# non-nullable and defaults to English) — the text at the call site is nearly
# identical. So resolution has to know which *class* `settings` is, and read
# that class's member, rather than grepping the repo for any `locale` it can
# find. An earlier version of this script did the latter and reported both
# AGStudio and daily-pulse as pinned; both were false.


class SourceIndex:
    """Class bodies and top-level declarations, for the app plus `agl_i18n`."""

    def __init__(self, app: pathlib.Path):
        self.files: list[tuple[pathlib.Path, str]] = []
        for f in dart_files(app, skip_generated=False):
            self.files.append((f, read(f)))
        pkg = ROOT / "packages" / "agl_i18n" / "lib"
        if pkg.is_dir():
            for f in sorted(pkg.rglob("*.dart")):
                self.files.append((f, read(f)))
        self.classes: dict[str, tuple[str, pathlib.Path]] = {}
        for f, text in self.files:
            for m in re.finditer(r"\bclass\s+(\w+)[^{;]*\{", text):
                name = m.group(1)
                if name not in self.classes:
                    # Keep the header: `extends StateNotifier<Locale?>` is the
                    # part that says whether the state can be null, and it sits
                    # outside the braces.
                    self.classes[name] = (m.group(0) + balanced_brace(text, m.end() - 1), f)
        # The file that declares MaterialApp is searched first. Without that,
        # `final locale = ...` resolves to whichever file sorts earliest, which
        # in CodeDeal was a different `locale` entirely.
        self.scope: pathlib.Path | None = None

    def find(self, pattern: str) -> tuple[re.Match, pathlib.Path] | None:
        rx = re.compile(pattern)
        ordered = self.files
        if self.scope is not None:
            ordered = sorted(self.files, key=lambda fx: fx[0] != self.scope)
        for f, text in ordered:
            m = rx.search(text)
            if m:
                return m, f
        return None


def balanced_brace(text: str, open_at: int) -> str:
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1]
    return text[open_at:]


FOLLOWS = "follows-device"
PINNED = "PINNED"


def classify_locale_arg(
    app: pathlib.Path, idx: SourceIndex, expr: str | None, depth: int = 0
) -> tuple[str, str]:
    """`(verdict, detail)` for `MaterialApp.locale`.

    `follows-device`  null, absent, or a nullable field that starts null
    `PINNED`          a non-null Locale always reaches MaterialApp, so the
                      phone's language is ignored until the user digs into
                      settings
    `unresolved`      could not be traced; read it by hand before trusting it
    """
    if expr is None:
        return FOLLOWS, "argument absent, so it defaults to null"
    if depth > 4:
        return "unresolved", "resolution too deep"

    bare = strip_comments(expr)
    if not bare or bare == "null":
        return FOLLOWS, "null"
    if PINNED_LITERAL.match(bare):
        return PINNED, f"`{bare[:50]}` is never null"

    # `a ?? b`: pinned only if the fallback is pinned.
    if "??" in bare:
        return classify_locale_arg(app, idx, bare.split("??", 1)[1].strip(), depth + 1)

    # `ref.watch(someProvider)` / `context.watch<T>()`
    m = re.match(r"(?:ref|context)\.(?:watch|read)\s*(?:<[^>]*>)?\s*\(\s*([\w.]*)", bare)
    if m and m.group(1):
        return classify_provider(app, idx, m.group(1).split(".")[0], depth + 1)

    parts = [p for p in re.split(r"[.?!]+", bare) if p]
    if len(parts) == 1:
        return classify_symbol(app, idx, parts[0], depth + 1)
    owner, field = parts[0], parts[-1]
    cls = owner_class(idx, owner)
    if cls is None:
        return classify_symbol(app, idx, field, depth + 1)
    return classify_member(idx, cls, field)


def strip_comments(expr: str) -> str:
    return re.sub(r"//.*$", "", " ".join(expr.split())).strip().rstrip(",").strip()


# `SomeProvider<Notifier, State>` — the state is the last type argument, and
# the state is what `ref.watch` hands back.
PROVIDER_DECL = r"\b{name}\s*=\s*\w*(?:Notifier|State|Change|Stream|Future)?Provider(?:\.\w+)?\s*<([^>]*)>"


def provider_state_class(idx: SourceIndex, provider: str) -> str | None:
    hit = idx.find(PROVIDER_DECL.format(name=re.escape(provider)))
    if hit is None:
        return None
    targs = [t.strip() for t in hit[0].group(1).split(",") if t.strip()]
    return targs[-1] if targs else None


def owner_class(idx: SourceIndex, name: str) -> str | None:
    """The class of a variable/parameter/field called `name`."""
    # `final settings = ref.watch(settingsControllerProvider);` — the class is
    # the provider's *state* type, not the notifier's.
    hit = idx.find(rf"\bfinal\s+{re.escape(name)}\s*=\s*(?:ref|context)\.(?:watch|read)\s*(?:<[^>]*>)?\s*\(\s*(\w+)")
    if hit:
        state = provider_state_class(idx, hit[0].group(1))
        if state and state.rstrip("?") in idx.classes:
            return state.rstrip("?")
    for pat in (
        rf"\bfinal\s+{re.escape(name)}\s*=\s*([A-Z]\w*)\s*\(",       # final x = Foo();
        rf"\b(?:final|late|const)?\s*([A-Z]\w*)\??\s+{re.escape(name)}\b\s*[;,){{=]",  # Foo? x;
        rf"Consumer<([A-Z]\w*)>\s*\(\s*builder:\s*\(\s*\w+\s*,\s*{re.escape(name)}\b",
        rf"Consumer2<([A-Z]\w*)\s*,",
        rf"ChangeNotifierProvider<([A-Z]\w*)>",
    ):
        hit = idx.find(pat)
        if hit and hit[0].group(1) in idx.classes:
            return hit[0].group(1)
    return None


def classify_member(idx: SourceIndex, cls: str, field: str) -> tuple[str, str]:
    """Read `cls.field` out of that class's body and decide."""
    entry = idx.classes.get(cls)
    if entry is None:
        return "unresolved", f"class {cls} not found"
    body, where = entry
    # A getter. Nullability of the return type is the whole answer: a
    # `Locale?` getter can hand MaterialApp a null and let the device win; a
    # `Locale` getter never can.
    m = re.search(rf"\bLocale(\??)\s+get\s+{re.escape(field)}\b\s*(?:=>\s*([^;]+);|\{{)", body)
    if m:
        if m.group(1) == "?":
            return FOLLOWS, f"`{cls}.{field}` is a `Locale?` getter ({where.name})"
        return PINNED, (
            f"`{cls}.{field}` is a non-nullable `Locale` getter"
            + (f" returning `{m.group(2).strip()[:40]}`" if m.group(2) else "")
            + f" ({where.name})"
        )
    # A plain field.
    m = re.search(rf"\bLocale(\??)\s+_?{re.escape(field)}\b\s*(=\s*[^;]+)?;", body)
    if m:
        init = (m.group(2) or "").lstrip("= ").strip()
        if not init:
            return FOLLOWS, f"`{cls}.{field}` declared with no initialiser ({where.name})"
        if init == "null":
            return FOLLOWS, f"`{cls}.{field}` starts null ({where.name})"
        if PINNED_LITERAL.match(init):
            return PINNED, f"`{cls}.{field}` starts as `{init[:40]}` ({where.name})"
    # A `StateNotifier<Locale?>` whose super() call sets the initial value.
    m = re.search(r"extends\s+StateNotifier<\s*Locale(\??)\s*>", body)
    if m:
        sup = re.search(r":\s*super\(\s*([^)]*)\)", body)
        if sup and sup.group(1).strip() == "null":
            return FOLLOWS, f"`{cls}` is a StateNotifier starting at null ({where.name})"
        if sup and PINNED_LITERAL.match(sup.group(1).strip()):
            return PINNED, f"`{cls}` starts at `{sup.group(1).strip()[:40]}` ({where.name})"
    return "unresolved", f"`{cls}.{field}` in {where.name}"


def classify_provider(
    app: pathlib.Path, idx: SourceIndex, name: str, depth: int
) -> tuple[str, str]:
    """A Riverpod provider read straight into `locale:`."""
    hit = idx.find(rf"\b{re.escape(name)}\s*=\s*(\w+)\s*<([^>]*)>\s*\(")
    if hit is None:
        return "unresolved", f"provider `{name}` not found"
    m, where = hit
    kind, targs = m.group(1), m.group(2)
    if kind.startswith("StateNotifierProvider"):
        cls = targs.split(",")[0].strip()
        return classify_member(idx, cls, "state") if cls in idx.classes else _notifier_seed(idx, cls, where)
    # StateProvider<Locale?>((ref) => <default>)
    default = strip_comments(_arg_value(m.string, m.end()))
    inner = re.sub(r"^\(\s*\w*\s*\)\s*=>\s*", "", default).strip()
    if targs.strip().endswith("?") and inner in ("null", ""):
        return FOLLOWS, f"`{name}` is a `{targs.strip()}` provider defaulting to null ({where.name})"
    if PINNED_LITERAL.match(inner):
        return PINNED, f"`{name}` defaults to `{inner[:40]}` ({where.name})"
    if targs.strip().endswith("?"):
        return FOLLOWS, f"`{name}` holds `{targs.strip()}` ({where.name})"
    return "unresolved", f"provider `{name}` <{targs}> = {inner[:40]}"


def _notifier_seed(idx: SourceIndex, cls: str, where: pathlib.Path) -> tuple[str, str]:
    entry = idx.classes.get(cls)
    if entry is None:
        return "unresolved", f"notifier {cls} not found"
    body, f = entry
    sup = re.search(r":\s*super\(\s*([^)]*)\)", body)
    if sup and sup.group(1).strip() == "null":
        return FOLLOWS, f"`{cls}` starts at null ({f.name})"
    if sup and PINNED_LITERAL.match(sup.group(1).strip()):
        return PINNED, f"`{cls}` starts at `{sup.group(1).strip()[:40]}` ({f.name})"
    return "unresolved", f"notifier `{cls}` ({f.name})"


def classify_symbol(
    app: pathlib.Path, idx: SourceIndex, name: str, depth: int
) -> tuple[str, str]:
    """A bare identifier passed to `locale:` — a local, a field or a provider."""
    if name in idx.classes:
        return classify_member(idx, name, "locale")
    hit = idx.find(rf"\bLocale(\??)\s+{re.escape(name)}\b\s*(=\s*[^;]+)?;")
    if hit:
        m, where = hit
        init = (m.group(2) or "").lstrip("= ").strip()
        if not init or init == "null":
            return FOLLOWS, f"`Locale{m.group(1)} {name}` starts null ({where.name})"
        if PINNED_LITERAL.match(init):
            return PINNED, f"`{name}` starts as `{init[:40]}` ({where.name})"
    hit = idx.find(rf"\bfinal\s+{re.escape(name)}\s*=\s*([^;]+);")
    if hit:
        return classify_locale_arg(app, idx, hit[0].group(1), depth)
    return "unresolved", f"identifier `{name}`"


INTERPOLATION = re.compile(r"\$\{[^}]*\}|\$\w+")


def is_copy(s: str) -> bool:
    """Is this literal English (or other) prose that a user reads?"""
    if NOT_COPY.search(s):
        return False
    # Strip interpolations first. `'${l.appTitle} 📡'` is a localized value in
    # a decorated wrapper, not a hardcoded string; what is left has no letters.
    plain = INTERPOLATION.sub("", s)
    return bool(re.search(r"[A-Za-z]", plain))


def count_ui_strings(app: pathlib.Path, skip: set[pathlib.Path] = frozenset()) -> tuple[int, int]:
    """(hardcoded user-visible literals, files containing at least one).

    `skip` is the app's own translation modules — the Spanish in a translation
    table is the opposite of a hardcoded string.
    """
    total = 0
    files = 0
    for f in dart_files(app):
        if f in skip:
            continue
        n = sum(1 for m in UI_STRING.finditer(read(f)) if is_copy(m.group("s")))
        total += n
        files += 1 if n else 0
    return total, files


def measure(repo: str, app_dir: str) -> dict:
    app = MIRROR / repo / app_dir
    pubspec = read(app / "pubspec.yaml")
    arb = sorted(
        p.stem.split("_", 1)[1] if "_" in p.stem else p.stem
        for p in (app / "lib" / "l10n").glob("app_*.arb")
    )

    found = find_app_widget(app)
    app_widget_file, args = ("", "") if found is None else (str(found[0].relative_to(app)), found[1])
    supported_expr = top_level_arg(args, "supportedLocales") if args else None
    locale_expr = top_level_arg(args, "locale") if args else None
    delegates_expr = top_level_arg(args, "localizationsDelegates") if args else None

    declared, source = resolve_locale_count(app, supported_expr, arb)
    idx = SourceIndex(app)
    if found is not None:
        idx.scope = found[0]
    verdict, detail = classify_locale_arg(app, idx, locale_expr)
    callsite_rx = callsite_pattern(app)
    callsites = 0
    callsite_files = 0
    for f in dart_files(app):
        n = len(callsite_rx.findall(read(f)))
        callsites += n
        callsite_files += 1 if n else 0

    modules = own_i18n_modules(app)
    readers: set[pathlib.Path] = set()
    for mod in modules:
        readers |= importers_of(app, mod)

    ui = [f for f in ui_files(app) if f not in modules]
    ui_localized = sum(1 for f in ui if callsite_rx.search(read(f)) or f in readers)

    hardcoded, hardcoded_files = count_ui_strings(app, set(modules))

    # Does anything ask the platform what language the phone is in?
    seeds_from_device = any(DEVICE_LOCALE.search(read(f)) for f in dart_files(app))
    own_default = ""
    delegate_backed = any(
        "LocalizationsDelegate" in read(m) or "Localizations.of<" in read(m) for m in modules
    )
    if modules and readers and not delegate_backed:
        for f in dart_files(app):
            m = ENGLISH_DEFAULT.search(read(f))
            if m:
                own_default = m.group("a") or m.group("b") or m.group("c") or ""
                break

    if supported_expr is None:
        verdict, detail = "n/a", "no supportedLocales — the app is not localizable at all"
    elif (
        verdict == FOLLOWS
        and own_default
        and callsites == 0
        and not seeds_from_device
    ):
        # `MaterialApp.locale` is null, so Material's own widgets follow the
        # phone — but the app's copy comes from a private `language` preference
        # that starts at English and is never seeded from the device. The
        # result on a Spanish phone is a Spanish date picker inside an English
        # app, and it is the same store-listing lie as a pinned locale.
        verdict = "english-default"
        detail = (
            f"own string layer defaults to '{own_default}' and nothing reads the "
            f"device locale; MaterialApp.locale is null but does not drive the copy"
        )

    ios_plist = read(app / "ios" / "Runner" / "Info.plist")
    m = re.search(r"<key>CFBundleLocalizations</key>\s*<array>(.*?)</array>", ios_plist, re.S)
    cfbundle = len(re.findall(r"<string>([\w-]+)</string>", m.group(1))) if m else 0

    gradle = ""
    for name in ("build.gradle", "build.gradle.kts"):
        p = app / "android" / "app" / name
        if p.exists():
            gradle = read(p)
            break
    # Groovy says `resConfigs "en", "es"`; the Kotlin DSL says
    # `resourceConfigurations += listOf("en", "es")`. Matching only the first
    # reported 0 for every .kts app, including ones that do set it.
    m = re.search(r"(?:resConfigs?|resourceConfigurations)\s*(?:\+?=)?\s*(?:listOf\s*\()?(.+)", gradle)
    res_configs = len(re.findall(r"[\"']([\w-]+)[\"']", m.group(1))) if m else 0

    return {
        "repo": repo,
        "app_dir": app_dir,
        "dep_agl_i18n": bool(re.search(r"^\s+agl_i18n\s*:", pubspec, re.M)),
        "dep_flutter_localizations": bool(re.search(r"^\s+flutter_localizations\s*:", pubspec, re.M)),
        "generate_flag": bool(re.search(r"^\s+generate:\s*true", pubspec, re.M)),
        "own_l10n_yaml": (app / "l10n.yaml").exists(),
        "arb_locales": arb,
        "app_widget_file": app_widget_file,
        "supported_locales_expr": " ".join(supported_expr.split()) if supported_expr else None,
        "declared_locales": declared,
        "declared_locales_source": source,
        "delegates_expr": (" ".join(delegates_expr.split())[:80]) if delegates_expr else None,
        "uses_agl_delegates": bool(delegates_expr and "aglLocalizationsDelegates" in delegates_expr),
        "locale_expr": " ".join(locale_expr.split()) if locale_expr else None,
        "locale_verdict": verdict,
        "locale_detail": detail,
        "l10n_callsites": callsites,
        "l10n_callsite_files": callsite_files,
        "own_i18n_modules": [str(m.relative_to(app / "lib")) for m in modules],
        "own_i18n_importers": len(readers),
        "own_i18n_languages": own_i18n_languages(modules),
        "own_i18n_default_language": own_default,
        "reads_device_locale": seeds_from_device,
        "dart_files": len(dart_files(app)),
        "ui_files": len(ui),
        "ui_files_localized": ui_localized,
        "hardcoded_ui_strings": hardcoded,
        "hardcoded_ui_files": hardcoded_files,
        # Constructed, not merely mentioned. Photriya names `AglLanguageScreen`
        # in a comment explaining how a picker would be offered, and does not
        # offer one; substring matching counted that as a picker.
        "has_language_picker": any(
            re.search(r"(?<!//)\b\w*Language(?:Screen|Picker|Sheet|Selector)\s*\(", uncommented(read(f)))
            for f in dart_files(app)
        ),
        "ios_cfbundle_localizations": cfbundle,
        "android_res_configs": res_configs,
    }


def grade(r: dict) -> str:
    """One word for "can the store listing claim more than one language?".

    none    nothing declared, nothing translated
    pinned  translated, but `MaterialApp.locale` overrides the device language
    shell   locales declared, delegates installed, no screen reads a string
    partial some of the UI is translated, most is not
    real    the UI is translated and the device chooses the language
    """
    if r["declared_locales"] == 0:
        return "none"
    if r["locale_verdict"] in ("PINNED", "english-default"):
        return "pinned"
    reach = (r["ui_files_localized"] / r["ui_files"]) if r["ui_files"] else 0.0
    # Below a tenth is not "partially translated", it is a wired-up shell with
    # one file touching the delegate. Verba scored 1/28 and read as partial.
    if reach < 0.10:
        return "shell"
    if reach < 0.6 or r["hardcoded_ui_strings"] > max(r["l10n_callsites"], 1) * 2:
        return "partial"
    return "real"


GRADE_MARK = {
    "real": "**real**",
    "partial": "partial",
    "shell": "shell",
    "pinned": "**PINNED**",
    "none": "none",
}


def markdown_table(rows: list[dict]) -> str:
    out = [
        "| App | agl_i18n | l10n.yaml | locales | iOS | Android | l10n calls | UI files reading l10n | hardcoded copy | `MaterialApp.locale` | verdict |",
        "| --- | :-: | :-: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for r in sorted(rows, key=lambda r: (["real", "partial", "pinned", "shell", "none"].index(r["grade"]), r["repo"].lower())):
        loc = {"follows-device": "device", "PINNED": "**pinned**", "english-default": "**English**", "n/a": "—"}.get(
            r["locale_verdict"], r["locale_verdict"]
        )
        # An Android build stripped to one language while iOS advertises twelve
        # is the sharpest contradiction in the table; make it visible.
        android = r["android_res_configs"]
        android = "—" if not android else (f"**{android}**" if android == 1 < r["declared_locales"] else str(android))
        out.append(
            f"| {r['repo']} "
            f"| {'yes' if r['dep_agl_i18n'] else '—'} "
            f"| {'yes' if r['own_l10n_yaml'] else '—'} "
            f"| {r['declared_locales'] or '—'} "
            f"| {r['ios_cfbundle_localizations'] or '—'} "
            f"| {android} "
            f"| {r['l10n_callsites']} "
            f"| {r['ui_files_localized']}/{r['ui_files']} "
            f"| {r['hardcoded_ui_strings']} "
            f"| {loc} "
            f"| {GRADE_MARK[r['grade']]} |"
        )
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", dest="show")
    ap.add_argument("--markdown", action="store_true", help="emit the docs/I18N.md table")
    ap.add_argument("--out", default=str(ROOT / "docs" / "i18n-audit.json"))
    args = ap.parse_args()

    apps = json.loads(read(ROOT / "apps.json"))["apps"]
    rows = []
    for a in apps:
        r = measure(a["repo"], a["dir"])
        r["grade"] = grade(r)
        rows.append(r)

    out = {
        "_comment": "Generated by scripts/audit_i18n.py. Do not hand-edit.",
        "standard_locales": standard_locales(),
        "apps": rows,
    }
    pathlib.Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    if args.markdown:
        print(markdown_table(rows))
    if args.show:
        hdr = f"{'app':18s} {'pkg':3s} {'yml':3s} {'loc':>4s} {'calls':>6s} {'ui':>8s} {'hard':>5s} {'locale':14s} grade"
        print(hdr)
        print("-" * len(hdr))
        for r in rows:
            print(
                f"{r['repo']:18s} "
                f"{'y' if r['dep_agl_i18n'] else '-':3s} "
                f"{'y' if r['own_l10n_yaml'] else '-':3s} "
                f"{r['declared_locales']:>4d} "
                f"{r['l10n_callsites']:>6d} "
                f"{r['ui_files_localized']:>3d}/{r['ui_files']:<4d} "
                f"{r['hardcoded_ui_strings']:>5d} "
                f"{r['locale_verdict']:14s} {r['grade']}"
            )
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
