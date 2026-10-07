# Manual actions

Things no agent can do, because they need a console login, a payment method, a
human identity, or an approval. Everything here is **verified as still
outstanding** at the date shown, not copied forward from an earlier list.

Ordered by consequence, not by effort.

---


## Where to look first

`status.csv` (generated) is the authoritative view of what each app has
met — the `gate: *` columns split it into what TestFlight beta and Play internal testing need versus what
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

## MA-004 · RESOLVED 2026-09-27 · every app has an upload keystore, and CI can reach it

All 43 keystores exist in `~/agl/.secrets/keystores/`, and all 43 are now
`KEYSTORE_<APP>_BASE64` secrets on `agl-manifest`. `ANDROID_KEYSTORE_CONFIG` was
regenerated from the local registry so it covers 43 apps rather than 30.

The gap was not the keystores — those had been generated. It was that 13 of them
had never been uploaded as secrets, which only became visible when the ship
pipeline built the whole portfolio for the first time (run 36304281088) and 13
apps reported `NO_KEYSTORE`:

AeroSwift, AGStudio, ApexMarketWatch, BuddyPlay, CalcMaster, CodeDeal,
DriftDate, Kinnav, MyCard, NexusTransferPay, PlantPulse, TripNest,
portfolio-board

Verified after uploading: 43/43 expected secret names are present.

The passwords live in `~/agl/.secrets/keystores.json`, which is gitignored and
must stay that way. A lost upload key still cannot be replaced without Google's
intervention, so that file is the one thing here worth backing up somewhere a
person controls.

---

## MA-005 · RESOLVED 2026-09-30 · CI builds and signs iOS

**Closed. CI produced a distribution-signed IPA on run 36688250993, every step
green including "Prove every IPA is distribution-signed".**

This was treated as permanently human because the one distribution
certificate's private key sat in a keychain where export needs a GUI prompt.
It did not need exporting. A certificate issued against a CSR generated
locally keeps its private key local from the start:

```
openssl req -newkey rsa:2048 -nodes -keyout dist.key -out dist.csr
Spaceship::ConnectAPI::Certificate.create(certificate_type: "DISTRIBUTION",
                                          csr_content: csr)
-> 2S2F6CDFY2  Apple Distribution: American Group LLC (TLH7Z3G27A)
```

Key and certificate verified to pair, packaged as a .p12, set as
IOS_DIST_CERT_P12 / IOS_DIST_CERT_PASSWORD. Then 45 provisioning profiles were
re-issued to accept it, because a profile pins which certificates may sign
against it and Apple has no update for that list.

Three further things stood behind it, each only visible once the one in front
was gone:

1. The Firebase plugins disagreed on firebase-ios-sdk — crashlytics wanted
   12.18.0, remote_config 12.19.0. Invisible locally, where CocoaPods
   resolves; CI uses Swift Package Manager, which refuses two versions.
   Aligned across 38 apps on 12.19.0.
2. GoogleService-Info.plist was gitignored in 6 apps and tracked in 37. It is
   not a credential — it ships inside every binary — so the six were made
   consistent with the other thirty-seven.
3. build_ipa.py recorded the reason for a failure but only printed the
   verdict, and a failed job skipped the artifact upload, so the reason never
   left the runner. Both fixed; that is how 1 and 2 were found at all.

---

## MA-005b · the original note

**Half of this is now resolved. Updated 2026-09-26.**

`ASC_KEY_ID`, `ASC_ISSUER_ID` and `ASC_KEY_CONTENT` are set, so App Store
Connect *API* calls work.

**Provisioning profiles: done, no longer manual.** `scripts/ios_profile_map.rb`
pulls them straight from the API — it maps all 43 bundle ids to an active App
Store profile and, with `--install`, writes the `.mobileprovision` files where
Xcode looks. Verified 2026-09-26 against a throwaway `HOME`: 43 files written,
and one decoded with `security cms -D` to confirm it is a real profile rather
than an empty placeholder. `match` is therefore not needed for profiles.

**The certificate is still blocked, and only this half is.** The API cannot
hand out a certificate's *private key*, so no script can obtain it. The iOS job
now fails immediately with this explanation instead of dying ten minutes later
inside `build_ipa.py`.

**Required:** from the Mac whose keychain already holds the Apple Distribution
identity, export it with the private key:

```
security find-identity -v -p codesigning        # confirm it is there
# Keychain Access -> My Certificates -> the "Apple Distribution: ..." row
# -> right-click -> Export -> .p12, set a password
base64 -i dist.p12 | pbcopy
```

then add two repository secrets:

| Secret | Value |
| --- | --- |
| `IOS_DIST_CERT_P12` | the base64 of the `.p12` |
| `IOS_DIST_CERT_PASSWORD` | the password set during export |

Nothing else is outstanding for iOS signing: the workflow already creates a
throwaway keychain, imports the identity, and asserts `security find-identity`
reports at least one distribution identity before it archives anything.

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

**Re-measured 2026-09-26 against the live API: 38 of 43 apps have a record, and 5 do not** — BodyQuest, FashionFactory, MyHealth, PlantPulse, radiotune. It was 14 when this was written. Creating them is genuinely console-only. `Spaceship::ConnectAPI::App`
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

Re-confirmed live on 2026-09-22 against AeroSwift — same refusal, word for word.
The API key is not going to start working.

### The one input that would automate this

"Needs an Apple ID password" is not the same as "needs a person to click 43
times". What `produce` actually needs is a **web session**, and fastlane mints
one from a single 2FA code:

```bash
cd ~/agl/agl-manifest
bundle exec fastlane spaceship spaceauth -u rainbow472.sri@gmail.com
# type the 2FA code once; it prints a FASTLANE_SESSION value, good for ~30 days
export FASTLANE_SESSION='...'
```

With that exported, the same session unlocks **both** Apple blockers in the
checklist, which no API key can touch:

| Blocker | Why the session fixes it |
| --- | --- |
| 14 missing app records (this entry) | `produce` creates records over the Apple ID session |
| 27 apps stuck on App Privacy (MA-022) | `appDataUsages` is served by spaceship's *tunes* client, which is cookie-authenticated |

Both are then scriptable in one pass, so the human cost of the entire Apple
side is one 2FA code rather than 41 console visits.

**Not yet verified.** This has not been executed here — generating the session
needs a 2FA code that only the account holder receives. What *is* verified is
that the tooling is installed (`fastlane 2.239.0`, `produce` and
`spaceship spaceauth` both present) and that
`spaceship/connect_api/tunes/client.rb` accepts a `cookie:` as well as a
`token:`. Treat the outcome as expected, not proven, until a run exists.

**Required:** in App Store Connect → Apps, use "Drag up to 10 apps here" with the
signed IPAs in `~/agl/.dist/ipa-for-asc/` (regenerated for the new ids by
`scripts/testflight/build_only.py`), or create each record by hand with the
bundle id from apps.json. `scripts/testflight/watch_records.sh` then ships the
TestFlight build for each app within five minutes of its record appearing.

The old records can be removed from App Store Connect once nothing refers to
them; the previous build inventory is in
`~/agl/.dist/ios-batch/results-americangroupllc-2026-09-15.json`.

---

## MA-009 · Play: 30 of 43 have a bundle — 7 need an app entry, 6 need an upload-key reset

**Re-measured 2026-09-28 against Play, not carried forward.** 30 HAS_BUNDLE,
6 LISTING_EMPTY (all six blocked on the upload key, below), 7 NO_LISTING.
The earlier figures — 23 with a bundle and 14 needing an entry — are stale.

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

Still live on 2026-09-22 — the AAB rebuilt that day still carries
`19:F9:46:43:71:52:66:A8:3C:43:B2:13:9E:4F:D7:10:16:E1:98:5A` for CalcMaster,
the same certificate Play rejected, because the local keystores were generated
on 2026-09-11, after Play had registered a different key.

**This does not block getting a build to a tester.** Internal app sharing does
not check the upload key, and on 2026-09-22 the six apps it delivered —
CalcMaster, iMaps, iMeasure, TripNest, Uscis-Case, VirtuBand — were *all* on
this list. So MA-020 gates the store release and the internal track, not test
distribution; `scripts/play_internal_share.py` routes around it. CarDeal and
Kinnav are the two that stayed unreachable, and only because they are still
Draft apps (MA-022).

## MA-021 — Seven apps have no Play entry (HUMAN ONLY)

**Re-measured 2026-09-28: seven, not eleven.** DriftDate, FashionFactory,
GadgetNest, GroceryMatch, HerJourney, Verba, portfolio-board.

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

Note on the old naming: **resolved 2026-09-26.** Four records used to sit on
the retired `com.americangroup.*` scheme — bodyquest, daily-pulse, radiotune
and yourtube. The owner has cleared them, and a sweep of all 43 legacy ids
against the live API now returns **zero** such records. Every App Store
Connect record is on `com.americangroupllc.*`, matching what the apps build.
The table below is kept as the record of what was there:

| stale record | name it holds | app id |
| --- | --- | --- |
| `com.americangroup.bodyquest` | BodyQuest | 6808737432 |
| `com.americangroup.daily-pulse` | daily-pulse | — |
| `com.americangroup.radiotune` | RadioTune World | 6799065525 |
| `com.americangroup.yourtube` | YourTube: Watch & Discover | — |

None of those four has a record under its current `com.americangroupllc.*`
bundle id, so they are counted among the 13 "missing" above — but they are
mis-bound rather than absent, which needs a different action. Apple does not
allow a record's bundle id to change, so the stale record must be deleted or
abandoned before the right one can be created, and until then it is holding
the app's name.

### Re-measured 2026-09-24 (later the same day): one is mis-bound, not four

The owner deleted the stale `com.americangroup.*` records for BodyQuest,
daily-pulse and yourtube, and created a correct record for daily-pulse. Asking
Apple for every old and new bundle id now returns exactly one collision:

| App | Stale record still holding the name |
| --- | --- |
| radiotune | `com.americangroup.radiotune` — "Radio Tune: Live Radio" |

The other twelve simply have no record and can be created directly. Apple holds
35 records in total, 30 of them bound to a current `com.americangroupllc.*`
identifier.

## MA-017 · P0 · Play Data safety deletion URL — deadline 2026-09-24

Google flagged VirtuBand on 2026-09-21: *"URL provided
https://americangroupllc.github.io/policy/virtuband/delete-account.html does not
link to a valid page, HTTP server is returning 404"*. Confirmed — that host is
retired and returns 404. **If this is not fixed by 2026-09-24 the app may face
further action**, and the same form field is wrong for the whole portfolio, not
just VirtuBand.

A second, larger problem was found while fixing it: `scripts/policy_pages.py`
only wrote `delete-account.html` for apps it judged to have accounts, so **27 of
43 apps had no deletion page at all** — since fixed; all 43 are live, verified
2026-09-28 by byte length against a nonsense control path and recorded in
[`deletion-urls.json`](deletion-urls.json). Google validates the URL regardless of
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

**Still outstanding on 2026-09-30, eight days on, and it is the single reason
nothing reaches a tester or the store.** Re-confirmed today by running the
distribution directly:

```
AGCleaner  build 202609250224 -> AGL Internal (6 account users, immediate)
                              +  AGL Testers (10/10)
           review submit failed: Beta contract is missing for the app.
```

This is what a tester sees as *"requested app not available or doesn't
exist"*. The build is fine — VALID, not expired, 10 testers on the external
group — but an external group receives nothing until Beta App Review accepts
it, and Beta App Review cannot be submitted without the contract.

**Internal testing is unaffected and works right now.** The internal group has
`hasAccessToAllBuilds = true` and the builds report
`internalBuildState: IN_BETA_TESTING`, so the six App Store Connect account
users can install today, on the Apple ID that is a user on the account. Anyone
else cannot, and no amount of re-uploading changes that.

Checked again that no API exposes this: `iris/v1/agreements` returns 404 "The
specified resource does not exist", and `ra/contracts` returns an empty body
to an Apple ID session.

## MA-019b — the original note

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

## MA-023 — Six apps show a paywall with no in-app purchase behind it (DECISION NEEDED)

Found 2026-09-24 while building `status.csv`. Six apps ship a
subscription or premium screen, several with real prices on it, and carry no
purchase SDK at all — no `in_app_purchase`, no `purchases_flutter`, no
`revenue_cat`:

| app | screen | price shown |
| --- | --- | --- |
| CodeDeal | `lib/features/paywall/paywall_page.dart` | $4.99 / $39.99 |
| NexusTransferPay | `lib/.../subscription_screen.dart` | $7.99 / $9.99 |
| Kinnav | `lib/screens/subscription_screen.dart` | $3.99/mo, $39.99/yr |
| VirtuBand | `lib/.../premium_screen.dart` | "Purchase" + price |
| NewsBoard | `lib/features/premium/premium_screen.dart` | price |
| daily-pulse | `lib/.../premium_news_card.dart` | price |

Kinnav's own source says it outright:

> Subscription plans ($3.99/mo, $39.99/yr). UI + local state only — real IAP
> (App Store / Play) lands in Phase 6.

That is **App Review guideline 3.1.1** — unlocking features has to go through
in-app purchase — and arguably 2.1 as well, because the button does not
complete a purchase. It is a rejection, not a warning, and it is the kind that
comes back after the binary is otherwise approved.

Three ways out, and it is a product call, not a technical one:

1. **Remove the paywall screen** from the build for the first release. Cheapest,
   and nothing else in these apps depends on the subscription state.
2. **Wire real IAP** — add the SDK, create the products in both consoles, and
   test a sandbox purchase per app. Console work per product on both stores.
3. **Make it clearly "coming soon"** with no prices and no purchase affordance.
   Apple tolerates this; prices with a dead button is what it rejects.

`scripts/store_master_csv.py` detects the condition, so whichever way it is
resolved the CSV stops flagging it once the paywall or the gap is gone.

## MA-031 — Two old-naming Play entries to remove (HUMAN ONLY)

Measured 2026-09-24 by opening an edit against the pre-rename package of every
app. Two survive from before the move to `com.americangroupllc.*`:

| Package | Listing title | Tracks |
| --- | --- | --- |
| `com.americangroup.yourtube` | "YourTube - Video Discovery" | all empty |
| `com.americangroup.myhealth` | "MyHealth" | internal has a completed release; production holds a draft |

Both apps already exist under their correct identifiers, so these are dead
entries. `com.americangroup.yourtube` has never had a release and should delete
cleanly. `com.americangroup.myhealth` has a completed internal release, so Play
may ask you to unpublish before it will delete.

**No API can do this.** The discovery document lists exactly one method on the
resource:

```
androidpublisher.applications.dataSafety
```

There is no create and no delete. Removal is **Play Console → the app →
Setup → Advanced settings → App availability**, or Delete app where Play
offers it.

Nothing else is needed to do it — in particular the developer registration
order number is a payment receipt, not a credential, and plays no part in
deleting an app. It is deliberately not recorded here.


## MA-024 — Five App Store records still cannot be created (2026-09-26)

A live Apple ID session (`fastlane spaceauth`) unblocked record creation, which
the API key refuses. Eight were created on 2026-09-26: AeroSwift, GadgetNest,
GroceryMatch, HerJourney, iMeasure, portfolio-board, Verba and yourtube. Apple
now holds 38 of 43.

Note for anyone reading the old note: `Spaceship::Tunes::Application.create!`
is dead — Apple answers "There is no route for the path 'apps/create/v2/'".
`fastlane run produce` uses the current endpoint and works.

Five remain, for two different reasons.

**Name already taken (2).** `produce` refuses before creating anything:

| App | Apple's answer |
| --- | --- |
| FashionFactory | "already being used for another app in **your** account" — `com.americangroupllc.styleradar` is holding "Fashion Factory: Deals" |
| PlantPulse | "already being used" on a **different** account — someone else owns the name "PlantPulse" |

FashionFactory is self-inflicted and fixable: rename or delete the styleradar
record, which is a duplicate of this app and already slated for removal.
PlantPulse needs a different App Store name; the portfolio's own precedent for
this is an `i` prefix (iMileMaster, iMyFinance, iNewsBoard), so "iPlantPulse"
would match, but it is a branding call rather than a mechanical one.

**Bundle id held by a record the API key cannot see (3).** BodyQuest, MyHealth
and radiotune: `produce` reports "App '<bundle id>' already exists" with an id
(6781642312, 6778216891, 6781629995), but fetching any of those ids with the API
key returns "There is no resource of type 'apps' with id …". A record that the
session can see and the key cannot is one Apple is still holding in a removed
state. Check each in App Store Connect; once Apple finishes releasing the
identifier, `produce` will create them.

## MA-025 — Play Data safety can be automated, but needs Google's CSV template first

`applications.dataSafety` is the one App content declaration with an API. It
takes the Data Safety answers as the contents of Google's own CSV, and it
validates the header row before anything else. Probed 2026-09-26 against
AGCleaner:

```
POST /androidpublisher/v3/applications/{pkg}/dataSafety   {"safetyLabels": "..."}
400  Invalid safety labels declaration:
     Line 1: Invalid header row. Download the sample CSV file to see an example.
```

The API will not name its own columns, and Data Safety is a legal statement
about what each app collects. Guessing the schema is not acceptable, so this is
not something to infer.

**One download unlocks it for all 43.** In Play Console, open any app's
**Policy → App content → Data safety** and use **Export to CSV**. Drop that file
in `store/data-safety-template.csv`. The accurate per-app answers already exist
in `store/privacy/<repo>.json` — derived from each app's real dependencies, not
asserted — so filling the template per app and POSTing it is then mechanical.

The other App content declarations (content rating questionnaire, target
audience, ads, app access) have no API at all: `edits` exposes only
`apks, bundles, countryavailability, deobfuscationfiles, details,
expansionfiles, images, listings, testers, tracks`.

## MA-026 — Three apps are held by stale review submissions that no API can clear

**Re-diagnosed 2026-09-28. The earlier reading — that these needed a new App
Store version — was wrong.**

AeroSwift, CalcMaster and Kinnav each carry **two `READY_FOR_REVIEW` review
submissions that were never actually submitted** (no `submittedDate`). They
hold the version, and every attempt to submit returns:

```
Version is not ready to be submitted yet, please try again later
```

They are the only three apps in the portfolio with un-submitted
`READY_FOR_REVIEW` submissions, and they are exactly the three apps not
progressing — the other 40 have none. That correlation is the evidence.

Neither route out exists for an API key, both tested today:

```
DELETE /v1/reviewSubmissions/{id}
  403  The resource 'reviewSubmissions' does not allow 'DELETE'.
       Allowed operations are: CREATE, GET_COLLECTION, GET_INSTANCE, UPDATE

PATCH  /v1/reviewSubmissions/{id}   {"attributes": {"canceled": true}}
  409  Resource is not in cancellable state
```

A submission can be cancelled only once it has been submitted; one that was
prepared and abandoned can only be removed in App Store Connect.

**Required:** App Store Connect → each app → the review submission that is
"Ready for Review" but never sent → remove it. Then the pipeline can submit,
which it will do unattended.

Fixed along the way, because it was genuinely missing and is required on an
update: both versions had an empty "What's New". The release notes already
existed in each repo at `fastlane/metadata/en-US/release_notes.txt` and had
never been pushed to App Store Connect; they are now set. That was not the
cause of the block, but it would have been the next one.

---

## MA-026b — the original diagnosis, kept for the record

36 of 43 apps are in App Store review. These two are not, and no retry will fix
them. Both sit at `PREPARE_FOR_SUBMISSION`, but their App Store version is
already attached to an earlier submission that has since completed:

```
Item is already present in another reviewSubmission -
appStoreVersions with id 887124460 was already added to a …
```

Apple will not add a version to a second review submission, so the surface
error is the misleading "App … must have an approved appStoreVersions for
platform IOS". Opening a fresh submission does not help, which was tested.

The fix is a new App Store version — CalcMaster 4.0.2 → 4.0.3, Kinnav
1.0.1 → 1.0.2 — with a build whose `CFBundleShortVersionString` matches. That
is a version decision rather than a mechanical one, which is why it is here and
not in a script. Once the version exists,
`bundle exec ruby scripts/testflight/submit_production.rb CalcMaster Kinnav`
finishes it.

Kinnav also had a screenshot stuck at `AWAITING_UPLOAD`, which blocked it
separately. That one was fixed: the unfinished asset was deleted and the
screenshots re-delivered.

## MA-027 — AdMob: the API reads but will not create; the console will not automate either

The goal is 86 AdMob apps (43 x 2 platforms) with a banner and interstitial unit
each. `scripts/admob_setup.py` does all of it and is committed and working up to
the write call. Both routes were tried on 2026-09-26.

**API.** v1 is read-only; **v1beta** does expose `accounts.apps.create` and
`accounts.adUnits.create`. An Application Default Credential with the
`admob.monetization` and `admob.readonly` scopes was obtained and **reads the
account fine** — `accounts.list` returns `accounts/pub-8528784688453695` and
`apps.list` returns the 8 apps already there. Creating is refused:

```
POST /v1beta/accounts/pub-8528784688453695/apps
403  {"message": "The caller does not have permission", "status": "PERMISSION_DENIED"}
```

No further detail is given. The AdMob API is enabled on the project and the
quota project header is sent (without it the call fails differently, naming the
missing quota project). Read and write therefore differ by permission, not by
setup, which points at AdMob write access needing to be granted for this
publisher rather than anything fixable here.

**Console.** `admob.google.com/v2/apps/list` cannot be driven by the Claude in
Chrome extension: `executeScript` waits the full 45 seconds for `document_idle`
and gives up, and screenshots fail with "Script injection timed out". The same
page returned its (nearly empty) text once while still loading, so the extension
is connected — the console simply never reaches the state the content script
needs. This matches the App Store Connect and Play Console behaviour in
`docs/KNOWN_ISSUES.md`.

**What unblocks it.** Either AdMob write access for pub-8528784688453695, after
which `python3 scripts/admob_setup.py` creates all 86 and writes the ids into
`docs/admob-ids.json`; or the apps are added by hand in the AdMob console.

## MA-028 — Every App Store rejection is the same one, and it is not a bug

**Updated 2026-09-28 — the resubmission path is now located exactly.**

23 apps sit on a review submission in `UNRESOLVED_ISSUES`, which is the
rejected one. Asking App Store Connect to resubmit it returns:

```
Version is not ready to be submitted yet, please try again later
```

That is not a transient state and waiting does not clear it. Apple's Guideline
2.1 text says to *reply in App Store Connect* with the requested information;
until that reply exists the submission is not resubmittable. Replying needs an
Apple ID web session — the public API 404s on `v1/resolutionCenterThreads`, so
an API key cannot post it, the same limit that made reading the reasons need
`spaceauth`.

Things ruled out today, each by testing rather than reasoning:

  * **Missing "What's New".** Real and now fixed for CalcMaster, Kinnav and
    yourtube — App Store Connect requires it on an update and all three were
    empty, with the text sitting unused in each repo's
    `fastlane/metadata/en-US/release_notes.txt`. Setting it did not unblock
    submission, so it was a genuine gap and not the cause.
  * **Missing demo credentials.** `demoAccountRequired` is false on every app
    checked, so Apple is not waiting on a login.
  * **Stale review submissions.** Only 4 apps carry un-submitted
    `READY_FOR_REVIEW` submissions; 24 are blocked. Counted before and after
    several submit runs: 9 across 4 apps both times, so the tooling is not
    creating them either.
  * **Incomplete metadata.** yourtube's version has a VALID build attached,
    733 characters of description, 79 of keywords, a support URL and 671
    characters of review notes.

**Required, per app:** App Store Connect → Resolution Center → reply to the
rejection with the six items Apple lists, the first of which is a screen
recording made on a physical device. The review notes already carry items 2-6
for all 39 apps with a record, written by `scripts/testflight/review_notes.rb`,
so the reply can quote them.

Once a reply is posted, `submit_production.rb` finishes the job unattended.

---

## MA-028b — the original note

All 20 rejected apps carry an identical Guideline 2.1 notice, read out of
Resolution Center on 2026-09-27:

> This app has been submitted by a developer account that has a limited App
> Review history. We need additional information to better understand the app
> and complete the review.

Nothing was rejected for a defect. Apple asks a new account for five things and
says to put them in the Notes field of App Review Information.

**Four are now written, for all 38 apps with a record**, by
`scripts/testflight/review_notes.rb`, from facts this repository already holds
rather than prose invented per app: the purpose and audience from the store
copy, how to reach the main features and whether a login exists from each app's
auth configuration, the external services from its own pubspec, and regional
differences from how many locales it ships.

**The fifth cannot be scripted.** Apple wants a screen recording made on a
physical device, starting at launch and showing the typical user flow, plus
account creation, deletion and any user-generated content where those exist.
That is one recording per app, attached as a reply in Resolution Center.

Reading the reasons at all needed the `iris` host and an Apple ID session: an
API key gets 404 on `v1/resolutionCenterThreads`, and a rejected submission
otherwise reports only its state with no text. `rejection_reasons.rb` does this
and writes `~/agl/.dist/rejections.json`.

## MA-029 — The Data safety deletion URL is still the old domain, and the new one needs .html

Google's rejection quotes
`https://americangroupllc.github.io/policy/iMaps/delete-account` returning 404.
Confirmed 2026-09-27: that URL does 404, and it is the retired GitHub Pages
mirror.

**Apple is clean.** All 38 App Store records carry a `www.safecodeg.com` privacy
URL; none still points at github.io.

**Play is not.** The account-deletion URL lives in the Data safety form, which is
Console-entered and has no API, so nothing here could have changed it. It still
holds the github.io address.

**There was a second, quieter problem.** Even on the right domain, only the
`.html` form worked:

| URL | Result |
| --- | --- |
| `…/policy/iMaps/delete-account.html` | 11,363 bytes, "Delete Your Account — iMaps" |
| `…/policy/iMaps/delete-account` | 154,027 bytes — byte-identical to a path that does not exist |

The extensionless form matched neither a file nor a directory, so Apache's SPA
catch-all answered with the site shell and HTTP 200. A crawler reasonably reads
that as the page not being there. `www.safecodeg.com` now has a rewrite that
serves the matching `.html` before the catch-all can claim the request, so both
forms work once that deploys.

`scripts/verify_deletion_urls.py` reported all 43 pages REAL throughout, because
it only ever tested the `.html` form. Worth knowing before trusting it again.

**To close this**: in Play Console, for each app, Policy → App content → Data
safety, set the deletion URL to
`https://www.safecodeg.com/policy/<slug>/delete-account.html` (slugs are in
`scripts/policy_pages.py`). Use the `.html` form even after the rewrite deploys;
it is the one proven to serve real content.

---

## MA-030 · P1 · Deploy the website, or the policy-URL fix is not live

**Both branches of `www.safecodeg.com` are pushed and correct. The site is not
serving them.** Verified 2026-09-28, after pushing:

```
https://www.safecodeg.com/policy/imaps/delete-account.html
  -> 200, 369,371 bytes, 0 redirects      (still the marketing homepage)
https://www.safecodeg.com/policy/iMaps/delete-account.html
  -> 200,  11,364 bytes                   (the real page, unchanged)
```

`main` is at `95b13f6` and `deploy` at `0c20820`, both carrying 41 rewrite
rules that make every miscased or aliased policy URL 301 to the canonical
slug. Pushing to `deploy` does not publish: `.cpanel.yml` only chmods files
after a checkout, and the checkout is triggered from the cPanel UI.

**Required:** cPanel → Git Version Control → the `safecodeg` repository →
**Deploy HEAD Commit**.

Then re-check the first URL above. It should answer 301 to
`/policy/iMaps/delete-account.html` and end at 11,364 bytes. If it still
returns 369,371, the deploy did not run — do not take a 200 as success on this
host, it serves the homepage for every unmatched path.

This gates MA-029: pasting the new deletion URLs into Play's Data safety form
is only worth doing once the URLs a reviewer might try actually resolve.

## MA-032 — Resubmitting after a rejection is a wait, not a fix

All 20 rejections were one Guideline 2.1 information request (MA-028), and the
information is now in App Review Notes for every app. Resubmitting them then hit
a second, unrelated wall.

A rejected version stays attached to the submission that carried it, which sits
in `UNRESOLVED_ISSUES`. A new submission cannot take that version:

```
Item is already present in another reviewSubmission -
appStoreVersions … was already added to another reviewSubmission with id …
```

and the symptom further down is the misleading "App … must have an approved
appStoreVersions for platform IOS". The way back in is to resubmit that same
submission, which is what the Console's Submit for Review does, and
`submit_production.rb` now does it. Apple's answer on 2026-09-28, for all 23:

```
Version is not ready to be submitted yet, please try again later
```

That is a wait imposed after a rejection, not a missing field.
`scripts/testflight/watch_resubmit.sh` retries every 30 minutes for a day and
stops as soon as none are blocked. It is running.

### The five records, re-tested the same day

| App | Result |
| --- | --- |
| FashionFactory | **created** — `com.americangroupllc.styleradar` was holding the name "Fashion Factory: Deals"; that record is an unreleased duplicate, so it was renamed to "StyleRadar (retired duplicate)" and the real record created |
| BodyQuest, MyHealth, radiotune | still "already exists" against a record id the API key cannot fetch — Apple has not finished releasing the identifier |
| PlantPulse | the name is owned on another account; it needs a different App Store name |


## MA-031 — BodyQuest, MyHealth and radiotune need new bundle ids

`produce` keeps answering "already exists" for these three with a record id the
API key cannot fetch. Queried through the `iris` host with an Apple ID session on
2026-09-28, those ids resolve and every one is a **deleted** record still holding
the identifier:

| App | Record id | Name on the dead record | Bundle id | removed |
| --- | --- | --- | --- | --- |
| BodyQuest | 6781642312 | "BodyQuest for AI" | `com.americangroupllc.bodyquest` | true |
| MyHealth | 6778216891 | "Srikanth Patchava" | `com.americangroupllc.myhealth` | true |
| radiotune | 6781629995 | "radiotune RADIO TUNE" | `com.americangroupllc.radiotune` | true |

Apple does not release the bundle identifier of a deleted app record. Waiting
will not clear this, which is why repeated retries have all returned the same
answer.

**These three need a different bundle id**, and because the portfolio keeps one
identifier per app across both stores, that is a decision rather than a
mechanical change — and it is permanent once a record exists. The Play side of
all three is fine and must not be touched.

A suffixed identifier is the usual way out, for example
`com.americangroupllc.bodyquestapp`. Say which form you want and the records can
be created, built, uploaded and submitted in one pass; nothing else about these
three is blocked.

## MA-032 · P0 · Android developer verification is due TODAY (2026-09-30)

Read from Play Console's notification panel on 2026-09-30, once the browser
extension started working. **This is invisible to the Play Developer API** —
there is no notifications resource — so nothing in this repository could have
surfaced it.

> AMERICAN GROUP LLC — Sep 8
> Ensure your apps are registered for Android developer verification by
> **Sep 30, 2026**

That is today. Google has been phasing in developer verification, and apps from
unverified developers stop being installable on certified Android devices once
it bites. Check it immediately under **Play Console → Settings → Developer
account → Developer verification**, or follow the notification itself.

Two other notices in the same panel, both time-limited:

| Notice | Deadline |
| --- | --- |
| RatioTune — "You have until **Oct 7, 2026** to recover this deleted app" | 7 Oct |
| a second deleted app — "You have until **Oct 1, 2026** to recover" | 1 Oct |

The recovery windows matter: a deleted Play app can be restored inside them, and
the identifier is otherwise gone for good. If either deletion was a mistake,
recovering is far cheaper than a new package name.

One notice is good news: "App update published. Users should see changes
immediately", dated Sep 30.

**Lesson worth keeping:** Play Console notifications carry hard deadlines that no
API exposes. They need a person, or a working browser extension, to read.

## MA-033 · P2 · Play testers must come from a Google Group or be typed by hand

**Who:** the Play Console admin, `rainbow472.sri@gmail.com`.

All nine external testers are on all 43 apps in TestFlight. On Google Play
they are on **none** of them, across `internal`, `alpha` and `beta`
(`python3 scripts/sync_play_testers.py --audit`).

This cannot be closed with a script as things stand. Play's `Testers` resource
accepts exactly one field:

```
PUT .../edits/{id}/testers/internal  {"testers": ["someone@gmail.com"]}
400 INVALID_ARGUMENT  Unknown name "testers" at 'testers': Cannot find field.

PUT .../edits/{id}/testers/internal  {"googleGroups": ["..."]}
200
```

So there are two routes and no third:

1. **Create one Google Group** containing the nine addresses, add its address
   to the `google_groups` array in `store/testers.json`, then run
   `PLAY_TESTER_GOOGLE_GROUP=<group> python3 scripts/sync_play_testers.py`.
   That applies it to 43 apps × 3
   tracks in one pass and keeps the roster in one file.
2. **Type the nine addresses into Play Console** for each app and track —
   129 lists to maintain by hand, and they drift the moment the roster changes.

Route 1 was previously declined in favour of plain email lists. Plain email
lists are only reachable through route 2, so this stays open until one of the
two is chosen. Nothing else about Play delivery is blocked on it.

## MA-034 · P1 · What a passing checklist still did not catch

Closed 2026-10-01, recorded because the lesson generalises: an audit that
never attempts the thing it is auditing will report ready and be wrong.

`asc_readiness.rb` reported 43/43 ready against Apple's own "Unable to Add for
Review" list. Submitting then failed on four requirements that list does not
mention and that save cleanly when written:

| Missing | Apps | Where it lives |
| --- | --- | --- |
| `copyright` | 1 | `appStoreVersions` |
| `appStoreReviewDetail` | 1 | its own resource, created against the version |
| screenshots for `APP_IPHONE_67` / `APP_IPAD_PRO_3GEN_129` | 4 | `appScreenshotSets` |
| age-rating answers | 16 | `appInfos/{id}/ageRatingDeclaration` |

And one it *did* list, which the check passed anyway: **pricing**. A bare
`GET appPriceSchedule` answers 200 with a schedule that contains no price, so
"has a schedule" is not "has a price". Three apps were reported ready and then
refused with "App is not eligible for submission until pricing has been set".
The check now asks for `?include=manualPrices` and counts them.

Two root causes worth keeping:

* **`store/ratings/<repo>.json` replaced `default.json` instead of layering
  over it.** When Apple added `socialMedia` and `socialMediaAgeRestricted`,
  answering them in `default.json` fixed 29 apps and silently missed the 14
  with a file of their own. It merges now, so a new Apple field is answered
  once.
* **PlantPulse's whole metadata delivery failed on its name.** Another
  developer holds "PlantPulse", so Apple answers 409 — and `deliver` aborts
  the run, meaning the screenshots never uploaded either. Both the manifest
  copy and `fastlane/metadata/en-US/name.txt` now say `iPlantPulse`.

After all of it: 43/43 clean, and BodyQuest, MyHealth and radiotune went from
blocked to WAITING_FOR_REVIEW.

## MA-028 · CLOSED 2026-10-01 — the 23 rejected apps are resubmitted

MA-028 concluded that an app held in `UNRESOLVED_ISSUES` could only be freed
by replying in Resolution Center, which needs an Apple ID session. That was
measured, and it is no longer what Apple does.

```
PATCH v1/reviewSubmissions/{id}  {"canceled": true}
200   state -> CANCELING   (previously 409 "not in cancellable state")
```

Verified end to end on AeroSwift before running it anywhere else: cancel 200,
state CANCELING, then `submit_production.rb` answered "SUBMITTED FOR APP STORE
REVIEW (build 202609260214)". Applied to all 24 held apps, all 24 cancelled,
13 submitted immediately and the rest were already waiting.

**App Store state is now 26 WAITING_FOR_REVIEW, 16 IN_REVIEW, 1 blocked.**

What it cost: canceling discards Apple's rejection thread, so the review
starts over. Acceptable only because the metadata gaps behind the original
rejections are closed first (`asc_readiness.rb` reports 43/43). If Apple
rejects these again, reading the reason still needs a session — the local
cookie expired on 2026-09-30 and `spaceauth` now prompts for a 2FA code.

**Still blocked: PlantPulse**, on `app-privacy-answers-not-published`. The
App Privacy answers have no API for an API key (MA-022), so this one needs a
person in App Store Connect.

## MA-035 · P1 · Play Console account access, and why it cannot be fixed by API

Read on 2026-10-02 from `developers/5590631437738173959/users`, which works
once you have the numeric developer id from the Console URL.

| Account | Permissions |
| --- | --- |
| `nehuwakhare04@gmail.com` | **all 17** — full admin |
| `mouni123.nekkalapudi@gmail.com` | `manage_track_apks_global` |
| `rainbow472.sri@gmail.com` | `manage_permissions_global` **only** |
| `american-group-publisher@…` (service account) | all 17 |
| `firebase-adminsdk-fbsvc@…` (service account) | all 17 |

Two things are wrong with this. The standing instruction is that only
`rainbow472.sri@gmail.com` holds Play access and everyone else is an external
tester, yet two other people have accounts — one of them full admin. And the
designated admin cannot actually administer: with only
`manage_permissions_global` they cannot edit app content, which is exactly
what clearing the Draft-app blockers requires.

**This cannot be done from here.** The publisher service account can *read*
the user list but not change it:

```
PATCH developers/5590631437738173959/users/rainbow472.sri%40gmail.com
403  You do not have permission to access this object
```

So, in Play Console → Users and permissions:

1. Give `rainbow472.sri@gmail.com` admin (all account permissions).
2. Remove `nehuwakhare04@gmail.com` and `mouni123.nekkalapudi@gmail.com`,
   then add them as testers per MA-033.

Do step 1 first. Removing the only full-permission human before promoting the
replacement would leave no person able to edit app content.

## MA-036 · P0 · No working test account exists, and it blocks review and screenshots

One root cause, three visible symptoms. Found 2026-10-03.

### The root cause

`AmericanGroupLLC — Complete Developer Integration Guide.md` states that three
persistent test accounts are provisioned in the production database. They are
not. Tested against the only Supabase project any app uses
(`smvvjivvlprjhzhoizym`, shared by 16 apps):

```
POST /auth/v1/token?grant_type=password   qa@safecodeg.com   400 Invalid login credentials
POST /auth/v1/token?grant_type=password   dev@safecodeg.com  400 Invalid login credentials
```

`AmericanGroupLLC-Backend/TODO.md` already carries the open item
"Demo/test account credentials for any app behind a login."

I created `qa@safecodeg.com` (`2e0f9e4d-5c96-4630-9288-1104f1496193`) with the
documented password. The project requires email confirmation, so it still
cannot sign in, and confirming it needs the **service-role key**, which is not
on this machine. That is the single action that unblocks everything below:

```
PUT /auth/v1/admin/users/2e0f9e4d-5c96-4630-9288-1104f1496193
    {"email_confirm": true}            # needs SUPABASE_SERVICE_ROLE_KEY
```

Then re-test the sign-in above and confirm it returns a token.

### Symptom 1 — App Review cannot get into 5 apps

`DriftDate`, `iMeasure`, `Kinnav`, `radiotune`, `yourtube` have a Supabase
sign-in and **no guest path**. All 43 apps declare `demoAccountRequired:
false` and supply no credentials, so a reviewer meets a login wall with
nothing to type. That is a Guideline 2.1 rejection waiting to happen.

The in-app bypasses do not ship. `testAccountEnabled` is
`!kReleaseMode && …` and `showDevShortcuts` is `kDebugMode && !screenshotMode`,
so in the build Apple reviews both are false.

### Symptom 2 — the store screenshots are login screens

Verified by eye on Kinnav and yourtube: the first App Store screenshot is the
sign-in form, and it shows debug-only affordances — "Demo mode (dev) — skip to
app", and a "Use test account" button that is inert in release. Kinnav's own
`app_config.dart` says a screenshot containing UI the shipped app lacks is
grounds for rejection. This predates the 2026-10-02 capture; the previous
screenshot was the same screen.

### Symptom 3 — the capture cannot do better

`screenshots.py` can only photograph what it can reach, and it cannot sign in.
Two script bugs found alongside and fixed:

* builds now pass `--dart-define=SCREENSHOT=true`, so dev shortcuts never
  appear in a capture again;
* `same_image` compared whole files, so the same screen captured at 11:55 and
  12:10 counted as two screenshots — which is how Kinnav shipped two copies of
  its login screen to Play as "two screenshots".

### Order of work

1. Confirm the QA user with the service-role key, and verify sign-in.
2. Add `QA_EMAIL`/`QA_PASSWORD` to the screenshot build so captures can get in.
3. Re-run `python3 scripts/screenshots.py` for the five apps.
4. Set `demoAccountRequired: true` with the credentials on those five apps'
   `appStoreReviewDetail`.

## MA-037 · CLOSED 2026-10-04 — Transporter works; it needed the proxy as -D flags

**This entry previously said Transporter was an incomplete install that could
not be fixed here. That was wrong.** It works, and all 43 apps have now been
delivered through it.

The symptom was real:

```
iTMSTransporter -version
ERROR: Could not download Defaults.properties (launcher)
```

The diagnosis was not. The file is perfectly reachable from this machine:

```
curl https://contentdelivery.itunes.apple.com/transporter/Defaults.properties  -> 200
```

It is the same JVM-proxy problem CLAUDE.md already documents for Gradle:
direct egress is blocked, everything goes through 127.0.0.1:10054, and a JVM
reads only the `http.proxyHost` / `https.proxyHost` system properties. Setting
`HTTP_PROXY`, `HTTPS_PROXY`, `TRANSPORTER_JAVA_OPTS` and `JVM_OPTIONS` all
changed nothing, because the launcher forwards **-D arguments** and nothing
else. Passed that way it bootstraps and reports `iTMSTransporter, version
4.1.0`.

Two more things it needed:

* **`-numStreams 1`.** On the default four parallel streams, 16 of 43 uploads
  died with `java.net.SocketException: Connection reset` / `Broken pipe` /
  `SSLException` after exhausting Transporter's own retries. (`-t DAV`, the
  other obvious lever, is refused: "The DAV transport is obsolete".)
* **Up to three attempts.** Even single-stream it is flaky through the proxy;
  EventSpark succeeded on attempt 3 with no change at all.

Use `scripts/testflight/transporter_upload.py`. **Run only one at a time** —
two concurrent runs overwrite each other's results file, which looked like
"0 apps processed" twice before it was spotted.

### Outcome

43/43 uploads returned "uploaded successfully", and App Store Connect holds a
VALID build for all 43. 32 now carry a build delivered today. The other 11 do
not, and that is not a failure: their IPA in `.dist` is **older** than what CI
already uploaded — CalcMaster's local IPA is version 4.0.2 build `5`, while
App Store Connect holds build `202609250224`. Apple kept the newer one.

If a Transporter-delivered build is wanted for those 11, rebuild their IPAs
first; the ones on disk are stale.


## MA-038 · Firebase App Distribution — working, with two things to know

Set up 2026-10-04. **All 43 apps have a release and 11 testers** (the 9
external plus both owners), verified by reading `releases` back for every app.

Use `scripts/firebase_distribute.py`. It calls the REST API rather than the
Firebase CLI, because the CLI (15.32.1) answers

```
Authentication Error: Your credentials are no longer valid.
Please run firebase login --reauth
```

and `--reauth` opens a browser. The gcloud token this machine already holds
works instead, given two things neither error message hints at:

* **`x-goog-user-project`**, or every call is refused with "the
  firebaseappdistribution.googleapis.com API requires a quota project";
* **the project number, not the id**. `projects/americangroupllc-5bdfc` is a
  400; `projects/9057515422` is correct.

A 404 from `/testers` or `/releases` means the collection is empty, not that
the path is wrong.

### Two real problems this surfaced

**Eight APKs in `.dist` were corrupt** — right size, zero zip entries.
CalcMaster's was 43 MB and `unzip -l` listed nothing. Firebase rejects them
with the unhelpful "Ensure you are uploading a valid IPA or APK". All eight
were rebuilt. The script now checks that an artifact is a readable zip with
entries before uploading.

**`.aab` uploads need Firebase linked to Play**: "Your Firebase project needs
to be connected to your Google Play developer account." APKs do not. If you
want bundle uploads to work, link the projects in the Firebase console —
otherwise keep building APKs for this channel.

### iOS is not wired, deliberately

App Distribution installs an iOS build only on devices listed in an **ad-hoc**
provisioning profile. Every IPA in `.dist` is an App Store distribution
build: it uploads cleanly and still will not install for a tester. The
`--ios` flag exists for when ad-hoc IPAs are built. Until then TestFlight is
the iOS channel, and all 43 are already there.

## MA-039 · P0 · Nine apps are serving Google's sample ads, four of them live

Measured 2026-10-06 from the shipped manifests and plists, not from a record.

`ca-app-pub-3940256099942544` is the AdMob id Google publishes in its own
documentation so a developer can test without an account. Nine of the eleven
ad-serving apps ship it:

| Where | Sample id | Apps |
| --- | --- | --- |
| iOS `Info.plist` | `~1458002511` | BodyQuest, iMeasure, PilotEnRoute, radiotune, TripNest, Uscis-Case, Verba, VirtuBand, yourtube |
| Android manifest | `~3347511713` | BodyQuest, Verba, yourtube |

Two consequences. The apps earn nothing — Google's test inventory does not
pay. And serving it from a production listing is against the AdMob policy.
**TripNest, Uscis-Case, VirtuBand and iMeasure are already live on Google
Play**, so this is happening now.

### Why it is not already fixed

`scripts/fix_admob_ids.py` will swap every sample id for the real one and
reports exactly which it cannot. Today it replaces none, because the real
ids do not exist:

```
docs/admob-ids.json — 43 entries
  35  no ids at all
   6  android_app_id + banner + interstitial
   1  android_app_id + ios_app_id
   1  all four
```

Only two apps have an iOS AdMob app id on record. The rest have to be
created, and MA-027 records that both routes were tried: the v1 API is
read-only, v1beta's `accounts.apps.create` is refused for this account, and
the console has no bulk import.

### What to do

1. In the AdMob console, create an app entry per platform for the nine
   above, and a banner and interstitial unit for each.
2. Put the ids into `docs/admob-ids.json`.
3. `python3 scripts/fix_admob_ids.py` — it rewrites the manifests and plists
   and lists anything still missing.
4. Rebuild and re-upload the four that are live first.

Until then, **do not promote any more ad-serving apps to production**: it
adds listings that serve Google's sample inventory.

## MA-040 · P0 · One Supabase toggle unblocks guest access, screenshots and review

`yourtube` now offers "Continue as guest" on its login screen, calling
`AuthService.signInAnonymously` — a method that had existed since the service
was written and was never reachable. The button is correct and tested, and
it is **inert until a toggle is flipped**:

```
POST https://smvvjivvlprjhzhoizym.supabase.co/auth/v1/signup   {}
-> "Anonymous sign-ins are disabled"
```

**Supabase dashboard → Authentication → Providers → Anonymous sign-ins →
enable**, on project `smvvjivvlprjhzhoizym` (shared by all 16 auth apps).

Three things follow from that one switch:

1. App Review can get into the app. Guideline 2.1 "we were unable to review
   the app" is what the sign-in wall produced.
2. `screenshots.py` can walk past the login screen, so the store screenshots
   stop being pictures of a login form — the 2.3.3 rejection.
3. `DriftDate` and `Kinnav` both have the same unused `signInAnonymously`
   and could be wired the same way. They are not, deliberately: guest
   browsing in a dating app and in a women's safety app changes who can see
   whom, and that is the owner's decision rather than a mechanical one.

Until it is enabled, the button fails with "Sign-in unavailable right now",
which is honest but useless — so enabling it or reverting the button are the
only two sensible states.
