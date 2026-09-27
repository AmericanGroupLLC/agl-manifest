# AdMob: 8 of 86 ids exist

Measured 2026-09-26 against `accounts/pub-8528784688453695`. One AdMob app is
needed per platform for 43 apps — **86 ids, of which 8 exist and 78 are
missing**. Only CalcMaster has both platforms; six others have Android only.

Creation is refused, retested today (MA-027). The API reads the account fine,
and `POST /v1beta/accounts/{pub}/apps` answers:

```
403  The caller does not have permission  (PERMISSION_DENIED)
```

`scripts/admob_setup.py` creates all 86 plus a banner and interstitial unit for
each, and writes the ids into `docs/admob-ids.json`, as soon as that is granted.
The AdMob console cannot be automated either: the page never reaches
`document_idle`, so the browser extension's content script never runs.

| App | AdMob name | Android | iOS |
| --- | --- | --- | --- |
| AeroSwift | AeroSwift | **missing** | **missing** |
| AGCleaner | AGCleaner | **missing** | **missing** |
| AGrammarly | AGrammarly: Reply Helper | **missing** | **missing** |
| AGRecorder | AGRecorder | **missing** | **missing** |
| AGStudio | AGStudio | **missing** | **missing** |
| ApexMarketWatch | ApexMarketWatch | **missing** | **missing** |
| BodyQuest | BodyQuest: Health Game | **missing** | **missing** |
| BuddyPlay | iBuddyPlay | **missing** | **missing** |
| CalcMaster | CalcMaster: World Calc | ca-app-pub-8528784688453695~5377349094 | ca-app-pub-8528784688453695~9148987425 |
| CarDeal | iCarDeal | **missing** | **missing** |
| ChefCount | ChefCount | **missing** | **missing** |
| CodeDeal | CodeDeal | **missing** | **missing** |
| daily-pulse | Daily Pulse: Morning Brief | **missing** | **missing** |
| DriftDate | DriftDate: Layered Dating | **missing** | **missing** |
| EventSpark | iEventSpark | **missing** | **missing** |
| FashionFactory | Fashion Factory: Deals | **missing** | **missing** |
| GadgetNest | GadgetNest | **missing** | **missing** |
| GroceryMatch | GroceryMatch: Save on Food | **missing** | **missing** |
| HerJourney | HerJourney: Cycle & Health | **missing** | **missing** |
| HomeWise | iHomeWise | **missing** | **missing** |
| iMaps | iMaps: Navigate & Report | ca-app-pub-8528784688453695~5082647691 | **missing** |
| iMeasure | iMeasure: Measure & Level | ca-app-pub-8528784688453695~9265279754 | **missing** |
| Kinnav | Kinnav | **missing** | **missing** |
| MileMaster | iMileMaster | **missing** | **missing** |
| MyCard | iMyCard | **missing** | **missing** |
| MyFinance | iMyFinance | **missing** | **missing** |
| MyHealth | MyHealth: Fitness Tracker | **missing** | **missing** |
| NearServe | NearServe | **missing** | **missing** |
| NewsBoard | iNewsBoard | **missing** | **missing** |
| NexusTransferPay | NexusTransferPay | **missing** | **missing** |
| Photriya | Photriya | **missing** | **missing** |
| PilotEnRoute | PilotEnRoute: Pilot Training | **missing** | **missing** |
| PlantPulse | PlantPulse | **missing** | **missing** |
| portfolio-board | Portfolio Board | **missing** | **missing** |
| radiotune | Radio Tune: Live Radio | ca-app-pub-8528784688453695~7770953426 | **missing** |
| RideZap | RideZap | **missing** | **missing** |
| RoomCraft | iRoomCraft | **missing** | **missing** |
| TripNest | TripNest: Travel Booking | ca-app-pub-8528784688453695~8044208178 | **missing** |
| Uscis-Case | USCIS Case Lookup | ca-app-pub-8528784688453695~2309537905 | **missing** |
| Verba | Verba: Voice Translator | **missing** | **missing** |
| VirtuBand | VirtuBand: Music Studio | ca-app-pub-8528784688453695~2836542125 | **missing** |
| WiFiTrail | WiFiTrail | **missing** | **missing** |
| yourtube | YourTube: Watch & Discover | **missing** | **missing** |
