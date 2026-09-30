# Play: taking each app out of Draft

Google Play has no API for this. Every one of the 34 apps with a live
internal release is refused production with Play's own words:

    Only releases with status draft may be created on draft app.

An app leaves Draft once its Console declarations are complete and a
person presses publish once. After that the API promotes freely, and
`python3 scripts/play_release.py --all --production` finishes all 34
in one run.

## Per app

| App | Play package | internal release | deletion URL to paste |
| --- | --- | --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` | live | https://www.safecodeg.com/policy/aeroswift/delete-account.html |
| AGCleaner | `com.americangroupllc.agcleaner` | live | https://www.safecodeg.com/policy/agcleaner/delete-account.html |
| AGrammarly | `com.americangroupllc.agrammarly` | live | https://www.safecodeg.com/policy/agrammarly/delete-account.html |
| AGRecorder | `com.americangroupllc.agrecorder` | live | https://www.safecodeg.com/policy/agrecorder/delete-account.html |
| AGStudio | `com.americangroupllc.agstudio` | live | https://www.safecodeg.com/policy/agstudio/delete-account.html |
| ApexMarketWatch | `com.americangroupllc.apexmarketwatch` | live | https://www.safecodeg.com/policy/apexmarketwatch/delete-account.html |
| BodyQuest | `com.americangroupllc.bodyquest` | live | https://www.safecodeg.com/policy/bodyquest/delete-account.html |
| BuddyPlay | `com.americangroupllc.buddyplay` | live | https://www.safecodeg.com/policy/buddyplay/delete-account.html |
| CalcMaster | `com.americangroupllc.calcmaster` | live | https://www.safecodeg.com/policy/calcmaster/delete-account.html |
| CarDeal | `com.americangroupllc.cardeal` | — | https://www.safecodeg.com/policy/cardeal/delete-account.html |
| ChefCount | `com.americangroupllc.chefcount` | live | https://www.safecodeg.com/policy/chefcount/delete-account.html |
| CodeDeal | `com.americangroupllc.codedeal` | live | https://www.safecodeg.com/policy/codedeal/delete-account.html |
| daily-pulse | `com.americangroupllc.dailypulse` | live | https://www.safecodeg.com/policy/dailypulse/delete-account.html |
| DriftDate | `com.americangroupllc.driftdate` | live | https://www.safecodeg.com/policy/driftdate/delete-account.html |
| EventSpark | `com.americangroupllc.eventspark` | live | https://www.safecodeg.com/policy/eventspark/delete-account.html |
| FashionFactory | `com.americangroupllc.fashionfactory` | live | https://www.safecodeg.com/policy/fashionfactory/delete-account.html |
| GadgetNest | `com.americangroupllc.gadgetnest` | live | https://www.safecodeg.com/policy/gadgetnest/delete-account.html |
| GroceryMatch | `com.americangroupllc.grocerymatch` | — | https://www.safecodeg.com/policy/grocerymatch/delete-account.html |
| HerJourney | `com.americangroupllc.herjourney` | live | https://www.safecodeg.com/policy/herjourney/delete-account.html |
| HomeWise | `com.americangroupllc.homewise` | — | https://www.safecodeg.com/policy/homewise/delete-account.html |
| iMaps | `com.americangroupllc.imaps` | — | https://www.safecodeg.com/policy/iMaps/delete-account.html |
| iMeasure | `com.americangroupllc.imeasure` | — | https://www.safecodeg.com/policy/iMeasure/delete-account.html |
| Kinnav | `com.americangroupllc.kinnav` | live | https://www.safecodeg.com/policy/kinnav/delete-account.html |
| MileMaster | `com.americangroupllc.milemaster` | live | https://www.safecodeg.com/policy/milemaster/delete-account.html |
| MyCard | `com.americangroupllc.mycard` | live | https://www.safecodeg.com/policy/mycard/delete-account.html |
| MyFinance | `com.americangroupllc.myfinance` | live | https://www.safecodeg.com/policy/myfinance/delete-account.html |
| MyHealth | `com.americangroupllc.myhealth` | live | https://www.safecodeg.com/policy/myhealth/delete-account.html |
| NearServe | `com.americangroupllc.nearserve` | live | https://www.safecodeg.com/policy/nearserve/delete-account.html |
| NewsBoard | `com.americangroupllc.newsboard` | live | https://www.safecodeg.com/policy/newsboard/delete-account.html |
| NexusTransferPay | `com.americangroupllc.nexustransferpay` | live | https://www.safecodeg.com/policy/nexustransferpay/delete-account.html |
| Photriya | `com.americangroupllc.photriya` | live | https://www.safecodeg.com/policy/photriya/delete-account.html |
| PilotEnRoute | `com.americangroupllc.pilotenroute` | live | https://www.safecodeg.com/policy/pilotenroute/delete-account.html |
| PlantPulse | `com.americangroupllc.plantpulse` | live | https://www.safecodeg.com/policy/plantpulse/delete-account.html |
| portfolio-board | `com.americangroupllc.portfolioboard` | live | https://www.safecodeg.com/policy/portfolio-board/delete-account.html |
| radiotune | `com.americangroupllc.radiotune` | live | https://www.safecodeg.com/policy/radiotune/delete-account.html |
| RideZap | `com.americangroupllc.ridezap` | live | https://www.safecodeg.com/policy/ridezap/delete-account.html |
| RoomCraft | `com.americangroupllc.roomcraft` | live | https://www.safecodeg.com/policy/roomcraft/delete-account.html |
| TripNest | `com.americangroupllc.tripnest` | — | https://www.safecodeg.com/policy/TripNest/delete-account.html |
| Uscis-Case | `com.americangroupllc.usciscase` | — | https://www.safecodeg.com/policy/uscis-case-tracker/delete-account.html |
| Verba | `com.americangroupllc.verba` | — | https://www.safecodeg.com/policy/verba/delete-account.html |
| VirtuBand | `com.americangroupllc.virtuband` | — | https://www.safecodeg.com/policy/virtuband/delete-account.html |
| WiFiTrail | `com.americangroupllc.wifitrail` | live | https://www.safecodeg.com/policy/wifitrail/delete-account.html |
| yourtube | `com.americangroupllc.yourtube` | live | https://www.safecodeg.com/policy/yourtube/delete-account.html |

34 of 43 have a live internal release and are ready to publish.

## What to do, per app

Play Console -> the app -> Policy -> App content, and complete:

1. **Data safety** — paste the deletion URL from the table above. This is
   also the fix for Google's rejection notice; the old
   `americangroupllc.github.io` URL is a 404 and the new one is verified live.
2. **Content rating (IARC)** — the questionnaire. No API exists for it.
3. **Target audience and content**, **Ads declaration**, **App access**
   (no login is required in any of these apps).
4. Then Production -> Create release -> the bundle is already uploaded ->
   review and roll out.

Only step 4 needs doing once; after the first publish this repository can
do the rest unattended.
