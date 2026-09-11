# Pending — what has to be created before anything ships

Measured, not asserted. Regenerate with `python3 scripts/status.py`.

Everything here needs an account this repository does not have. The code side
is done and waiting: each item says exactly what unblocks when it lands.

## 1. Credentials and API keys

| # | What | Where to create it | Unblocks | Status |
| --- | --- | --- | --- | --- |
| 1 | **`AGL_PACKAGES_TOKEN`** — a fine-grained PAT or GitHub App token | GitHub → Settings → Developer settings. Read on every app repo **and** on `AmericanGroupLLC-Backend`; add **write** to publish release binaries. Store it as an **organization** secret so it exists once. | **Everything.** Without it every job dies at `flutter pub get` with `could not read Username for 'https://github.com'` | missing (0/43 repos) |
| 2 | **App Store Connect API key** (`.p8`), key id, issuer id | App Store Connect → Users and Access → Keys. The `.p8` downloads once. | Every iOS lane: TestFlight and App Store upload | `ASC_KEY_ID` and `ASC_ISSUER_ID` are missing everywhere; `ASC_KEY_CONTENT` exists in 1 repo |
| 3 | **Play service-account JSON** | Play Console → Setup → API access → link `americangroupllc-5bdfc` → create a service account → grant *Release manager* → download | `android beta` / `release` upload to Play | present in 1 of 37 repos |
| 4 | **Firebase config files** — `google-services.json` and `GoogleService-Info.plist`, per app | Firebase console → project `americangroupllc-5bdfc` → Project settings → Your apps. The exact package name, bundle id and destination path for all 43 apps is in `AmericanGroupLLC-Backend/docs/FIREBASE_REGISTRATION.md` | Crash reporting. `AglCrash.isActive` is false in every build until these exist; the Gradle plugins apply themselves the moment the JSON appears | missing in 43 of 43 |
| 5 | **match password**, or Apple distribution certificate + profiles | A Mac signed into the Apple account: `bundle exec fastlane match appstore`. The `match-certificates` branch already exists in the backend repo. | iOS signing on CI. Without it the lanes fall back to Xcode automatic signing, which a runner cannot do | missing |
| 6 | **An AdMob app + unit ids** for the 4 apps that have neither: BodyQuest, PilotEnRoute, Verba, yourtube | AdMob console → Apps → Add app, then Ad units | They serve ads today against Google's **test** application id, so they earn nothing. Everything else has an Android app id; see [MATRIX.md](MATRIX.md) | 4 of 11 ad apps have no console record |
| 6b | **iOS AdMob apps and unit ids** | AdMob console → Apps → Add app (iOS) | iOS ads. No app has iOS unit ids, so an iOS release build serves test ads by design | 9 of 11 ad apps carry Google's test iOS app id |
| 7 | **A GDPR message published** in AdMob | AdMob console → Privacy & messaging | The UMP consent form. The code is in every ad app and gated; until a message is published UMP reports “not required” everywhere and no form appears | not published |
| 8 | **Privacy policy URL** that resolves, plus a support URL and contact | Your hosting | Both store listings, and the in-app link | templated per app; the pages must exist |

> **Put them on the organization, not on 37 repositories.** Delivery runs from
> here now, so each secret is needed in one place. The Android keystore secrets
> were set per repo before that was true — see §3.

## 2. Store listing copy

18 of 37 Flutter apps have no description, which both stores
require. A description makes claims about what an app does, so it is written by
someone who knows the product, not generated.

Edit `AmericanGroupLLC-Backend/store/apps/<repo>.json`, then run
`python3 scripts/store_metadata.py generate` there.

| Needs a description |
| --- |
| AGCleaner |
| AGRecorder |
| CarDeal |
| ChefCount |
| CodeDeal |
| EventSpark |
| GadgetNest |
| HomeWise |
| MileMaster |
| MyFinance |
| NearServe |
| NewsBoard |
| NexusTransferPay |
| portfolio-board |
| RideZap |
| RoomCraft |
| WiFiTrail |
| yourtube |

## 3. Secrets that exist but under the wrong name

The workflows read the four names below. A secret spelled differently is the
same as one that is missing.

| Repo | Has | Missing |
| --- | --- | --- |
| CalcMaster | `ANDROID_STORE_PASSWORD` | `ANDROID_KEYSTORE_PASSWORD` |
| CodeDeal | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| Kinnav | `ANDROID_KEY_PROPERTIES` | `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| NexusTransferPay | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| portfolio-board | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| AeroSwift | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| AGStudio | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| ApexMarketWatch | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| BuddyPlay | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| MyCard | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |
| PlantPulse | — | `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` |

## 4. Apps that cannot be delivered at all yet

| App | Why |
| --- | --- |
| CodeDeal | A partial Flutter port that does not compile — 5 analyzer errors |
| AGStudio, ApexMarketWatch, BuddyPlay, MyCard, PlantPulse | Not Flutter yet; outside this manifest until ported |

## 5. What is now credentialed, and what one thing is not

Loaded into this repository's secrets on 2026-09-10, read from the material
already on the build machine:

| Credential | Source | Status |
| --- | --- | --- |
| `ASC_KEY_ID` `UV8NYF9767` | `AuthKey_UV8NYF9767.p8` in the backend repo root, untracked | **set** |
| `ASC_ISSUER_ID` | the planning workbook, sheet 8 | **set** |
| `ASC_KEY_CONTENT` | the same `.p8`, base64 | **set**, verified a 256-bit EC key |
| 30 × `KEYSTORE_<APP>_BASE64` | `~/agl/.secrets/keystores/` | **set** — all 30 verified to open with their recorded password |
| `ANDROID_KEYSTORE_CONFIG` | `~/agl/.secrets/keystores.json` | **set** — alias and passwords for all 30 |

So App Store Connect authentication and Android signing are both credentialed
here now. **`AGL_PACKAGES_TOKEN` is the one thing still missing**, and nothing
can build without it — not because of signing, but because `flutter pub get`
cannot reach the shared packages. It is the single blocker between this
repository and a set of signed binaries.

Two credentials remain beyond it: the Play service-account JSON (upload), and a
distribution certificate via `match` (iOS signing).

## 6. What a full sweep of the backend actually turned up

`/Users/spatchava/agl/AmericanGroupLLC-Backend` was searched for every
credential-shaped file — `.p8`, `.p12`, `.cer`, `.pem`, `.mobileprovision`,
`.jks`, service-account JSON, `.env`, and both Firebase config filenames.

| Looking for | Found |
| --- | --- |
| App Store Connect API key | **yes** — `AuthKey_UV8NYF9767.p8`, now in secrets |
| In-app-purchase key | `SubscriptionKey_PX7TXTDSHP.p8` — for the App Store Server API, not delivery |
| ASC issuer id | **yes** — sheet 8 of the planning workbook, now in secrets |
| Apple Team ID `TLH7Z3G27A` | in `RELEASE_PIPELINE.md` |
| Android upload keystores | **yes** — 30, in `~/agl/.secrets/`, all verified and now in secrets |
| Play service-account JSON | **no** — nothing anywhere in the mirror |
| Distribution certificate / provisioning profiles | **no** — `certs/` holds only a Supabase CA |
| Real Firebase configs | **no** |

The last row needs care. Two `google-services.json` files exist under MyHealth,
and both are placeholders: project `myhealth-local-dev`, project_number
`000000000000`. A placeholder is worse than nothing — it makes Crashlytics
initialise against a project that does not exist, so `AglCrash.isActive` turns
true and every report vanishes, which reads as an app that never crashes. The
sanity suite now rejects any config that is not `americangroupllc-5bdfc`.
