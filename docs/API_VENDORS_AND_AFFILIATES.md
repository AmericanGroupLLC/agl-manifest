# API vendors, affiliate programmes and missing tokens

Measured 2026-10-12 from the app source (`scripts/api_vendor_audit.py` →
`docs/api-vendor-keys.json`, which has every key with file:line). Regenerate the
JSON rather than editing counts here.

**The headline:** the apps read **61** build-time credentials across **27** apps,
and **51 are empty in every release build**. The delivery path
(`build_release.py`, `build_ipa.py`, `ship.yml`) passes only AdMob unit ids, and
the repo's GitHub secrets hold no third-party key at all. So every feature
behind those keys is off in what users get, and **no affiliate programme is
earning today**. Signing up is a founder action (Charter §4: accounts and
credentials).

Signup URLs are the vendors' public portals as known on 2026-10-12; they were
not fetched in this pass.

## 1. Affiliate and commission programmes (these earn money)

| Programme | Sign up | Apps wired for it | What the code carries today | What you get, and where it goes |
| --- | --- | --- | --- | --- |
| **Amazon Associates** | affiliate-program.amazon.com | BodyQuest, CalcMaster, VirtuBand, ChefCount, FashionFactory | Hard-coded tags that are not known to be registered: `bodyquest-20` (BodyQuest `lib/screens/shop_screen.dart`, 7 links), `calcmaster-20`/`-21` (CalcMaster `lib/monetization/monetization_config.dart`, marked `// REPLACE`), `virtuband-20` (VirtuBand `lib/services/monetization.dart`), `americangroupllc` (ChefCount `lib/domain/models.dart:91`, no region suffix, so not a valid store id). FashionFactory reads `AGL_AFFILIATE_TAGS`, which is empty | One Associates account, one tracking id per app. Amazon closes accounts with no 3 qualifying sales in the first 180 days |
| **Travelpayouts** (flights, hotels, cars, buses, tours, tickets) | travelpayouts.com | TripNest, EventSpark | Marker `americangroupllc` (`TRIPNEST_AFFILIATE_MARKER`, `EVENTSPARK_AFFILIATE_MARKER` defaults) on `*.tp.st/click` links. Travelpayouts markers are numeric partner ids, so these clicks almost certainly earn nothing | Numeric marker, and joining each brand programme (Viator, Ticketmaster, Eventbrite, car hire, buses) inside the dashboard |
| **Impact.com** | impact.com (partner sign-up) | GroceryMatch (DoorDash, Uber Eats, Grubhub), VirtuBand | `DOORDASH_AFFILIATE_ID`, `UBEREATS_AFFILIATE_ID`, `GRUBHUB_AFFILIATE_ID` all empty, so links open the plain sites. `AFFILIATE_SUB_ID=americangroupllc` is only a sub-id | Publisher id plus per-brand approval. Each brand's programme being open was not verified |
| **Rakuten Advertising** | rakutenadvertising.com (publishers) | FashionFactory (Nordstrom, Macy's, Jomashop), VirtuBand | Nothing configured (`AGL_AFFILIATE_TAGS` empty) | Publisher site id, then brand approvals |
| **Awin** | awin.com | FashionFactory (Zalando, ASOS) | Nothing configured | Publisher id (Awin charges a small refundable deposit at sign-up) |
| **Expedia Group affiliate** | affiliates.expediagroup.com | RideZap, TripNest | RideZap hard-codes `affiliateId = 'americangroupllc'` (`mobile/lib/services/affiliate_links.dart:40`) — a placeholder | Affiliate id / camref |
| **Booking.com affiliate partner** | booking.com/affiliate-program | RideZap, TripNest | Same placeholder as above (TripNest goes through Travelpayouts) | Affiliate id (`aid`) |
| **eBay Partner Network** / Amazon / retailer networks | partnernetwork.ebay.com | GadgetNest | Only a sub-id (`GADGETNEST_AFFILIATE_MARKER=americangroupllc`); no network id | Campaign id from whichever network carries the electronics retailers chosen |
| **Instacart Developer Platform** | docs.instacart.com/developer_platform_api | GroceryMatch | `INSTACART_API_KEY` empty | API key; shoppable-link revenue terms per Instacart's agreement |
| **Walmart affiliates** | affiliates.walmart.com | GroceryMatch | `WALMART_API_KEY` empty (and the old `api.walmart.io` client was removed today: the host no longer resolves) | Affiliate id via Walmart's network |

Not configured, not verified to exist as consumer affiliate programmes: Uber and
Lyft for RideZap (it links to their front doors).

## 2. Data APIs that need a key (features, not commission)

All empty in release unless a default is shown.

| Vendor | Sign up | App · key | Secret? |
| --- | --- | --- | --- |
| Google Sign-In, iOS OAuth client | console.cloud.google.com | 15 apps · `GOOGLE_IOS_CLIENT_ID` (BodyQuest, CalcMaster, daily-pulse, DriftDate, GroceryMatch, HerJourney, iMaps, iMeasure, Kinnav, MyHealth, Photriya, PilotEnRoute, radiotune, Uscis-Case, yourtube). `GOOGLE_SERVER_CLIENT_ID` has a default | Public id |
| Google Maps Platform | console.cloud.google.com (billing account) | GroceryMatch `GOOGLE_MAPS_API_KEY`, Kinnav `MAPS_API_KEY` | Public, restrict by bundle id |
| YouTube Data API v3 | console.cloud.google.com | yourtube `YOUTUBE_API_KEY` | Restrict by bundle id |
| Pexels / Pixabay | pexels.com/api · pixabay.com/api/docs | yourtube `PEXELS_API_KEY`, `PIXABAY_API_KEY` | Low risk |
| Finnhub | finnhub.io/register | ApexMarketWatch `FINNHUB_API_KEY` | Keep server-side |
| OpenAI | platform.openai.com | Photriya `OPENAI_API_KEY` | **Server-side only** |
| Anthropic | console.anthropic.com | PilotEnRoute `ANTHROPIC_API_KEY` | **Server-side only** |
| LLM provider (unnamed) | — | HerJourney `LLM_API_KEY`, VirtuBand `AI_API_KEY` | **Server-side only** |
| Spoonacular · Edamam · Nutritionix · FatSecret | spoonacular.com/food-api · developer.edamam.com · developer.nutritionix.com · platform.fatsecret.com | GroceryMatch | Secrets server-side |
| USDA FoodData Central, NREL | api.data.gov/signup (one free key serves both) | GroceryMatch `USDA_API_KEY`, iMaps `NREL_API_KEY` — both default to the rate-limited `DEMO_KEY` | Low risk |
| Veryfi (receipt OCR, paid) | veryfi.com | GroceryMatch `VERYFI_*` (4 keys) | **Server-side only** |
| Kroger | developer.kroger.com | GroceryMatch `KROGER_CLIENT_ID`/`_SECRET` | Secret server-side |
| Yelp Fusion · Foursquare · RapidAPI | yelp.com/developers · foursquare.com/developers · rapidapi.com | GroceryMatch | Keep server-side |
| Open Charge Map · NASA FIRMS | openchargemap.org/site/develop/api · firms.modaps.eosdis.nasa.gov/api | iMaps `OPENCHARGEMAP_KEY`, `NASA_FIRMS_KEY` | Low risk |
| Agora (voice/video calls) | agora.io | Kinnav `AGORA_APP_ID` | App id public; tokens server-side |
| Sentry · PostHog | sentry.io · posthog.com | DriftDate, MyHealth, NexusTransferPay `SENTRY_DSN`; MyHealth `POSTHOG_API_KEY` | Optional — Crashlytics already covers crashes |

## 3. Keys with no vendor behind them (nothing to sign up for)

`AGSTUDIO_API_KEY`, `CARDEAL_API_KEY`, `RIDEZAP_API_KEY`, `NEARSERVE_API_TOKEN`,
`HOMEWISE_LISTINGS_API_KEY`, `AGL_API_GATEWAY_KEY` (FashionFactory),
`GATEWAY_API_KEY` (GroceryMatch, now read by nothing), `NEXUSPAY_ACCOUNTS`.
They point at an American Group API server that does not exist. Each needs
either a real vendor chosen (HomeWise listings, for example) or a Supabase
function, or the feature removed.

## 4. How tokens should reach the apps

- **Public ids** — affiliate tags and markers, publisher ids, OAuth client ids,
  Maps/YouTube keys restricted to the bundle id — can be passed as
  `--dart-define` at build time. Today only `admob_defines()` in
  `scripts/agl_paths.py` does this; it needs a sibling that reads a per-app,
  non-secret id file in the same way.
- **Secret keys** (OpenAI, Anthropic, Veryfi, Kroger/FatSecret secrets, paid data
  APIs) must **not** ship inside an app: anything in a binary can be extracted
  and billed against us. They belong behind a Supabase Edge Function on project
  `smvvjivvlprjhzhoizym` (`supabase secrets set`), which the app calls with the
  user's session.
- Every affiliate surface needs a visible disclosure (ChefCount already shows
  one; FashionFactory's appears only when tags are configured).
