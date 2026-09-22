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

## MA-006 · RESOLVED 2026-09-17 · Firebase config files

All 43 apps now carry a real `google-services.json` and `GoogleService-Info.plist`,
committed and on mainline. Done without a console: `scripts/firebase_register.py`
registers each app through the Firebase Management API and pulls its config.

Two API behaviours the console hides, both handled in that script:

* `androidApps/{id}/config` returns the **project-wide** google-services.json
  listing every app registered so far. Shipping it unfiltered would put 42 other
  apps' keys in each binary, so the JSON is cut down to the app's own client.
* App creation is rate-limited ("Quota exceeded", and bursts are refused with
  "Too many Apps"), so creation is paced and retries, and a project Google calls
  full is believed over any local count.

Apps are spread over three projects because one project holds 30 apps and each
app needs two slots — see `docs/RELEASE_PIPELINE.md` §2.

---

## MA-007 · P3 · Store descriptions are missing for 18 apps

Copy is a product decision, not an engineering one. `docs/STORE_METADATA.md`
lists which apps still need a description, keywords and screenshots.

---

## MA-008 · P1 · Create the App Store Connect records for the new identifiers

**Decision 2026-09-15:** every app is now `com.americangroup.<name>` on both
platforms (`scripts/rename_identifiers.py`, apps.json regenerated). Bundle ids
are permanent once a record has a build, so the 33 records under
`com.americangroupllc.*` and their TestFlight builds are abandoned; each app
needs a **new** App Store Connect record. The API cannot create records
(`apps` refuses CREATE) and fastlane `produce` needs an Apple ID password.

**Required:** in App Store Connect → Apps, use "Drag up to 10 apps here" with the
signed IPAs in `~/agl/.dist/ipa-for-asc/` (regenerated for the new ids by
`scripts/testflight/build_only.py`), or create each record by hand with the
bundle id from apps.json. `scripts/testflight/watch_records.sh` then ships the
TestFlight build for each app within five minutes of its record appearing.

The old records can be removed from App Store Connect once nothing refers to
them; the previous build inventory is in
`~/agl/.dist/ios-batch/results-americangroupllc-2026-09-15.json`.

---

## MA-009 · Play: 21 of 43 uploaded — 14 need an app entry, 8 need an upload-key reset

**Resolved 2026-09-17:** the credential problem is gone.
`american-group-publisher@american-group-llc.iam.gserviceaccount.com` already
held Admin/all-apps in Play Console, so no new grant was needed.
`scripts/play_upload.py` uses it by **impersonation** — gcloud mints a
short-lived token, no long-lived key file is created. (The IAM Credentials API
had to be enabled on project `american-group-llc` first.) Each app gets an
edit → bundle upload → internal track as a **draft** release → commit.

**Uploaded to internal testing (21):** AGCleaner, AGRecorder, AGStudio, AGrammarly, ApexMarketWatch, BuddyPlay, ChefCount, CodeDeal, EventSpark, HomeWise, MileMaster, MyCard, MyFinance, MyHealth, NearServe, NewsBoard, NexusTransferPay, PilotEnRoute, RideZap, RoomCraft, WiFiTrail

### Still blocked, and both need a person

**a) No Play app entry (14)** — `Package not found`. There is no
creation API; each must be created in Play Console → Create app, using the
package name from `apps.json`. Re-run `python3 scripts/play_upload.py --all`
afterwards; it skips anything already uploaded.

AeroSwift, BodyQuest, DriftDate, FashionFactory, GadgetNest, GroceryMatch, HerJourney, Photriya, PlantPulse, Verba, daily-pulse, portfolio-board, radiotune, yourtube

**b) Upload key does not match Play's registered one (8)** — these
apps already exist on Play with Play App Signing, and the upload certificate
they were published with is **not on this machine**. Every one of the 43
keystores in `~/agl/.secrets/keystores/` was fingerprinted against the
certificate Google names in each rejection: **zero matches**. The original
upload keys are lost.

| App | Play expects (SHA1) |
| --- | --- |
| CalcMaster | `60:D8:BB:7F:30:04:2F:C0:4A:5D:1D:71:3B:3D:99:F9:32:73:46` |
| CarDeal | `ED:9C:A5:63:CF:8C:C0:18:2A:63:09:CD:8A:B8:20:57:19:F9:6F` |
| Kinnav | `96:8B:C8:DB:89:F4:90:9A:A9:93:7D:C0:4C:8E:03:CD:F6:05:89` |
| TripNest | `D6:8C:D1:56:01:26:6D:0A:EA:F7:BD:6E:56:9F:6C:57:48:43:E4` |
| Uscis-Case | `FB:60:4C:AB:6E:10:DC:96:1A:E0:6E:04:CE:D0:BE:58:49:69:95` |
| VirtuBand | `ED:9C:A5:63:CF:8C:C0:18:2A:63:09:CD:8A:B8:20:57:19:F9:6F` |
| iMaps | `12:8E:4F:EB:E8:74:D7:41:4F:64:B6:E8:41:E8:F6:09:15:67:FA` |
| iMeasure | `EA:C1:09:67:DE:E3:9F:85:91:F9:0A:DA:1D:5A:EF:70:98:99:F9` |

Fix: Play Console → the app → Test and release → Setup → App integrity → App
signing → **Request upload key reset**, uploading the new certificate exported
from that app's keystore. Google processes it in about two days; after that the
new key in `~/agl/.secrets/keystores/` is the registered one and the upload
works.

---

## MA-010 · P1 · safecodeg.com/policy/* is not live yet — the store URLs depend on it

**Verified 2026-09-14.** Every listing's privacy and support URL is
`https://www.safecodeg.com/policy/<slug>/...`. The pages exist in
`www.safecodeg.com/client/public/policy/` (generated by
`scripts/policy_pages.py`, pushed to `main`), but the live host still answers
those paths with the React homepage (HTTP 200, SPA fallback): the repository's
GitHub Actions deploy has failed on every run since 2026-09-06 — HostGator
closes the SSH connection from the runner on port 22 and on 2222 — and the
website is delivered by a separate agent/pipeline.

**Required:** publish the current `main` of `www.safecodeg.com` to the live
host so `https://www.safecodeg.com/policy/calcmaster/` returns the policy page,
then re-check with `curl -s <url> | grep -c "Privacy Policy"`. Do not submit a
listing for review before that: a privacy URL that shows the homepage is a
rejection.

A GitHub Pages mirror was created during the 2026-09-14 session at
`https://www.safecodeg.com/policy/<slug>/` (repository
`AmericanGroupLLC/AmericanGroupLLC.github.io`). The organisation no longer uses
GitHub Pages; delete that repository once safecodeg.com serves the pages.

---

## MA-011 · P2 · App Privacy labels must be entered in App Store Connect by a person

**Verified 2026-09-14.** The App Store "nutrition label" is not exposed by the
App Store Connect API; fastlane's `upload_app_privacy_details_to_app_store`
logs in with an Apple ID web session and fails here with *"Missing password
for user … running in non-interactive shell"*. Everything else in the listing
(text, URLs, category, age rating, review notes, screenshots) is uploaded by
`scripts/deliver_metadata.py`.

**Required:** for each app, App Store Connect → App Privacy → answer with the
data types in `store/privacy/<repo>.json` (derived from what actually leaves
the device: accounts, ads with/without ATT, health, purchases). Apps whose file
says `DATA_NOT_COLLECTED` are a single click. Alternatively run
`fastlane run upload_app_privacy_details_to_app_store json_path:store/privacy/<repo>.json app_identifier:<bundle id>`
from a Mac with the Apple ID logged in.

---

## MA-012 · P1 · Xcode 27.0 licence must be accepted before anything builds again

**Verified 2026-09-14 18:55.** `/Applications/Xcode.app` is now 27.0 (27A266a);
the licence on record is for 26.4.1. Every `xcodebuild`, `flutter build ipa`
and simulator build fails with *"You have not agreed to the Xcode license
agreements"*. This stopped the EventSpark and radiotune TestFlight retries and
the screenshot rerun.

**Required (needs an administrator password, so a person):**

```bash
sudo xcodebuild -license accept
```

Then resume: `python3 scripts/testflight/run_batch.py --wave records` (EventSpark,
radiotune) and `python3 scripts/screenshots.py --all --skip-done`.

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

## MA-013 — TestFlight internal groups cannot be filled through the API (RESOLVED by working around it)

`POST /v1/betaTesters` against an internal beta group is refused with
"Tester(s) cannot be assigned": internal testers are Users and Access members and
Apple only lets the web console add them. The account's existing internal groups
(`Internal testers`, `Kinnav`, `Tether-health`, `Test`) therefore all had zero
testers, so 29 uploaded builds reached nobody.

Worked around with `scripts/testflight/distribute.rb`, which creates one external
group named **AGL Testers** per app and fills it with the 10 beta testers Apple
already holds. Verified 2026-09-21: 29/29 apps have 10 testers, the newest build
attached, and a Beta App Review submission in `WAITING_FOR_REVIEW`.

Nothing is required of a human unless you prefer internal distribution, which
would mean adding the six Users and Access members to each app's internal group
by hand in App Store Connect.

## MA-014 — Google Play internal testing has no tester list (HUMAN ONLY)

All 21 Play apps now have a **live** (no longer draft) internal-testing release,
but `GET /edits/{id}/testers/internal` returns `{}` for every one of them, so no
one can install yet. The Play Developer API can only attach *Google Groups* to a
track; the per-app email lists the team uses are creatable in Play Console alone.

In Play Console: **Test and release → Testers → Email lists**, create one list
with the ten addresses below, then on each app open **Internal testing →
Testers** and select it.

  srikanth.patchava@outlook.com, rainbow472.sri@gmail.com, sirishapatchava@gmail.com,
  aadiboddapati@gmail.com, ramana.gokul@icloud.com, nehuwakhare04@gmail.com,
  siddarthaandalu@gmail.com, rashmi.advani@gmail.com, vspatel24@gmail.com,
  pranathim95@gmail.com

Alternative that would remove the manual step for good: create a Google Group
containing those addresses and attach it once per app through the API.

The Claude in Chrome extension cannot do this. Re-tested 2026-09-21 on
`https://play.google.com/console/developers`: both `get_page_text` and
`read_page` time out, as they did on every earlier attempt.
