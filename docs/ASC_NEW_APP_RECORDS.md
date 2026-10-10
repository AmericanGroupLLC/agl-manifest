# Creating the 14 missing App Store Connect records

These 14 apps are the **only** remaining failures in the `check: *` columns of `status.csv`.
Every other check passes for all 43 apps. Each of these has a signed IPA and a
signed AAB already built; they cannot be delivered because no App Store Connect
app record exists to receive the build.

## Why this cannot be automated

Proven three ways on 2026-09-22 — please do not spend time re-trying it:

1. `Spaceship::ConnectAPI::App.create` exists and Apple refuses the call:
   `The resource 'apps' does not allow 'CREATE'. Allowed operations are:
   GET_COLLECTION, GET_INSTANCE, UPDATE`
2. The Developer Portal bundle ids are **not** missing — all 14 already exist, so
   they will appear in the Bundle ID dropdown.
3. Uploading a build does not create the record. A real `upload_to_testflight`
   run returned `Couldn't find app 'com.americangroupllc.aeroswift' on the
   account of 'rainbow472.sri@gmail.com' on App Store Connect`.

`fastlane produce` is not a way round it either — it needs an Apple ID password,
not the API key this machine holds.

## What App Store Connect asks for

**My Apps → + → New App.** Five fields, all given per app below:

| Field | Value |
| --- | --- |
| Platforms | **iOS** only |
| Name | the *App Store name* column (all are within Apple's 30-character limit) |
| Primary Language | **English (U.S.)** for all 14 |
| Bundle ID | pick the matching `com.americangroupllc.*` from the dropdown |
| SKU | the *SKU* column — any unique string; these follow the existing convention |
| User Access | **Full Access** unless you want it restricted |

The name must be unique across the entire App Store, not just this account. If
one is taken, Apple rejects it at this step — the subtitle column gives you a
longer form to fall back on.

## The 14 apps

| App Store name | Bundle ID (iOS) | SKU | Ver | Category |
| --- | --- | --- | --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` | `aeroswift-001` | 1.0.0 | Travel |
| BodyQuest: Health Game | `com.americangroupllc.bodyquest` | `bodyquest-001` | 1.1.0 | Health & Fitness |
| Daily Pulse: Morning Brief | `com.americangroupllc.dailypulse` | `dailypulse-001` | 1.0.0 | Lifestyle |
| Fashion Factory: Deals | `com.americangroupllc.fashionfactory` | `fashionfactory-001` | 2.2.0 | Lifestyle |
| GadgetNest | `com.americangroupllc.gadgetnest` | `gadgetnest-001` | 1.0.0 | Shopping |
| GroceryMatch: Save on Food | `com.americangroupllc.grocerymatch` | `grocerymatch-001` | 2.1.0 | Shopping |
| HerJourney: Cycle & Health | `com.americangroupllc.herjourney` | `herjourney-001` | 1.2.0 | Health & Fitness |
| iMeasure: Measure & Level | `com.americangroupllc.imeasure` | `imeasure-001` | 5.0.1 | Utilities |
| MyHealth: Fitness Tracker | `com.americangroupllc.myhealth` | `myhealth-001` | 1.0.0 | Health & Fitness |
| PlantPulse | `com.americangroupllc.plantpulse` | `plantpulse-001` | 1.0.0 | Utilities |
| Portfolio Board | `com.americangroupllc.portfolioboard` | `portfolioboard-001` | 1.0.0 | Productivity |
| Radio Tune: Live Radio | `com.americangroupllc.radiotune` | `radiotune-001` | 2.0.1 | Music |
| Verba: Voice Translator | `com.americangroupllc.verba` | `verba-001` | 1.0.0 | Education |
| YourTube: Watch & Discover | `com.americangroupllc.yourtube` | `yourtube-001` | 1.0.2 | Entertainment |

Android package names are identical to the iOS bundle ids in every case, so the
same string works for the Play listing.

## Listing fields, once the record exists

All of these are already written and, for the URLs, **content-verified live** —
not merely checked for HTTP 200, which is meaningless on this host because it
serves the marketing homepage for any unknown path.

### AeroSwift

* **Bundle ID** `com.americangroupllc.aeroswift`  ·  **SKU** `aeroswift-001`  ·  **Version** 1.0.0
* **Subtitle** (24/30) — Flight and airport board
* **Category** — Travel
* **Privacy Policy URL** — https://www.americangroup.ai/policy/aeroswift/  _(live (2982 B))_
* **Support URL** — https://www.americangroup.ai/policy/aeroswift/support.html  _(live (1640 B))_
* **Keywords** (85/100) — `flight,tracker,airport,arrivals,departures,aviation,opensky,callsign,aircraft,flights`
* Description, promotional text and release notes are in
  `AeroSwift/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/AeroSwift/screenshots/`.

### BodyQuest: Health Game

* **Bundle ID** `com.americangroupllc.bodyquest`  ·  **SKU** `bodyquest-001`  ·  **Version** 1.1.0
* **Subtitle** (28/30) — Wellness, learned by playing
* **Category** — Health & Fitness
* **Privacy Policy URL** — https://www.americangroup.ai/policy/bodyquest/  _(live (3509 B))_
* **Support URL** — https://www.americangroup.ai/policy/bodyquest/support.html  _(live (2524 B))_
* **Keywords** (96/100) — `health,wellness,education,game,fitness,diet,nutrition,workout,breathing,mindfulness,learn,habits`
* Description, promotional text and release notes are in
  `BodyQuest/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/BodyQuest/screenshots/`.

### Daily Pulse: Morning Brief

* **Bundle ID** `com.americangroupllc.dailypulse`  ·  **SKU** `dailypulse-001`  ·  **Version** 1.0.0
* **Subtitle** (28/30) — News, weather, air & markets
* **Category** — Lifestyle
* **Privacy Policy URL** — https://www.americangroup.ai/policy/dailypulse/  _(live (3860 B))_
* **Support URL** — https://www.americangroup.ai/policy/dailypulse/support.html  _(live (2347 B))_
* **Keywords** (94/100) — `news,briefing,morning,weather,air quality,stocks,markets,good news,world news,crypto,headlines`
* Description, promotional text and release notes are in
  `daily-pulse/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/daily-pulse/screenshots/`.

### Fashion Factory: Deals

* **Bundle ID** `com.americangroupllc.fashionfactory`  ·  **SKU** `fashionfactory-001`  ·  **Version** 2.2.0
* **Subtitle** (27/30) — Compare prices, track drops
* **Category** — Lifestyle
* **Privacy Policy URL** — https://www.americangroup.ai/policy/fashionfactory/  _(live (3375 B))_
* **Support URL** — https://www.americangroup.ai/policy/fashionfactory/support.html  _(live (2456 B))_
* **Keywords** (96/100) — `deals,price comparison,shopping,fashion,shoes,bags,perfume,watches,tech,discount,sale,price drop`
* Description, promotional text and release notes are in
  `FashionFactory/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/FashionFactory/screenshots/`.

### GadgetNest

* **Bundle ID** `com.americangroupllc.gadgetnest`  ·  **SKU** `gadgetnest-001`  ·  **Version** 1.0.0
* **Subtitle** (27/30) — Compare tech before you buy
* **Category** — Shopping
* **Privacy Policy URL** — https://www.americangroup.ai/policy/gadgetnest/  _(live (2988 B))_
* **Support URL** — https://www.americangroup.ai/policy/gadgetnest/support.html  _(live (1650 B))_
* **Keywords** (81/100) — `tech deals,compare,price history,laptop,phone,gpu,specs,gadgets,shopping,pc build`
* Description, promotional text and release notes are in
  `GadgetNest/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/GadgetNest/screenshots/`.

### GroceryMatch: Save on Food

* **Bundle ID** `com.americangroupllc.grocerymatch`  ·  **SKU** `grocerymatch-001`  ·  **Version** 2.1.0
* **Subtitle** (29/30) — Compare grocery & meal prices
* **Category** — Shopping
* **Privacy Policy URL** — https://www.americangroup.ai/policy/grocerymatch/  _(live (3864 B))_
* **Support URL** — https://www.americangroup.ai/policy/grocerymatch/support.html  _(live (2420 B))_
* **Keywords** (90/100) — `grocery,price comparison,shopping list,coupons,walmart,kroger,target,aldi,doordash,savings`
* Description, promotional text and release notes are in
  `GroceryMatch/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/GroceryMatch/screenshots/`.

### HerJourney: Cycle & Health

* **Bundle ID** `com.americangroupllc.herjourney`  ·  **SKU** `herjourney-001`  ·  **Version** 1.2.0
* **Subtitle** (27/30) — Cycle, pregnancy, menopause
* **Category** — Health & Fitness
* **Privacy Policy URL** — https://www.americangroup.ai/policy/herjourney/  _(live (5045 B))_
* **Support URL** — https://www.americangroup.ai/policy/herjourney/support.html  _(live (3212 B))_
* **Keywords** (95/100) — `cycle,period,tracker,ovulation,fertility,pregnancy,due date,menopause,women,health,symptoms,log`
* Description, promotional text and release notes are in
  `HerJourney/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/HerJourney/screenshots/`.

### iMeasure: Measure & Level

* **Bundle ID** `com.americangroupllc.imeasure`  ·  **SKU** `imeasure-001`  ·  **Version** 5.0.1
* **Subtitle** (28/30) — Ruler, level, compass & more
* **Category** — Utilities
* **Privacy Policy URL** — https://www.americangroup.ai/policy/iMeasure/  _(live (8871 B))_
* **Support URL** — https://www.americangroup.ai/policy/iMeasure/support.html  _(live (2364 B))_
* **Keywords** (97/100) — `ruler,level,compass,protractor,measure,converter,barometer,altimeter,pedometer,bubble,angle,tools`
* Description, promotional text and release notes are in
  `iMeasure/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/iMeasure/screenshots/`.

### MyHealth: Fitness Tracker

* **Bundle ID** `com.americangroupllc.myhealth`  ·  **SKU** `myhealth-001`  ·  **Version** 1.0.0
* **Subtitle** (29/30) — Activity, diet, sleep, vitals
* **Category** — Health & Fitness
* **Privacy Policy URL** — https://www.americangroup.ai/policy/myhealth/  _(live (3741 B))_
* **Support URL** — https://www.americangroup.ai/policy/myhealth/support.html  _(live (2607 B))_
* **Keywords** (91/100) — `health,fitness,tracker,activity,diet,nutrition,sleep,vitals,medicine,workout,running,hiking`
* Description, promotional text and release notes are in
  `MyHealth/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/MyHealth/screenshots/`.

### PlantPulse

* **Bundle ID** `com.americangroupllc.plantpulse`  ·  **SKU** `plantpulse-001`  ·  **Version** 1.0.0
* **Subtitle** (23/30) — Remote for your own hub
* **Category** — Utilities
* **Privacy Policy URL** — https://www.americangroup.ai/policy/plantpulse/  _(live (2932 B))_
* **Support URL** — https://www.americangroup.ai/policy/plantpulse/support.html  _(live (1657 B))_
* **Keywords** (79/100) — `remote,smart home,tv remote,lights,gamepad,hub,controller,local,home automation`
* Description, promotional text and release notes are in
  `PlantPulse/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/PlantPulse/screenshots/`.

### Portfolio Board

* **Bundle ID** `com.americangroupllc.portfolioboard`  ·  **SKU** `portfolioboard-001`  ·  **Version** 1.0.0
* **Subtitle** (28/30) — Offline spec and stage board
* **Category** — Productivity
* **Privacy Policy URL** — https://www.americangroup.ai/policy/portfolio-board/  _(live (3430 B))_
* **Support URL** — https://www.americangroup.ai/policy/portfolio-board/support.html  _(live (1680 B))_
* **Keywords** (92/100) — `portfolio,roadmap,specs,pipeline,stage,tracker,product,board,offline,startup,research,search`
* Description, promotional text and release notes are in
  `portfolio-board/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/portfolio-board/screenshots/`.

### Radio Tune: Live Radio

* **Bundle ID** `com.americangroupllc.radiotune`  ·  **SKU** `radiotune-001`  ·  **Version** 2.0.1
* **Subtitle** (26/30) — 50,000+ stations worldwide
* **Category** — Music
* **Privacy Policy URL** — https://www.americangroup.ai/policy/radiotune/  _(live (8157 B))_
* **Support URL** — https://www.americangroup.ai/policy/radiotune/support.html  _(live (2514 B))_
* **Keywords** (81/100) — `radio,live radio,fm,am,stations,tuner,music,news,talk,streaming,world,sleep timer`
* Description, promotional text and release notes are in
  `radiotune/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/radiotune/screenshots/`.

### Verba: Voice Translator

* **Bundle ID** `com.americangroupllc.verba`  ·  **SKU** `verba-001`  ·  **Version** 1.0.0
* **Subtitle** (23/30) — Translate, talk & learn
* **Category** — Education
* **Privacy Policy URL** — https://www.americangroup.ai/policy/verba/  _(live (3673 B))_
* **Support URL** — https://www.americangroup.ai/policy/verba/support.html  _(live (2464 B))_
* **Keywords** (92/100) — `translate,translator,voice,speech,language,learn,phrasebook,flashcards,conversation,practice`
* Description, promotional text and release notes are in
  `Verba/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/Verba/screenshots/`.

### YourTube: Watch & Discover

* **Bundle ID** `com.americangroupllc.yourtube`  ·  **SKU** `yourtube-001`  ·  **Version** 1.0.2
* **Subtitle** (27/30) — Stock video, worth watching
* **Category** — Entertainment
* **Privacy Policy URL** — https://www.americangroup.ai/policy/yourtube/  _(live (3929 B))_
* **Support URL** — https://www.americangroup.ai/policy/yourtube/support.html  _(live (1947 B))_
* **Keywords** (79/100) — `video,watch,stock video,shorts,streaming,player,trending,for you,tv,watch later`
* Description, promotional text and release notes are in
  `yourtube/fastlane/metadata/en-US/`, and screenshots in
  `agl-manifest/store/graphics/yourtube/screenshots/`.

## After the records exist

```sh
source scripts/testflight/env.sh
cd scripts/testflight && python3 run_batch.py --wave records
```

That uploads the already-built, already-signed IPA for every app whose bundle id
now has a record, and skips the ones already delivered. Then re-run
`python3 scripts/asc_build_state.rb` and `python3 scripts/store_checklist.py` —
the checklist should go to zero failures.
