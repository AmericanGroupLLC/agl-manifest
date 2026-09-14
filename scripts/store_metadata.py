#!/usr/bin/env python3
"""Store listings, held in this repository and rendered into the app repos.

Listing copy used to live only inside each app repo, in the shape Fastlane
happens to want, duplicated between the iOS and Android trees. That made it
impossible to answer "what does this app say on the stores" without opening
37 repositories, and it meant the same sentence was maintained twice per app.

The source of truth is now `store/apps/<repo>.json` here, with the values every
app shares in `store/defaults.json`. This script moves copy in both directions:

    python3 scripts/store_metadata.py import      # repos  → this repository
    python3 scripts/store_metadata.py generate    # this repository → repos
    python3 scripts/store_metadata.py check       # what is still missing

`generate` writes text files only. Screenshots and icons stay in the app repos
under `fastlane/metadata/android/<locale>/images/`; they are binary, they are
per-device, and Fastlane already knows where to find them.

Locale codes differ between the stores — Play wants `es-ES`, the App Store
wants `es-ES` too but spells Chinese `zh-Hans` where Play says `zh-CN` — so the
JSON is keyed by the plain language code and the mapping lives here.
"""

from __future__ import annotations

import json
import pathlib
import sys

BACKEND = pathlib.Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
AUDIT = BACKEND / "docs" / "release-readiness.json"
STORE = BACKEND / "store"
APPS = STORE / "apps"

# language code → (App Store locale, Play locale)
LOCALES = {
    "en": ("en-US", "en-US"),
    "es": ("es-ES", "es-ES"),
    "zh": ("zh-Hans", "zh-CN"),
    "hi": ("hi", "hi-IN"),
    "fr": ("fr-FR", "fr-FR"),
    "ar": ("ar-SA", "ar"),
    "de": ("de-DE", "de-DE"),
    "ja": ("ja", "ja-JP"),
    "pt": ("pt-BR", "pt-BR"),
    "ko": ("ko", "ko-KR"),
    "it": ("it", "it-IT"),
    "ru": ("ru", "ru-RU"),
}

# The two stores are not one listing with two file layouts. They have different
# fields and different limits, and several apps already say different things in
# each — CalcMaster is "CalcMaster: World Calc" on the App Store and
# "CalcMaster — World Calculator" on Play. Flattening the pair would have
# silently rewritten one of them, so each store keeps its own key.
#
# field → (App Store file, Play file, fallback field)
FIELDS = {
    # App Store: 30 characters. Play title: 30 characters.
    "name": ("name.txt", None, None),
    "title": (None, "title.txt", "name"),
    # App Store subtitle: 30 characters. Play short description: 80.
    "subtitle": ("subtitle.txt", None, None),
    "short_description": (None, "short_description.txt", "subtitle"),
    # App Store description: 4000. Play full description: 4000.
    "description": ("description.txt", None, None),
    "full_description": (None, "full_description.txt", "description"),
    "keywords": ("keywords.txt", None, None),
    "promotional_text": ("promotional_text.txt", None, None),
    "release_notes": ("release_notes.txt", None, None),
    "changelog": (None, "changelogs/default.txt", "release_notes"),
}

SHARED_FILES = {
    "copyright": "copyright.txt",
    "primary_category": "primary_category.txt",
    "secondary_category": "secondary_category.txt",
}

REVIEW_FILES = (
    "first_name",
    "last_name",
    "email_address",
    "phone_number",
    "notes",
)


def apps() -> list[dict]:
    return [a for a in json.loads(AUDIT.read_text()) if a.get("flutter")]


def app_dir(a: dict) -> pathlib.Path:
    repo = ROOT / a["repo"]
    return repo if a["app_dir"] == "." else repo / a["app_dir"]


def read(p: pathlib.Path) -> str:
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def defaults() -> dict:
    path = STORE / "defaults.json"
    return json.loads(path.read_text()) if path.exists() else {}


def do_import() -> None:
    APPS.mkdir(parents=True, exist_ok=True)
    imported = 0
    for a in apps():
        md = app_dir(a) / "fastlane" / "metadata"
        record: dict = {"repo": a["repo"], "copy": {}}
        for lang, (ios_loc, play_loc) in LOCALES.items():
            entry: dict[str, str] = {}
            for field, (ios_name, play_name, fallback) in FIELDS.items():
                if ios_name:
                    value = read(md / ios_loc / ios_name)
                else:
                    value = read(md / "android" / play_loc / play_name)
                if value:
                    entry[field] = value
            # Only keep a store-specific value when it actually differs from
            # the one it falls back to; otherwise the JSON fills with
            # duplicates and the next editor has to change two places.
            for field, (_, _, fallback) in FIELDS.items():
                if fallback and entry.get(field) == entry.get(fallback):
                    entry.pop(field, None)
            for key in ("support_url", "privacy_url", "marketing_url"):
                value = read(md / ios_loc / f"{key}.txt")
                if value:
                    entry[key] = value
            if entry:
                record["copy"][lang] = entry

        # review_information/notes describes *this* app to a reviewer, so it is
        # per app however much the rest of the contact block is shared.
        review = {}
        for key in REVIEW_FILES:
            value = read(md / "review_information" / f"{key}.txt")
            if value:
                review[key] = value
        if review:
            record["review_information"] = review
        if not record["copy"]:
            continue
        out = APPS / f"{a['repo']}.json"
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        imported += 1
        langs = ", ".join(record["copy"])
        print(f"{a['repo']:18} imported [{langs}]")
    print(f"\n{imported} app(s) imported into store/apps/")


def do_generate() -> None:
    shared = defaults()
    written = 0
    for a in apps():
        source = APPS / f"{a['repo']}.json"
        if not source.exists():
            continue
        record = json.loads(source.read_text())
        md = app_dir(a) / "fastlane" / "metadata"
        files = 0

        for lang, entry in record.get("copy", {}).items():
            ios_loc, play_loc = LOCALES[lang]
            for field, (ios_name, play_name, fallback) in FIELDS.items():
                value = entry.get(field) or (entry.get(fallback) if fallback else "")
                if not value:
                    continue
                target = (md / ios_loc / ios_name) if ios_name else (
                    md / "android" / play_loc / play_name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(value + "\n", encoding="utf-8")
                files += 1
            for key in ("support_url", "privacy_url", "marketing_url"):
                value = entry.get(key) or shared.get(f"{key}_template", "").format(
                    slug=record.get("slug", a["repo"].lower())
                )
                if not value:
                    continue
                target = md / ios_loc / f"{key}.txt"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(value + "\n", encoding="utf-8")
                files += 1

        for key, filename in SHARED_FILES.items():
            value = record.get(key) or shared.get(key)
            if not value:
                continue
            target = md / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(value) + "\n", encoding="utf-8")
            files += 1

        review = {**shared.get("review_information", {}),
                  **record.get("review_information", {})}
        for key in REVIEW_FILES:
            if key not in review:
                continue
            target = md / "review_information" / f"{key}.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(review[key]) + "\n", encoding="utf-8")
            files += 1

        written += 1
        print(f"{a['repo']:18} {files} file(s)")
    print(f"\n{written} app(s) written")


def do_check() -> None:
    rows = []
    for a in apps():
        source = APPS / f"{a['repo']}.json"
        if not source.exists():
            rows.append((a["repo"], "no store/apps entry at all", []))
            continue
        record = json.loads(source.read_text())
        langs = list(record.get("copy", {}))
        english = record.get("copy", {}).get("en", {})
        gaps = [f for f in ("name", "subtitle", "description")
                if not english.get(f)]
        missing_langs = [l for l in LOCALES if l not in langs]
        rows.append((a["repo"], ", ".join(gaps) or "English complete", missing_langs))

    print(f"{'app':20} {'English':28} untranslated")
    for repo, state, missing in sorted(rows):
        print(f"{repo:20} {state:28} {len(missing)} of {len(LOCALES)}")
    nothing = sum(1 for r in rows if "no store/apps" in r[1])
    print(f"\n{len(rows) - nothing} app(s) have listing copy, {nothing} have none.")
    print("Store copy is product writing — add it to store/apps/<repo>.json, "
          "then run `generate`.")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "import":
        do_import()
    elif command == "generate":
        do_generate()
    elif command == "check":
        do_check()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
