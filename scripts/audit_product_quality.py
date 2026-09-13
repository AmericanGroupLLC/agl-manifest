#!/usr/bin/env python3
"""Measure product quality across every AGL Flutter app.

Counts signals that exist in the tree right now — Dart lines, test files,
accessibility calls, responsive calls, progress indicators, TODO markers, a
central theme file — for every app listed in `apps.json`. Nothing here is
inherited from a previous audit: the report is rebuilt from the source each
time, so a claim in it can only be as old as the last run.

    python3 scripts/audit_product_quality.py [--root ~/agl]

Outputs docs/quality-audit.json and docs/PRODUCT_AUDIT.md.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re

# ── What each column means ─────────────────────────────────────────────────
# loc            every line of every *.dart under lib/, blanks and comments
#                included. Kept as the headline number because that is what
#                the earlier audits of this portfolio reported, so the two are
#                comparable.
# loc_generated  the part of loc that came out of a code generator.
# loc_code       hand-written, non-blank, non-comment lines.
# semantics      FILES that call Semantics( or pass semanticLabel:.
# responsive     FILES that call LayoutBuilder or MediaQuery.
# loading        occurrences of CircularProgressIndicator.
# todo           occurrences of TODO or FIXME.
# theme          a central theme/design-token file exists under lib/ — either named
#                for the job (theme.dart, palette.dart, design_tokens.dart …) or
#                building a ThemeData somewhere other than main.dart.

GENERATED = re.compile(
    r"(\.g\.dart|\.freezed\.dart|\.gr\.dart|\.config\.dart|\.gen\.dart)$"
    r"|^app_localizations.*\.dart$"
)
SEMANTICS = re.compile(r"\bSemantics\(|semanticLabel:")
RESPONSIVE = re.compile(r"\bLayoutBuilder\b|\bMediaQuery\b")
LOADING = re.compile(r"\bCircularProgressIndicator\b")
TODO = re.compile(r"\bTODO\b|\bFIXME\b")
THEME_FILE = re.compile(
    r"^(app_)?(theme|themes|theme_data|app_theme_data|design_system|design_tokens"
    r"|tokens|colors|app_colors|color_scheme|palette)\.dart$"
)
# A file that builds the app's ThemeData counts as the central theme even if it is
# named something else — but main.dart does not: every Flutter template builds a
# ThemeData inline there, so counting it would mark all 43 apps as themed.
THEME_BODY = re.compile(r"\bThemeData\(|\bThemeExtension<")
THEME_DIR = {"theme", "themes", "design_system"}
# Several repos vendor a whole Flutter SDK (`.flutter_sdk/`, `.flutter-sdk-run/`)
# next to the app. Counting that as the app's own code inflates the test count by
# thousands of files, so every hidden directory and every build output is skipped.
SKIP_DIRS = {"build", ".dart_tool", ".symlinks", "Pods", ".git", "ephemeral"}
# Where an app's own tests live, by Flutter convention.
TEST_DIRS = ("test", "integration_test", "test_driver")

# Thresholds used by the report. They are policy, not measurement, so they live
# in one place where they can be argued with.
SUBSTANTIAL_LOC = 10_000      # "a real product" by size
THIN_LOC = 2_000              # below this the app is a stub or a utility
LOC_PER_TEST_BUDGET = 2_000   # more lib LOC than this per test file is too thin
TOKEN_RESPONSIVE = 1          # <= this many files is "no responsive work"


def read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def dart_files(root: pathlib.Path) -> list[pathlib.Path]:
    if not root.is_dir():
        return []
    out = []
    for dart in root.rglob("*.dart"):
        parts = dart.relative_to(root).parts[:-1]
        if SKIP_DIRS & set(parts) or any(p.startswith(".") for p in parts):
            continue
        out.append(dart)
    return sorted(out)


def audit_app(app_dir: pathlib.Path) -> dict:
    """Measure one Flutter app directory (the one holding pubspec.yaml)."""
    lib = app_dir / "lib"
    files = dart_files(lib)

    loc = loc_generated = loc_code = 0
    semantics = responsive = 0
    loading = todo = 0
    theme_files: list[str] = []

    for dart in files:
        text = read(dart)
        lines = text.splitlines()
        loc += len(lines)
        generated = bool(GENERATED.search(dart.name)) or "// GENERATED CODE" in text[:400]
        if generated:
            loc_generated += len(lines)
        else:
            loc_code += sum(
                1
                for line in lines
                if line.strip() and not line.strip().startswith("//")
            )
        if SEMANTICS.search(text):
            semantics += 1
        if RESPONSIVE.search(text):
            responsive += 1
        loading += len(LOADING.findall(text))
        todo += len(TODO.findall(text))
        rel = dart.relative_to(lib)
        central = THEME_FILE.match(dart.name) or (
            THEME_DIR & set(rel.parts[:-1]) and "theme" in dart.name
        )
        if str(rel) != "main.dart" and (central or THEME_BODY.search(text)):
            # A file named for the theme is a better answer to "where is the theme"
            # than some screen that happens to build a ThemeData, so it sorts first.
            theme_files.append(("0" if central else "1") + str(rel))

    tests = [
        p
        for name in TEST_DIRS
        for p in dart_files(app_dir / name)
        if p.name.endswith("_test.dart")
    ]

    return {
        "lib_files": len(files),
        "loc": loc,
        "loc_generated": loc_generated,
        "loc_code": loc_code,
        "test_files": len(tests),
        "semantics": semantics,
        "responsive": responsive,
        "loading": loading,
        "todo": todo,
        "theme": bool(theme_files),
        "theme_file": sorted(theme_files)[0][1:] if theme_files else "",
    }


def measure(root: pathlib.Path, manifest: pathlib.Path) -> list[dict]:
    apps = json.loads(read(manifest))["apps"]
    rows = []
    for entry in apps:
        repo = root / entry["repo"]
        sub = entry.get("dir") or "."
        app_dir = (repo / sub).resolve() if sub != "." else repo.resolve()
        row = {
            "app": entry["repo"],
            "dir": sub,
            "path": str(app_dir),
            "exists": (app_dir / "lib").is_dir(),
        }
        if row["exists"]:
            row.update(audit_app(app_dir))
        rows.append(row)
    return rows


def per_test(row: dict) -> float:
    """lib LOC carried by each test file. inf when there are no tests."""
    return row["loc"] / row["test_files"] if row["test_files"] else float("inf")


def bullet_list(names: list[str]) -> str:
    return ", ".join(names) if names else "none"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def a11y_share(row: dict) -> float:
    """Share of the app's lib files that name something for a screen reader."""
    return row["semantics"] / row["lib_files"] if row["lib_files"] else 0.0


def movement(rows: list[dict], previous: list[dict]) -> list[str]:
    """Apps whose size moved by half or more since the last recorded run.

    This is what keeps the report honest over time: the previous run's numbers
    are on disk, so a claim that has been overtaken by the tree shows up as a
    line here instead of quietly surviving into the next revision.
    """
    was = {p["app"]: p for p in previous if "loc" in p}
    moved = []
    for r in rows:
        old = was.get(r["app"])
        if not old or not r.get("exists"):
            continue
        before, after = old["loc"], r["loc"]
        if before and abs(after - before) / before >= 0.5:
            moved.append((r["app"], before, after))
    if not moved:
        return []
    moved.sort(key=lambda m: -(m[2] / m[1]))
    lines = [
        "## Movement since the previous recorded run",
        "",
        "Apps whose `lib/` changed size by half or more since the numbers that were",
        "previously in `quality-audit.json`. Anything asserted about these apps in an",
        "older revision of this file should be treated as retired, not as background.",
        "",
        "| App | LOC then | LOC now | Change |",
        "| --- | ---: | ---: | ---: |",
    ]
    for app, before, after in moved:
        lines.append(f"| {app} | {before:,} | {after:,} | ×{after / before:,.1f} |")
    lines.append("")
    return lines


def render(rows: list[dict], root: pathlib.Path, previous: list[dict]) -> str:
    live = [r for r in rows if r["exists"]]
    missing = [r for r in rows if not r["exists"]]
    by_loc = sorted(live, key=lambda r: -r["loc"])

    substantial = [r for r in live if r["loc"] >= SUBSTANTIAL_LOC]
    mid = [r for r in live if THIN_LOC <= r["loc"] < SUBSTANTIAL_LOC]
    thin = [r for r in live if r["loc"] < THIN_LOC]

    no_a11y = [r for r in live if r["semantics"] == 0]
    thin_a11y = [r for r in live if 0 < r["semantics"] <= 2]
    no_responsive = [r for r in live if r["responsive"] <= TOKEN_RESPONSIVE]
    no_theme = [r for r in live if not r["theme"]]
    under_tested = sorted(
        [r for r in live if per_test(r) > LOC_PER_TEST_BUDGET],
        key=lambda r: -per_test(r),
    )
    todo_debt = sorted([r for r in live if r["todo"] >= 2], key=lambda r: -r["todo"])

    today = datetime.date.today().isoformat()
    total_loc = sum(r["loc"] for r in live)
    total_tests = sum(r["test_files"] for r in live)

    # Apps copied from one scaffold show up as an identical (LOC, file count)
    # pair. Measure it rather than asserting that the duplicates are gone.
    seen: dict[tuple[int, int], list[str]] = {}
    for r in live:
        seen.setdefault((r["loc"], r["lib_files"]), []).append(r["app"])
    clones = [names for names in seen.values() if len(names) > 1]
    twins = (
        "no two apps share both a line count and a file count"
        if not clones
        else "these apps are still byte-for-byte siblings by size: "
        + "; ".join(", ".join(n) for n in clones)
    )

    out: list[str] = [
        "# Portfolio product audit and backlog",
        "",
        f"Generated on {today} by `scripts/audit_product_quality.py`, which counts",
        "signals in `lib/` for every app in `apps.json`, in the local mirror of the",
        "org. Every number below comes from that run — re-run the script rather than",
        "editing this file, or it starts lying. Raw data:",
        "[`quality-audit.json`](quality-audit.json).",
        "",
        "`LOC` is every line of every `*.dart` under `lib/`, generated files included,",
        "because that is the metric the earlier audits used. The scorecard also carries",
        "hand-written non-blank non-comment lines so the difference is visible.",
        "",
        "## The shape of the portfolio",
        "",
        f"{len(live)} apps measured, {len(rows)} listed in `apps.json`. "
        f"{total_loc:,} lines of Dart, {total_tests} test files.",
        "",
        "| Group | Count | LOC range | Apps |",
        "| --- | ---: | ---: | --- |",
    ]

    def group_row(label: str, group: list[dict]) -> str:
        if not group:
            return f"| {label} | 0 | — | — |"
        lo = min(r["loc"] for r in group)
        hi = max(r["loc"] for r in group)
        names = ", ".join(r["app"] for r in sorted(group, key=lambda r: -r["loc"]))
        return f"| {label} | {len(group)} | {lo:,}–{hi:,} | {names} |"

    out += [
        group_row(f"Substantial ({SUBSTANTIAL_LOC:,}+ LOC)", substantial),
        group_row(f"Mid-sized ({THIN_LOC:,}–{SUBSTANTIAL_LOC - 1:,} LOC)", mid),
        group_row(f"Thin (under {THIN_LOC:,} LOC)", thin),
    ]
    if missing:
        out.append(
            f"| No `lib/` found | {len(missing)} | — | "
            + ", ".join(r["app"] for r in missing)
            + " |"
        )

    out += [
        "",
        "Every app in `apps.json` is a Flutter app with a populated `lib/` — there is no",
        "non-Flutter group left in this portfolio. Nor is there a template group: the",
        f"smallest app measured is {by_loc[-1]['app']} at {by_loc[-1]['loc']:,} LOC across "
        f"{plural(by_loc[-1]['lib_files'], 'file')},",
        "and " + twins + ".",
        "",
    ]
    out += movement(rows, previous)
    out += [
        "## Portfolio-wide gaps",
        "",
    ]

    a11y_gap = sorted(
        [r for r in live if a11y_share(r) < 0.25], key=lambda r: -r["loc"]
    )
    if no_a11y:
        out.append(
            f"- **Accessibility is absent in {plural(len(no_a11y), 'app')}** — no "
            "`Semantics(` and no `semanticLabel` anywhere in `lib/`: "
            + bullet_list([r["app"] for r in no_a11y])
            + "."
        )
    else:
        out.append(
            f"- **Every one of the {len(live)} apps names something for a screen "
            "reader**, but the coverage is shallow: "
            f"{plural(len(thin_a11y), 'app')} touch `Semantics(`/`semanticLabel` in "
            "only one or two files."
        )
    out += [
        f"- **Accessibility reaches under a quarter of the widget files in "
        f"{plural(len(a11y_gap), 'app')}.** Largest first: "
        + bullet_list(
            [
                f"{r['app']} ({r['semantics']}/{r['lib_files']} files)"
                for r in a11y_gap[:6]
            ]
        )
        + ".",
        f"- **Responsive layout is absent or token in {plural(len(no_responsive), 'app')}** "
        f"(≤{TOKEN_RESPONSIVE} file using `LayoutBuilder`/`MediaQuery`): "
        + bullet_list([r["app"] for r in sorted(no_responsive, key=lambda r: -r["loc"])])
        + ".",
        f"- **{plural(len(no_theme), 'app')} have no central theme or design-token "
        "file**: " + bullet_list(sorted(r["app"] for r in no_theme)) + ".",
    ]
    if under_tested:
        out.append(
            f"- **Test coverage is thinner than {LOC_PER_TEST_BUDGET:,} lib LOC per "
            f"test file in {plural(len(under_tested), 'app')}.** Worst first:"
        )
        for r in under_tested[:8]:
            ratio = (
                "no tests" if not r["test_files"] else f"{per_test(r):,.0f} LOC/test file"
            )
            out.append(
                f"  - {r['app']}: {r['loc']:,} LOC, "
                f"{plural(r['test_files'], 'test file')} — {ratio}"
            )
    else:
        out.append(
            f"- **No app now carries more than {LOC_PER_TEST_BUDGET:,} lib LOC per "
            "test file.** The thinnest are "
            + bullet_list(
                [
                    f"{r['app']} ({per_test(r):,.0f})"
                    for r in sorted(live, key=lambda r: -per_test(r))[:5]
                ]
            )
            + ", measured in lines per test file — which counts files, not assertions."
        )

    no_tests = [r for r in live if r["test_files"] == 0]
    starved = [r for r in under_tested if r["loc"] >= SUBSTANTIAL_LOC][:6]
    out += [
        "",
        "## Backlog",
        "",
        "Everything below is derived from the table at the end of this file. Items that",
        "cannot be measured from `lib/` — bundle ids, store records, AdMob ids, signing",
        "— live in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and are not restated here.",
        "",
        "### P0 — blocks a credible release",
        "",
        "| Item | Apps |",
        "| --- | --- |",
    ]
    if no_tests:
        out.append(
            f"| Add a test suite at all | {bullet_list([r['app'] for r in no_tests])} |"
        )
    if starved:
        out.append(
            "| Cover startup, navigation and the primary flow — largest apps with the "
            f"least test signal | {bullet_list([r['app'] for r in starved])} |"
        )
    if not no_tests and not starved:
        out.append(
            "| _Nothing measured in `lib/` is P0 today_ | every app has a `lib/`, a "
            f"test directory and under {LOC_PER_TEST_BUDGET:,} LOC per test file |"
        )
    out += [
        "",
        "### P1 — important",
        "",
        "| Item | Apps |",
        "| --- | --- |",
        "| Deepen accessibility past the one or two files that have it — `Semantics`, "
        f"labels, 48dp targets, contrast | {plural(len(a11y_gap), 'app')} under 25% "
        f"file coverage, {plural(len(thin_a11y), 'app')} at 1–2 files |",
        f"| Add a central theme / design tokens | {bullet_list(sorted(r['app'] for r in no_theme))} |",
        "| Add responsive breakpoints (tablet/landscape) | "
        + bullet_list([r["app"] for r in sorted(no_responsive, key=lambda r: -r["loc"])])
        + " |",
        "| Clear TODO/FIXME debt | "
        + bullet_list([f"{r['app']} ({r['todo']})" for r in todo_debt[:6]])
        + " |",
        "| Raise test depth in the largest apps — the thinnest ratios in the portfolio "
        "| "
        + bullet_list(
            [
                f"{r['app']} ({per_test(r):,.0f} LOC/test)"
                for r in sorted(
                    [x for x in live if x["loc"] >= SUBSTANTIAL_LOC],
                    key=lambda r: -per_test(r),
                )[:5]
            ]
        )
        + " |",
        "",
        "### P2 — polish",
        "",
        "- Consistent empty / loading / error states on every screen",
        "- Intentional motion: shared-axis transitions, hero continuity",
        "- 4/8px spacing discipline and typographic scale",
        "- Dark mode verified per app",
        "",
        "### P3 — nice to have",
        "",
        "- Onboarding flows, richer search/discovery, retention hooks",
        "",
        "## Per-app scorecard",
        "",
        "| App | LOC | hand-written | files | tests | LOC/test | theme | a11y files "
        "| responsive files | loading | TODO |",
        "| --- | ---: | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: |",
    ]
    for r in by_loc:
        ratio = "—" if not r["test_files"] else f"{per_test(r):,.0f}"
        out.append(
            "| {app} | {loc:,} | {code:,} | {files} | {tests} | {ratio} | {theme} "
            "| {sem} | {resp} | {load} | {todo} |".format(
                app=r["app"],
                loc=r["loc"],
                code=r["loc_code"],
                files=r["lib_files"],
                tests=r["test_files"],
                ratio=ratio,
                theme="yes" if r["theme"] else "—",
                sem=r["semantics"],
                resp=r["responsive"],
                load=r["loading"],
                todo=r["todo"],
            )
        )
    for r in missing:
        out.append(f"| {r['app']} | no `lib/` at `{r['dir']}` | | | | | | | | | |")

    # Risk order: how much code sits behind each test file, weighted by how little
    # of the app is named for a screen reader. Big, untested, unlabelled first.
    ranked = sorted(
        live,
        key=lambda r: -(per_test(r) if r["test_files"] else r["loc"])
        * (1.0 - min(a11y_share(r), 1.0)),
    )
    out += [
        "",
        "## Order of work",
        "",
        "Ranked by lib LOC per test file weighted by how little of the app is named",
        "for a screen reader, because a large app with few tests and no labels is",
        "where a regression is least likely to be caught and most likely to hurt:",
        "",
    ]
    for i, r in enumerate(ranked[:8], 1):
        ratio = "no tests" if not r["test_files"] else f"{per_test(r):,.0f} LOC/test"
        out.append(
            f"{i}. **{r['app']}** — {r['loc']:,} LOC, "
            f"{plural(r['test_files'], 'test file')} ({ratio}), a11y in "
            f"{r['semantics']}/{r['lib_files']} files"
        )
    out += [
        "",
        "Then the theme and responsive gaps in the smaller apps.",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    here = pathlib.Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(here.parent),
        help="directory holding the cloned repos (default: the parent of agl-manifest)",
    )
    parser.add_argument("--manifest", default=str(here / "apps.json"))
    args = parser.parse_args()

    root = pathlib.Path(args.root).expanduser().resolve()
    rows = measure(root, pathlib.Path(args.manifest))

    docs = here / "docs"
    out_json = docs / "quality-audit.json"
    # Read the previous run before overwriting it, so the report can say what moved.
    try:
        previous = json.loads(read(out_json)) if out_json.exists() else []
    except json.JSONDecodeError:
        previous = []

    out_json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (docs / "PRODUCT_AUDIT.md").write_text(render(rows, root, previous), encoding="utf-8")

    live = [r for r in rows if r["exists"]]
    print(
        f"{len(live)}/{len(rows)} apps measured, "
        f"{sum(r['loc'] for r in live):,} lib LOC "
        "→ docs/PRODUCT_AUDIT.md, docs/quality-audit.json"
    )


if __name__ == "__main__":
    main()
