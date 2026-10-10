# Every store field, measured per app

Answers "is this taken care of for each application". Measured against both
stores on 2026-09-27 — not read from a tracker. Regenerate the inputs with
`scripts/store_checklist.py`, `scripts/play_state.py` and
`scripts/testflight/store_gates.rb`.

## Apple — 38 of 43 records, and those 38 are complete

| Field | Covered |
| --- | --- |
| SKU, bundle id, primary language | 38/38 |
| Primary category | 38/38 |
| Subtitle | 38/38 |
| Full description, keywords | 38/38 |
| Support URL, privacy policy URL | 38/38 |
| Marketing URL | 38/38 |
| Screenshots | 38/38 |
| Age rating | 38/38 |
| App Privacy (published) | 38/38 |
| Export compliance | 38/38 |
| Content rights | 38/38 |
| Pricing (free) | 38/38 |
| Review notes | 38/38 |
| Build uploaded | 38/38 |

Five apps have no record at all: BodyQuest, FashionFactory, MyHealth, PlantPulse
and radiotune (MA-024).

## Google — 35 of 43 entries, and the listings are complete

| Field | Covered |
| --- | --- |
| Title | 35/35 |
| Short and full description | 35/35 |
| Icon, feature graphic | 35/35 |
| Screenshots (2 or more) | 35/35 |
| Support email | 35/35 |
| Bundle uploaded | 28/35 |
| Internal-track release live | 28/35 |

Eight entries have no bundle because every upload is refused with "signed with
the wrong key" — the original upload keys are not on this machine and none of
the 43 local keystores matches. Those need an upload-key reset (MA-020):
CalcMaster, CarDeal, Kinnav, TripNest, Uscis-Case, VirtuBand, iMaps, iMeasure.

## Fields with no API at all — Play Console only

Measured by asking the API what `edits` exposes: `apks, bundles,
countryavailability, deobfuscationfiles, details, expansionfiles, images,
listings, testers, tracks`. Nothing here can be scripted:

- Content rating questionnaire (IARC), and its contact email and category
- Target audience and age groups
- Ads declaration
- App access / reviewer sign-in
- Data safety, including the **account deletion URL** — see MA-029, the value to
  use is `https://www.americangroup.ai/policy/<slug>/delete-account.html`
- Government, financial and health declarations
- Countries and territories, and the production rollout itself

`applications.dataSafety` is the one exception and takes Google's own CSV, which
has to be exported from the Console first (MA-025).

## Fields that are derived, not entered

These come from the repository rather than a form, and are already correct:
third-party SDK list (each app's pubspec), sensitive permissions (its
entitlements and Info.plist), login required and demo account (its auth
configuration), in-app purchases and subscriptions (whether it depends on
`in_app_purchase`), signing and certificates, version codes and target API.
