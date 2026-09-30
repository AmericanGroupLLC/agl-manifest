# Play: what is left, per app

Measured 43 apps against the Play API. Re-run
`python3 scripts/play_gap_audit.py` rather than trusting these numbers.

- **6** already have a *completed* production release
- **35** have the release **staged as draft on the production track** —
  the bundle is in place and goes live the moment the app is published
- **4** still have a gap the API can reach

## Why every app refuses production

```
Only releases with status draft may be created on draft app.
```

It is not a missing field. Each app is a *Draft app* in Console and stays
that way until five declarations are answered and a person publishes once.
None of the five has an API — verified against Play's discovery document,
which exposes 145 methods and no way to publish an app:

1. Content rating (IARC)
2. Data safety — paste the deletion URL below
3. Target audience and content
4. Ads declaration
5. App access (no app here requires a login)

Everything else is done. Listings, descriptions, icons, feature graphics,
screenshots, contact details, country availability and the production
release itself are all in place, written through the API.

## Per app

| App | production track | API gap | deletion URL for Data safety |
| --- | --- | --- | --- |
| AeroSwift | draft | — | https://www.safecodeg.com/policy/aeroswift/delete-account.html |
| AGCleaner | draft | — | https://www.safecodeg.com/policy/agcleaner/delete-account.html |
| AGrammarly | draft | — | https://www.safecodeg.com/policy/agrammarly/delete-account.html |
| AGRecorder | draft | — | https://www.safecodeg.com/policy/agrecorder/delete-account.html |
| AGStudio | draft | — | https://www.safecodeg.com/policy/agstudio/delete-account.html |
| ApexMarketWatch | draft | — | https://www.safecodeg.com/policy/apexmarketwatch/delete-account.html |
| BodyQuest | draft | — | https://www.safecodeg.com/policy/bodyquest/delete-account.html |
| BuddyPlay | draft | — | https://www.safecodeg.com/policy/buddyplay/delete-account.html |
| CalcMaster | completed | — | https://www.safecodeg.com/policy/calcmaster/delete-account.html |
| CarDeal | draft | no production release | https://www.safecodeg.com/policy/cardeal/delete-account.html |
| ChefCount | draft | — | https://www.safecodeg.com/policy/chefcount/delete-account.html |
| CodeDeal | draft | — | https://www.safecodeg.com/policy/codedeal/delete-account.html |
| daily-pulse | draft | phoneScreenshots(1) | https://www.safecodeg.com/policy/dailypulse/delete-account.html |
| DriftDate | draft | — | https://www.safecodeg.com/policy/driftdate/delete-account.html |
| EventSpark | draft | — | https://www.safecodeg.com/policy/eventspark/delete-account.html |
| FashionFactory | draft | — | https://www.safecodeg.com/policy/fashionfactory/delete-account.html |
| GadgetNest | draft | — | https://www.safecodeg.com/policy/gadgetnest/delete-account.html |
| GroceryMatch | no Play entry | — | https://www.safecodeg.com/policy/grocerymatch/delete-account.html |
| HerJourney | draft | — | https://www.safecodeg.com/policy/herjourney/delete-account.html |
| HomeWise | draft | — | https://www.safecodeg.com/policy/homewise/delete-account.html |
| iMaps | completed | — | https://www.safecodeg.com/policy/iMaps/delete-account.html |
| iMeasure | completed | — | https://www.safecodeg.com/policy/iMeasure/delete-account.html |
| Kinnav | none | phoneScreenshots(1), no production release | https://www.safecodeg.com/policy/kinnav/delete-account.html |
| MileMaster | draft | — | https://www.safecodeg.com/policy/milemaster/delete-account.html |
| MyCard | draft | — | https://www.safecodeg.com/policy/mycard/delete-account.html |
| MyFinance | draft | — | https://www.safecodeg.com/policy/myfinance/delete-account.html |
| MyHealth | draft | — | https://www.safecodeg.com/policy/myhealth/delete-account.html |
| NearServe | draft | — | https://www.safecodeg.com/policy/nearserve/delete-account.html |
| NewsBoard | draft | — | https://www.safecodeg.com/policy/newsboard/delete-account.html |
| NexusTransferPay | draft | — | https://www.safecodeg.com/policy/nexustransferpay/delete-account.html |
| Photriya | draft | — | https://www.safecodeg.com/policy/photriya/delete-account.html |
| PilotEnRoute | draft | — | https://www.safecodeg.com/policy/pilotenroute/delete-account.html |
| PlantPulse | draft | — | https://www.safecodeg.com/policy/plantpulse/delete-account.html |
| portfolio-board | draft | — | https://www.safecodeg.com/policy/portfolio-board/delete-account.html |
| radiotune | draft | — | https://www.safecodeg.com/policy/radiotune/delete-account.html |
| RideZap | draft | — | https://www.safecodeg.com/policy/ridezap/delete-account.html |
| RoomCraft | draft | — | https://www.safecodeg.com/policy/roomcraft/delete-account.html |
| TripNest | completed | — | https://www.safecodeg.com/policy/TripNest/delete-account.html |
| Uscis-Case | completed | — | https://www.safecodeg.com/policy/uscis-case-tracker/delete-account.html |
| Verba | draft | phoneScreenshots(1) | https://www.safecodeg.com/policy/verba/delete-account.html |
| VirtuBand | completed | — | https://www.safecodeg.com/policy/virtuband/delete-account.html |
| WiFiTrail | draft | — | https://www.safecodeg.com/policy/wifitrail/delete-account.html |
| yourtube | draft | — | https://www.safecodeg.com/policy/yourtube/delete-account.html |

## The three that need something first

| App | What |
| --- | --- |
| CarDeal | Upload key mismatch, so it has no bundle at all — MA-020, console reset |
| GroceryMatch | No Play entry exists — MA-021 |
| Kinnav, daily-pulse, Verba | One phone screenshot; Play wants two |

## After the first publish

```
python3 scripts/play_release.py --all --production
```

finishes every remaining app without further help.
