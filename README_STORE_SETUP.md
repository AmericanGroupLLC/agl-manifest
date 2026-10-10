# Store setup — the console work

Everything here needs a Play Console or App Store Connect login, so it cannot
be scripted. Everything that *can* be scripted already is; see
[`docs/API_ACTIONS.md`](docs/API_ACTIONS.md).

Current state is measured, not asserted — regenerate with
`python3 scripts/status.py` and read `status.csv`, or
`python3 scripts/store_master_csv.py --gaps` for just the open fields.

**43 apps. 5 have no blocker. Every one of the 50 that remain needs a console
login — none of them can be fixed in code.**

What each step is worth, measured:

| zero-blocker apps | after |
| ---: | --- |
| 5 / 43 | today |
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

**5 apps need an App Store Connect record** — BodyQuest, FashionFactory,
MyHealth, PlantPulse, radiotune. Re-measured against the live API on
2026-09-26; it was 13.

> **Resolved 2026-09-26.** Those four records — BodyQuest, daily-pulse,
> radiotune and yourtube — were on the retired `com.americangroup.*` scheme.
> The owner has cleared them. Verified against the live API: **zero**
> `com.americangroup.*` records remain, and 38 of 43 apps now have a record
> under their real `com.americangroupllc.*` id.

**27 apps need App Privacy published.** The answers are already written, per
app, in `store/privacy/<repo>.json` — nothing to compose, only to publish.

---

## 2. Play — create the 9 missing apps

`androidpublisher`'s `applications` resource exposes exactly one method,
`dataSafety`. There is no create. Each of these needs **Create app** in Play
Console under the package name below, which is permanent once set:

| app | package name |
| --- | --- |
| BodyQuest | `com.americangroupllc.bodyquest` |
| DriftDate | `com.americangroupllc.driftdate` |
| FashionFactory | `com.americangroupllc.fashionfactory` |
| GadgetNest | `com.americangroupllc.gadgetnest` |
| GroceryMatch | `com.americangroupllc.grocerymatch` |
| HerJourney | `com.americangroupllc.herjourney` |
| Photriya | `com.americangroupllc.photriya` |
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
   Contact email: `contact@americangroup.ai`.
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

Four apps sold a subscription with no purchase SDK behind it — App Review
guideline 3.1.1, a rejection. CodeDeal was the worst of them: it opened a
Stripe checkout in a browser. Real `in_app_purchase` billing is now wired in
all four. The **products must be created in both consoles**, and the ids have
to match exactly or the paywall shows no price and no purchase can start.

| app | product ids |
| --- | --- |
| Kinnav | `kinnav_premium_monthly`, `kinnav_premium_annual` |
| CodeDeal | `codedeal_pro_monthly`, `codedeal_pro_yearly`, `codedeal_pro_lifetime` |
| NexusTransferPay | `nexustransferpay_plus_monthly`, `nexustransferpay_plus_yearly` |
| VirtuBand | `virtuband_pro_monthly`, `virtuband_pro_yearly`, `virtuband_pro_lifetime` |

**NewsBoard and daily-pulse need nothing here.** Both were flagged by an early
version of the detector and neither sells anything — NewsBoard's screen says
"There is no paid plan" and has a test asserting no price appears. Creating
products for them would mean selling a subscription that grants nothing, which
is guideline 3.1.2.

VirtuBand ships with `BILLING_ENABLED` unset, so its paywall stays hidden until
someone builds with it on. The purchase path behind it is real.

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

## 7. HomeWise needs a listings feed

HomeWise is meant to be MLS listings *and* the affordability calculator. The
listings half now exists — Browse is the first tab, and every result is scored
against the buyer's own budget by the same engine the calculator tabs use.

It ships inert. No feed is configured, so the tab says "No listing feed in this
build" and the search box is disabled. Nothing is faked: a made-up mortgage
rate is a labelled assumption, a made-up property is a claim that a specific
house exists at a specific price, and shipping those would be guideline 2.3.1.

To turn it on, build with a feed:

```sh
flutter build ipa \
  --dart-define=HOMEWISE_LISTINGS_API_URL=https://example.com/v1/listings \
  --dart-define=HOMEWISE_LISTINGS_API_KEY=...
```

The endpoint takes the query parameters in `ListingQuery.toQueryParameters` and
returns a JSON array or `{"listings": [...], "hasMore": bool}`. Vendor-shaped
JSON is mapped in `Listing.fromJson`, so a different provider is a mapping
change rather than a rewrite.

**The commercial decision is yours.** Real MLS data needs an IDX/MLS licence
through a local board, or a paid aggregator — ATTOM, Bridge Interactive, or
Realtor's feed via RapidAPI. Zillow closed its public API. Most IDX licences
also require a visible link back to the source listing, which the detail screen
already has.

Two things to change **when a feed goes live**, and not before:

- **Store copy.** `store/apps/HomeWise.json` describes only the calculator
  ("What house can I afford?"), which is accurate today. Once listings work it
  undersells the app.
- **Category.** It is `FINANCE`, right for a calculator and wrong for a
  listings app — Redfin and Zillow are both Lifestyle. That also drives the
  *Provides Financial Features* column in `status.csv`.

---

## 8. Decisions nobody has made yet

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
