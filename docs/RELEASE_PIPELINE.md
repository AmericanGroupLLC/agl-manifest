# AGL Mobile Release Pipeline

How every AmericanGroupLLC app gets from a git push to the App Store and Google
Play. This is the single source of truth for the delivery path; per-app detail
lives in [`app-inventory.json`](app-inventory.json) and
[`admob-ids.json`](admob-ids.json).

> **No credentials in this repository.** Everything secret is referenced by the
> name of the environment variable or GitHub secret that carries it. The
> planning workbook `SFG-AGL-MobileApp_Devlopment-Tools.xlsx` does contain live
> credentials and is deliberately gitignored — keep it local.

---

## 1. The pipeline

```
git push
   │
   ├─► CI (.github/workflows/ci.yml)            every push / PR
   │      flutter pub get → flutter analyze → flutter test
   │      android: build AAB (signed if secrets present, else compile-check)
   │      ios:     flutter build ios --release --no-codesign
   │
   └─► Release (.github/workflows/release.yml)  manual dispatch
          bundle install
             │
             ├── ios    → fastlane ios beta | release | metadata
             │             match (certs + profiles)
             │             flutter build ipa --release
             │             upload_to_testflight / deliver
             │
             └── android → fastlane android beta | release | metadata
                           flutter build appbundle --release
                           upload_to_play_store (supply)
```

Every app exposes the same lanes, so one runbook covers the portfolio:

| Lane | iOS | Android |
| --- | --- | --- |
| `test` | `flutter test` | `flutter test` |
| `signing` | `match` (skipped when `MATCH_GIT_URL` is unset) | n/a |
| `build` | signed IPA | signed AAB |
| `metadata` | `deliver`, listing only | `supply`, listing only |
| `beta` | TestFlight | Play **internal** track |
| `release` | App Store Connect | Play **production**, as a draft |

```sh
bundle exec fastlane ios beta
bundle exec fastlane android release
```

Always `bundle exec` — the Gemfile pins the fastlane version for local and CI
alike.

---

## 2. Store accounts

| | Value |
| --- | --- |
| Apple Developer Program | American Group LLC, **Organization** |
| Apple Team ID | `TLH7Z3G27A` |
| Apple renewal | 2027-06-08 |
| App Store Connect API Key ID | `UV8NYF9767` (key file `AuthKey_UV8NYF9767.p8`) |
| In-App Purchase Key ID | `PX7TXTDSHP` (key file `SubscriptionKey_PX7TXTDSHP.p8`) |
| Google Play Console | AMERICAN GROUP LLC, developer `5590631437738173959` |
| Firebase / GCP projects | `americangroupllc-5bdfc` (9057515422), `americangroupllc-agl2` (170143925591), `americangroupllc-agl3` (209455037382) |
| Why three | A Firebase project holds **30 apps**, and one of our apps needs two slots (android + ios), so a project fits 15 apps. 43 apps need three projects. Crash reports therefore land in three consoles; `scripts/firebase_register.py` records which project each app belongs to. |
| FCM Sender ID | `9057515422` |
| AdMob publisher | `pub-8528784688453695` |
| Account owner | rainbow472.sri@gmail.com |
| Support email | americangroupllc@googlegroups.com |

The App Store Connect **Issuer ID** and the IAP **shared secret** are
credentials — they live in the workbook and in GitHub secrets, not here.

> `UV8NYF9767` is the **API key id**, not the team id. The workbook originally
> labelled it "American Group LLC", which reads as a team id; that has been
> corrected. `AuthKey_<KeyID>.p8` is how Apple names the file, which is what
> gives it away.

---

## 3. Secrets each repo needs

Set these once per app repository (or once at org level and inherit).

### iOS

| Secret | What it is |
| --- | --- |
| `ASC_KEY_ID` | `UV8NYF9767` |
| `ASC_ISSUER_ID` | Issuer UUID from App Store Connect → Users and Access → Keys |
| `ASC_KEY_CONTENT` | `base64 -i AuthKey_UV8NYF9767.p8` — the whole file, base64 |
| `MATCH_GIT_URL` | Defaults to this repo; override only to relocate storage |
| `MATCH_GIT_BRANCH` | Defaults to `match-certificates`, an orphan branch of this repo |
| `MATCH_PASSWORD` | Passphrase that encrypts the match repo |
| `MATCH_GIT_BASIC_AUTHORIZATION` | `base64` of `user:token`, for CI to read that repo |

Without `MATCH_GIT_URL` the `signing` lane is skipped and Xcode automatic
signing is used — fine locally, not viable on a clean CI runner.

### Android

| Secret | What it is |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | `base64 -i upload.jks` |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Usually `upload` |
| `ANDROID_KEY_PASSWORD` | Key password |
| `PLAY_SERVICE_ACCOUNT_JSON` | Play Console service-account JSON, whole file |

`scripts/set-store-secrets.sh` pushes all of these to a repo with `gh`.

---

## 4. First-time match setup

`match` keeps one signing identity shared by every machine and CI runner.

Signing storage is the **`match-certificates` orphan branch of this
repository** — certificates, files and signing all live in one project. The
branch already exists; its contents are encrypted with `MATCH_PASSWORD`.

```sh
# once, from a developer Mac with the Apple account
export MATCH_GIT_URL=https://github.com/AmericanGroupLLC/AmericanGroupLLC-Backend.git
export MATCH_GIT_BRANCH=match-certificates
export MATCH_PASSWORD='<choose a strong passphrase>'
export ASC_KEY_ID=UV8NYF9767 ASC_ISSUER_ID=<uuid> ASC_KEY_CONTENT=$(base64 -i AuthKey_UV8NYF9767.p8)

cd <app-repo>
bundle exec fastlane match appstore
```

CI then runs match `readonly`, so profiles must be created from a developer
machine first. Never let CI mint certificates — Apple caps how many you can have.

---

## 5. AdMob

Ad ids ship inside the binary, so they are not secrets and are tracked in
[`admob-ids.json`](admob-ids.json).

Two things routinely go wrong:

1. **A publisher id is not an app id.** `pub-8528784688453695` identifies the
   account. `GADApplicationIdentifier` needs a per-app value shaped
   `ca-app-pub-8528784688453695~XXXXXXXXXX`, and iOS and Android are
   *different* ids for the same app.
2. **A missing or wrong id is a launch-time crash, not a build error.**
   google_mobile_ads raises `GADInvalidInitializationException` and iOS
   terminates the app. A wrong id therefore passes CI and fails in review.

Until an app has real ids, keep Google's public test id
`ca-app-pub-3940256099942544~1458002511` rather than guessing a suffix.

---

## 6. Per-app store requirements

Both stores reject a submission that is missing any of these.

| Requirement | Apple | Google |
| --- | --- | --- |
| Signed binary | `.ipa`, distribution cert + profile | `.aab`, upload keystore |
| Icon | 1024×1024, no transparency | 512×512 |
| Screenshots | per supported iPhone size (+ iPad if supported) | phone, plus feature graphic 1024×500 |
| Description | subtitle ≤30 chars, description ≤4000 | short + full description |
| Privacy policy | HTTPS URL that resolves | HTTPS URL that resolves |
| Data disclosure | App Privacy nutrition labels | Data Safety form |
| Age rating | questionnaire | content rating questionnaire |
| Account deletion | required if the app has accounts | required if the app has accounts |
| Demo account | required if login exists | required if login exists |

A privacy-policy URL that 404s is the most common avoidable rejection — check
it resolves before submitting.
