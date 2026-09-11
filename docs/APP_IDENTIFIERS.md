# App identifiers and AdMob

Generated from the repositories themselves, not from the planning workbook —
every bundle id below is what the app actually builds today.

- Flutter apps: **36**
- Mobile apps not yet Flutter: **5** — AGStudio, ApexMarketWatch, BuddyPlay, CodeDeal, MyCard
- Apps with a real AdMob **Android** app id: **7** of 36
- Apps with a real AdMob **iOS** app id: **1** of 36

Machine-readable: [`app-identifiers.json`](app-identifiers.json), [`admob-ids.json`](admob-ids.json)

## Every Flutter app

`GAD in plist` is what `GADApplicationIdentifier` is set to right now.
`TEST` means Google's public test id — safe, but earns nothing.

| App | iOS bundle id | Android applicationId | AdMob iOS | AdMob Android | GAD in plist |
| --- | --- | --- | --- | --- | --- |
| AGCleaner | `com.americangroupllc.agcleaner` | `com.americangroupllc.agcleaner` | — | — | — none set |
| AGrammarly | `com.americangroup.agrammarly` | `com.americangroup.agrammarly` | — | — | — none set |
| AGRecorder | `com.americangroupllc.agrecorder` | `com.americangroupllc.agrecorder` | — | — | — none set |
| BodyQuest | `com.americangroup.bodyquest` | `com.americangroup.bodyquest` | — | — | `TEST` |
| CalcMaster | `com.americangroupllc.calcmaster` | `com.americangroupllc.calcmaster` | `ca-app-pub-8528784688453695~9148987425` | `ca-app-pub-8528784688453695~5377349094` | `ca-app-pub-8528784688453695~9148987425` |
| CarDeal | `com.americangroupllc.cardeal` | `com.americangroupllc.cardeal` | — | — | — none set |
| ChefCount | `com.americangroupllc.chefcount` | `com.americangroupllc.chefcount` | — | — | — none set |
| daily-pulse | `com.americangroup.dailypulse` | `com.americangroup.daily_pulse` ⚠️ differs | — | — | — none set |
| DriftDate | `com.americangroupllc.driftdate` | `com.americangroupllc.driftdate` | — | — | — none set |
| EventSpark | `com.americangroupllc.eventspark` | `com.americangroupllc.eventspark` | — | — | — none set |
| FashionFactory | `com.americangroupllc.styleradar` | `com.americangroupllc.styleradar` | — | — | — none set |
| GadgetNest | `com.americangroupllc.gadgetnest` | `com.americangroupllc.gadgetnest` | — | — | — none set |
| GroceryMatch | `com.americangroupllc.grocerymatch` | `com.americangroupllc.grocerymatch` | — | — | — none set |
| HerJourney | `com.americangroupllc.herJourney` | `com.americangroupllc.her_journey` ⚠️ differs | — | — | — none set |
| HomeWise | `com.americangroupllc.homewise` | `com.americangroupllc.homewise` | — | — | — none set |
| iMaps | `com.americangroupllc.imaps` | `com.americangroupllc.imaps` | — | `ca-app-pub-8528784688453695~5082647691` | ⚠️ `$(ADMOB_APP_ID)` unresolved |
| iMeasure | `com.americangroupllc.imeasure` | `com.americangroupllc.imeasure` | — | `ca-app-pub-8528784688453695~9265279754` | — none set |
| Kinnav | `com.americangroupllc.kinnav` | `com.americangroupllc.kinnav` | — | — | — none set |
| MileMaster | `com.americangroupllc.milemaster` | `com.americangroupllc.milemaster` | — | — | — none set |
| MyFinance | `com.americangroupllc.myfinance` | `com.americangroupllc.myfinance` | — | — | — none set |
| MyHealth | `com.americangroupllc.myhealth` | `com.americangroupllc.myhealth` | — | — | — none set |
| NearServe | `com.americangroupllc.nearserve` | `com.americangroupllc.nearserve` | — | — | — none set |
| NewsBoard | `com.americangroup.newsboard` | `com.americangroup.newsboard` | — | — | — none set |
| NexusTransferPay | `com.americangroupllc.nexuspay` | `com.americangroupllc.nexuspay` | — | — | — none set |
| Photriya | `com.americangroupllc.photriya` | `com.americangroupllc.photriya` | — | — | — none set |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | `com.americangroupllc.pilot_enroute` ⚠️ differs | — | — | `TEST` |
| portfolio-board | `com.americangroupllc.portfolioboard` | `com.americangroupllc.portfolioboard` | — | — | — none set |
| radiotune | `com.americangroup.ratiotune` | `com.americangroup.ratiotune` | — | `ca-app-pub-8528784688453695~7770953426` | — none set |
| RideZap | `com.americangroupllc.ridezap` | `com.americangroupllc.ridezap` | — | — | — none set |
| RoomCraft | `com.americangroupllc.roomcraft` | `com.americangroupllc.roomcraft` | — | — | — none set |
| TripNest | `com.americangroupllc.tripnest` | `com.americangroupllc.tripnest` | — | `ca-app-pub-8528784688453695~8044208178` | `TEST` |
| Uscis-Case | `com.americangroupllc.usciscase` | `com.americangroupllc.usciscase` | — | `ca-app-pub-8528784688453695~2309537905` | — none set |
| Verba | `com.americangroupllc.verba` | `com.americangroupllc.verba` | — | — | `TEST` |
| VirtuBand | `com.americangroupllc.virtuband` | `com.americangroupllc.virtuband` | — | `ca-app-pub-8528784688453695~2836542125` | — none set |
| WiFiTrail | `com.americangroupllc.wifitrail` | `com.americangroupllc.wifitrail` | — | — | — none set |
| yourtube | `com.americangroup.yourtube` | `com.americangroup.yourtube` | — | — | ⚠️ wrong publisher — `ca-app-pub-1804742004018995~8063161149` |

## Ad unit ids

| App | Banner | Interstitial |
| --- | --- | --- |
| CalcMaster | `ca-app-pub-8528784688453695/7665581023` | `ca-app-pub-8528784688453695/7474009334` |
| iMaps | `ca-app-pub-8528784688453695/1143402684` | `ca-app-pub-8528784688453695/8340879191` |
| iMeasure | `ca-app-pub-8528784688453695/1222409251` | `ca-app-pub-8528784688453695/9950162694` |
| radiotune | `ca-app-pub-8528784688453695/4087643109` | `ca-app-pub-8528784688453695/2327055058` |
| TripNest | `ca-app-pub-8528784688453695/3721819782` | `ca-app-pub-8528784688453695/5528514029` |
| Uscis-Case | `ca-app-pub-8528784688453695/5539491423` | `ca-app-pub-8528784688453695/9095593054` |
| VirtuBand | `ca-app-pub-8528784688453695/6914604113` | `ca-app-pub-8528784688453695/9569471431` |

## Problems to fix

### 1. Three apps use a different id on each platform

| App | iOS | Android |
| --- | --- | --- |
| HerJourney | `com.americangroupllc.herJourney` | `com.americangroupllc.her_journey` |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | `com.americangroupllc.pilot_enroute` |
| daily-pulse | `com.americangroup.dailypulse` | `com.americangroup.daily_pulse` |

The Android side uses underscores where iOS uses camelCase or no separator.
Nothing forbids the two platforms differing, but here it looks accidental, and
both are **immutable once published**. Decide the canonical form before first
release. Note `com.americangroupllc.herJourney` also carries a capital letter,
which is legal but unconventional for an Android package.

### 2. yourtube points at someone else's AdMob account

**FIXED (2026-09-09).** yourtube carried publisher `pub-1804742004018995` on
*both* platforms — `~8063161149` in `Info.plist` and `~7568337124` in
`AndroidManifest.xml`. That publisher is not American Group LLC
(`pub-8528784688453695`), so ads would not have served under this app and any
that did would have credited another account.

Both now use Google's official test ids, the same call CalcMaster already made
for the identical problem. **yourtube's real AdMob app ids are still needed** —
until then it runs with test ads, which earn nothing.

### 3. iMaps uses a build variable — CORRECTED, not a defect

`iMaps` sets `GADApplicationIdentifier` to `$(ADMOB_APP_ID)`. An earlier
revision of this document called that unresolved; that was wrong. The variable
**is** defined, in `ios/Flutter/MapsRadar.xcconfig`, as Google's test app id.
The pattern is sound — it keeps the id out of the plist and lets the release
build inject the real one. What iMaps still needs is its **real iOS app id**
substituted for the test value in that xcconfig.

### 4. AdMob apps still to create

Publisher `pub-8528784688453695`. Every app needs a **separate id per platform**.

| App | iOS needed | Android needed |
| --- | --- | --- |
| AGCleaner | yes | yes |
| AGrammarly | yes | yes |
| AGRecorder | yes | yes |
| BodyQuest | yes | yes |
| CarDeal | yes | yes |
| ChefCount | yes | yes |
| daily-pulse | yes | yes |
| DriftDate | yes | yes |
| EventSpark | yes | yes |
| FashionFactory | yes | yes |
| GadgetNest | yes | yes |
| GroceryMatch | yes | yes |
| HerJourney | yes | yes |
| HomeWise | yes | yes |
| iMaps | yes | — |
| iMeasure | yes | — |
| Kinnav | yes | yes |
| MileMaster | yes | yes |
| MyFinance | yes | yes |
| MyHealth | yes | yes |
| NearServe | yes | yes |
| NewsBoard | yes | yes |
| NexusTransferPay | yes | yes |
| Photriya | yes | yes |
| PilotEnRoute | yes | yes |
| portfolio-board | yes | yes |
| radiotune | yes | — |
| RideZap | yes | yes |
| RoomCraft | yes | yes |
| TripNest | yes | — |
| Uscis-Case | yes | — |
| Verba | yes | yes |
| VirtuBand | yes | — |
| WiFiTrail | yes | yes |
| yourtube | yes | yes |

Send the ids over as `App, platform, ca-app-pub-…~…` and they will be written
into `Info.plist` and `AndroidManifest.xml`. Until then the test id stays: a
wrong id passes CI and crashes on launch, so guessing is worse than waiting.

