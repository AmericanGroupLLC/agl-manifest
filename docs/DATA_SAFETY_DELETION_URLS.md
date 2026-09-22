# Play Data safety — account deletion URLs

Google flagged VirtuBand on 2026-09-21: the account-deletion URL in its Data
safety form returns 404 because it points at `americangroupllc.github.io`,
which is retired. Deadline **2026-09-24**.

The Data safety form is console-only — there is no Play API for it — so these
must be pasted by hand, per app, at:

  Play Console → the app → Policy → App content → Data safety →
  *Data collection and security* → **Account deletion URL**

Every URL below was generated from the live site checkout and all 43 pages are
committed to the website's `deploy` branch. **They go live only after cPanel →
Git Version Control → Deploy HEAD Commit is run** — verify one in a browser
before pasting the rest.

Do not trust an HTTP 200 when checking these. The host serves an SPA catch-all,
so an absent page still answers 200 with the marketing homepage; compare the
response body against a path you know does not exist.

| App | Play package | Account deletion URL |
| --- | --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` | https://www.safecodeg.com/policy/aeroswift/delete-account.html |
| AGCleaner | `com.americangroupllc.agcleaner` | https://www.safecodeg.com/policy/agcleaner/delete-account.html |
| AGrammarly | `com.americangroupllc.agrammarly` | https://www.safecodeg.com/policy/agrammarly/delete-account.html |
| AGRecorder | `com.americangroupllc.agrecorder` | https://www.safecodeg.com/policy/agrecorder/delete-account.html |
| AGStudio | `com.americangroupllc.agstudio` | https://www.safecodeg.com/policy/agstudio/delete-account.html |
| ApexMarketWatch | `com.americangroupllc.apexmarketwatch` | https://www.safecodeg.com/policy/apexmarketwatch/delete-account.html |
| BodyQuest | `com.americangroupllc.bodyquest` | https://www.safecodeg.com/policy/bodyquest/delete-account.html |
| BuddyPlay | `com.americangroupllc.buddyplay` | https://www.safecodeg.com/policy/buddyplay/delete-account.html |
| CalcMaster | `com.americangroupllc.calcmaster` | https://www.safecodeg.com/policy/calcmaster/delete-account.html |
| CarDeal | `com.americangroupllc.cardeal` | https://www.safecodeg.com/policy/cardeal/delete-account.html |
| ChefCount | `com.americangroupllc.chefcount` | https://www.safecodeg.com/policy/chefcount/delete-account.html |
| CodeDeal | `com.americangroupllc.codedeal` | https://www.safecodeg.com/policy/codedeal/delete-account.html |
| daily-pulse | `com.americangroupllc.dailypulse` | https://www.safecodeg.com/policy/dailypulse/delete-account.html |
| DriftDate | `com.americangroupllc.driftdate` | https://www.safecodeg.com/policy/driftdate/delete-account.html |
| EventSpark | `com.americangroupllc.eventspark` | https://www.safecodeg.com/policy/eventspark/delete-account.html |
| FashionFactory | `com.americangroupllc.fashionfactory` | https://www.safecodeg.com/policy/fashionfactory/delete-account.html |
| GadgetNest | `com.americangroupllc.gadgetnest` | https://www.safecodeg.com/policy/gadgetnest/delete-account.html |
| GroceryMatch | `com.americangroupllc.grocerymatch` | https://www.safecodeg.com/policy/grocerymatch/delete-account.html |
| HerJourney | `com.americangroupllc.herjourney` | https://www.safecodeg.com/policy/herjourney/delete-account.html |
| HomeWise | `com.americangroupllc.homewise` | https://www.safecodeg.com/policy/homewise/delete-account.html |
| iMaps | `com.americangroupllc.imaps` | https://www.safecodeg.com/policy/iMaps/delete-account.html |
| iMeasure | `com.americangroupllc.imeasure` | https://www.safecodeg.com/policy/iMeasure/delete-account.html |
| Kinnav | `com.americangroupllc.kinnav` | https://www.safecodeg.com/policy/kinnav/delete-account.html |
| MileMaster | `com.americangroupllc.milemaster` | https://www.safecodeg.com/policy/milemaster/delete-account.html |
| MyCard | `com.americangroupllc.mycard` | https://www.safecodeg.com/policy/mycard/delete-account.html |
| MyFinance | `com.americangroupllc.myfinance` | https://www.safecodeg.com/policy/myfinance/delete-account.html |
| MyHealth | `com.americangroupllc.myhealth` | https://www.safecodeg.com/policy/myhealth/delete-account.html |
| NearServe | `com.americangroupllc.nearserve` | https://www.safecodeg.com/policy/nearserve/delete-account.html |
| NewsBoard | `com.americangroupllc.newsboard` | https://www.safecodeg.com/policy/newsboard/delete-account.html |
| NexusTransferPay | `com.americangroupllc.nexustransferpay` | https://www.safecodeg.com/policy/nexustransferpay/delete-account.html |
| Photriya | `com.americangroupllc.photriya` | https://www.safecodeg.com/policy/photriya/delete-account.html |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | https://www.safecodeg.com/policy/pilotenroute/delete-account.html |
| PlantPulse | `com.americangroupllc.plantpulse` | https://www.safecodeg.com/policy/plantpulse/delete-account.html |
| portfolio-board | `com.americangroupllc.portfolioboard` | https://www.safecodeg.com/policy/portfolio-board/delete-account.html |
| radiotune | `com.americangroupllc.radiotune` | https://www.safecodeg.com/policy/radiotune/delete-account.html |
| RideZap | `com.americangroupllc.ridezap` | https://www.safecodeg.com/policy/ridezap/delete-account.html |
| RoomCraft | `com.americangroupllc.roomcraft` | https://www.safecodeg.com/policy/roomcraft/delete-account.html |
| TripNest | `com.americangroupllc.tripnest` | https://www.safecodeg.com/policy/TripNest/delete-account.html |
| Uscis-Case | `com.americangroupllc.usciscase` | https://www.safecodeg.com/policy/uscis-case-tracker/delete-account.html |
| Verba | `com.americangroupllc.verba` | https://www.safecodeg.com/policy/verba/delete-account.html |
| VirtuBand | `com.americangroupllc.virtuband` | https://www.safecodeg.com/policy/virtuband/delete-account.html |
| WiFiTrail | `com.americangroupllc.wifitrail` | https://www.safecodeg.com/policy/wifitrail/delete-account.html |
| yourtube | `com.americangroupllc.yourtube` | https://www.safecodeg.com/policy/yourtube/delete-account.html |
