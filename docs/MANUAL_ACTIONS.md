# Manual actions

Things no agent can do, because they need a console login, a payment method, a
human identity, or an approval. Everything here is **verified as still
outstanding** at the date shown, not copied forward from an earlier list.

Ordered by consequence, not by effort.

---


## Where to look first

`docs/STORE_GATES.md` (generated) is the authoritative view of what each app has
met, split into what TestFlight beta and Play internal testing need versus what
App Store review and a Play production release need. Verified 2026-09-22:
**no app has been submitted for App Store review and none has a release on any
Play track other than internal.** The gates below are the ones no API exposes.

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

**Superseded 2026-09-21.** The scheme is `com.americangroupllc.<lowercase>` on
both platforms — *not* `com.americangroup.<name>` as this entry previously said.
All 43 apps now match it with no exceptions; HerJourney was the last holdout and
was fixed by deleting its old capital-J App ID (`DELETE /v1/bundleIds/PWUK6FB2Y8`
→ HTTP 204, which Spaceship exposes no method for) and registering the lowercase
one.

**Measured 2026-09-21:** App Store Connect holds 41 app records; **14 of the 43
apps have none**. Creating them is genuinely console-only. `Spaceship::ConnectAPI::App`
*does* expose `.create`, so this is worth stating precisely — the method exists and
Apple refuses the call. All 14 attempts returned:

```
The given operation is not allowed - The resource 'apps' does not allow 'CREATE'.
Allowed operations are: GET_COLLECTION, GET_INSTANCE, UPDATE
```

Evidence: `~/agl/.sweep/asc-create-evidence.json`. fastlane `produce` is not a way
around it either; it needs an Apple ID password, not the API key.

**Proven three ways on 2026-09-22, so nobody re-tries it:**

1. `Spaceship::ConnectAPI::App.create` — the method exists and Apple refuses the
   call for all 14 apps with the error quoted above.
2. The Developer Portal bundle ids are **not** the blocker. All 14 already exist
   (`BundleId.all` lists every one); creating them is not what is missing.
3. Uploading a build does not auto-create the record. A real `upload_to_testflight`
   run against AeroSwift returned:
   `Couldn't find app 'com.americangroupllc.aeroswift' on the account of
   'rainbow472.sri@gmail.com' on App Store Connect`, then polled indefinitely for a
   build that can never appear.

Creating these 14 records in the App Store Connect UI is the single remaining
blocker in the entire store checklist. Everything else passes for all 43 apps.

**Needs a record (14):** AeroSwift, BodyQuest, daily-pulse, FashionFactory,
GadgetNest, GroceryMatch, HerJourney, iMeasure, MyHealth, PlantPulse,
portfolio-board, radiotune, Verba, yourtube

**Required:** in App Store Connect → Apps, use "Drag up to 10 apps here" with the
signed IPAs in `~/agl/.dist/ipa-for-asc/` (regenerated for the new ids by
`scripts/testflight/build_only.py`), or create each record by hand with the
bundle id from apps.json. `scripts/testflight/watch_records.sh` then ships the
TestFlight build for each app within five minutes of its record appearing.

The old records can be removed from App Store Connect once nothing refers to
them; the previous build inventory is in
`~/agl/.dist/ios-batch/results-americangroupllc-2026-09-15.json`.

---

## MA-009 · Play: 23 of 43 have a bundle — 14 need an app entry, 6 need an upload-key reset

**Re-measured 2026-09-21 against the API, not against the local evidence file.**
`.sweep/play-upload-evidence.json` could not be trusted: a single-app run
overwrote it wholesale, so it recorded one app and had erased the history of the
rest. `.sweep/play_state.py` now asks Play directly per package and writes
`.sweep/play-state.json`; `play_upload.py` merges instead of clobbering.

Today's real counts: **HAS_BUNDLE 23, NO_LISTING 14, LISTING_EMPTY 6.**
CalcMaster and Kinnav are no longer blocked — both now carry a bundle, so the
key-reset list below is 6, not 8. The 6 remaining `LISTING_EMPTY` apps are
exactly the 6 whose upload key does not match.

The historical detail below is kept for context; where it disagrees with the
counts above, the counts above are the measured ones.

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

**b) Upload key does not match Play's registered one (6 as of 2026-09-21)** —
CalcMaster and Kinnav have since been resolved and now carry a bundle; the rows
for them below are historical. Re-verified on 2026-09-21: all 43 local keystores
were fingerprinted again with `keytool -list -v` and **still zero match** the
certificate Google names. Note CarDeal and VirtuBand expect the *same* cert,
which suggests those two listings were created with one shared upload key by
someone, on a machine that is not this one. These
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

## MA-010 · MOSTLY RESOLVED 2026-09-21 · policy pages are live; the www redirect is not

**Re-measured 2026-09-21.** The premise below is no longer true — the policy
pages ARE live. `https://www.safecodeg.com/policy/calcmaster/` returns 3,835
bytes titled *"CalcMaster Privacy Policy | American Group LLC"*, not the React
homepage. A sweep of every `safecodeg.com` URL referenced by app code and store
metadata (`.sweep/url_sweep.py` → `.sweep/url-sweep.json`) found **89 of 91 real**,
the other two being the site root, which legitimately is the homepage.

**How to check this correctly.** The host serves an SPA catch-all: *any* unknown
path returns HTTP 200 with the marketing homepage. A status code therefore proves
nothing — this is exactly how "43/43 URLs return 200" was once reported for pages
that did not exist. Fetch the body and compare its md5 against a deliberately
nonexistent path (`ddac27de41efeeca0c1ffddc113e6b74`, 369,371 bytes); anything
matching that hash is a 404 in disguise. The sweep script does this.

That check caught 8 apps still pointing at invented paths — `/privacy-policy`
(6 apps), `/terms`, `/support`, `/DriftDate`, `/Verba` — all now repointed at real
`/policy/<slug>/` pages and committed.

**Still outstanding:** the apex → www canonical redirect. `https://safecodeg.com/policy/calcmaster/`
answers 200 directly instead of redirecting to `www`. The `.htaccess` change is
pushed to the `deploy` branch but not published; it needs **Deploy HEAD Commit**
in cPanel → Git Version Control.

Historical context follows.

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

## MA-013 — SUPERSEDED 2026-09-22 · internal TestFlight groups CAN be filled by API

**The finding below is wrong and the workaround is no longer necessary.**
Re-tested against the live API: `POST /v1/betaTesters` carrying a `betaGroups`
relationship returns **HTTP 201** against an internal group, and the tester then
appears in `GET /v1/betaGroups/{id}/betaTesters`. The 409 that produced the
original conclusion was Apple refusing to move a tester who was *already* on
that app under another group — not a rule about internal groups. Creating an
internal group by API works too: `POST /v1/betaGroups` with
`isInternalGroup: true` returns 201.

This matters because an internal group needs **no Beta App Review**, so builds
reach the team as soon as they finish processing, rather than waiting on Apple.

`scripts/sync_testflight_testers.rb` now does this. Run 2026-09-22 across the
account: internal groups created where missing, **185 tester assignments added**,
and all **29 apps with an App Store Connect record now have an internal group
with 7 testers and `hasAccessToAllBuilds` enabled** — so future uploads
distribute with nobody touching a console. The external "AGL Testers" group is
still synced afterwards for testers who are not account users.

The original entry follows, for the record.

### Original entry (superseded)

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

**Superseded in part, 2026-09-22 — no Google Group is to be created.** The
standing decision on this account is to deliver to the people already inside it
rather than build a tester roster. That route is **internal app sharing**
(`scripts/play_internal_share.py`), which needs neither a group nor a tester
list: it returns a `play.google.com/apps/test/...` link that any user on the
Play Console account can install. Run that day, it delivered 6 of 43 apps to
the 5 installable account users. The remaining 37 are blocked by app state, not
by testers — 11 have no Play entry (MA-021) and 26 are still Draft apps, which
sharing rejects with `NOT_PUBLISHED`.

So this item is no longer "create an email list". What is left of it is only the
people who are **not** on the Play Console account and therefore cannot use a
sharing link at all. For them a Console email list is still the only mechanism:
**Test and release → Testers → Email lists**, then **Internal testing →
Testers** per app.

  srikanth.patchava@outlook.com, rainbow472.sri@gmail.com, sirishapatchava@gmail.com,
  aadiboddapati@gmail.com, ramana.gokul@icloud.com, nehuwakhare04@gmail.com,
  siddarthaandalu@gmail.com, rashmi.advani@gmail.com, vspatel24@gmail.com,
  pranathim95@gmail.com

Do not resolve this by attaching a Google Group. It was considered and rejected;
`scripts/sync_play_testers.py` remains only as the audit that names which
packages Play does not know.

The Claude in Chrome extension cannot do this. Re-tested 2026-09-21 on
`https://play.google.com/console/developers`: both `get_page_text` and
`read_page` time out, as they did on every earlier attempt.

---

## MA-015 · P1 · AdMob: real ad unit ids are needed, and ads are gated off until they arrive

**Measured 2026-09-21.** Eleven apps carried Google's public test id
`ca-app-pub-3940256099942544`. An audit classified each by whether a release
build could actually serve it, and the answer was yes for most of them:

* **No build-mode guard at all** — BodyQuest, PilotEnRoute. Test units went
  straight to `BannerAd`/`InterstitialAd.load`.
* **A guard that looked real but was inert** — Verba. `_useTestIds => kDebugMode`
  selected `VerbaConfig`, whose values were themselves test ids.
* **iOS release aliased to the test unit** — iMeasure, radiotune, Uscis-Case,
  TripNest, e.g. `static const _iosBannerRelease = _iosBannerTest;`. Android was
  correct in all four.
* **Empty prod id falling back to test** — iMaps, on iOS ×4 plus Android native
  and rewarded.
* **Another publisher's units** — yourtube shipped `ca-app-pub-1804742004018995`,
  which is not American Group LLC. One was a real, loadable unit; the rest were
  literal `YOUR_IOS_BANNER_ID` placeholders.
* **Already correct** — CalcMaster (ads hard-off until ids are real), VirtuBand.

**What was done:** every app now gates ads off unless the id is a real
`ca-app-pub-8528784688453695/...` unit, following the pattern CalcMaster already
used. No test or third-party id can reach the SDK in release, the ad slot
collapses to zero height rather than leaving a grey box, and debug builds still
get test ads. Ads switch back on automatically when a real id is filled in — no
other code change needed.

**What a person must do.** Real ids cannot be minted from here; the AdMob API
returned HTTP 401 with no ADC token. Run:

```
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/admob.readonly,https://www.googleapis.com/auth/cloud-platform
```

Units still needed: BodyQuest 6, iMaps 6, PilotEnRoute 6, Verba 4, iMeasure 2,
radiotune 2, TripNest 2, Uscis-Case 2, yourtube 2.

**Separately, the GAD application id.** Ten of the eleven still declare Google's
test app id (`~1458002511` iOS, `~3347511713` Android) in `Info.plist` /
`AndroidManifest.xml`. Only CalcMaster has real ones on both platforms. These
were deliberately left alone: registering a real AdMob *app* id is console work,
and it is a separate rejection risk from the ad-unit ids above.

---

## MA-016 · RESOLVED 2026-09-21 · iOS crash reporting had never worked

Crashlytics was wired into the apps months ago and could never have reported
anything on iOS. Measured: **0 of 42** `ios/Runner.xcodeproj/project.pbxproj`
files referenced `GoogleService-Info.plist`, so it was not copied into the app
bundle — unzipping the shipped IPAs confirmed zero copies inside
`Payload/Runner.app/`. No `AppDelegate.swift` called `FirebaseApp.configure()`,
and there is no `firebase_options.dart` anywhere, so `Firebase.initializeApp()`
had nothing to read and threw `[core/no-app]`.

It never crashed an app — every call site is wrapped in try/catch, and the code
comments document this exact state — it simply reported nothing. Android was
unaffected; the `google-services` Gradle plugin is applied in all 43.

**Fixed** for the 7 apps that depend on `firebase_crashlytics` (ApexMarketWatch,
CarDeal, GadgetNest, MyHealth, RoomCraft, Verba, WiFiTrail) by adding the plist
to the Runner target's Copy Bundle Resources with the `xcodeproj` gem — a 4-line
addition per project, verified idempotent and byte-clean. Proven rather than
assumed: WiFiTrail was rebuilt and `Payload/Runner.app/GoogleService-Info.plist`
now exists with `BUNDLE_ID = com.americangroupllc.wifitrail`, where the pre-fix
IPA of the same app had none.

**One thing still needs a decision (P2):** MyHealth's `.gitignore:53` excludes
`**/GoogleService-Info.plist`, so its config is untracked and absent from a fresh
clone — the committed pbxproj now references a file CI will not have. That repo's
own .gitignore contradicts itself on the point. Either track the config (Google
documents it as non-secret and it ships inside the binary anyway, which is what
the other six repos do) or supply it in CI.

## MA-020 — Eight Play apps need an upload-key reset (HUMAN ONLY, evidence attached)

CalcMaster, CarDeal, iMaps, iMeasure, Kinnav, TripNest, Uscis-Case and VirtuBand
are rejected at upload with "signed with the wrong key". Verified 2026-09-21:
all 43 keystores in `~/agl/.secrets/keystores/` were read with `keytool` and
**none** produces any of the eight expected SHA1 fingerprints, so the original
upload keys are not on this machine and cannot be recovered here.

| app | Play expects (SHA1, truncated by the API error) |
| --- | --- |
| CalcMaster | `60:D8:BB:7F:30:04:2F:C0:4A:5D:1D:71:3B:3D:99:F9:32:73:46` |
| CarDeal | `ED:9C:A5:63:CF:8C:C0:18:2A:63:09:CD:8A:B8:20:57:19:F9:6F` |
| iMaps | `12:8E:4F:EB:E8:74:D7:41:4F:64:B6:E8:41:E8:F6:09:15:67:FA` |
| iMeasure | `EA:C1:09:67:DE:E3:9F:85:91:F9:0A:DA:1D:5A:EF:70:98:99:F9` |
| Kinnav | `96:8B:C8:DB:89:F4:90:9A:A9:93:7D:C0:4C:8E:03:CD:F6:05:89` |
| TripNest | `D6:8C:D1:56:01:26:6D:0A:EA:F7:BD:6E:56:9F:6C:57:48:43:E4` |
| Uscis-Case | `FB:60:4C:AB:6E:10:DC:96:1A:E0:6E:04:CE:D0:BE:58:49:69:95` |
| VirtuBand | `ED:9C:A5:63:CF:8C:C0:18:2A:63:09:CD:8A:B8:20:57:19:F9:6F` |

CarDeal and VirtuBand expect the *same* key, so one shared original key covers
both. In Play Console: the app's **Setup → App integrity → App signing →
Request upload key reset**, attaching the certificate of the keystore this
machine holds for that app. Uploads work again within 48 hours.

## MA-021 — Eleven apps have no Play entry (HUMAN ONLY)

Re-measured 2026-09-22 by opening an edit against every Android package. **32 of
43 now have a Play entry**; the count was 29 earlier the same day because
daily-pulse, radiotune, yourtube, iMeasure and MyHealth were created in between.
Bundles for daily-pulse and radiotune were uploaded and are live on internal
testing as a result.

Still missing, and needing **Create app** in Play Console under the package name
in `apps.json`: AeroSwift, BodyQuest, DriftDate, FashionFactory, GadgetNest,
GroceryMatch, HerJourney, Photriya, PlantPulse, Verba, portfolio-board.

The Play Developer API cannot create an app, so this stays a console action.
`python3 scripts/sync_play_testers.py --audit` re-measures it at any time and
names exactly which packages Play does not know.

Note on the old naming: `com.americangroup.yourtube` still exists from before the
rename. YourTube now also exists under `com.americangroupllc.yourtube`, so the
old entry is dead and should be deleted.
## MA-017 · P0 · Play Data safety deletion URL — deadline 2026-09-24

Google flagged VirtuBand on 2026-09-21: *"URL provided
https://americangroupllc.github.io/policy/virtuband/delete-account.html does not
link to a valid page, HTTP server is returning 404"*. Confirmed — that host is
retired and returns 404. **If this is not fixed by 2026-09-24 the app may face
further action**, and the same form field is wrong for the whole portfolio, not
just VirtuBand.

A second, larger problem was found while fixing it: `scripts/policy_pages.py`
only wrote `delete-account.html` for apps it judged to have accounts, so **27 of
43 apps had no deletion page at all**. Google validates the URL regardless of
what the form declares, so the identical strike was queued for all of them. The
generator now writes one for every app; apps with no sign-in get a page that
says so and gives the email route rather than describing a button that does not
exist. All 43 pages are committed to the website's `main` and `deploy` branches.

**Two things a person must do.**

**1. Publish the site.** The 27 new pages are pushed but not live — verified by
fetching them and getting the marketing homepage back. Either:
   * cPanel → Git Version Control → **Deploy HEAD Commit** on the `deploy`
     branch (it already carries all 43 pages, and only `policy/` was touched, so
     `.cpanel.yml` and `.htaccess` are untouched); or
   * fix the SSH key below so the Actions deploy works on its own.

**2. Paste the URL into each app's Data safety form.** There is no Play API for
it. `docs/DATA_SAFETY_DELETION_URLS.md` lists the exact URL per app.
Play Console → app → Policy → App content → Data safety → Account deletion URL.

### The Actions deploy: diagnosed, and the last step is server-side

`docs/KNOWN_ISSUES.md` and MA-010 recorded this as "HostGator closes the SSH
connection from the runner". That was a misreading of the symptom. Two real
client-side bugs were fixed in `.github/workflows/deploy.yml`:

* the key was written with `echo`, losing the trailing newline OpenSSH requires;
* a 4096-bit RSA key is offered as three separate signature algorithms
  (rsa-sha2-512, rsa-sha2-256, ssh-rsa), each counting against the server's
  `MaxAuthTries` — which is what produced *"Too many authentication failures"*
  and made it look like the host was refusing the runner.

With `printf`, `IdentitiesOnly=yes` and `PubkeyAcceptedAlgorithms=+ssh-rsa`, the
error changed to:

```
Permission denied (publickey,password,keyboard-interactive)
```

That is one clean attempt being rejected, which means **the deploy key is not
authorised on the host**. The key is valid and parses in CI:

```
4096 SHA256:TxRQmF8ca2zS0ys/cnZ4Th+fbzCHUJ8ZGFL+iQlXHJI github-actions-deploy@safecodeg.com (RSA)
```

**Required:** add that public key to `~/.ssh/authorized_keys` for the
`SSH_USERNAME` account in cPanel → SSH Access → Manage SSH Keys (and mark it
authorised), or confirm `SSH_USERNAME`/`SSH_HOST` are right. The private half is
only in the GitHub secret, so the public half has to come from cPanel's key
manager or be regenerated as a pair.

The workflow's verify step was also replaced. It used to curl the homepage,
which returns 200 for every path on this SPA host, so it printed a success tick
whether or not anything deployed — the same false signal that let store listings
point at pages that did not exist. It now fetches a real page and fails the job
if it gets the homepage back.

## MA-022 — Production release is blocked on two console-only gates (HUMAN ONLY, attempted and measured)

Production release was attempted for every app on 2026-09-22. Both stores refused,
each for one reason, and the same reason every time.

**Apple — App Privacy answers are not published.** 27 of the 29 apps with a record
failed at the final step with:

> This resource cannot be reviewed … Answers to what data your app collects and
> how it's used are needed. - You must have published answers to your app's data usages.

Everything before that step now succeeds: `scripts/testflight/submit_production.rb`
attaches the newest valid build to the App Store version, opens a review
submission and adds the version to it. The two apps that failed differently are
CalcMaster, whose version is REJECTED and must be replaced, and one app whose
screenshot upload was still processing.

This gate cannot be closed by a script. `v1/appDataUsages` and
`dataUsagePublishState` both return "does not exist" for an API key; they need an
Apple ID web session. The answers themselves are already written for all 43 apps
in `store/privacy/<repo>.json`. Enter them under **App Privacy** in App Store
Connect and press Publish, then run `bundle exec ruby submit_production.rb`.

**Google — every app is still a Draft.** All 21 refused with:

> Only releases with status draft may be created on draft app.

Google requires the first production release of a draft app to be made in Play
Console, after the App content declarations (content rating, data safety, target
audience and content, ads, app access) are complete. Once an app is published
once, `python3 scripts/play_release.py --all --production` promotes every later
release.

Confirmed against the v3 discovery document on 2026-09-22: of those
declarations only Data safety is reachable by API, as
`applications.dataSafety` (a Safety Labels CSV). `edits` exposes just
`apks, bundles, countryavailability, deobfuscationfiles, details,
expansionfiles, images, listings, testers, tracks` — there is no content
rating, target audience, ads or app access resource, and no
`applications.create` either (`applications` has the single method
`dataSafety`).

**The Draft state also blocks the no-console delivery route,** which is the part
that was not obvious. Internal app sharing needs the app published too:
`scripts/play_internal_share.py` reached 6 of 43 apps, and the other 37 split
into 11 with no Play entry (`404`, MA-021) and 26 Draft apps (`400
UploadException: NOT_PUBLISHED`). Uploading another bundle does not help —
AGCleaner's internal track already holds a `completed` release at version code
2 and sharing still refuses it. Publishing the app once is the only unlock, and
it is the same Console work described above.

Results: `~/agl/.dist/appstore-submit-results.json`,
`~/agl/.dist/play-production-results.json` and
`~/agl/.dist/play-internal-share.json`.

## MA-018 — Tester synchronisation is automated; Android still needs one input

`.github/workflows/sync-testers.yml` keeps every tester list in step with App
Store Connect's Users and Access. It runs every six hours, on demand, and after
a delivery. The roster is `GET /v1/users` plus anyone already recorded as a beta
tester.

**iOS is finished.** Each app has two groups:

| Group | Who | Delivery |
| --- | --- | --- |
| **AGL Internal** (internal, `hasAccessToAllBuilds`) | all 7 account users | every uploaded build, immediately, **no Beta App Review** |
| **AGL Testers** (external) | the 4 roster members who are not account users | Apple reviews each build first |

Verified 2026-09-22 across the portfolio: **29 of 29 apps** report 7 account
users in the internal group, `hasAccessToAllBuilds` true, and the newest build
reachable through it. Adding someone to Users and Access is now enough — the
next sync puts them in all 29 internal groups and every build is on their phone
without anyone touching a console.

**Android takes a different route, decided 2026-09-22: no Google Group.**
Play's internal track accepts Google Groups only — `GET
/edits/{id}/testers/internal` returns `{}` for every app and the resource takes
a `googleGroups` array, not addresses — so the track is not the delivery
mechanism here. Delivery is **internal app sharing**
(`scripts/play_internal_share.py`), which reaches everyone already on the Play
Console account with no group, no tester list and no roster to maintain.

That makes `PLAY_TESTER_GOOGLE_GROUP` deliberately unset. The Play step of the
workflow then audits and reports rather than changing anything, which is the
intended steady state, not a gap. Required secrets:

| Secret | What it is |
| --- | --- |
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_CONTENT` | the App Store Connect key, base64 |
| `PLAY_SERVICE_ACCOUNT_JSON` | key for `american-group-publisher@american-group-llc.iam.gserviceaccount.com` |
| `PLAY_DEVELOPER_ID` | the number in the Play Console URL, for the account-user comparison |

What Android is actually short of is not an input but app state: sharing only
works once an app is published, so 26 Draft apps and 11 missing entries are the
real blockers (MA-021, MA-022).
## MA-019 — An App Store Connect agreement needs accepting (HUMAN ONLY, urgent)

TestFlight beta submission started failing on 2026-09-22 with:

> Beta contract is missing for the app. - Beta Contract is missing.

Measured on DriftDate, MyCard and MyFinance, each of which has a processed build
and 11 testers. In the same window eight beta reviews flipped to REJECTED
(AGrammarly, CalcMaster, EventSpark, NexusTransferPay, Photriya, PilotEnRoute,
Uscis-Case, iMaps) — and AGrammarly, EventSpark and NexusTransferPay were
rejected on freshly built binaries, so the cause is not the code.

Earlier the same day 17 apps passed beta review normally, so this is a change in
account state rather than a per-app problem. The usual cause is an updated Apple
Developer Program License Agreement waiting for the Account Holder
(srikanth.patchava@outlook.com) in **App Store Connect → Business → Agreements**.
Until it is accepted, no build reaches a tester and no version can be submitted.

There is no API for this: agreements are not exposed to an API key, and the
rejection reasons live in Resolution Center, which also is not
(`v1/reviewRejections` returns "does not exist"; the submission itself reports
only `betaReviewState: REJECTED`).

After accepting, re-run:

```
bundle exec ruby scripts/testflight/distribute.rb --all
```

which resubmits everything that is not already approved. Builds already approved
(18 apps) keep working throughout.
