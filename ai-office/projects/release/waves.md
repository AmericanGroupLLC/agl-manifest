# Delivery waves

Founder rule (2026-10-13): deliver now only the apps that can reach production with their AdMob IDs alone. Apps that need a vendor token or partner ID wait until the founder has it (`store/vendors/AGL_Vendor_Signup_Playbook.xlsx`).

Measured 2026-10-13 from the app code (`scripts/api_vendor_audit.py`, placeholder grep) and AdMob (86 apps exist, `admob_setup.py --dry-run`). Apps are still being reworked (issue #24), so re-measure before each release.

## Wave 1 — deliver now (34)

AGCleaner, AGRecorder, AGStudio, AGrammarly, AeroSwift, ApexMarketWatch, BodyQuest, BuddyPlay, CalcMaster, CarDeal, CodeDeal, EventSpark, FashionFactory, GadgetNest, GroceryMatch, HerJourney, HomeWise, Kinnav, MileMaster, MyCard, MyFinance, MyHealth, NearServe, NewsBoard, NexusTransferPay, Photriya, PlantPulse, RideZap, RoomCraft, Verba, WiFiTrail, daily-pulse, portfolio-board, yourtube

No ads SDK, so they ship ad-free: AGrammarly, Kinnav.

Still required before production (not vendor-related): Real Apps QA pass (#24), the pre-delivery checklist with a device sign-off, Apple's 5.6 freeze lifted (#13) and the agreement accepted (#33), Play App content declarations, and for apps with accounts the backend items (#12, #14).

## Wave 2 — wait for a vendor token (9)

| App | Waiting for |
| --- | --- |
| ChefCount | Amazon Associates tag (current tag=americangroupllc is not a valid store ID) |
| DriftDate | Google iOS OAuth client ID |
| PilotEnRoute | Google iOS OAuth client ID; Anthropic API key (server-side) |
| TripNest | Travelpayouts numeric marker |
| Uscis-Case | Google iOS OAuth client ID |
| VirtuBand | Amazon Associates tag (virtuband-20 not verified as registered); AI_API_KEY provider |
| iMaps | Google iOS OAuth client ID; NASA FIRMS key; Open Charge Map key |
| iMeasure | Google iOS OAuth client ID |
| radiotune | Google iOS OAuth client ID |

Six of the nine need only a Google iOS OAuth client ID (free, one Google Cloud console session, batch 3 of the playbook).
