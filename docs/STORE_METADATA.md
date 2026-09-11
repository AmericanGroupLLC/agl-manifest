# Store listings

Every word the App Store and Google Play show for an AGL app is held here, in
[`store/`](../store), and rendered into the app repositories in the shape
Fastlane expects.

```
store/
  defaults.json        what every listing shares — copyright, contact, URL templates
  apps/<repo>.json     one file per app: the copy, per language, per store
```

```sh
python3 scripts/store_metadata.py check      # what is still missing
python3 scripts/store_metadata.py generate   # store/ → each app's fastlane/metadata
python3 scripts/store_metadata.py import     # pull copy back out of an app repo
```

## Why it moved here

Listing copy lived only inside each app repo, in Fastlane's directory layout,
duplicated between the iOS and Android trees. Answering "what does this app say
on the stores" meant opening 37 repositories, and the same sentence was
maintained twice per app.

## What is *not* here

- **Screenshots, icons and feature graphics.** They stay in the app repos under
  `fastlane/metadata/android/<locale>/images/`. They are binary, per-device, and
  Fastlane already knows where to find them.
- **The generated output is still committed** to each app repo. `deliver` and
  `supply` read from disk at delivery time, and a release should not depend on
  fetching another repository mid-run. Run `generate` and commit the result in
  the same change as the copy edit.

## The two stores are not one listing

They have different fields and different limits, and several apps already say
different things in each — CalcMaster is *CalcMaster: World Calc* on the App
Store and *CalcMaster — World Calculator* on Play. So each store keeps its own
key, and the Play one falls back to the Apple one only when it is absent:

| JSON key | App Store | Play | Limit |
| --- | --- | --- | --- |
| `name` | `name.txt` | — | 30 |
| `title` | — | `title.txt` (falls back to `name`) | 30 |
| `subtitle` | `subtitle.txt` | — | 30 |
| `short_description` | — | `short_description.txt` (falls back to `subtitle`) | 80 |
| `description` | `description.txt` | — | 4000 |
| `full_description` | — | `full_description.txt` (falls back to `description`) | 4000 |
| `keywords` | `keywords.txt` | — | 100 |
| `promotional_text` | `promotional_text.txt` | — | 170 |
| `release_notes` | `release_notes.txt` | — | 4000 |
| `changelog` | — | `changelogs/default.txt` (falls back to `release_notes`) | 500 |

Locale codes differ too — Play says `zh-CN` where the App Store says `zh-Hans` —
so the JSON is keyed by plain language code and the mapping lives in the script.

## `review_information/notes` is per app

It tells an App Review engineer what the app is and how to reach every feature,
including how to get past a login. It is **not** in `defaults.json`, and it must
not be: templating one app's notes across the portfolio would tell Apple that
every app is CalcMaster. Each app's notes live in its own
`store/apps/<repo>.json`.

## Adding a language

Only once the app itself is translated. A listing in Spanish for a binary that
shows English is the exact failure [`I18N.md`](I18N.md) exists to prevent — the
app's `l10n_callsites` count in the readiness audit is what says whether it is
really translated, not the presence of ARB files.

```json
"copy": {
  "en": { "name": "…", "subtitle": "…", "description": "…" },
  "es": { "name": "…", "subtitle": "…", "description": "…" }
}
```

## State today

`python3 scripts/store_metadata.py check` prints it. As of 2026-09-10: 37 apps
have an entry, 19 carry full English copy imported from their repos, and the
remaining 18 have a name and a one-line subtitle taken from the app inventory
but **no description** — which both stores require.

A description is product writing. It makes claims about what an app does, and
getting that wrong in a store listing is worse than leaving it blank, so the
generator does not invent one.
