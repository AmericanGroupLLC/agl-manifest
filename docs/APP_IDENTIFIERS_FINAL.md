# App identifiers — the list to re-create store records from

All 43 apps use `com.americangroupllc.<appname>`. Regenerate this table rather
than editing it; it is read from `apps.json` and each app's Xcode project.

| App | iOS bundle id | Android applicationId |
| --- | --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` | `com.americangroupllc.aeroswift` |
| AGCleaner | `com.americangroupllc.agcleaner` | `com.americangroupllc.agcleaner` |
| AGrammarly | `com.americangroupllc.agrammarly` | `com.americangroupllc.agrammarly` |
| AGRecorder | `com.americangroupllc.agrecorder` | `com.americangroupllc.agrecorder` |
| AGStudio | `com.americangroupllc.agstudio` | `com.americangroupllc.agstudio` |
| ApexMarketWatch | `com.americangroupllc.apexmarketwatch` | `com.americangroupllc.apexmarketwatch` |
| BodyQuest | `com.americangroupllc.bodyquest` | `com.americangroupllc.bodyquest` |
| BuddyPlay | `com.americangroupllc.buddyplay` | `com.americangroupllc.buddyplay` |
| CalcMaster | `com.americangroupllc.calcmaster` | `com.americangroupllc.calcmaster` |
| CarDeal | `com.americangroupllc.cardeal` | `com.americangroupllc.cardeal` |
| ChefCount | `com.americangroupllc.chefcount` | `com.americangroupllc.chefcount` |
| CodeDeal | `com.americangroupllc.codedeal` | `com.americangroupllc.codedeal` |
| daily-pulse | `com.americangroupllc.dailypulse` | `com.americangroupllc.dailypulse` |
| DriftDate | `com.americangroupllc.driftdate` | `com.americangroupllc.driftdate` |
| EventSpark | `com.americangroupllc.eventspark` | `com.americangroupllc.eventspark` |
| FashionFactory | `com.americangroupllc.fashionfactory` | `com.americangroupllc.fashionfactory` |
| GadgetNest | `com.americangroupllc.gadgetnest` | `com.americangroupllc.gadgetnest` |
| GroceryMatch | `com.americangroupllc.grocerymatch` | `com.americangroupllc.grocerymatch` |
| HerJourney | `com.americangroupllc.herJourney` | `com.americangroupllc.herjourney` ⚠️ differs |
| HomeWise | `com.americangroupllc.homewise` | `com.americangroupllc.homewise` |
| iMaps | `com.americangroupllc.imaps` | `com.americangroupllc.imaps` |
| iMeasure | `com.americangroupllc.imeasure` | `com.americangroupllc.imeasure` |
| Kinnav | `com.americangroupllc.kinnav` | `com.americangroupllc.kinnav` |
| MileMaster | `com.americangroupllc.milemaster` | `com.americangroupllc.milemaster` |
| MyCard | `com.americangroupllc.mycard` | `com.americangroupllc.mycard` |
| MyFinance | `com.americangroupllc.myfinance` | `com.americangroupllc.myfinance` |
| MyHealth | `com.americangroupllc.myhealth` | `com.americangroupllc.myhealth` |
| NearServe | `com.americangroupllc.nearserve` | `com.americangroupllc.nearserve` |
| NewsBoard | `com.americangroupllc.newsboard` | `com.americangroupllc.newsboard` |
| NexusTransferPay | `com.americangroupllc.nexustransferpay` | `com.americangroupllc.nexustransferpay` |
| Photriya | `com.americangroupllc.photriya` | `com.americangroupllc.photriya` |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | `com.americangroupllc.pilotenroute` |
| PlantPulse | `com.americangroupllc.plantpulse` | `com.americangroupllc.plantpulse` |
| portfolio-board | `com.americangroupllc.portfolioboard` | `com.americangroupllc.portfolioboard` |
| radiotune | `com.americangroupllc.radiotune` | `com.americangroupllc.radiotune` |
| RideZap | `com.americangroupllc.ridezap` | `com.americangroupllc.ridezap` |
| RoomCraft | `com.americangroupllc.roomcraft` | `com.americangroupllc.roomcraft` |
| TripNest | `com.americangroupllc.tripnest` | `com.americangroupllc.tripnest` |
| Uscis-Case | `com.americangroupllc.usciscase` | `com.americangroupllc.usciscase` |
| Verba | `com.americangroupllc.verba` | `com.americangroupllc.verba` |
| VirtuBand | `com.americangroupllc.virtuband` | `com.americangroupllc.virtuband` |
| WiFiTrail | `com.americangroupllc.wifitrail` | `com.americangroupllc.wifitrail` |
| yourtube | `com.americangroupllc.yourtube` | `com.americangroupllc.yourtube` |

## HerJourney is the one exception

Its iOS bundle id keeps the capital J (`com.americangroupllc.herJourney`)
because the lowercase form is **not available** — Apple returned *"An App ID
with Identifier com.americangroupllc.herjourney is not available"* and never
releases a retired App ID. iOS and Android identifiers are independent
namespaces, so the Android side uses the lowercase form.

