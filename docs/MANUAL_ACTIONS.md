# Manual actions

Things no agent can do, because they need a console login, a payment method, a
human identity, or an approval. Everything here is **verified as still
outstanding** at the date shown, not copied forward from an earlier list.

Ordered by consequence, not by effort.

---

## MA-001 · P0 · A credentials workbook is still downloadable from GitHub

**Verified 2026-09-11.**

`SFG-AGL-MobileApp_Devlopment-Tools.xlsx` — which contains live credentials —
was committed to `agl-manifest` and then removed by force-push. Removing it from
the branch did not delete it. Git objects survive until GitHub garbage-collects
them, and GitHub does not do that on its own.

Evidence it is still retrievable:

```
$ gh api repos/AmericanGroupLLC/agl-manifest/git/trees/763015b \
    --jq '.tree[] | select(.path|test("xlsx"))'
SFG-AGL-MobileApp_Devlopment-Tools.xlsx      blob=663149af3d2fb366dec9703067a2ffcea6e1f476  94544
SFG-AGL-MobileApp_Devlopment-Tools.xlsx.orig blob=42d8627690c1709258c64dd14fd60b6f4faa0d67 145679

$ git hash-object SFG-AGL-MobileApp_Devlopment-Tools.xlsx
663149af3d2fb366dec9703067a2ffcea6e1f476     # byte-identical to the exposed blob
```

What bounds the damage: the repository is `internal`, not public, and has **0
forks** — so the audience is org members, not the internet. The org has no
public repositories at all. That is a reason not to panic; it is not a reason to
leave it.

**Required, in this order:**

1. **Rotate every credential in that workbook.** This is the only step that
   actually closes the exposure. Purging the blob afterwards is hygiene; until
   rotation happens, assume the values are compromised. Do not skip this because
   the repo is private — "internal" means every member of the org, and a leaked
   token does not care how it was obtained.
2. Ask GitHub Support to garbage-collect unreachable objects in
   `AmericanGroupLLC/agl-manifest`, quoting commit `763015b`. Support has to do
   it; there is no API or setting for it.
3. Re-run the `gh api` command above. While it returns a blob, the file is still
   there.

Prevention is already in place: `.gitignore` blocks `*.xlsx` and the specific
filename, and both files are untracked. The failure was a `git add -A` that was
never read before committing.

---

## MA-002 · P1 · `AGL_PACKAGES_TOKEN` is not set, and nothing can build in CI

**Verified 2026-09-11** — `gh secret list --repo AmericanGroupLLC/agl-manifest`
returns 34 secrets: 30 `KEYSTORE_*_BASE64`, plus `ANDROID_KEYSTORE_CONFIG`,
`ASC_ISSUER_ID`, `ASC_KEY_CONTENT`, `ASC_KEY_ID`. `AGL_PACKAGES_TOKEN` is not
among them.

Apps consume `agl_i18n`, `agl_observability` and `agl_ads` as **git**
dependencies from a private repository. Without a token, `flutter pub get` fails
before compilation starts, so every CI job fails identically regardless of the
app.

**Required:** create a fine-grained PAT with *read* access to the packages
repository and add it as the `AGL_PACKAGES_TOKEN` secret. Read-only is
sufficient and is what should be granted.

This blocks CI only. Local builds are unaffected — the packages are already on
this machine — which is why signed bundles can be produced today.

---

## MA-003 · P1 · No Google Play service account, so nothing can be uploaded

No Play credential exists in the secret list. Fastlane's `upload_to_play_store`
cannot authenticate without one.

**Required:** in Google Cloud, create a service account for Play Developer
account `5590631437738173959`, grant it *Release manager* in Play Console, and
add the JSON key as a secret. An app must also have had **one manual first
upload** per package name before the API will accept automated ones — Google
enforces this and there is no way around it.

---

## MA-004 · P2 · Seven apps have no upload keystore

30 keystores exist in `~/agl/.secrets/keystores/` for 37 Flutter apps. Missing:

`CalcMaster`, `CodeDeal`, `DriftDate`, `Kinnav`, `NexusTransferPay`,
`TripNest`, `portfolio-board`

An agent *can* generate these with `keytool` — but a lost upload key cannot be
replaced without Google's intervention, and the passwords have to go somewhere a
human controls. Generating them is only useful once there is an agreed home for
the passwords.

**Required:** confirm where keystore passwords are to be stored, then the
keystores can be generated and uploaded as `KEYSTORE_<APP>_BASE64` secrets to
match the existing 30.

---

## MA-005 · P2 · iOS signing has no certificate to use

`ASC_KEY_ID`, `ASC_ISSUER_ID` and `ASC_KEY_CONTENT` are set, so App Store
Connect *API* calls work. Building a signed `.ipa` additionally needs a
distribution certificate and provisioning profiles, which `match` keeps in a
private repository that does not exist yet.

**Required:** create the `match` certificates repository, run `fastlane match
appstore` once from a machine with the Apple ID, and add `MATCH_PASSWORD` and
the repo's deploy key as secrets.

---

## MA-006 · P2 · Firebase config files are missing for most apps

Crashlytics cannot report from an app without `google-services.json` (Android)
and `GoogleService-Info.plist` (iOS). These are per-app downloads from the
Firebase console for project `americangroupllc-5bdfc`.

**Required:** register each app in the console and commit the two files. Note
that a *placeholder* config is worse than none — it makes the app look
instrumented while reporting nothing — which is why none has been invented.

---

**Update 2026-09-14.** App Store Connect rejects an upload whose Info.plist
carries the placeholder URL scheme `com.googleusercontent.apps.REVERSED_CLIENT_ID`
(DriftDate build 2026091400: *"URL schemes need to begin with an alphabetic
character"*). The placeholder was removed from 13 apps so TestFlight uploads
can proceed; Google Sign-In on iOS will not return to the app until the real
`REVERSED_CLIENT_ID` from each `GoogleService-Info.plist` is added back as a
`CFBundleURLTypes` entry. Add it in the same commit as the plist itself.

---

## MA-007 · P3 · Store descriptions are missing for 18 apps

Copy is a product decision, not an engineering one. `docs/STORE_METADATA.md`
lists which apps still need a description, keywords and screenshots.

---

## MA-008 · P1 · Thirteen apps have no App Store Connect record, and the API cannot create one

**Verified 2026-09-13.** `Spaceship::ConnectAPI::App.create` returns *"The
resource 'apps' does not allow 'CREATE'. Allowed operations are:
GET_COLLECTION, GET_INSTANCE, UPDATE"*, and fastlane `produce` falls back to an
Apple ID login, which needs a password this machine does not have. So a build
can be uploaded to every existing record (`scripts/testflight/`), but nothing
can create the missing ones.

Bundle ids were registered in the Developer Portal on 2026-09-13 for:
AeroSwift, GadgetNest, GroceryMatch, HerJourney, iMeasure, NewsBoard,
PlantPulse, portfolio-board, Verba (MyHealth's already existed).

**Required:** in App Store Connect → My Apps → **+**, create a record for each
of the ten above using its registered bundle id (`docs/APP_IDENTIFIERS.md`), then
`python3 scripts/testflight/run_batch.py --apps <names>`.

Three more need a decision first, because an existing record holds a *different*
bundle id for the same product: AGrammarly (`com.americangroupllc.agrammarly`
vs the app's `com.americangroup.agrammarly`), daily-pulse
(`com.americangroup.daily-pulse` vs `com.americangroup.dailypulse`),
NexusTransferPay (`com.americangroupllc.nexustransferpay` vs
`com.americangroupllc.nexuspay`). Either change the record's bundle id in App
Information (possible only while it has no build) or create a new record under a
new name.

---

## MA-009 · P1 · Google Play: no credential this machine can use, and the console cannot be driven

**Verified 2026-09-13.** MA-003 still stands (no service-account JSON). In
addition: `~/google-cloud-sdk/bin/gcloud` has no logged-in account, and Play
Console pages never finish loading for the Claude in Chrome extension, which is
also blocked from `console.cloud.google.com` by its site permissions. All 43
signed `.aab` files are staged in `~/agl/.dist/` and
`scripts/upload_play.py` is written (untested) for the moment a key exists.

**Required, one of:**

1. Create a service account in project `americangroupllc-5bdfc`, grant it
   *Release manager* in Play Console → Users and permissions, download the JSON
   key, then `PLAY_JSON_KEY_FILE=<path> python3 scripts/upload_play.py`.
2. Upload each app's first bundle by hand in Play Console (Internal testing →
   Create new release); Google requires a manual first upload for a Draft app
   in any case.

---

## Not a manual action, but needs a human decision

**Do five sibling apps still read as duplicates?** `CarDeal`, `HomeWise`,
`NearServe`, `RideZap` and `portfolio-board` were one 939-line scaffold. They
are not any more: measured on 2026-09-13 they are 5,522–7,390 lines of Dart
across 22–38 files each, with different domain code in each (mortgage maths,
service booking, travel quotes, car comparison, a markdown project board). The
table is in `docs/KNOWN_ISSUES.md`.

What remains is a judgement no script can make: whether five apps from one
publisher, built on a shared house style, still invite an App Store guideline
4.3 (spam) rejection. That is a human call before submission, not a build gap.
