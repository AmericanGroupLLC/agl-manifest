# What is left, in the order that unblocks the most

Generated from measurement on 2026-09-22, not from memory. Every item here was
attempted through an API first and refused; the refusal is quoted.

## The state a machine has reached

| | Apple | Google |
| --- | --- | --- |
| App records / Play entries | 30 of 42 | 31 of 42 |
| Binary uploaded | 29 | 26 |
| Reaches every account user automatically | **29 of 29** | 0 — no tester list |
| Store listing complete | 29 | 26 |
| Submitted for public release | 0 — blocked below | 0 — blocked below |

Every one of the remaining checklist failures is a Console action. Nothing is
waiting on code, a build, or a script.

## 0. One sign-in unlocks items 2 and 4 below

The App Store Connect **API key** cannot create an app record or publish App
Privacy answers. Both live on the `iris` host behind the Console, which takes an
Apple ID session instead — measured today: `iris/v1/apps/{id}/dataUsages`
returns 401 "No valid credentials found" for a key, and `POST v1/apps` returns
"The resource 'apps' does not allow 'CREATE'".

A session lasts about a month. Capture one once:

```bash
cd ~/agl/agl-manifest && bundle exec fastlane spaceauth -u srikanth.patchava@outlook.com
```

Paste the printed value into `~/agl/.secrets/fastlane-session` (git-ignored),
then:

```bash
source scripts/testflight/env.sh
bundle exec ruby scripts/testflight/create_records_session.rb --dry-run
bundle exec ruby scripts/testflight/create_records_session.rb
```

That creates every missing App Store record and publishes the App Privacy
answers already written in `store/privacy/`. The record watcher then builds,
uploads and distributes each new app within five minutes.

A stored session for the account holder already exists at
`~/.fastlane/spaceship/srikanth.patchava@outlook.com/cookie` but has expired: a
login attempt today asked for a 6-digit code, which a non-interactive session
cannot answer. That prompt is the only human step here.

## 1. Accept the App Store Connect agreement — unblocks Apple beta review

Every beta submission is refused with:

> Beta contract is missing for the app. - Beta Contract is missing.

Measured again today on DriftDate and MyCard. Eight builds were auto-rejected in
the same window (AGrammarly, CalcMaster, EventSpark, NexusTransferPay, Photriya,
PilotEnRoute, Uscis-Case, iMaps) after seventeen passed review hours earlier, so
this is account state, not code.

**App Store Connect → Business → Agreements**, as the Account Holder
(srikanth.patchava@outlook.com). Then:

```
bundle exec ruby scripts/testflight/distribute.rb --all
```

This does **not** affect the 29 apps already reaching account users — internal
distribution needs no review and is unaffected.

## 2. Publish App Privacy answers — unblocks every App Store submission

Submission is refused for 27 of 29 apps with:

> You must have published answers to your app's data usages.

The answers are already written for all 43 apps in `store/privacy/<repo>.json`.
Enter them under **App Privacy** and press Publish.

There is no API for this, proven on both hosts today:
`api.appstoreconnect.apple.com/v1/apps/{id}/dataUsages` → 404 "the relationship
'dataUsages' does not exist"; `appstoreconnect.apple.com/iris/v1/...` → 401
"No valid credentials found" (that host takes an Apple ID session, not a key).

Then: `bundle exec ruby scripts/testflight/submit_production.rb`

## 3. Create one Google Group of testers — unblocks Android delivery to phones

26 Play apps have a completed internal-track release that reaches nobody,
because the internal track has no testers. Google's own discovery document
settles why:

```json
"Testers": { "googleGroups": { "items": {"type": "string"}, "type": "array" } }
```

There is no way to add a tester by email. Create one Google Group holding the
roster, then set `PLAY_TESTER_GOOGLE_GROUP` (plus `PLAY_SERVICE_ACCOUNT_JSON`)
as repository secrets. The six-hourly **Sync testers** workflow attaches it to
every app.

## 4. Create the 12 missing App Store records

`POST v1/apps` → "The resource 'apps' does not allow 'CREATE'". daily-pulse was created on 2026-09-23 and shipped itself. The table, with
the bundle id, SKU, version and category for each, is in
`docs/APPS_TO_CREATE.md`. All 14 bundle ids are already registered in the
Developer Portal, so each appears in the Bundle ID dropdown.

`scripts/testflight/watch_records.sh` is running: each record is built,
uploaded, put in the internal group and submitted within five minutes of being
created. Nothing else to do per app.

## 5. Create the 11 missing Play entries

`applications` exposes one method, `dataSafety` — there is no `applications.create`.
Packages: AeroSwift, BodyQuest, DriftDate, FashionFactory, GadgetNest,
GroceryMatch, HerJourney, Photriya, PlantPulse, Verba, portfolio-board.

## 6. Reset six Play upload keys

CarDeal, iMaps, iMeasure, TripNest, Uscis-Case and VirtuBand reject every upload
with "signed with the wrong key". All 43 local keystores were read with
`keytool`; none matches the fingerprints Play expects, so the original keys are
not recoverable here. **Setup → App integrity → App signing → Request upload key
reset**. Fingerprints are in MA-020.

## 7. Leave Draft on Play — the last gate before production

Production promotion is refused for all 26 with:

> Only releases with status draft may be created on draft app.

Google requires the first production release of a Draft app to be made in
Console, after the App content declarations. `edits` exposes only
`apks, bundles, countryavailability, deobfuscationfiles, details, expansionfiles,
images, listings, testers, tracks` — the content rating questionnaire, target
audience, ads declaration and app access have no API at all. Data safety is the
one exception (`applications.dataSafety`).

After the first release, `python3 scripts/play_release.py --all --production`
promotes every later one.
