# AdMob: 14 of 86 ids exist

Measured 2026-10-08 against `accounts/pub-8528784688453695`,
read live with the AdMob v1beta API. One AdMob app is needed per platform for
43 apps — **86 ids, of which 14 exist and 72 are missing**.

## Why they cannot be created from here

Two independent walls, both verified today.

**The API refuses every write.** The credential is fine: it carries
`admob.monetization` and `admob.readonly`, `accounts.list` and `apps.list`
both answer, and the quota project is set. Every write still returns

```
POST /v1beta/accounts/pub-8528784688453695/apps     403 PERMISSION_DENIED
POST /v1beta/accounts/pub-8528784688453695/adUnits  403 PERMISSION_DENIED
```

Reads from the same token in the same second succeed, so this is AdMob
withholding the v1beta write methods from this publisher, not a scope or a
quota problem. See MA-027.

**The browser is signed in to the wrong Google account.** The AdMob console
is the other route, and the browser attached to this session is signed in as
`srikanth@embeddedos.org`, which has no AdMob account — admob.google.com
redirects it to `/signup`. The publisher belongs to `rainbow472.sri@gmail.com`.
Signing in is the account owner's action, not one this session can take.

## Collecting ids made by hand

```bash
python3 scripts/admob_setup.py --sync    # creates nothing; harvests what exists
```

`--sync` reads the account and writes every app id and banner/interstitial
unit id it finds into `docs/admob-ids.json`, which is what the build reads.
Run it after creating apps in the console and the repository catches up with
no transcription.

Matching is by the package name or bundle id AdMob records in
`linkedAppInfo.appStoreId`, falling back to a case- and punctuation-insensitive
display-name match. The names had already drifted — the account holds
"CalcMaster" where the store copy says "CalcMaster: World Calc", and "Case
Tracker for USCIS" where it says "USCIS Case Lookup" — so a name-only match
would have created a second AdMob app for every one that already exists.

## Two records to fix while you are in there

* **RatioTune** is linked to `com.americangroup.ratiotune`, the package that
  was deleted in the rename. The repo is `radiotune` on
  `com.americangroupllc.radiotune`. The ids still work, but the link points at
  a dead listing.
* **TripNest** and the iOS **CalcMaster** app are `ACTION_REQUIRED`, and
  RatioTune is `IN_REVIEW`; only five of the records are `APPROVED`.

## What to create, and how to make it link itself

All 43 apps now have a record in **both** stores, so every one of these can
be added with *"Yes, it is listed on a store"* and searched by the
identifier below. Doing it that way is worth the extra click: AdMob fills in
the name itself and writes `linkedAppInfo.appStoreId`, which is the key
`--sync` matches on — so the id comes back into the repository with no
transcription and no name-drift to repair later.

After a batch, run:

```bash
cd ~/agl/agl-manifest && python3 scripts/admob_setup.py --sync
```

### Still to create (72)

| App | Platform | Search AdMob for |
| --- | --- | --- |
| AGCleaner | Android | `com.americangroupllc.agcleaner` |
| AGCleaner | iOS | `com.americangroupllc.agcleaner` |
| AGrammarly | Android | `com.americangroupllc.agrammarly` |
| AGrammarly | iOS | `com.americangroupllc.agrammarly` |
| AGRecorder | Android | `com.americangroupllc.agrecorder` |
| AGRecorder | iOS | `com.americangroupllc.agrecorder` |
| AGStudio | Android | `com.americangroupllc.agstudio` |
| AGStudio | iOS | `com.americangroupllc.agstudio` |
| ApexMarketWatch | Android | `com.americangroupllc.apexmarketwatch` |
| ApexMarketWatch | iOS | `com.americangroupllc.apexmarketwatch` |
| BodyQuest | Android | `com.americangroupllc.bodyquest` |
| BodyQuest | iOS | `com.americangroupllc.bodyquest` |
| BuddyPlay | Android | `com.americangroupllc.buddyplay` |
| BuddyPlay | iOS | `com.americangroupllc.buddyplay` |
| CarDeal | Android | `com.americangroupllc.cardeal` |
| CarDeal | iOS | `com.americangroupllc.cardeal` |
| ChefCount | Android | `com.americangroupllc.chefcount` |
| ChefCount | iOS | `com.americangroupllc.chefcount` |
| CodeDeal | Android | `com.americangroupllc.codedeal` |
| CodeDeal | iOS | `com.americangroupllc.codedeal` |
| daily-pulse | Android | `com.americangroupllc.dailypulse` |
| daily-pulse | iOS | `com.americangroupllc.dailypulse` |
| DriftDate | Android | `com.americangroupllc.driftdate` |
| DriftDate | iOS | `com.americangroupllc.driftdate` |
| EventSpark | Android | `com.americangroupllc.eventspark` |
| EventSpark | iOS | `com.americangroupllc.eventspark` |
| FashionFactory | Android | `com.americangroupllc.fashionfactory` |
| FashionFactory | iOS | `com.americangroupllc.fashionfactory` |
| GadgetNest | Android | `com.americangroupllc.gadgetnest` |
| GadgetNest | iOS | `com.americangroupllc.gadgetnest` |
| GroceryMatch | Android | `com.americangroupllc.GroceryMatch` |
| GroceryMatch | iOS | `com.americangroupllc.grocerymatch` |
| HerJourney | Android | `com.americangroupllc.herjourney` |
| HerJourney | iOS | `com.americangroupllc.herjourney` |
| HomeWise | Android | `com.americangroupllc.homewise` |
| HomeWise | iOS | `com.americangroupllc.homewise` |
| Kinnav | Android | `com.americangroupllc.kinnav` |
| Kinnav | iOS | `com.americangroupllc.kinnav` |
| MileMaster | Android | `com.americangroupllc.milemaster` |
| MileMaster | iOS | `com.americangroupllc.milemaster` |
| MyCard | Android | `com.americangroupllc.mycard` |
| MyCard | iOS | `com.americangroupllc.mycard` |
| MyFinance | Android | `com.americangroupllc.myfinance` |
| MyFinance | iOS | `com.americangroupllc.myfinance` |
| MyHealth | Android | `com.americangroupllc.myhealth` |
| MyHealth | iOS | `com.americangroupllc.myhealth` |
| NearServe | Android | `com.americangroupllc.nearserve` |
| NearServe | iOS | `com.americangroupllc.nearserve` |
| NewsBoard | Android | `com.americangroupllc.newsboard` |
| NewsBoard | iOS | `com.americangroupllc.newsboard` |
| NexusTransferPay | Android | `com.americangroupllc.nexustransferpay` |
| NexusTransferPay | iOS | `com.americangroupllc.nexustransferpay` |
| Photriya | Android | `com.americangroupllc.photriya` |
| Photriya | iOS | `com.americangroupllc.photriya` |
| PilotEnRoute | Android | `com.americangroupllc.pilotenroute` |
| PilotEnRoute | iOS | `com.americangroupllc.pilotenroute` |
| PlantPulse | Android | `com.americangroupllc.plantpulse` |
| PlantPulse | iOS | `com.americangroupllc.plantpulse` |
| portfolio-board | Android | `com.americangroupllc.portfolioboard` |
| portfolio-board | iOS | `com.americangroupllc.portfolioboard` |
| radiotune | iOS | `com.americangroupllc.radiotune` |
| RideZap | Android | `com.americangroupllc.ridezap` |
| RideZap | iOS | `com.americangroupllc.ridezap` |
| RoomCraft | Android | `com.americangroupllc.roomcraft` |
| RoomCraft | iOS | `com.americangroupllc.roomcraft` |
| Verba | Android | `com.americangroupllc.verba` |
| Verba | iOS | `com.americangroupllc.verba` |
| VirtuBand | iOS | `com.americangroupllc.virtuband` |
| WiFiTrail | Android | `com.americangroupllc.wifitrail` |
| WiFiTrail | iOS | `com.americangroupllc.wifitrail` |
| yourtube | Android | `com.americangroupllc.yourtube` |
| yourtube | iOS | `com.americangroupllc.yourtube` |

## Per app

| App | Android | iOS |
| --- | --- | --- |
| AeroSwift | ca-app-pub-8528784688453695~3416319568 | ca-app-pub-8528784688453695~4318337690 |
| AGCleaner | **missing** | **missing** |
| AGrammarly | **missing** | **missing** |
| AGRecorder | **missing** | **missing** |
| AGStudio | **missing** | **missing** |
| ApexMarketWatch | **missing** | **missing** |
| BodyQuest | **missing** | **missing** |
| BuddyPlay | **missing** | **missing** |
| CalcMaster | ca-app-pub-8528784688453695~5377349094 | ca-app-pub-8528784688453695~9148987425 |
| CarDeal | **missing** | **missing** |
| ChefCount | **missing** | **missing** |
| CodeDeal | **missing** | **missing** |
| daily-pulse | **missing** | **missing** |
| DriftDate | **missing** | **missing** |
| EventSpark | **missing** | **missing** |
| FashionFactory | **missing** | **missing** |
| GadgetNest | **missing** | **missing** |
| GroceryMatch | **missing** | **missing** |
| HerJourney | **missing** | **missing** |
| HomeWise | **missing** | **missing** |
| iMaps | ca-app-pub-8528784688453695~5082647691 | ca-app-pub-8528784688453695~3933082470 |
| iMeasure | ca-app-pub-8528784688453695~9265279754 | ca-app-pub-8528784688453695~7680755795 |
| Kinnav | **missing** | **missing** |
| MileMaster | **missing** | **missing** |
| MyCard | **missing** | **missing** |
| MyFinance | **missing** | **missing** |
| MyHealth | **missing** | **missing** |
| NearServe | **missing** | **missing** |
| NewsBoard | **missing** | **missing** |
| NexusTransferPay | **missing** | **missing** |
| Photriya | **missing** | **missing** |
| PilotEnRoute | **missing** | **missing** |
| PlantPulse | **missing** | **missing** |
| portfolio-board | **missing** | **missing** |
| radiotune | ca-app-pub-8528784688453695~7770953426 | **missing** |
| RideZap | **missing** | **missing** |
| RoomCraft | **missing** | **missing** |
| TripNest | ca-app-pub-8528784688453695~8044208178 | ca-app-pub-8528784688453695~7973677521 |
| Uscis-Case | ca-app-pub-8528784688453695~2309537905 | ca-app-pub-8528784688453695~5246164144 |
| Verba | **missing** | **missing** |
| VirtuBand | ca-app-pub-8528784688453695~2836542125 | **missing** |
| WiFiTrail | **missing** | **missing** |
| yourtube | **missing** | **missing** |
