# Credentials — what exists, what you must create

Status as of 2026-09-09. Split by whether it could be created from the
development machine or needs a human signed into a vendor console.

---

## Done — created and verified

| Item | Count | Where it lives | Verified by |
| --- | --- | --- | --- |
| Android upload keystores | 30 new (+3 already existed = 33) | `~/agl/.secrets/keystores/<App>-upload.jks` | `keytool -list` opens all 30 with their recorded password; 2048-bit RSA, SHA256withRSA, valid to 2054 |
| Keystore passwords | 30 | `~/agl/.secrets/keystores.json` (mode 600) | generated with `secrets.choice`, 28 chars |
| `ANDROID_KEYSTORE_BASE64` / `_PASSWORD` / `KEY_ALIAS` / `KEY_PASSWORD` | 33 repos | GitHub repo secrets | `gh secret list` shows 4 per repo, 33/33 |
| Local `android/key.properties` | 30 | each app, pointing at `~/agl/.secrets` | written only where `git check-ignore` already covered the path |
| match signing storage | 1 branch | `match-certificates` orphan branch of this repo | `git ls-remote` shows the branch; separate certificates repo removed |
| Fastlane lanes | 37 repos | `fastlane/Fastfile` | `fastlane lanes` executes in all 37 |

**The Android half of delivery is now credentialed.** `fastlane android beta`
will build and sign; it will stop only at the Play upload, which needs the
service-account JSON below.

> ⚠️ **Back up `~/agl/.secrets/` somewhere durable today.** Lose an upload
> keystore and that app can never be updated on Play again. It is outside every
> git repo on purpose, which also means nothing is backing it up.

---

## Cannot be created here — you must create these

Each needs an authenticated session with a vendor console that this machine does
not have. `firebase` and `gcloud` are installed but not logged in; there is no
Apple CLI session.

| # | Item | Where to create it | Blocks | Then do |
| --- | --- | --- | --- | --- |
| 1 | **App Store Connect API key** `AuthKey_UV8NYF9767.p8` | App Store Connect → Users and Access → **Keys** → download (one chance only) | Every iOS lane | Put in `~/agl-secrets/`, run `scripts/set-store-secrets.sh --all` |
| 2 | **ASC Issuer ID** | Same page, shown above the key list | Every iOS lane | Export as `ASC_ISSUER_ID` |
| 3 | **Play service-account JSON** | Play Console → Setup → **API access** → link project `americangroupllc-5bdfc` → create service account → grant *Release manager* → download JSON | `android beta` / `release` upload | Set as `PLAY_SERVICE_ACCOUNT_JSON` secret |
| 4 | **match certificates** | A Mac signed into the Apple account: `bundle exec fastlane match appstore` | iOS signing on CI | Branch already created; pick a `MATCH_PASSWORD` |
| 5 | **AdMob app IDs** — iOS for 6 apps, both platforms for 26 | AdMob → Apps → Add app → App settings | Ads; a wrong id crashes on launch | Send them over; I will write the plist/manifest entries |
| 6 | **`google-services.json` / `GoogleService-Info.plist`** per app | Firebase console → Project settings → Your apps | Firebase Auth, FCM, Crashlytics | Drop into `android/app/` and `ios/Runner/` |
| 7 | **App Store Connect app records** | App Store Connect → My Apps → **+** | `deliver` has nothing to upload to | Or `fastlane produce` once item 1 exists |
| 8 | **Play Console app entries** | Play Console → Create app | `supply` has nothing to upload to | — |
| 9 | **MyHealth bundle id** | Its identifier is reported unavailable | MyHealth entirely | Recover it, or choose a new id before first publish |
| 10 | **yourtube rejection reason** | Play Console → the rejected release | yourtube | — |
| 11 | **Privacy-policy / account-deletion URLs that resolve** | Your hosting | Both stores reject a 404 | — |
| 12 | **Store artwork** — 1024×1024 icon, screenshots, 1024×500 feature graphic | Design | Both store listings | I can capture simulator screenshots once you confirm sizes |

---

## Deliberately not done

| Item | Why |
| --- | --- |
| Rotating the exposed credentials | Only you can rotate them; see `TODO.md` §2 |
| Writing real `GADApplicationIdentifier` values | The suffix cannot be derived from the publisher id, and a wrong one fails at launch rather than at build. Google's test id stays until real ids arrive. |
| Purging the leaked blobs from git history | Rewrites every commit SHA and breaks existing clones — your call |
| Creating App Store / Play app records with `produce` | Needs item 1 first |

---

## The one command that finishes the setup

Once items 1–3 are in `~/agl-secrets/`:

```sh
export AGL_SECRETS_DIR=~/agl-secrets
export ASC_ISSUER_ID='<uuid from App Store Connect>'
export ANDROID_KEYSTORE_PASSWORD=… ANDROID_KEY_ALIAS=upload ANDROID_KEY_PASSWORD=…
export MATCH_GIT_URL=https://github.com/AmericanGroupLLC/AmericanGroupLLC-Backend.git
export MATCH_GIT_BRANCH=match-certificates
export MATCH_PASSWORD='<passphrase>'

scripts/set-store-secrets.sh --all
gh workflow run release.yml --repo AmericanGroupLLC/CalcMaster -f platform=android -f lane=beta
```

Android already works without any of that, because its secrets are set —
only the Play upload step needs item 3.
