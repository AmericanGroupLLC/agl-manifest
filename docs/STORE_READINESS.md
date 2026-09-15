# Store listing readiness

What each of the 43 apps is still missing before its App Store and Play listings
can be submitted, and the order to close the gaps in.

Measured on 2026-09-13 against `store/apps/*.json`, `store/defaults.json` and the
field table in `scripts/store_metadata.py`. Every "missing" below is a field that
script would fail to write, not an opinion about the copy.

Regenerate the raw version of the table with:

```bash
python3 scripts/store_metadata.py check
```

## The two stores are not one listing

`store_metadata.py` keeps a separate key per store on purpose, and this document
follows it. `title`, `short_description`, `full_description` and `changelog` are
Play's; `name`, `subtitle`, `description`, `keywords`, `promotional_text` and
`release_notes` are Apple's. A Play field falls back to its Apple counterpart
only when it is absent, so an app with a deliberately different Play title keeps
it. Divergence is the norm here, not the exception — across the 43 records,
**16 apps carry a Play `title` that differs from the App Store `name`, 19 carry a
different `full_description`, 42 a different `short_description`, and one
(Photriya) a different `changelog`.** Do not "deduplicate" any of them.

`review_information/notes` is **per app and must stay per app.** It once got
templated and told Apple that every app in the portfolio was CalcMaster. All 19
notes currently in the tree were checked and are distinct; none mentions
CalcMaster except CalcMaster's own.

## Two fields the pipeline cannot currently deliver at all

| Field | State |
| --- | --- |
| `primary_category` | `store_metadata.py` writes it (`SHARED_FILES`), reading `record["primary_category"]` or `defaults["primary_category"]`. **Neither exists.** No app has it and the default does not define it, so `primary_category.txt` is never written for any of the 43. |
| Age rating | **There is no field for it anywhere in the schema.** Not in `FIELDS`, not in `SHARED_FILES`, not in `defaults.json`, not in any record. Apple's age-rating questionnaire and Play's IARC questionnaire are both submission-blocking. |

These are counted as missing for all 43 apps below and are not repeated per row.
Neither is guessed at in the records: category identifiers have to match the
string format the delivery step expects, and inventing an age rating for a
portfolio that includes a dating app, a finance app and a video app is not a
store-ops call.

## Privacy and support URLs — all 43 resolve (verified 2026-09-14)

**This section previously claimed "26 apps point at a page that does not exist."
That was wrong.** It was written without network access, by comparing record
slugs against a partial view of the policy tree, and it said so at the time. The
URLs have now actually been fetched.

`store/defaults.json` templates both URLs from the slug against
`www.safecodeg.com` (not the old `americangroupllc.github.io`, which also still
resolves). Every one of the 43 effective privacy URLs and all 43 support URLs
were requested with `curl -L`:

```
both privacy and support returned HTTP 200: 43/43
```

`www.safecodeg.com` issues a 301 to the apex `safecodeg.com` and the host is
case-insensitive, so the three records once flagged as case mismatches
(`iMaps`, `iMeasure`, `TripNest`) resolve correctly as written. No `slug`
overrides are needed.

The policy tree at `www.safecodeg.com/client/public/policy/` now holds 47
directories covering all 43 apps, each with `index.html`, `privacy.html`,
`terms.html` and `support.html`.

Account-deletion pages exist for the 16 apps that have real remote accounts.
`MyCard` and `NexusTransferPay` do **not** need one: their only auth provider is
`Biometric` with `login_screen: false`, which is a device-local lock, not an
account. `scripts/policy_pages.py` gates the page on a Supabase/Google/Apple/
Firebase provider and is correct to skip them.

## Per-app state

Four states. `primary_category` and age rating are missing everywhere and are
omitted from the rows.

### Ready except for the two portfolio-wide fields — 19 apps

Human-written copy, complete on both stores, with per-app review notes and
explicit privacy and support URLs.

AGrammarly · BodyQuest · CalcMaster · daily-pulse · DriftDate · FashionFactory ·
GroceryMatch · HerJourney · iMaps · iMeasure · Kinnav · MyHealth · Photriya ·
PilotEnRoute · radiotune · TripNest · Uscis-Case · Verba · VirtuBand

Two length violations in this group will be rejected on upload:

| App | Field | Length | Limit |
| --- | --- | --- | --- |
| AGrammarly | `keywords` | 102 | 100 |
| AGrammarly | `promotional_text` | 173 | 170 |

These are human product copy and were left alone — trimming them is an editorial
decision, not a mechanical one.

### Description drafted from source, needs approval — 8 apps

Each record now carries a `_drafted` block with the exact fields written, the
source files they were drawn from, and a warning that nothing here is approved.

| App | Drafted | Still missing |
| --- | --- | --- |
| AeroSwift | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| AGRecorder | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| ApexMarketWatch | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| BuddyPlay | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| HomeWise | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| MyCard | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| PlantPulse | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |
| RoomCraft | subtitle, short_description, description, keywords | promotional_text, release_notes, changelog, review notes |

Things the drafts deliberately do *not* say, each because the code does not
support it:

- **AGRecorder** — no video. `CaptureSource.camera` exists in the enum, but
  `RecordBackend.start()` ignores its argument and always records AAC audio.
- **BuddyPlay** — no Bluetooth. `TransportKind.ble` exists with no
  implementation; only the Wi-Fi/hotspot `LanTransport` is real.
- **RoomCraft** — no camera, no photo upload, no AI. `RedesignScreen` takes its
  "OCR analysis" from a `TextEditingController`, and the repo has no imaging
  dependency.
- **ApexMarketWatch** — the Deals tab is not described. It needs
  `API_GATEWAY_URL`, which has no default.
- **AeroSwift** — the copy states that the app ships on offline sample data and
  that live OpenSky is a Settings switch, because that is what `Env` does.
- **PlantPulse** — the copy says the hub is yours and that the app simulates
  when no hub address is set. Also worth knowing before anyone writes marketing:
  **this app has nothing to do with plants.** It is a TV / lights / gamepad
  remote.

### Drafted but gated on build configuration — 8 apps

The feature is genuinely implemented, but the shipped default points at sample
data or at no backend. Each record carries a `_blocker` block naming exactly what
must be set. The copy describes the live product, so **submitting it against a
default build is a false listing** — App Store 2.3 and Play's deceptive-listing
policy both catch this.

| App | Why it is gated |
| --- | --- |
| AGStudio | `AGSTUDIO_API_BASE_URL` and `AGSTUDIO_API_KEY` both default empty. Without them `preview_image_generation_service.dart` draws a poster with `PREVIEW · NOT AI GENERATED` burned into the pixels. It generates nothing. |
| CarDeal | `CARDEAL_API_KEY` has no default; falls back to `sample_listing_data_source.dart`. The app ships a `sample_data_notice.dart` banner admitting it. |
| CodeDeal | Every screen is fed by `https://api.codedeal.com/api/trpc`. No egress here, so I could not confirm that host is live. |
| EventSpark | Inventory defaults to `sample`, `supplierApiKeyConfigured` defaults false. |
| GadgetNest | `GADGETNEST_INVENTORY` defaults to `sample`, which the source calls "deterministic and invented"; `GADGETNEST_SUPPLIER_CONFIGURED` defaults false. |
| NearServe | `NEARSERVE_API_BASE_URL` / `_TOKEN` have no defaults; runs on an invented provider directory that cannot be booked. |
| RideZap | `RIDEZAP_API_BASE_URL` / `_KEY` have no defaults; quoted prices come from `sample_price_source.dart`. For a price-comparison app that is the whole product being fake. |
| yourtube | Returns `_getMockVideos()` unless `PEXELS_API_KEY` is set. Separately: the content is third-party stock footage, not user uploads, and the name needs a trademark review before submission. |

### No honest copy exists yet — 8 apps

No description was drafted for these, on purpose. Each record carries a
`_blocked` block with the evidence. Writing marketing copy for them would mean
claiming features the code does not contain.

| App | Finding |
| --- | --- |
| AGCleaner | `domain/cleaner.dart` is a state machine over constants — `demoDuplicateContacts` ("John Doe", "Maria Santos"), `initialMemoryUsed = 74`, `clearedSizeLabel = '1.84 GB'`, and fixed delays that exist only to look like work. No contacts, photo or storage plugin in pubspec. It frees nothing. |
| ChefCount | `analyzeFridgePicture()` hashes the image **filename string** and indexes a fixed pool. It never reads a pixel; there is no camera or ML dependency. The recipe and kitchen-inventory tabs are real and a listing could be built around those instead. |
| MileMaster | `main.dart:121-125` `_recentTrips` is four literal trips. The dashboard total, the weekly chart and the tax-deduction figure (`_totalMiles * 0.67`) all derive from them. Geolocator is called once for a position and no trip is ever recorded. The `pdf` dependency is declared and never referenced. Highest-risk app in the portfolio: an IRS-deduction claim over invented data. |
| MyFinance | `domain/demo_data.dart` is documented as "Static demo data, extracted verbatim from the RN App.tsx". No http client and no database — nowhere for a real transaction to come from or go. |
| NewsBoard | `app_state.dart:19` builds `NewsRepository()` with no fetcher, so everything falls through to `seedArticles`, which calls itself the offline fallback and fakes freshness against `DateTime.now()`. Nothing ever fetches an article. |
| NexusTransferPay | Copy withheld by choice. Transfers, loans, cards, credit score and insurance all run against `https://nexustransferpay.app`, unreachable from here. Money transmission is a regulated category; copy must come from the product owner with the required licensing and disclosure text. |
| portfolio-board | Loads AGL's own delivery roadmap from a bundled asset and states it has no network path by design. Stages, gate criteria, portfolio health — an internal tool with no public value that would publish internal roadmap data. Needs a distribution decision, not copy. |
| WiFiTrail | `domain/models.dart`: the network list is a `const` ("HomeNetwork_5G", "Office_WiFi"). `speed_test.dart` computes `download = step * 94.7` over 25 × 200 ms ticks and transfers no bytes; idle shows a hard-coded 947/473/12. No wifi or connectivity plugin. It will report 947 Mbps in airplane mode. |

## Priority order

**P0 — unblocks all 43 and is pure configuration.**

1. Define `primary_category` (per app, or a `defaults.json` fallback) and confirm
   the string format the delivery step wants.
2. Add an age-rating field to the schema and to `store_metadata.py`, then answer
   both questionnaires. Nothing ships without this.
3. `curl` the 43 templated privacy and support URLs. Fix the 3 case mismatches
   with explicit `slug` keys, publish the 26 missing pages, rename `plantpluse`,
   and add the 3 missing `support.html` files.

**P1 — 19 apps, one edit each.** After P0 the "ready" group is submittable. Trim
AGrammarly's two over-length fields first.

**P2 — 8 drafted apps.** A human reads each `_drafted` block against the running
app, then writes `promotional_text`, `release_notes` and a per-app
`review_information/notes`. Do not template the notes.

**P3 — 8 gated apps.** Engineering, not writing: set the configuration in each
`_blocker.requires`, rebuild, confirm the app shows real data, then release the
drafted copy. CodeDeal only needs its host confirmed and may move straight to P2.

**P4 — 8 blocked apps.** Product decisions. MileMaster, WiFiTrail, AGCleaner,
MyFinance, NewsBoard and ChefCount each need a real implementation behind the UI
before they can have a listing at all. NexusTransferPay needs owner-written copy.
portfolio-board probably needs to leave the public track entirely.

## What was not verified

- No URL was fetched. The privacy/support finding is a filesystem comparison
  against a different repository than the one the template names.
- No app was built or launched. Every claim about behaviour comes from reading
  Dart source, and a runtime check could still contradict it.
- Category identifier formats and both age-rating questionnaires are untouched.
- `scripts/store_metadata.py generate` was **not** run. It writes into the app
  repositories, which this work was scoped out of. The records here are the
  source of truth; rendering them is a separate, deliberate step.
