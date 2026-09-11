# App Store Connect records

Live from the API on the last sync: **40 app records exist**,
and **29 of 42** match a bundle id this portfolio
actually builds. Refresh with `bundle exec ruby scripts/appstore_records.rb`.

This matters because a bundle id that does not match a record is not a
warning at upload time — it is a rejected build.

## Matched

| # | App | Bundle id | Store record |
| --: | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | AGCleaner |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | AGRecorder |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | BodyQuest |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | Calculator: World Class |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | iCarDeal |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | ChefCount |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | CodeDeal |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | iDriftDate |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | iEventSpark |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.styleradar` | StyleRadar |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | iHomeWise |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | iMaps Route |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | iMileMaster |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | iMyFinance |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | NearServe |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | Photriya Camera Colors |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | PilotEnRoute |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.radiotune` | RadioTune World |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | RideZap |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | iRoomCraft |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | TravelZap |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | USCIS Case Lookup |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | VirtuBand |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | WifiTrail |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | YourTube: Watch & Discover |
| 38 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `com.americangroupllc.agstudio` | AGStudio |
| 39 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `com.americangroupllc.apexmarketwatch` | ApexMarketWatch |
| 40 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `com.americangroupllc.buddyplay` | iBuddyPlay |
| 41 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `com.americangroupllc.mycard` | iMyCard |

## No matching record

Each of these needs a record created — or, where the app was renamed, the
existing record below reused by changing the app's bundle id back to it.
A bundle id is permanent once published, so decide before the first upload.

| # | App | Bundle id it builds with |
| --: | --- | --- |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | `com.americangroupllc.herJourney` |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` |
| 37 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` |
| 42 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` |

## Records with no app

Mostly the portfolio's rename history — FoodRadar became GroceryMatch,
OfflineBuddy became Verba, DealZap became GadgetNest, StayDeal became
TripNest. Each is a decision: rename the record and keep its history, or
leave it and create a new one.

| Bundle id | Store record |
| --- | --- |
| `com.americangroup.daily-pulse` | daily-pulse |
| `com.americangroupllc.Mykarma` | iMykarma |
| `com.americangroupllc.agrammarly` | AGrammarly |
| `com.americangroupllc.careerupgradeai` | CareerUpgradeAI |
| `com.americangroupllc.dealzap` | iDealZap |
| `com.americangroupllc.foodradar` | iFoodRadar |
| `com.americangroupllc.kinnav` | Kinnav |
| `com.americangroupllc.newsboard` | iNewsBoard |
| `com.americangroupllc.nexustransferpay` | NexusTransferPay |
| `com.americangroupllc.offlinebuddy` | OfflineBuddy |
| `com.americangroupllc.staydeal` | StayDeal |
