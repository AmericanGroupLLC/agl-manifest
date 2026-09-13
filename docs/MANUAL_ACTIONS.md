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

## MA-007 · P3 · Store descriptions are missing for 18 apps

Copy is a product decision, not an engineering one. `docs/STORE_METADATA.md`
lists which apps still need a description, keywords and screenshots.

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
