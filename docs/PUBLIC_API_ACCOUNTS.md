# Public API Accounts

Every third-party API the AGL portfolio depends on, where to sign up, and what
credential you get back. Transcribed from the planning workbook
(`SFG-AGL-MobileApp_Devlopment-Tools.xlsx`, sheets *Devloper-APIs*,
*Logins-APis*, *SuperMarket APIs*, *Ticket-Booking-APIs*, *iMaps-Police-APIs*,
*BackEnd-Server*).

**No keys in this file.** Each row names the credential; the value belongs in
the app's `--dart-define`, a GitHub secret, or the backend's environment — never
in git.

---

## Backend platform

The whole portfolio sits on one Firebase/GCP project.

| Service | Purpose |
| --- | --- |
| Firebase Authentication | User authentication |
| Firebase Firestore | Database |
| Firebase Storage | Images |
| Firebase Cloud Messaging | Push notifications |
| Firebase Analytics | Analytics |
| Firebase Crashlytics | Crash reporting |
| Cloud Functions | Serverless backend |

Project `americangroupllc-5bdfc`, project number / FCM sender `9057515422`.
Each app also needs its own `google-services.json` (Android) and
`GoogleService-Info.plist` (iOS), downloaded per app from Firebase → Project
settings → Your apps.

---

## Authentication

| Provider | Type | Portal | Free | Credential you receive |
| --- | --- | --- | --- | --- |
| Google | OAuth / Google Sign-In | console.cloud.google.com | Yes | Client ID, Client Secret |
| Apple | Sign in with Apple | developer.apple.com/account | Needs membership | Services ID, Team ID, Key ID, Private Key |
| Phone | Firebase Auth | firebase.google.com | Spark | API Key, Project ID |
| Email/Password | Firebase Auth | firebase.google.com | Yes | API Key |

Apple requires Sign in with Apple whenever any other third-party sign-in is
offered, and both stores require account deletion for account-based apps.

---

## Payments

| Provider | Purpose | Portal |
| --- | --- | --- |
| Stripe | Credit cards | dashboard.stripe.com/register |
| Apple Pay | iOS payments | developer.apple.com/apple-pay |
| Google Pay | Android payments | developers.google.com/pay |
| PayPal | PayPal checkout | developer.paypal.com |
| Square | POS and payments | developer.squareup.com |

---

## Grocery, food and nutrition
*(GroceryMatch, ChefCount)*

| API | Purpose | Free tier | Portal |
| --- | --- | --- | --- |
| Kroger | Products, stores, carts, fulfilment | Yes | developer.kroger.com |
| Spoonacular | Recipes, ingredients, meal planning | Yes | spoonacular.com/food-api |
| Edamam | Nutrition analysis, recipe search | Yes | developer.edamam.com |
| USDA FoodData Central | Official nutrition database | Yes | fdc.nal.usda.gov/api-guide |
| Open Food Facts | Barcode / product database | Yes | world.openfoodfacts.org/data |
| FatSecret | Nutrition and food diary | Yes | platform.fatsecret.com |
| Nutritionix | Restaurant and grocery nutrition | Limited | developer.nutritionix.com |
| Instacart | Grocery delivery | Partner | docs.instacart.com |
| DoorDash Drive | Delivery logistics | Partner | developer.doordash.com |
| Walmart Marketplace | Seller integration | Limited | developer.walmart.com |
| eBay Browse | Product comparison | Yes | developer.ebay.com |
| Amazon Product Advertising | Amazon products | Approval | webservices.amazon.com |

---

## Places and discovery
*(GroceryMatch, NearServe, HomeWise, FashionFactory)*

| API | Purpose | Free tier |
| --- | --- | --- |
| Google Places | Store and POI search | Credit-based |
| Yelp Fusion | Reviews and local recommendations | Yes |
| Foursquare Places | Nearby discovery | Limited |

---

## Maps, traffic and safety
*(iMaps, Radar360_CAD)*

| Category | Source | Coverage | Free |
| --- | --- | --- | --- |
| Base maps | OpenStreetMap | Worldwide | Yes |
| Commercial maps | HERE / TomTom / Mapbox | Worldwide | Limited |
| Satellite imagery | Google Maps Platform, Esri ArcGIS | Worldwide | Paid / limited |
| Traffic flow | HERE Traffic, TomTom Traffic, Google Traffic | Worldwide | Paid |
| Traffic incidents | DATEX II (Europe), 511 APIs (US/Canada) | Regional | Yes |
| Road closures | Government APIs | Worldwide | Yes |
| Construction | Municipal GIS | Worldwide | Yes |
| Speed limits | OpenStreetMap | Worldwide | Yes |

---

## Travel and ticketing
*(TripNest, EventSpark)*

**Flights** — Amadeus (400+ airlines, self-service), Duffel (self-service),
Sabre and Travelport (GDS, business application), Kiwi.com Tequila (partner,
affiliate).

**Hotels** — Booking.com Demand API and Expedia Group (both affiliate/partner
application, 29M+ and 750K+ properties).

Self-service providers (Amadeus, Duffel) can be signed up for today; the GDS and
affiliate programmes need a business application and lead time, which is worth
starting early.

---

## What each app needs to ship

Anything below marked "not obtained" blocks a real release, because the app
currently falls back to modelled or sample data.

| App | APIs required | Status |
| --- | --- | --- |
| GroceryMatch | Kroger, Spoonacular/Edamam, Places | not obtained |
| ChefCount | Spoonacular, Amazon affiliate tag | affiliate tag present in code, API key not obtained |
| TripNest | Amadeus or Duffel, Booking/Expedia affiliate | not obtained |
| iMaps | Maps + traffic + 511 | not obtained |
| HomeWise | Real-estate listing API | not obtained |
| NearServe | Places / Yelp | not obtained |
| MyFinance | Plaid or equivalent for real accounts | not obtained |
| All apps | Firebase config, AdMob per-app ids | partial — see [`admob-ids.json`](admob-ids.json) |
