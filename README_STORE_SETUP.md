# Store setup — the console work

Everything here needs a Play Console or App Store Connect login, so it cannot
be scripted. Everything that *can* be scripted already is; see
[`docs/API_ACTIONS.md`](docs/API_ACTIONS.md).

Current state is measured, not asserted — regenerate with
`python3 scripts/status.py` and read `status.csv`, or
`python3 scripts/store_master_csv.py --gaps` for just the open fields.

**43 apps. 4 have no blocker. The rest are waiting on the steps below.**

What each step is worth, measured:

| zero-blocker apps | after |
| ---: | --- |
| 4 / 43 | today |
| 5 / 43 | the six paywalls get real in-app purchase |
| 6 / 43 | § 1 — an Apple ID session |
| 17 / 43 | § 2 — 11 Play apps created |
| **43 / 43** | § 3 — 26 Play drafts published |

Section 3 is the one that matters. Do it first if you only do one thing.

---

## 1. Apple — one session unlocks two blockers

The App Store Connect **API key cannot create an app record** (`apps` does not
allow `CREATE`, re-confirmed 2026-09-22) and **cannot publish App Privacy
answers** (`appDataUsages` is served by a cookie-authenticated host). Both take
an Apple ID web session, and fastlane mints one from a single 2FA code:

```bash
cd ~/agl/agl-manifest
unset FASTLANE_SESSION
bundle exec fastlane spaceship spaceauth -u rainbow472.sri@gmail.com
```

Paste the printed value into `~/agl/.secrets/fastlane-session` — `env.sh`
already picks it up from there. It lasts about a month.

> Requires fastlane ≥ 2.240.0. On 2.239.0 this fails with
> `Service key is empty` (upstream issue #30199 — Apple moved the Olympus
> config). Already updated in `Gemfile.lock`.

With that in place, these become scriptable:

**13 apps need an App Store Connect record** — AeroSwift, BodyQuest,
FashionFactory, GadgetNest, GroceryMatch, HerJourney, MyHealth, PlantPulse,
Verba, iMeasure, portfolio-board, radiotune, yourtube.

**27 apps need App Privacy published.** The answers are already written, per
app, in `store/privacy/<repo>.json` — nothing to compose, only to publish.

---

## 2. Play — create the 11 missing apps

`androidpublisher`'s `applications` resource exposes exactly one method,
`dataSafety`. There is no create. Each of these needs **Create app** in Play
Console under the package name below, which is permanent once set:

| app | package name |
| --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` |
| BodyQuest | `com.americangroupllc.bodyquest` |
| DriftDate | `com.americangroupllc.driftdate` |
| FashionFactory | `com.americangroupllc.fashionfactory` |
| GadgetNest | `com.americangroupllc.gadgetnest` |
| GroceryMatch | `com.americangroupllc.grocerymatch` |
| HerJourney | `com.americangroupllc.herjourney` |
| Photriya | `com.americangroupllc.photriya` |
| PlantPulse | `com.americangroupllc.plantpulse` |
| Verba | `com.americangroupllc.verba` |
| portfolio-board | `com.americangroupllc.portfolioboard` |

---

## 3. Play — publish the 26 draft apps

This is the big one: it takes the portfolio from 17 to 43.

Play refuses every release on a draft app with *"Only releases with status draft
may be created on draft app."* An app leaves draft only after **App content** is
complete and a first release is rolled out and reviewed.

Of the App content items, **only Data safety has an API**. Content rating,
target audience, ads and app access are console-only. So per app:

1. **App content → Data safety** — answers derived in `store/privacy/<repo>.json`.
   Export the CSV template from any app here and hand it over; the rest can then
   be generated for all 43 and uploaded through `applications.dataSafety`.
2. **App content → Content rating** — the IARC questionnaire. No API exists.
   Contact email: `contact@safecodeg.com`.
3. **App content → Target audience and content**
4. **App content → Ads** — 11 apps serve ads. `status.csv` column *Contains Ads*
   is measured from whether the binary actually links google_mobile_ads, so trust
   it over memory.
5. **App content → App access** — 18 apps require a login. See § 6.
6. **Store listing** — title, short and full description are already written in
   `store/apps/<repo>.json`; screenshots and the feature graphic are in
   `store/graphics/<repo>/`.
7. Roll out to a track and let it review.

Apps still in draft: AGCleaner, AGRecorder, AGStudio, AGrammarly,
ApexMarketWatch, BuddyPlay, CarDeal, ChefCount, CodeDeal, EventSpark, HomeWise,
Kinnav, MileMaster, MyCard, MyFinance, MyHealth, NearServe, NewsBoard,
NexusTransferPay, PilotEnRoute, RideZap, RoomCraft, WiFiTrail, daily-pulse,
radiotune, yourtube.

> **Uploading another bundle does not clear this.** AGCleaner's internal track
> already holds a `completed` release at version code 2 and internal app sharing
> still refuses it. The gate is the app's draft state, not the track's.

---

## 4. In-app purchase products

Six apps sold a subscription with no purchase SDK behind it — App Review
guideline 3.1.1, a rejection. Real `in_app_purchase` billing is now wired in
each. The **products themselves must be created in both consoles**, and the ids
must match exactly or the paywall shows no price and no purchase can start.

| app | product ids |
| --- | --- |
| Kinnav | `kinnav_premium_monthly`, `kinnav_premium_annual` |
| CodeDeal | `codedeal_pro_monthly`, `codedeal_pro_yearly` |
| NexusTransferPay | `nexustransferpay_plus_monthly`, `nexustransferpay_plus_yearly` |
| VirtuBand | `virtuband_pro_monthly`, `virtuband_pro_yearly` |
| NewsBoard | `newsboard_premium_monthly`, `newsboard_premium_yearly` |
| daily-pulse | `dailypulse_premium_monthly`, `dailypulse_premium_yearly` |

Each id is overridable at build time (`--dart-define=IAP_MONTHLY_ID=...`) so a
staging SKU needs no code change.

Prices are **not** hardcoded any more — the screens render the store's own
localised price. Whatever you set in the console is what the user sees, so the
two can no longer drift apart.

Apple also requires a visible **Restore Purchases** control wherever a
non-consumable is sold; every one of these screens has one.

After creating the products, test a sandbox purchase per app before submitting.

---

## 5. Eight apps need an upload-key reset

`CalcMaster, CarDeal, iMaps, iMeasure, Kinnav, TripNest, Uscis-Case, VirtuBand`
are rejected at upload with *"signed with the wrong key"*. The keystores on the
build machine were generated 2026-09-11, after Play had registered different
upload keys, and the originals are not recoverable here.

Play Console → the app → **Setup → App integrity → App signing → Request upload
key reset**, attaching the certificate of the keystore in
`~/agl/.secrets/keystores/<App>-upload.jks`. Google turns these round in about
48 hours. CarDeal and VirtuBand expect the *same* key, so one original covers
both.

This does **not** block getting a build to a tester — internal app sharing does
not check the upload key, and all six apps it delivered were on this list. It
blocks the store release and the internal track.

---

## 6. Demo accounts for review

18 apps require a login, and App Review rejects a login-gated app without
working credentials.

Several apps' review notes already tell Apple the credentials come from
`demo_user.txt` / `demo_password.txt` beside the fastlane metadata — **those
files do not exist anywhere on the build machine.** Create them, or supply the
credentials directly in the submission's *Sign-in required* fields.

They are deliberately untracked, so they must not be committed.

---

## 7. Decisions nobody has made yet

`python3 scripts/store_master_csv.py --gaps` lists these as `NEEDS-INPUT`
across all 43:

- **Countries / territories** — where each app is sold.
- **IARC content rating and app category** — § 3, no API.
- **Target age groups**.
- **Developer Program Policies** — the console acceptance checkbox.
- **App preview / promo video** — none exist; optional on both stores.
- **Release notes** — 24 apps have no `release_notes.txt`.
- **Subscriptions** — for the 7 apps with in-app purchase, whether each product
  is auto-renewing or one-off. This changes how it is created in the console.

---

## Already done, so don't redo it

- Every app is Flutter/Dart, builds a signed `.aab` and a signed `.ipa`.
- Apple **age ratings** are set for all 30 apps that have a record, and match
  what each binary ships (`scripts/testflight/sync_age_rating.rb`, which refuses
  to weaken a declaration).
- **Export compliance** is answered in `Info.plist` for all 43, so Apple never
  asks.
- **Firebase** works on both platforms for all 43, including Crashlytics,
  Analytics, Performance and Remote Config. iOS only started working on
  2026-09-23: the config file was on disk but not referenced by the Xcode
  project in 36 apps, so it was never bundled.
- The App Review contact number is `+1 669 388 1960`. It was a 555 placeholder
  that nobody could answer.
- Store copy, screenshots and feature graphics exist for every app.
