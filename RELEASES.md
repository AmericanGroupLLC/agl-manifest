# Release binaries

All 42 mobile apps in the organization: what each one is, where it
stands, and what you can download and run right now. Regenerate with
`python3 scripts/status.py`. Also published as
[`releases.csv`](releases.csv) for a spreadsheet.

The package name in each row is what AdMob, Play, App Store Connect and
`keytool` all ask for, so this table is the one to work from when creating
AdMob entries, upload keys or store records.

`artifacts.yml` publishes the binaries — an APK that installs on a device, the
AAB Play needs, and for iOS a simulator build. A `.aab` **cannot** be
sideloaded; it is a Play upload format, which is why both are published. The
iOS build is unsigned, so it runs in the Simulator and not on a phone —
TestFlight is the only route to real hardware.

| # | App | Package / bundle id | Status | Android | iOS | Ads | Login | Build | Binaries |
| --: | --- | --- | --- | :-: | :-: | :-: | --- | --- | --- |
| 1 | [AGCleaner](https://github.com/AmericanGroupLLC/AGCleaner) | `com.americangroupllc.agcleaner` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 2 | [AGrammarly](https://github.com/AmericanGroupLLC/AGrammarly) | `com.americangroup.agrammarly` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 3 | [AGRecorder](https://github.com/AmericanGroupLLC/AGRecorder) | `com.americangroupllc.agrecorder` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 4 | [BodyQuest](https://github.com/AmericanGroupLLC/BodyQuest) | `com.americangroup.bodyquest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | no release | — |
| 5 | [CalcMaster](https://github.com/AmericanGroupLLC/CalcMaster) | `com.americangroupllc.calcmaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | v1.0.0 | **none — tag only** |
| 6 | [CarDeal](https://github.com/AmericanGroupLLC/CarDeal) | `com.americangroupllc.cardeal` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 7 | [ChefCount](https://github.com/AmericanGroupLLC/ChefCount) | `com.americangroupllc.chefcount` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 8 | [CodeDeal](https://github.com/AmericanGroupLLC/CodeDeal) | `com.americangroupllc.codedeal` | Does not compile — 5 analyzer errors | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 9 | [daily-pulse](https://github.com/AmericanGroupLLC/daily-pulse) | `com.americangroup.dailypulse` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (optional) | no release | — |
| 10 | [DriftDate](https://github.com/AmericanGroupLLC/DriftDate) | `com.americangroupllc.driftdate` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple | v1.0.0 | **none — tag only** |
| 11 | [EventSpark](https://github.com/AmericanGroupLLC/EventSpark) | `com.americangroupllc.eventspark` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 12 | [FashionFactory](https://github.com/AmericanGroupLLC/FashionFactory) | `com.americangroupllc.styleradar` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | no release | — |
| 13 | [GadgetNest](https://github.com/AmericanGroupLLC/GadgetNest) | `com.americangroupllc.gadgetnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | no release | — |
| 14 | [GroceryMatch](https://github.com/AmericanGroupLLC/GroceryMatch) | `com.americangroupllc.grocerymatch` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | v1.0.0 | **none — tag only** |
| 15 | [HerJourney](https://github.com/AmericanGroupLLC/HerJourney) | A `com.americangroupllc.her_journey`<br>i `com.americangroupllc.herJourney` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Google + Apple (no screen) | no release | — |
| 16 | [HomeWise](https://github.com/AmericanGroupLLC/HomeWise) | `com.americangroupllc.homewise` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 17 | [iMaps](https://github.com/AmericanGroupLLC/iMaps) | `com.americangroupllc.imaps` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | v1.0.0 | **none — tag only** |
| 18 | [iMeasure](https://github.com/AmericanGroupLLC/iMeasure) | `com.americangroupllc.imeasure` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | v1.0.0 | **none — tag only** |
| 19 | [MileMaster](https://github.com/AmericanGroupLLC/MileMaster) | `com.americangroupllc.milemaster` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 20 | [MyFinance](https://github.com/AmericanGroupLLC/MyFinance) | `com.americangroupllc.myfinance` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 21 | [MyHealth](https://github.com/AmericanGroupLLC/MyHealth) | `com.americangroupllc.myhealth` | Binary published | yes | yes | — | Supabase + Google + Apple (optional) | v1.1.0 | `myhealth-server-v1.1.0.tar.gz`, `MyHealth-web-v1.1.0.tar.gz` |
| 22 | [NearServe](https://github.com/AmericanGroupLLC/NearServe) | `com.americangroupllc.nearserve` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 23 | [NewsBoard](https://github.com/AmericanGroupLLC/NewsBoard) | `com.americangroup.newsboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 24 | [NexusTransferPay](https://github.com/AmericanGroupLLC/NexusTransferPay) | `com.americangroupllc.nexuspay` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Biometric (no screen) | v1.0.0 | **none — tag only** |
| 25 | [Photriya](https://github.com/AmericanGroupLLC/Photriya) | `com.americangroupllc.photriya` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | Supabase + Firebase + Google + Apple (optional) | v1.0.0 | **none — tag only** |
| 26 | [PilotEnRoute](https://github.com/AmericanGroupLLC/PilotEnRoute) | `com.americangroupllc.pilotenroute` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | no release | — |
| 27 | [portfolio-board](https://github.com/AmericanGroupLLC/portfolio-board) | `com.americangroupllc.portfolioboard` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 28 | [radiotune](https://github.com/AmericanGroupLLC/radiotune) | `com.americangroup.ratiotune` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple | no release | — |
| 29 | [RideZap](https://github.com/AmericanGroupLLC/RideZap) | `com.americangroupllc.ridezap` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 30 | [RoomCraft](https://github.com/AmericanGroupLLC/RoomCraft) | `com.americangroupllc.roomcraft` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 31 | [TripNest](https://github.com/AmericanGroupLLC/TripNest) | `com.americangroupllc.tripnest` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | no release | — |
| 32 | [Uscis-Case](https://github.com/AmericanGroupLLC/Uscis-Case) | `com.americangroupllc.usciscase` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | v1.0.0 | **none — tag only** |
| 33 | [Verba](https://github.com/AmericanGroupLLC/Verba) | `com.americangroupllc.verba` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | none | v1.0.0 | **none — tag only** |
| 34 | [VirtuBand](https://github.com/AmericanGroupLLC/VirtuBand) | `com.americangroupllc.virtuband` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase (optional) | v1.0.0 | **none — tag only** |
| 35 | [WiFiTrail](https://github.com/AmericanGroupLLC/WiFiTrail) | `com.americangroupllc.wifitrail` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | — | none | v1.0.0 | **none — tag only** |
| 36 | [yourtube](https://github.com/AmericanGroupLLC/yourtube) | `com.americangroup.yourtube` | Ready — needs AGL_PACKAGES_TOKEN | yes | yes | yes | Supabase + Google + Apple (optional) | no release | — |
| 37 | [AeroSwift](https://github.com/AmericanGroupLLC/AeroSwift) | `com.americangroupllc.aeroswift` _(reserved)_ | Not ported | — | — | — | — | — | — |
| 38 | [AGStudio](https://github.com/AmericanGroupLLC/AGStudio) | `com.americangroupllc.agstudio` _(reserved)_ | Not ported | — | — | — | — | — | — |
| 39 | [ApexMarketWatch](https://github.com/AmericanGroupLLC/ApexMarketWatch) | `com.americangroupllc.apexmarketwatch` _(reserved)_ | Not ported | — | — | — | — | — | — |
| 40 | [BuddyPlay](https://github.com/AmericanGroupLLC/BuddyPlay) | `com.americangroupllc.buddyplay` _(reserved)_ | Not ported | — | — | — | — | — | — |
| 41 | [MyCard](https://github.com/AmericanGroupLLC/MyCard) | `com.americangroupllc.mycard` _(reserved)_ | Not ported | — | — | — | — | — | — |
| 42 | [PlantPulse](https://github.com/AmericanGroupLLC/PlantPulse) | `com.americangroupllc.plantpulse` _(reserved)_ | Not ported | — | — | — | — | — | — |

**1 of 42 apps have a binary anyone can download.** 27 carry a release tag, so most of those tags are empty — they look like a release on the Releases page with nothing attached to install. 36 apps are Flutter and buildable; 6 are not ported yet and have no Flutter package name to register anywhere.

## Not in the organization

Still delivered by this manifest, but the repository is owned elsewhere and
reachable only through a GitHub redirect. If that redirect is ever removed,
delivery for it stops.

| App | Where it lives now | Package |
| --- | --- | --- |
| Kinnav | `transferred to srpatcha/Kinnav; pushes follow a redirect` | `com.americangroupllc.kinnav` |

## Producing the binaries

```sh
# from the Actions tab: “Publish test builds”, or locally:
bundle exec fastlane publish_artifacts platform:android apps:all
bundle exec fastlane publish_artifacts platform:ios apps:all
```

Nothing will publish until `AGL_PACKAGES_TOKEN` exists with **write** access —
see [PENDING.md](PENDING.md).
