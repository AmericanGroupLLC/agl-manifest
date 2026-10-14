# Spec: RideZap — an open-world racing game with cars and motorbikes

Author: product-manager (AI office), 2026-10-14
Project: real-apps (`../plan.md`, criteria 1–7). Approval request: `../../../reports/approvals/2026-10-14-ridezap-racing-game.md` (GitHub issue #46).
Replaces: `RideZap.md` (the fare-log spec). The fare app is removed by this spec (§6.4).
Repo: `/Users/spatchava/agl/RideZap`, Flutter app in `mobile/`. Bundle id / package `com.americangroupllc.ridezap`. **Permanent: never changes** (`android/app/build.gradle.kts:32,45`).
Base: `main` @ `f2b733ccd10653a85bdbdaf7724279f53235bc36` (`git rev-parse HEAD`, `git branch --show-current` → `main`, run 2026-10-14).

> **Status: working assumption R1 = a** (top-down open world, Flutter + Flame). The founder has not answered R1–R4 yet. Every section that changes under R1 b or c carries an **[R1 b/c]** note, and §0.2 summarises them. R2–R4 are needed before release, not before building M1.

**Leave other people's work alone.** `git status --short` (2026-10-14) shows uncommitted edits to `mobile/fastlane/metadata/**` (descriptions, review notes, every phone/tablet screenshot), `mobile/fastlane/screenshots/en-US/*` and `mobile/ios/Podfile.lock`. They belong to the fare-app submission that is in review. Do not commit, revert or overwrite them without asking chief-of-staff. Adding the new native plugins (§0.3) rewrites `Podfile.lock`, so check `git diff mobile/ios/Podfile.lock` first and coordinate.

---

## 0. Decisions, stack, and what the founder must still answer

### 0.1 Stack (R1 a)

The versions below come from `pub.dev`, read with `curl -s https://pub.dev/api/packages/<name>` on 2026-10-14. The local toolchain is `/Users/spatchava/agl/.flutter-sdk/bin/flutter --version`, which reports Flutter 3.44.2 and Dart 3.12.2. CI pins the same Flutter version (`.github/workflows/ci.yml:40`). Note that `release.yml:69-71` uses `channel: stable` with no version pin.

| Package | Version to use | Its constraint | Why |
|---|---|---|---|
| `flame` | `^1.38.2` (published 2026-08-27) | Dart `>=3.11.0`, Flutter `>=3.41.0` | Game loop, components, camera, sprite batches, particles, keyboard events. Pure Dart, **no native code**. **Do not** use `2.0.0-dev.1` (2026-10-06): it is a pre-release. |
| `flame_audio` | `^2.12.2` | Dart `>=3.11`, Flutter `>=3.41` | Engine loops and sound effects. Pulls in `audioplayers ^6.2.0`, which **is native** and adds pods. |
| `in_app_purchase` | `^3.3.1` (2026-09-18) | Dart `^3.10`, Flutter `>=3.38` | The official plugin. Its iOS side, `in_app_purchase_storekit` 0.4.13+2, uses **StoreKit 2 by default** ("0.4.0 BREAKING CHANGE: StoreKit 2 is now the default", pub.dev changelog) and exposes `expirationDate` on `SK2PurchaseDetails` (0.4.13). Native. |
| `sensors_plus` | `^7.1.1` | — | **SHOULD, M2:** tilt steering only. Native. Leave it out if tilt is cut. |
| not used: `flame_tiled`, `flame_forge2d` | — | — | Tiled cannot author a 64 km² map for one developer (§5.2). Box2D is heavier than the arcade model in §4.3 and is not bit-reproducible for our tests. |

The `pubspec.yaml` environment must rise from `sdk: '>=3.0.0 <4.0.0'` (`pubspec.yaml:6`) to `'>=3.11.0 <4.0.0'`. Flame requires it.

`google_mobile_ads` stays a transitive dependency through `agl_ads`. It is locked at 9.1.0 (`pubspec.lock:293-297`).

### 0.2 What changes under R1 b or c

| Area | R1 b: pseudo-3D road racer (OutRun style) | R1 c: Unity 3D |
|---|---|---|
| §1 identity | Becomes "long routes through five regions" instead of a seamless map. Free roam shrinks to route choice at forks. | Same identity, in 3D. |
| §4 controls, physics | Physics is 1-D along the road (speed, lateral offset, curvature pull). There is no free 2-D heading. Bike lean becomes the main visual. | Rewritten for a 3-D engine (Unity wheel colliders or a custom arcade rig). |
| §5 world | Route segments (curve, hill, scenery sprites) replace chunks and the road graph. The authoring tool emits segment lists. | 3-D terrain and meshes. Assets grow by more than 10×, and the office cannot produce them under the same licence checks. |
| §6 performance, size | Lighter than a. | New budgets. The app size likely triples. |
| §3 monetization | No change (Flutter + `agl_ads`). | `agl_ads` **cannot be used**. Needs the Google Mobile Ads Unity plugin, Unity IAP, a new UMP flow, new CI, and new gates. |
| §8 tests | Same structure. | Dart tests are replaced by the Unity Test Framework. None of the portfolio's Flutter gates apply. |

### 0.3 Open founder decisions

They are R1–R4 from the approval request, plus new ones found while writing this spec (R5–R9). The full list is in §9.

---

## 0.3 Competitive bar — founder, 2026-10-14: "it has to be good and better"

The founder named the games RideZap must stand next to: CarX Street (open world), Asphalt Legends (arcade, nitro, stunts),
Drive Zone Online (open-world multiplayer), Need for Speed No Limits (street racing, police chases), GRID Autosport
(circuit realism), Wreckfest (damage and destruction), CarX Drift Racing 3 (drift), Rush Rally 3 (rally surfaces),
Traffic Rider (bike traffic weaving) and Mad Skills Motocross 3 (bike stunts). All of them except Mad Skills are **3D**.

**Consequence for R1 (office position, revised):** a top-down 2D game (R1 a) would not be judged against these titles
at all. It would look like a different, smaller genre. To meet the founder's bar, RideZap has to be 3D. The revised
recommendation is a new option:

- **R1 d — stylized low-poly 3D open world in Godot 4** (Godot 4.7.2-stable, MIT, no account or licence fee; checked
  with `gh api repos/godotengine/godot/releases/latest` on 2026-10-14). Assets: Kenney Car Kit and City Kit Roads
  (CC0, licence text checked on kenney.nl 2026-10-14) plus original models. Ads: poingstudios/godot-admob-plugin
  (MIT, last push 2026-10-13). Purchases: godot-sdk-integrations/godot-google-play-billing (MIT) and
  godot-ios-plugins `inappstore`. Builds are headless CLI exports, so they fit CI. The cost is a **new lane in ship.yml**,
  because the other 42 apps are Flutter.
- R1 c (Unity) gives the same 3D, but needs a Unity account and Editor licence and has a heavier CI footprint.
- R1 a (Flame, top-down) stays the cheapest. `flame_3d` is 0.3.2 and labelled "Experimental", so Flame is not the 3D path.

**What RideZap can honestly beat them on.** It will not beat Asphalt or CarX on photorealism; that takes studio budgets.
It can beat them on fairness, size, offline play, variety and older phones:

| Founder's reference | Their strength we match | Where RideZap goes further |
| --- | --- | --- |
| CarX Street, Drive Zone | Free-roam city and highway map, tuning | Map regions are seamless and offline. No energy timers and no online requirement to roam |
| Asphalt Legends | Nitro, jumps, spectacle | Every vehicle earnable by play (§2). No random boxes |
| NFS No Limits | Police chases, street culture | Heat level and pursuit events in free roam, not menu-only |
| Wreckfest | Crashes and damage | Visual damage and wrecks on cars **and** bikes (cartoon-level, age rating stays 9+ or lower, confirm) |
| CarX Drift 3, Rush Rally 3 | Drift scoring, surfaces | Surface-grip table (§4): tarmac, gravel, dirt, sand, wet; drift and rally events in the same world |
| Traffic Rider, Mad Skills | Bikes, traffic weaving, stunts | Cars and bikes in one garage, with highway weaving events and trick ramps in the mountains |
| All of them | | Download target ≤ 250 MB (Asphalt-class games are multi-GB), 60 fps target on an iPhone 11-class device, ads never during a race |

Multiplayer (Drive Zone, Asphalt) is **out of v1**. It needs a realtime server we don't run. It is a candidate for v2 on
the existing Supabase project (Realtime), as a founder decision because of the cost.

Claims about the competitors' features come from the founder's list and general knowledge, and were not checked on the
stores (store pages are blocked from this machine). Download sizes and pay-to-win claims are **not verified**.

## 1. Product identity (Apple 4.3 applies to games too)

**[R1 b/c]** Under b, the seamless map becomes long routes with forks. Under c, the same identity in 3D (§0.2).

**One sentence.** RideZap is a top-down open-world racer. One seamless map has five regions. You race **cars and motorbikes** that handle differently, in events you drive to, and you paint every vehicle your own way.

**What makes it distinct.** Each item is a build requirement, not a slogan.

1. **One seamless region map**, 8 km × 8 km, streamed in 256 m chunks (§5). There are no loading screens between regions.
   - **Voltport** is the city: downtown grid, harbour, neon district.
   - **Loop 8** is the highway ring that joins every region.
   - **Saltpan Flats** is the desert: salt flat, canyon, dunes.
   - **Gullwing Coast**: cliff road, beaches, Lighthouse Point.
   - **Ridgeback Range** is the mountains: switchbacks, Old Mine Pass, wind farm ridge.
   - All names are fictional, and every name is checked under R8.
2. **Cars and bikes are different games inside one game** (§4.3).
   - Cars have more grip, can drift (handbrake), and shrug off contact.
   - Bikes accelerate harder, lean into corners, slip through gaps (narrower hitbox), have no drift, and **wipe out** on a hard hit (a 2 s respawn penalty).
   - Off-road machines (buggy, rally, desert truck, enduro, dirt bike) lose much less grip on dirt and sand.
3. **"Flavours" = liveries.** Paint (solid, metallic, pearl), patterns (stripes, chequer, flames, lightning, split, gradient…), decals and race numbers, car underglow (visible at night), and bike light trails and helmet colour.
   - Vehicles are **drawn by code** (§5.4): a body path with layers. A livery is therefore real layered paint, not a recoloured sprite.
   - Every livery can be previewed on any vehicle before buying.
4. **Time and weather.**
   - A 24-minute day: 1 real minute = 1 in-game hour. Headlights, streetlights and underglow come on at dusk.
   - Weather by region: rain (city, coast, mountains), morning fog (coast, mountains), sandstorm (desert). Each changes grip and visibility (§4.3).
5. **Free roam plus events.** You drive to an event marker on the map to start it. Fast travel works only to landmarks you have already discovered. It is always free.
   - **Checkpoint sprint**: A→B through gates.
   - **Circuit**: 2–4 laps.
   - **Time trial**: solo, against medal times.
   - **Rival duel**: 1-on-1 against a named AI rival.
   - 8 rivals, each with a callsign and a signature livery that **can only be won by beating them**.
6. **Free-roam activities**: 300 **bolt tokens** to collect, speed traps, and drift zones (cars only).

**Fictional only (Apple 5.2.1, Play IP policy).**
- No real car or bike makes, models, logos or recognisable body shapes. No real places.
- No reference anywhere in the app, assets, store copy or screenshots to Forza, Horizon (as a title), The Crew, Motorfest, Test Drive, Solar Crown, or any other game.
- A source test enforces this (§8.1, `ip_names_test.dart`).
- The vehicle and place names in this spec are **proposals pending R8** (trademark check).

**Who it is for.** Phone players who want quick races (2–5 minutes) and a world to drive around. It runs offline, needs no account, and is playable one-handed with auto-accelerate.

**Honesty rules carried from the portfolio** (`../plan.md` criterion 5, `company/policies.md`):
- No fake player counts, ratings, "online rivals" or leaderboards. Every rival is an AI and is labelled "AI".
- No remote switches and no build-time feature flags. Everything in the binary is reachable by any user (this is what the 5.6 rejection was about).
- There is no debug or cheat menu in any build. Tests inject state through Riverpod overrides only.

---

## 2. Core loop and economy

**[R1 b/c]** No change to the economy numbers. Under b, events become route segments. Under c, the code moves to C#.

### 2.1 Loop

Drive in free roam → find an event → race → earn coins (+ an optional rewarded double) → garage: buy a vehicle, upgrade, or paint → unlock the next tier of events → repeat.

**One currency: coins.** Earned by play, or bought in packs (§3.3).
- Coins never expire (Apple 3.1.1).
- There is no second "premium" currency. The founder's "paid points for premium cars" is met by coin packs: premium (S-class) vehicles cost coins, and those coins can also be earned.
- **No loot boxes, no random rewards, no spins.** Every reward amount is fixed and shown before the user acts. So there is no odds disclosure (3.1.1) and no simulated-gambling rating.
- Seeded randomness is allowed **only** for weather and decorative props, never in `lib/economy/` or `lib/monetization/`. A source test enforces this.

### 2.2 Event payouts

Payout = `base(tier) × placeMultiplier × difficultyMultiplier`, rounded to 10. On top of that, a **first-win bonus** of +50% of the 1st-place payout is paid once per event.

| Tier | Vehicle class allowed | Base coins | Typical length | Events in v1 |
|---|---|---|---|---|
| C | D or C | 500 | 2.0 min | 14 |
| B | B | 800 | 2.5 min | 12 |
| A | A | 1,200 | 3.0 min | 10 |
| S | S | 2,000 | 5.0 min | 4 (incl. the "Grand Tour", a cross-map sprint) |

The 40 events break down as 12 sprints, 10 circuits, 10 time trials and 8 rival duels.
- Each event is tagged **Cars**, **Bikes** or **Any**, in roughly a 40 / 30 / 30 split.
- Circuits and sprints have 5 AI rivals. Duels have 1.

| Placing (race) | 1st | 2nd | 3rd | 4th–6th | Did not finish / quit |
|---|---|---|---|---|---|
| Multiplier | 1.00 | 0.60 | 0.40 | 0.20 | 0 |

| Medal (time trial) | Gold | Silver | Bronze | None |
|---|---|---|---|---|
| Multiplier | 1.00 | 0.60 | 0.40 | 0.10 |

| Difficulty | Easy | Normal | Hard |
|---|---|---|---|
| AI skill (§4.5) | 0.88 | 0.94 | 0.98 |
| Payout multiplier | 0.8 | 1.0 | 1.25 |

Free roam pays too:
- Bolt token: 25 coins each. 300 tokens = 7,500 in total.
- Speed trap or drift zone star: 50 coins the first time each star is earned.
- Discovering a landmark: 200 coins once.

### 2.3 Vehicles: starter garage and prices (names pending R8)

**Starter garage:** Pipsqueak (car) and Sprigbolt (bike), both free and owned from the first launch.

| # | Name | Type | Class | Price (coins) | Top speed | 0–100 km/h | Grip (lateral g) | Mass | Speciality |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Pipsqueak | car, hatchback | D | 0 (starter) | 150 km/h | 9.5 s | 0.90 | 1,050 kg | — |
| 2 | Burrowbug | car, buggy | D | 5,000 | 140 | 8.8 | 0.85 | 900 | dirt / sand |
| 3 | Kerbsider | car, compact sport | C | 12,000 | 185 | 7.2 | 0.98 | 1,150 | — |
| 4 | Gritwhistle | car, rally | C | 14,000 | 175 | 6.9 | 0.95 | 1,200 | dirt |
| 5 | Tidebreaker GT | car, coupé | B | 28,000 | 225 | 5.6 | 1.05 | 1,350 | — |
| 6 | Duneplough | car, desert truck | B | 30,000 | 200 | 6.0 | 0.95 | 1,900 | sand |
| 7 | Lanternfly | car, grand tourer | A | 55,000 | 265 | 4.3 | 1.12 | 1,450 | — |
| 8 | Shalecutter | car, rally | A | 60,000 | 245 | 4.0 | 1.08 | 1,300 | dirt |
| 9 | Brightwake | car, hypercar | **S (premium)** | 120,000 | 320 | 3.0 | 1.25 | 1,350 | — |
| 10 | Stormglass | car, electric hyper | **S (premium)** | 130,000 | 305 | 2.6 | 1.20 | 1,700 | boost recharges 2× |
| 11 | Sprigbolt | bike, street | D | 0 (starter) | 145 | 8.0 | 0.85 | 160 kg | — |
| 12 | Pebblehop | bike, dirt | C | 10,000 | 150 | 6.8 | 0.80 | 120 | dirt |
| 13 | Quillrider | bike, sport | B | 26,000 | 230 | 4.4 | 0.98 | 190 | — |
| 14 | Saltskipper | bike, enduro | B | 28,000 | 205 | 4.9 | 0.90 | 150 | sand / dirt |
| 15 | Cindertail | bike, superbike | A | 52,000 | 285 | 3.2 | 1.05 | 200 | — |
| 16 | Arcwhisper | bike, electric superbike | **S (premium)** | 115,000 | 300 | 2.8 | 1.10 | 230 | boost recharges 2× |

Totals: cars 454,000, bikes 231,000, **all 16 vehicles 685,000 coins**.
- **Every vehicle has a coin price. None is IAP-only.** A unit test asserts this.

### 2.4 Upgrades

There are four categories, each with three tiers: Street → Sport → Race.

| Category | Effect per tier | Cost per tier (% of the vehicle's reference price*) |
|---|---|---|
| Engine | +4% top speed, +5% acceleration | T1 4% · T2 8% · T3 13% |
| Grip (tyres, suspension) | +5% lateral grip | same |
| Nitro | +12% nitro capacity, +5% boost force | same |
| Weight | +3% acceleration, +3% steering response | same |

\*The reference price is the vehicle price, or 5,000 for the free starters. Costs are rounded to 100.
- Fully upgrading one vehicle costs 100% of its reference price. All 16 cost 695,000 coins.
- **Upgrades never change class.** A fully upgraded vehicle ends just below the next class's stock performance.
- The **Zap Rating** shown on cards uses these bands: D 100–299, C 300–499, B 500–699, A 700–849, S 850–999. Do not use "PI": that is another franchise's term.

### 2.5 Liveries ("flavours")

Buying a livery item unlocks it **for every vehicle** it fits.

| Item | Count | Price each |
|---|---|---|
| Solid paint | 12 | free |
| Metallic paint | 8 | 1,500 |
| Pearl / chrome-effect paint | 4 | 4,000 |
| Patterns (stripes, twin stripes, chequer, flames, lightning, split, gradient, number panel) | 8 | 2,000 |
| Race numbers 0–99 | — | free |
| Decal shapes | 16 | 500 |
| Underglow (cars) | 6 colours | 3,000 |
| Light trail (bikes) | 6 colours | 2,000 |
| Helmet colour (bikes) | 12 | free |
| Rival signature liveries | 8 | **not for sale**: won by beating that rival's duel |

All for-sale cosmetics together cost 82,000 coins.

### 2.6 Daily reward (deterministic)

A 7-step ladder that advances **one step per calendar day on which you claim**. It does not need consecutive days. Missing a day loses nothing, so there is no fear-of-missing-out pressure. After day 7 it restarts.

| Claim # | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Coins | 200 | 300 | 400 | 500 | 600 | 800 | 1,200 + a 24 h free trial of one listed pattern |

Rules:
- One claim per local calendar day.
- **Clock-rollback guard:** if the device date is earlier than the last claim date, nothing can be claimed until the date passes the last claim again.
- The reward is shown before the tap. Nothing is random.

### 2.7 Progression curve: every premium vehicle can be earned by play

The model lives in `lib/economy/progression_model.dart` (pure Dart), and the tests pin it.

**"Typical player" assumptions** (on Normal, with 0.5 min of menu overhead per event):
- Places 1st 35%, 2nd 25%, 3rd 20%, 4th–6th 20%. The mean multiplier is 0.62.
- **Excluded:** first-win bonuses, daily rewards, tokens, stars and rewarded doubles. The hours below are therefore **upper bounds** for a player who never spends.

| Tier | Events / hour | Coins / hour |
|---|---|---|
| C | 24.0 | 7,440 |
| B | 20.0 | 9,920 |
| A | 17.1 | 12,754 |
| S | 10.9 | 13,527 |

The cheapest path to the first premium car is to buy each tier's cheapest vehicle as soon as you can:

| Step | Cost | Earned at | Hours | Total |
|---|---|---|---|---|
| Kerbsider (C) | 12,000 | tier C | 1.6 | 1.6 h |
| Tidebreaker GT (B) | 28,000 | tier C | 3.8 | 5.4 h |
| Lanternfly (A) | 55,000 | tier B | 5.5 | 10.9 h |
| **Brightwake (S, premium)** | 120,000 | tier A | 9.4 | **≈ 20 h** |

- **First premium bike** (Arcwhisper, by the bike path): **≈ 19 h**.
- **The whole 16-vehicle garage, stock:** ≈ 20 h + 470,000 / 13,527 ≈ **55 h**. Adding every upgrade: **≈ 106 h**.
- Taking the rewarded double after every event roughly halves all of these.

What purchases are worth, in play time:
- Smallest pack (5,000 coins) ≈ 40 min of tier-C play.
- Largest pack (140,000) ≈ one S-class vehicle ≈ 11 h of tier-A play.
- Pass weekly bonus (2,500) ≈ 20 min of tier-C play.

These figures are for pricing review under R2. They are not claims to put in store copy.

**Tests pin the curve** (§8.1):
- first S vehicle ≥ 12 h and ≤ 25 h;
- full stock garage ≤ 70 h;
- no vehicle price above the largest coin pack.

Changing a number is fine. Breaking a bound is a product decision and goes back to the PM.

---

## 3. Monetization

**[R1 b/c]** No change under b. Under c, `agl_ads` and `in_app_purchase` cannot be used, and Unity's Google Mobile Ads plugin and Unity IAP replace them (§0.2).

### 3.1 AdMob through the shared `agl_ads` package

**What the package gives us** (read 2026-10-14, `agl-manifest/packages/agl_ads`):
- Exports: `AglAdBanner`, `AglAdIds`, `AglNativeAd`, `AglAds`, `AglConsent` (`lib/agl_ads.dart:37-41`).
- `AglAds.onTransition()` shows a ready interstitial only after a warm-up of 2 transitions (`ads.dart:26`) and at most once every 3 minutes (`ads.dart:22`, enforced at `ads.dart:146-152`). It must be called *after* the navigation (`ads.dart:137-139`).
- `AglAds.preloadRewarded()` and `AglAds.showRewarded(onReward:)` (`ads.dart:185,225`). `AglAds.rewardedReady` (`ads.dart:180`) lets a button enable itself only when an ad is loaded.
- `AglAdBanner` takes no space until it fills, and must sit in normal layout flow, never stacked over content (`ad_banner.dart:22-25`).
- Store-screenshot builds (`--dart-define=SCREENSHOT=true`) load no ads (`ads.dart:40-46`).
- UMP consent gates every request and fails closed (`consent.dart:91-104`).

**RideZap already has AdMob set up:**
- `main.dart:42-46` configures the app ids `ca-app-pub-8528784688453695~6433412875` (Android) and `~2566320057` (iOS) and starts initialisation without awaiting it.
- `Info.plist:63-64` carries the iOS app id and 50 SKAdNetwork ids.
- The production **rewarded** units already exist: `docs/admob-ids.json:486` (Android `…/6268841478`) and `:493` (iOS `…/5076188460`). They are passed at build time as `ADMOB_REWARDED_ANDROID` / `ADMOB_REWARDED_IOS` (`ad_ids.dart:63-65`).

**Placement rules.** These are MUST. `AdPolicy` (pure Dart, `lib/monetization/ad_policy.dart`) decides; screens ask it.

| Format | Allowed | Never |
|---|---|---|
| Banner (`AglAdBanner`) | Home menu, garage list, world map / event list. Always at the bottom of a `Column`. | Any driving (race, countdown, free roam), pause, loading, results, shop, settings, livery editor, onboarding |
| Interstitial (`AglAds.onTransition()`) | **Only** when the user taps **Continue** on a results screen after a **finished** event, and only on every 2nd finished event of the session (an app rule on top of the package's 2-transition warm-up and 3-minute cap). | During or before a race, on quit or restart, on DNF, from the shop or any purchase flow, from settings |
| Rewarded (`showRewarded`) | Only from a button that states the reward. See below. | Automatically. Never as the only way to get anything. |

**Rewarded features.** All are deterministic, and the amount is printed on the button.
1. **"Watch an ad: +{N} coins"** on the results screen. N equals that event's payout, so the coins double.
   - Once per results screen. At most 10 rewarded views a day across all features.
2. **"Pit-stop bonus: watch an ad for +300 coins"** on the home menu.
   - Once every 4 hours, at most 4 a day.
3. **"Test drive: watch an ad to race {locked vehicle} in this event"** on the pre-race screen.
   - One event only. Payout is normal. Ownership does not change.
4. **"Try this livery for 24 h"** in the livery editor. It applies a locked paint or pattern for 24 hours, then reverts.

On each button:
- The button is disabled with "Ad not ready" when `AglAds.rewardedReady` is false.
- If an ad fails to show, the user loses nothing: their coins are already banked and the button stays.
- `preloadRewarded()` is called when the results, home or pre-race screen opens, not from `main()` (`ads.dart:182-184`).

**The ad-free gate (important: the package cannot do this as-is).**
- `AglAds.setSuspended(true)` disposes the rewarded ad too (`ads.dart:55-63`), and blocks it (`ads.dart:186,226`). The banner also checks it (`ad_banner.dart:54`).
- So **for "Remove ads" or Pass owners, do not call `setSuspended`.** Instead, `AdPolicy` must:
  - stop building `AglAdBanner`;
  - stop calling `onTransition()`;
  - keep rewarded available as opt-in.
- Side effect: `AglAds.initialize()` still preloads one interstitial (`ads.dart:94`) that is never shown. That is acceptable for v1.
- **SHOULD (package change, office-owned, with a package test):** add `AglAds.setInterstitialsEnabled(bool)` so ad-free users make no interstitial request at all.

**Content rating of ads (MUST before release).**
- A 4+ game must not serve mature ads. `agl_ads` does not set `maxAdContentRating` today: `initialize()` only sets test-device ids (`ads.dart:80-90`).
- Add an optional `maxAdContentRating` (value `G`) to `AglAds.configure` in the package, applied with `MobileAds.instance.updateRequestConfiguration`, plus a package test.
- Also set the same rating ceiling in the AdMob console (Blocking controls → sensitive categories). That console step is for the account holder.

### 3.2 In-app purchases: the official `in_app_purchase` plugin

**Product catalogue.** Ids are proposed. Prices are **placeholders pending R2**, and the column shows the office's R2 a.

| Product id (App Store and Play) | Type | Grants | R2 a placeholder |
|---|---|---|---|
| `com.americangroupllc.ridezap.coins.pocket` | consumable | 5,000 coins | $0.99 |
| `com.americangroupllc.ridezap.coins.stack` | consumable | 30,000 coins | $4.99 |
| `com.americangroupllc.ridezap.coins.vault` | consumable | 65,000 coins | $9.99 |
| `com.americangroupllc.ridezap.coins.garage` | consumable | 140,000 coins | $19.99 |
| `com.americangroupllc.ridezap.removeads` | non-consumable | No banners or interstitials, forever. Rewarded stays available as opt-in. | $4.99 |
| Subscription group **"RideZap Pass"**: `com.americangroupllc.ridezap.pass.monthly` and `.pass.yearly` | auto-renewing (iOS) | While active: no banners or interstitials, plus a **2,500-coin weekly bonus** claimed in-app (every 7 days since the last claim). Rewarded stays opt-in. | $2.99 / month · $19.99 / year |
| Play: subscription `ridezap_pass` with base plans `monthly` and `yearly` | Play subscription | same | same |

- **R2 b offers only three coin prices.** If the founder picks b, a fourth pack price is needed, or the catalogue drops to three packs.
- The Pass benefit is ongoing (ad-free plus weekly coins), which subscriptions require.
- Coins already granted stay after the Pass lapses.

**State machine.** `lib/monetization/purchase_controller.dart` is pure logic over an injectable `InAppPurchase` facade. Per purchase:

`idle → pending → purchased → delivered → completed`, with side exits `canceled`, `error` and `restored`.

- **Deliver exactly once.** Before adding coins, check that the `purchaseID` / transaction id is not already in the save's `deliveredTransactions` set. Add it, persist the save, **then** call `completePurchase`. A crash between deliver and complete must not double-credit on replay.
- Consumables use `buyConsumable(autoConsume: true)`. Non-consumable and subscriptions use `buyNonConsumable`.
- Listen to `purchaseStream` from app start (in `main`, before `runApp`) so purchases that finish while the app is closed are delivered on the next launch.
- `pending` (Ask to Buy, slow cards) shows "Waiting for approval" and grants nothing yet.

**Entitlements** (`lib/monetization/entitlements.dart`):
- **Remove ads:** owned once seen as `purchased` or `restored`. Cached in the save.
- **Pass on iOS:** active while `SK2PurchaseDetails.expirationDate > now`. The cached expiry is honoured offline.
- **Pass on Android:** active while the subscription appears in the latest restore or query result. The cache is honoured for 72 h offline.
  - The claim that Play's restore returns only active subscriptions comes from Play Billing documentation. **Not verified here; must be confirmed in M3 with a licence-tester purchase** that lapses.
- At every launch, call `restorePurchases()` silently. Under StoreKit 2 this does not prompt for a password (iOS 16+, deployment target 16.0 per `project.pbxproj:498`). Confirm this in M3: not verified.

**Shop UI: Apple 3.1.2 and 3.1.1 requirements.** These are MUST, and widget tests check them.
- Prices come **only** from `ProductDetails.price`, which is localised. Nothing is hard-coded.
  - If the store is unavailable (`isAvailable()` false, or a product id not found), the shop shows "The store isn't available right now" and offers **no** buy buttons.
  - This is the portfolio's MA-023 lesson: no prices on a button that cannot complete a purchase (`docs/MANUAL_ACTIONS.md:971-993`).
- The subscription screen shows:
  - the subscription name, length and price per period ("$2.99 per month");
  - what it includes;
  - "Renews automatically unless cancelled at least 24 hours before the end of the period";
  - how to cancel (Settings → Apple ID → Subscriptions / Play Store → Subscriptions);
  - links to **Terms of Use** and **Privacy Policy**.
- **Restore purchases** buttons appear in the shop and in Settings.
- **Links** (all returned HTTP 200 to `curl` on 2026-10-14, and the app already holds them in `lib/core/sources.dart:30-35`):
  - Privacy `https://www.americangroup.ai/policy/ridezap/privacy.html` (the app currently links `…/policy/ridezap/`, which is also 200);
  - Terms `https://www.americangroup.ai/policy/ridezap/terms.html`;
  - Support `https://www.americangroup.ai/policy/ridezap/support.html`.
- **Blocker, R5:** both pages are out of date and must be changed before IAP ships.
  - Terms §3 says "The app is free to download and contains no purchases".
  - The privacy page says "The app does not show advertisements and does not include an advertising SDK", "The app has no in-app purchases", and "This release sends no analytics and no crash reports".
  - The privacy page is **already wrong today**: the current app starts Crashlytics, Analytics and AdMob at `main.dart:35-46`.
  - Legal text is a founder decision (Charter §6). Alternatively, the app and listing can link **Apple's standard EULA** for Terms of Use.
- Interstitials never show from the shop. The shop never shows a banner.

**Receipt validation: the honest v1 approach.**
- No server. On iOS, StoreKit 2 verifies the signed transaction on the device; the plugin reports unverified results separately (storekit changelog 0.4.6 and 0.4.8+1). On Android, Play Billing reports purchase state. We trust those.
- **Risks, accepted for v1:**
  - Coins can be faked on jailbroken or rooted devices.
  - Refunds and voided purchases are not taken back (Android needs the server-side Voided Purchases API; iOS revocation is not handled).
  - Impact is low: the game is single-player, with no leaderboards and nothing traded between players.
- **Later:** a Supabase Edge Function that checks App Store Server API and Play Developer API tokens. It needs new keys, which is a Charter §4 founder action. Out of scope for v1.

**Store-side prerequisites (R4, founder):**
- The products and subscription group are created in App Store Connect and Play Console.
- The Paid Applications agreement must be active. **Not verified** (the approval request says the same).
- On Apple, the IAP products must be **submitted with the build**. Otherwise review stops (`docs/APPLE_REQUIREMENTS.md:10`, 2.1(b)/3.1.1, seen on NexusTransferPay).
- **The shop must not ship in any build whose products are not created in both consoles.**

---

## 4. Controls, camera, physics, AI, HUD

**[R1 b/c]** Rewritten under both. Under b: 1-D road physics with a fixed behind-the-vehicle camera. Under c: a 3-D vehicle rig. The checkpoint, clock and AI-speed logic carries over in concept.

### 4.1 Orientation

The game is **landscape only**: landscape left and right on phone and iPad.

Today the app is portrait:
- `main.dart:54-57` sets `portraitUp`/`portraitDown`.
- `Info.plist:54-58` lists only the portrait orientations.

`UIRequiresFullScreen` is already `true` (`Info.plist:52-53`), so iPad may be landscape-only without breaking multitasking upload rules.

Change both files, and add `UISupportedInterfaceOrientations~ipad` with the two landscape values. iPad launch must still be checked on a simulator (2.1(a), `docs/APPLE_REQUIREMENTS.md:8`).

### 4.2 Controls (touch first)

**Default layout "Buttons":**
- Bottom-left: ◀ ▶ steering pads, each about 88 dp.
- Bottom-right: a large **throttle**, **brake/reverse** to its left, **nitro** above throttle, and **drift** (handbrake, cars only; on bikes this becomes "tuck", a small top-speed boost while going straight).

**Options in Settings:**
- **Tilt steering** (SHOULD, M2; needs `sensors_plus`), with a sensitivity slider.
- **Auto-accelerate**: throttle always on, and brake slows. Accessibility, and one-handed play.
- **Steering assist** (Easy default): mild pull toward the road centre-line.
- Haptics on or off (`HapticFeedback`, no plugin).
- Swap left and right.

**Hardware keyboard** (iPad, Android) through Flame `KeyboardEvents`, which needs no plugin: arrows / WASD, Space = drift, Shift = nitro, Esc = pause.

**Game controllers:** out of scope for v1. They would need a third-party plugin.

### 4.3 Physics: arcade top-down, pure Dart, deterministic

Lives in `lib/game/sim/`. It **must not import Flutter or Flame**, so it runs in plain `dart test`.

**Stepping:**
- **Fixed step:** 60 Hz (`dt = 1/60`), with an accumulator and at most 4 steps per frame (a guard against the spiral of death). Rendering interpolates between the last two states.
- **Determinism:** the same initial state plus the same input sequence must give bit-identical state on the same platform. There is no wall-clock time inside the simulation, and no `Random` without a seed.

**Vehicle state:** position (m), heading (rad), velocity (m/s, world frame), yaw rate, nitro charge, and drift flag / lean angle.

**Each step:**
1. Split the velocity into forward (`vf`) and lateral (`vl`) parts in the vehicle frame.
2. Drive force: `throttle × accelCurve(vf / vmax)`. Brake force is fixed per class. Reverse is capped at 25 km/h.
   - Drag is `k × vf²`, with `k` chosen so that terminal speed equals the table's top speed.
   - Rolling resistance comes from the surface.
3. Lateral grip:
   - `vl ← vl × max(0, 1 − gripRate × surfaceGrip × weatherGrip × dt)`.
   - `gripRate` is derived from the lateral g in §2.3.
4. Steering: yaw rate = `steer × steerRate(v)`. `steerRate` falls off with speed, keeping 35% of its low-speed value at top speed.
5. **Drift (cars):**
   - Starts when drift is held at more than 30 km/h, or when full steer is held above 60% of vmax and the slip angle exceeds 12°.
   - While drifting, grip is multiplied by 0.45 and yaw rate by 1.3.
   - Ends when the slip angle drops below 8° and drift is released.
   - Drift zones score slip angle × speed × time.
6. **Bikes:**
   - Lean angle = `clamp(steer × v / vmax × 45°, ±45°)`. It is visual, but above 20° of lean, lateral grip gets +10%.
   - No drift.
   - **Wipe-out:** an impact with a relative normal speed above 25 km/h, or more than 1.5 s on sand on a non-sand bike above 120 km/h, triggers a 2 s respawn at the nearest road node, facing along the road.
7. **Nitro:**
   - +35% drive force and +8% vmax while active.
   - Capacity is 3 s at stock. It recharges at 0.15 s per second while driving and faster while drifting, and 2× for the electric S-class vehicles.

**Surface and weather multipliers.** A unit test pins this table.

| Surface | Grip | Top-speed cap | Off-road vehicles (dirt / sand specialists) |
|---|---|---|---|
| Asphalt, dry | 1.00 | 100% | same |
| Asphalt, wet (rain) | 0.80 | 100% | same |
| Kerb | 0.95 | 100% | same |
| Dirt | 0.70 | 90% | 0.90 grip, 100% |
| Grass | 0.65 | 80% | 0.80, 90% |
| Sand | 0.55 | 75% | 0.85, 95% |
| Sandstorm (desert, any surface) | × 0.90 | — | — |
| Fog | grip unchanged; visibility radius 120 m | — | — |

**Collision:**
- Vehicles are oriented boxes; bikes use a narrower box.
- Narrow phase: separating-axis test. Broad phase: a uniform grid per chunk.
- Static obstacles are circles and boxes baked per chunk: buildings, rocks, guard-rails as thick (≥ 2 m) segments, and the shoreline.
- Response: positional separation plus an impulse with restitution 0.3 and friction 0.5. Cars lose speed in proportion to the impact. There is no damage model.
- At top speed (S class, 320 km/h ≈ 89 m/s) a car moves 1.48 m per step. That is less than half a car length, and walls are at least 2 m thick, so no continuous collision detection is needed. A test asserts that no tunnelling happens at 100 m/s.
- **Stuck:** after 3 s below 2 km/h while throttling, a **Reset** button appears and puts the vehicle at the nearest road node.

**The world edge** is the ocean (west) and impassable cliffs (the other three sides). They are collision edges, never invisible walls in open land.

### 4.4 Camera

- **Chase (default):** the camera rotates with the vehicle, so "left" always means the vehicle's left.
- **Map:** north stays up. The setting lives in Settings → Controls.
- **Look-ahead:** the camera centre leads the vehicle by 0.6 s of velocity, capped at 40 m.
- **Zoom:** 1.0 at standstill down to 0.7 at top speed. The visible width is about 60 m at 1.0 and about 85 m at 0.7. Zoom changes are smoothed with a critically damped spring (0.4 s).
- **Collision shake:** at most 6 px for 150 ms. It can be switched off ("Reduce motion").

### 4.5 AI rivals

- **Racing line:** each event has a polyline baked from the road graph (§5.2). Apexes are shifted toward the inside of each curve by up to 35% of the road half-width, in proportion to curvature.
- **Target speed** per point: `min(vmax, sqrt(μ·g / κ))`, followed by a backward pass that limits deceleration to the vehicle's braking ability.
- **Driving:**
  - Pure-pursuit steering toward a look-ahead point (8 m + 0.4 s × speed).
  - Throttle and brake from a PI controller on `targetSpeed × skill`.
  - Skill is 0.88 / 0.94 / 0.98 for Easy / Normal / Hard (§2.2).
- AI uses **the same physics** as the player. There is no catch-up teleporting.
- **Mild rubber-banding:** ±4% skill at most, based on the gap to the player. Kept small on purpose.
- **Overtaking:** if a vehicle is less than 8 m ahead on the line and slower, the AI takes a lateral offset of ±half a lane for up to 3 s.
- **AI field:** rivals use vehicles of the event's class and type, in fixed liveries.
  - Rival-duel opponents use their signature vehicle and livery. They are named by callsign only ("Static", "Gravel Queen", …): no faces, no real people.
- There are no pedestrians anywhere (this keeps the 4+ rating).
- **SHOULD (M2):** light ambient traffic in Voltport and on Loop 8 in free roam. At most 30 cars, following lanes. Not present during events.

### 4.6 Checkpoints and lap timing

- A checkpoint is a gate segment with a forward normal.
- It counts when the vehicle's movement in one step (previous → current position) **crosses the gate in the forward direction**, and it is the **next expected** gate.
- A gate crossed out of order or backwards does nothing. If the vehicle drives more than 150 m past an expected gate without crossing it, the HUD shows "Missed checkpoint" and an arrow back.
- **Circuit:** a lap counts on crossing start/finish only after every gate in that lap.
- **Sprint:** finishing means crossing the last gate.
- **Timing uses simulation ticks** (`tick × 1/60 s`), never the wall clock, so pause and frame drops do not change times.
  - Times are reported to 0.01 s.
  - The best lap and best event time are saved per event and per vehicle type.
  - Split deltas against your best are shown at each gate.

### 4.7 HUD and minimap

The HUD is a Flutter overlay on top of the `GameWidget`, so widget tests can find its parts by key.

**HUD:**
- Speed in km/h, or mph when the locale's region is US, GB or LR. The unit can be changed in Settings.
- Position "2 / 6", lap "1 / 3", event timer, and split delta (green / red, with a text label for colour-blind players).
- Nitro gauge.
- Pause.
- In free roam: a token counter and the nearest-event hint.

**Minimap:**
- A 140 dp circle, top-right.
- Drawn from a baked world image (`assets/world/minimap.png`, 2048 × 2048 for 8 km, about 3.9 m per pixel).
- Shows the player arrow, rivals, the event route in cyan, the next checkpoint, and event markers.
- It rotates in Chase camera mode.

**World map screen:** the full baked image, with discovered landmarks, events (tier, type, best result), fast travel, and region names.

**Pause:** resume, restart event, quit event (no coins), settings. No ads.

---

## 5. World build

**[R1 b/c]** Rewritten under both. Under b: route-segment lists instead of chunks. Under c: 3-D terrain, and assets with new licence checks.

### 5.1 Size

The world is 8 km × 8 km = 64 km², split into 32 × 32 = 1,024 chunks of 256 m. About a fifth of it is ocean along the west coast.

The road network is **about 140 km** in total:

| Road type | Length |
|---|---|
| Loop 8 highway ring | ≈ 30 km |
| Voltport street grid | ≈ 40 km |
| Region roads (coast road, mountain switchbacks, desert highway) | ≈ 50 km |
| Dirt and sand trails | ≈ 20 km |

Crossing the map takes about 3 minutes at 150 km/h.

### 5.2 How the map is authored: a procedural road graph plus hand-placed landmarks

Tiled maps are **not** used. Hand-painting 1,024 chunks is not feasible for one developer, and grid tiles cannot draw smooth open-road curves.

**Source:** `mobile/tool/world/plan.svg`, edited in any SVG editor and reviewable as a picture. It has these layers:
- `roads-highway`, `roads-street`, `roads-dirt`: paths.
- `biomes`: polygons for city, desert, coast, mountain, water.
- `landmarks`: named circles.
- `events`: named paths for each event route, with gate markers.
- `spawn`: one point.

The Voltport street grid inside the city polygon is **generated** (a jittered grid, seeded) instead of drawn.

**Baker:** `mobile/tool/bake_world.dart` (pure Dart, run with `dart run tool/bake_world.dart`). It:
1. Samples the SVG Bézier paths into polylines every 2 m.
2. Builds the road graph: nodes at junctions, edges with road type, width and lane count.
3. Clips roads, shoreline and cliffs to each chunk.
4. Places static collision (city building footprints from the grid; rocks and cliffs from the biome edges).
5. Bakes each event's gates and AI racing line (§4.5).
6. Renders `minimap.png`.

Output goes to `mobile/assets/world/` as one indexed binary `world.bin` (chunk table plus per-chunk records, gzip) and `minimap.png`.

**Generated at run time, not stored:** decorative props (trees, cacti, rocks, streetlights, cones, parked cars). They are a deterministic function of `(chunkX, chunkY, worldSeed)` and the road mask, which keeps the asset small.

**The baked output is committed.** `world_bake_test.dart` re-bakes from `plan.svg` and compares the hash with the committed `world.bin`, so the source and the output cannot drift apart.

**v1 has no elevation.** Mountains are drawn with rock shading, cliff edges and switchbacks. Bridges cross water only, so the road graph is planar apart from bridges. Tunnels are drawn as a roof overlay that fades while you are under it.

### 5.3 Streaming

- Active set: the 3 × 3 chunks around the camera. Prefetch: a 5 × 5 ring, biased in the direction of travel. The cache holds at most 25 chunks, with least-recently-used eviction.
- Chunk records are decoded off the UI thread (`compute` / an isolate). Building each chunk's ground and road layer as a `ui.Picture` happens on the UI thread with a budget of 2 ms or less per frame. Above that, the work is spread across frames.
- An S-class vehicle at top speed crosses a chunk in about 2.9 s. Prefetching at 2 chunks ahead gives at least 5 s of warning.
- Chunk coordinates use floor division, so negative coordinates are correct. A unit test covers this.

### 5.4 Asset plan: original art or verified CC0 only

**Vehicles: drawn by code** (`lib/game/render/vehicle_painter.dart`).
- Each of the 16 vehicles is a top-down body outline (a `Path` built from a small spec of control points), plus panel lines, windows, lights, wheels and (for bikes) rider and helmet shapes.
- Livery layers are painted clipped to the body path: base paint → pattern → decals → number → (night) underglow and light glow.
- **Benefits:** the art is original (helping Apple 4.3), costs almost nothing in app size, and liveries need no extra sprites.
- **Silhouettes must be generic.** No copying of recognisable real bodies (trade dress).

**Kenney "Racing Pack": CC0, verified.**
- Downloaded 2026-10-14 from the URL on `https://kenney.nl/assets/racing-pack` into `/tmp/kenney_dl_untrusted/` (1,380,632 bytes).
- Its `License.txt` reads: "License: (Creative Commons Zero, CC0) http://creativecommons.org/publicdomain/zero/1.0/ … free to use in personal, educational and commercial projects".
- The page lists "Files 420×, License Creative Commons CC0".
- **Contents:**
  - `PNG/Tiles` (274 files, 128 × 128 px) with asphalt, dirt and sand roads, plus 15 each of grass, sand and dirt ground tiles;
  - `PNG/Objects` (40: cones, barriers, tyres, trees);
  - `PNG/Cars` (51 = 10 body shapes × 5 colours, 71 × 131 px);
  - `PNG/Motorcycles` (5 colours, one shape, 44 × 100 px);
  - spritesheets with XML.
- **Use:** ground textures, applied as repeating image shaders per biome, and track objects.
- Kenney cars and motorcycles are allowed **only as M1 placeholders**. They are replaced by the drawn vehicles in M2: the pack has one bike shape, and fixed colours cannot carry liveries.
- **Do not use** `PNG/Characters`, which are people (no pedestrians).
- Bundle only the files used (the target is 1.5 MB or less). Ship `License.txt` and register it with `LicenseRegistry` the way the fonts are registered (`main.dart:17-28`).

**Other Kenney packs, CC0 per their pages** (each page shows "License Creative Commons CC0", fetched 2026-10-14):
- UI: `ui-pack`.
- Sound effects: `impact-sounds` (collisions), `interface-sounds` (menus), `digital-audio` (token pickup, nitro).
- Before bundling each pack, download its zip, confirm that its `License.txt` says CC0, and record the URL, date and byte size in `mobile/assets/LICENSES.md`.

**Water, coast, snowless mountain rock, city roofs:** drawn by code (filled polygons, gradients, simple shaders). There are no third-party textures for these.

**Engine audio: original.**
- `tool/make_engine_audio.py` synthesises four loops per engine family (car petrol, car electric, bike petrol, bike electric) at idle / low / mid / high RPM, from harmonics and noise. It writes 22 kHz mono, about 2 s each, encoded AAC (`.m4a`).
- At run time the four loops are cross-faded by RPM. The design does **not** rely on pitch-shifting through `audioplayers`, because playback-rate pitch behaviour on iOS is **not verified**.

**Music:** none in v1 unless a track is found whose licence file is verified CC0 the same way. **Not sourced yet.**

**Fonts:** keep the bundled Big Shoulders (display, which suits a racing HUD) and Schibsted Grotesk, both SIL OFL (`pubspec.yaml:61-67`, licences registered at `main.dart:19-28`).

### 5.5 App size budget

Current builds:
- iOS IPA 23,178,452 bytes (`docs/ios-ipa-evidence.json`, RideZap entry).
- Android AAB 58,471,060 bytes (`docs/build-evidence.json`, RideZap entry, all ABIs).

| Item | Budget |
|---|---|
| `world.bin` | ≤ 5 MB |
| `minimap.png` | ≤ 2 MB |
| Kenney subset | ≤ 1.5 MB |
| Audio | ≤ 6 MB |
| Fonts (already bundled) | — |
| **New assets in total** | **≤ 15 MB** |
| **IPA** | **≤ 45 MB** |
| **AAB** | **≤ 85 MB** |

`release_sanity_test` gets a size check for `assets/`. The office measures IPA and AAB size at build time.

---

## 6. Performance, offline, save data, and removing the fare app

**[R1 b/c]** §6.1 budgets change under both. §6.2–6.4 apply unchanged under b. Under c, the whole Flutter app is replaced, not edited.

### 6.1 Performance targets

| Target | Value |
|---|---|
| Frame rate | 60 fps. p95 frame time ≤ 16.7 ms and p99 ≤ 25 ms over a scripted 3-minute circuit with 6 vehicles at night in rain, on an **iPhone 11** profile build and on a **mid-range Android** (Pixel 6a or Galaxy A5x class) |
| Chunk boundary at top speed | No single frame above 50 ms when crossing chunk boundaries at top speed |
| Memory | ≤ 350 MB resident on iPhone 11; ≤ 400 MB PSS on Android |
| Cold start to home menu | ≤ 3 s on iPhone 11 |
| CPU | Simulation plus AI for 8 vehicles ≤ 3 ms per frame, measured with a `Stopwatch` around `step()` in a profile build. A host benchmark test reports it. |
| Battery | Rendering capped at 60 fps. A "Battery saver" setting caps it at 30 fps. |

**Honest limit:** simulator frame times do not count. The office has no record of owning an iPhone 11 or a mid-range Android test device. **Device performance stays "not verified" until someone runs it on hardware (R9).**

### 6.2 Offline and accounts

- **Everything works offline.** Ads and the shop are simply absent offline: the shop shows its "store unavailable" state.
- **No account, no login, no Supabase.** There is none today, so there is nothing to remove:
  - `grep -rniE 'supabase|login|sign ?in|auth'` over `lib`, `test`, `integration_test` and `pubspec.yaml` found only `release_sanity_test.dart:28,55` ("signingConfig") and `onboarding_test.dart:26`, which asserts that there is **no** "Sign in".
  - `pubspec.yaml:8-43` has no Supabase package.
- The public delete-account page (`docs/deletion-urls.json:41`) stays as it is, for Play Data Safety.

### 6.3 Save data

- One `shared_preferences` key, `ridezap.game.v1`, holding versioned JSON (target ≤ 50 KB).
- **Contents:** coins; owned vehicles; upgrades per vehicle; owned liveries; the livery applied per vehicle; event results and best times; rival wins; discovered landmarks and tokens collected; the daily-ladder state; Pass claim dates; `deliveredTransactions`; cached entitlements (remove ads, Pass expiry); tutorial done; difficulty.
- Settings live under the existing key `ridezap.settings.v1` (`providers.dart:90`), with new fields.
- **When it is written:** after every finished event, purchase delivery, claim and garage change. Never mid-race.
- **Damage:** a save that cannot be read is renamed to `ridezap.game.v1.corrupt` and the game starts a new profile. Starters are owned and owned entitlements come back through restore. A widget test covers this, following the tolerant-reader pattern of `models/json_read.dart`.
- **Migration** runs by `version` field, with a test for each version.
- **The fare data is deleted.** On first launch of the game, remove `ridezap.places.v1`, `ridezap.trips.v1`, `ridezap.quotes.v1`, `ridezap.rides.v1` (`ridezap_store.dart:61-64`) and the older `legacyKeys` (`ridezap_store.dart:68-72`).
  - The fare app is not live on either store: Apple rejected it under 5.6 (`/Users/spatchava/agl/.dist/rejections.json:464`), and Play is `PRODUCTION_DRAFT_STAGED` per `RideZap.md` §1. So no public users are known to have data. Whether any TestFlight testers do is **not verified**.
- **Cloud save** (iCloud key-value / Play Games) is out of scope for v1.

### 6.4 The fare app: delete, keep or rewrite

Every path is under `mobile/`. The line counts come from `wc -l` on 2026-10-14.

**DELETE (fare features):**
- `lib/domain/` (all 4 files): `hour_pattern.dart`, `usual_fare.dart`, `ride_log.dart`, `rough_guide.dart`.
- `lib/models/`: `fare_quote.dart`, `place.dart`, `ride.dart`, `ride_service.dart`, `trip.dart`.
- `lib/services/`: `map_services.dart` (Photon/OSRM), `hand_off_links.dart` (Uber/Lyft), `ridezap_store.dart`, after its key list is copied into the migration in §6.3.
- `lib/features/`: `check/`, `places/`, `rides/`, `trips/` (incl. `trip_usuals.dart`), `onboarding/` (replaced by the first-drive tutorial).
- `lib/widgets/`: `quote_keypad.dart`, `trip_text.dart`, `attribution_line.dart`, `receipt_card.dart`, `verdict_card.dart`, `hour_pattern_chart.dart`.
- `lib/core/`: `money.dart`, `device_currency.dart`, `copy.dart` (which imports `domain/usual_fare.dart`), and the map and ride constants in `sources.dart:12-28,38`.
- `test/domain/*` (4), `test/services/map_services_test.dart`, `hand_off_links_test.dart`, `stores_test.dart`, `test/widgets/{verdict, ride_form, place_search, rides_log, check_fares, trip_screen, onboarding, trip_editor}_test.dart`, and `test/fixtures/*` (the OSRM and Photon captures).
- `integration_test/look_at_it_test.dart` and `store_screenshots_test.dart` are **rewritten** for the game (§8.3), not deleted.
- In `pubspec.yaml`, remove the `dio` dependency (`:35`). Change the description `Know your usual ride fare` (`:2`). Change the version from `1.0.0+4` (`:4`) to `2.0.0+<next build>`.
- In `providers.dart`: `_mapDioProvider`, `placeSearchServiceProvider`, `routingServiceProvider` (`:59-73`), `RideZapController` / `dataProvider` (`:133-393`), and the hand-off, measuring and fare-point providers (`:396-425`).

**Plan criterion 6 says "no test deleted or skipped to go green".** These deletions are allowed because the code they test is deleted with them. The commit must list each deleted test next to the deleted file it covered, and qa-reviewer checks that the pairs match.

**KEEP (possibly edited):**
- `main.dart`: crash, insights and ads start-up, and the font licences. Change the orientations and add the Kenney licence.
- `app/app.dart`.
- `core/app_info.dart`.
- `core/layout.dart`, for menus on tablets and foldables.
- `core/theme/` (re-skinned, §7.4).
- `widgets/privacy_choices_tile.dart` (the UMP privacy row, `settings_screen.dart:123`).
- `widgets/state_views.dart`.
- `services/link_launcher.dart`, for the legal links.
- `models/app_settings.dart` and `models/json_read.dart`.
- `features/settings/settings_screen.dart`, rewritten for game settings.
- Packages: `url_launcher`, `shared_preferences`, `go_router`, `flutter_riverpod`, `package_info_plus`, `agl_*`, `intl`.

**REWRITE tests:**
- `test/widget_test.dart`: today it asserts "exactly one ad in the app, on the trip page only" (`:70`).
- `test/release_sanity_test.dart`:
  - "exactly one banner, on the trip page, and no interstitial" (`:179-184`) becomes "banners only in the three allowed menu files; `onTransition` only in the results flow";
  - "no gateway, flight, hotel…" (`:153`) becomes the IP-names check;
  - keep "the only build-time define is the shared ads package's ids" (`:168-173`). The game adds **no** `fromEnvironment`.
- `test/identity/identity_test.dart`: the "Kerbside receipt" palette (`:70`), the receipt icon and storyboard (`:158-200`), and "the pubspec says what the app does now" (`:202`).
- Keep `test/i18n_test.dart` and `test/foldable_layout_test.dart`, pointed at the menus.

**Repo leftovers. SHOULD delete in M1** (template tells, plan criterion 4). The CI workflows do not reference them: `grep -n -iE 'npm|jest|tests_suite|mobile-rn|extension|web/' .github/workflows/*.yml` returned nothing.
- Tracked: `mobile-rn/` (24 files), `web/` (4), `extension/` (7), `tests_suite/` (5), `mobile/App.tsx`, `mobile/package.json`, `mobile/__tests__/`, and root `app.json`, `eas.json`, `.env.example`.
- Confirm with `git ls-files` before deleting.

---

## 7. Privacy, store listing and review

**[R1 b/c]** Data collected, ATT, rating and category stay the same. Screenshots and description follow the chosen style.

### 7.1 Data collected

| Source | Data | Today's record |
|---|---|---|
| AdMob (`agl_ads`) | Device ID, advertising data. Third-party advertising, not linked. | Already declared: `store/privacy/RideZap.json` (`DEVICE_ID`, `ADVERTISING_DATA`) |
| Crashlytics (`AglCrash.init`, `main.dart:35`) | Crash data, for app functionality | Declared (`CRASH_DATA`) |
| Firebase Analytics and Performance (`AglInsights.init`, `main.dart:38`) | Product interaction (analytics), performance data | Declared |
| In-app purchases | Apple and Google process the payment, and we run no server. **But** Firebase Analytics may log purchase events automatically (Play billing in particular). | `"iap": false` (`store/privacy/RideZap.json:54`) must become `true`. **Recommendation:** declare **Purchase History: Analytics, not linked** on both stores unless store-compliance verifies that Analytics receives no purchase events. Not verified. |

- Game progress stays on the device and is not sent anywhere.
- No location, camera, microphone or contacts. Tilt uses the motion sensors, which need no permission prompt.
- The Android permissions stay `INTERNET` and `ACCESS_NETWORK_STATE` (`AndroidManifest.xml:8-9`).

### 7.2 App Tracking Transparency

**Keep the current non-tracking setup:**
- `Info.plist:61-62` says "Non-tracking setup: no ATT prompt is requested".
- `PrivacyInfo.xcprivacy:18-19` has `NSPrivacyTracking` set to `false`.
- `store/privacy/RideZap.json:52` has `"att_prompt": false`.
- AdMob serves ads without the advertising id (IDFA).

**If the founder ever wants ATT for ad revenue** (an optional question in §9):
- Add `NSUserTrackingUsageDescription` and set `NSPrivacyTracking` to true.
- Show the prompt **before** any tracking, after the UMP consent form.
- Update both privacy records.
- Apple checks this (`docs/APPLE_REQUIREMENTS.md:11`, 2.1/5.1.2).

### 7.3 Age rating and category

**Age rating target: Apple 4+; IARC "Everyone" / PEGI 3.**
- No violence: vehicle contact only, no injury, no pedestrians.
- No simulated gambling.
- No user-generated content.
- No web browsing apart from the legal links, which open externally.
- Questionnaire answers: IAP **yes**, ads **yes**, "unrestricted web access" **no**.
- The final rating is set by the questionnaire (R4). **Not verified.**

**Category:**
- Today: `TRAVEL` / `SHOPPING` (`store/apps/RideZap.json:46,48`, `fastlane/metadata/primary_category.txt`).
- Proposed: Apple **Games**, subcategories **Racing** and **Action**; Play **Game → Racing**. This is part of R4.

**Play target audience: R7.** If the founder includes ages under 13, Play's Families policy applies: ads must be child-directed, and so on. The office recommends **13+**. Play may still judge a cartoon racer as "appealing to children". That is a risk.

### 7.4 Identity

Plan criterion 4 requires the app's own identity.
- **Palette "Night circuit":** asphalt `#14161B`, zap yellow `#FFD23F`, electric cyan `#2EC4F1`, signal red `#E5484D` (warnings only), chalk `#F2F4F7`.
  - Every text pair must reach 4.5:1 or better, measured in `identity_test`, the way the current palette test does (`identity_test.dart:91`).
  - Hex values are proposals for the developer to tune.
- **Icon and splash:** rewrite `tool/draw_brand.py` (today it draws the receipt slip, `draw_brand.py:1-9`). The new art is a yellow lightning-bolt road on asphalt, drawn by code and not by the portfolio generator.
  - The launch storyboard and Android splash are redrawn to match, and `identity_test:158-200` is updated.
- Menus are full-bleed garage and map art with sharp angled panels. No Material cards, no pill chips. `identity_test:149` already bans 12/16/20 px rounded cards.

### 7.5 Store listing proposals

These need store-compliance and the R8 name check. There are no trademarks and no other game names.

**Name (≤ 30 characters), one of:**
- "RideZap: Open Road Racing" (25)
- "RideZap - Car & Bike Racing" (27)

**Subtitle (≤ 30):** "Race cars and bikes, roam free" (30).

**Keywords (≤ 100):** `racing,car,bike,motorcycle,drift,open world,driving,rally,top down,nitro,garage,livery,road trip` (96).

**Play short description (≤ 80):** "Race cars and motorbikes across one open map: city, coast, desert and mountains." (80).

**Description outline:** the open map and its five regions; cars vs bikes; liveries; day, night and weather; 40 events and 8 AI rivals; free-roam tokens and drift zones; offline, no account.
- Then purchases, stated plainly: "Every vehicle can be earned by racing. Coin packs, Remove Ads and RideZap Pass are optional."
- Then the Pass terms paragraph, plus Terms of Use and Privacy links. Apple wants these in the metadata as well as in the app.
- **No** "#1", "best", ratings, player counts or comparisons with other games.

### 7.6 Screenshot plan

**Sizes:** landscape. iPhone 6.9" at 2868 × 1320, iPad 13" at 2752 × 2064, Play phone and 10" tablet.

**Capture method:**
- Taken from `integration_test/store_screenshots_test.dart` running the **real** app on simulators.
- `--dart-define=SCREENSHOT=true` loads no ads (`ads.dart:40-46`). This define is the package's own, so nothing is added to `lib/`.
- The player vehicle is driven through a test-only input seam (it feeds the AI driver's output into the player's input). The race, world and HUD are real.

**Shots:**
1. Voltport at night, Kerbsider with cyan underglow, in free roam with the HUD. The underglow comes from the garage's **preview** or rewarded trial, labelled as such if it is not owned.
2. A circuit race on Loop 8 with 5 AI rivals: position, lap and minimap.
3. Saltskipper in a Saltpan Flats sandstorm (bike lean visible).
4. Garage livery editor: a pattern, decals and paint on Tidebreaker GT.
5. The world map with all five regions and event markers.
6. Gullwing Coast sprint at sunset, with checkpoint gates.

**Rules:**
- No ads visible.
- No "Test mode".
- No placeholder art. After M2, no Kenney placeholder vehicles.
- Each image is passed by `scripts/screenshot_audit.py` (`company/policies.md`, Stores).

### 7.7 Review notes (draft for store-compliance)

> RideZap 2.0 replaces the app's previous content with an original racing game. No account or login is needed and it works offline.
>
> To play: launch → Start (a 60-second first drive teaches the controls; it can be skipped) → open Map → pick any yellow event marker → Race.
>
> In-app purchases (all optional; every vehicle can also be bought with coins earned by racing):
> - four coin packs (consumable);
> - "Remove ads forever" (non-consumable; removes banners and interstitials; rewarded ads stay available by choice);
> - "RideZap Pass", monthly or yearly (auto-renewing; no banners or interstitials, and a weekly coin bonus).
>
> "Restore purchases" is in Shop and in Settings. Ads: banners only on menus, never while driving; an occasional full-screen ad only after a finished race; rewarded ads only when the player taps a button that states the reward. There are no random or paid-chance rewards.

**Do not submit while `docs/store-holds.json` carries the 5.6 hold for RideZap** (`store-holds.json:192-196`; Charter §1, MA-043). Submission is the founder's call (R6).

---

## 8. Tests and acceptance criteria

**[R1 b/c]** Same structure under b. Under c, everything moves to the Unity Test Framework and the portfolio's Flutter gates no longer apply.

### 8.1 Pure-Dart unit tests

All live under `mobile/test/`, run with `flutter test` and need no device.

| File | Must prove |
|---|---|
| `economy/payouts_test.dart` | The §2.2 tables exactly. The first-win bonus is paid once. Difficulty multipliers. DNF pays 0. Rounding to 10. |
| `economy/catalog_test.dart` | Every vehicle has a coin price, and no vehicle is IAP-only. Prices are non-decreasing by class. The starters are free and owned on a new profile. Rival liveries are not for sale. |
| `economy/upgrades_test.dart` | Costs equal 4/8/13% of the reference price, rounded to 100. A fully upgraded vehicle never reaches the next class's stock rating. |
| `economy/progression_model_test.dart` | First S vehicle between 12 h and 25 h. Full stock garage ≤ 70 h. No vehicle costs more than the largest coin pack. |
| `economy/daily_reward_test.dart` | The ladder values, one claim per day, missed days do not reset, it restarts after 7, the clock-rollback guard. |
| `economy/no_randomness_test.dart` | Source check: no `Random(` / `math.Random` anywhere under `lib/economy/` or `lib/monetization/`. |
| `game/physics_determinism_test.dart` | The same initial state and a 3,600-step input script, run twice, give bit-identical state. One 33.3 ms frame equals two 16.7 ms frames (accumulator). Top speed reached within ±2% of the table on dry asphalt. Surface table applied. Drift enters and exits at the thresholds. Bike lean stays within ±45°. |
| `game/collision_test.dart` | Box-vs-box separation. No tunnelling through a 2 m wall at 100 m/s. Bike wipe-out above 25 km/h relative speed; a car does not wipe out. |
| `game/checkpoints_test.dart` | Gates must be crossed in order. A backward crossing does not count. The missed-checkpoint state. A lap needs every gate. Sprint finish. A crossing is caught when one step moves 1.5 m across the gate. |
| `game/race_clock_test.dart` | Time = ticks / 60. Pause does not advance it. Best lap and splits. 0.01 s formatting. |
| `game/ai_driver_test.dart` | On the baked test circuit, a Normal AI finishes 3 laps within 8% of the reference lap time and is never more than 2 s off-road. Target speed follows `sqrt(μg/κ)`. |
| `world/chunk_index_test.dart` | Floor division with negative coordinates. The cache stays at 25 chunks or fewer. Props are identical for the same seed and chunk. |
| `world/world_bake_test.dart` | Re-baking `plan.svg` gives the committed `world.bin` hash. Every event's gates lie on roads. |
| `monetization/purchase_controller_test.dart` | Driven through a fake `InAppPurchase`: success delivers once; pending then purchased; cancel; error; **replaying the same transaction does not double-credit**; `completePurchase` is called exactly once and only after the save is written; restore re-grants Remove ads; Pass active and expired (iOS expiry; Android 72 h cache). |
| `monetization/ad_policy_test.dart` | No banner on any driving, results, shop, settings or editor route. `onTransition` only on results → Continue after a **finished** event, on every 2nd one. Never after DNF or quit. **With Remove ads or Pass: no banner and no `onTransition`, but rewarded is still offered.** Rewarded caps (10 a day; pit-stop every 4 h, 4 a day). |
| `save/save_store_test.dart` | Round trip. Migration per version. A corrupt save gives a new profile and keeps the corrupt copy. The fare keys are removed on first launch. |
| `ip_names_test.dart` | Case-sensitive word-boundary check over `lib/`, `assets/` (text), `fastlane/metadata/**` and `store/` copy for other games' names (Forza, Motorfest, Solar Crown, Test Drive, The Crew) and a list of real vehicle makes (Ferrari, Lamborghini, Porsche, BMW, Audi, Mercedes, Ford, Chevrolet, Toyota, Honda, Nissan, Subaru, Mazda, Tesla, Bugatti, McLaren, Ducati, Yamaha, Kawasaki, Suzuki, Harley, KTM, Triumph, Aprilia, …). |

### 8.2 Widget tests

| File | Must prove |
|---|---|
| `widgets/home_test.dart` | Boots in landscape onto Home with Start, Map, Garage, Shop and Settings. The banner slot is in the Column. No "Sign in". |
| `widgets/garage_test.dart` | Owned and locked vehicles. A locked vehicle shows its coin price and a Buy button that is disabled when coins are short. Buying deducts coins and saves. The upgrade tier buy works. |
| `widgets/livery_editor_test.dart` | Preview any item. Buy applies it. The 24 h trial reverts after the clock passes 24 h (injected clock). |
| `widgets/shop_test.dart` | With fake products: prices come from `ProductDetails.price`; the Pass shows price **and** period, the auto-renew text, and the cancel instructions; **Restore purchases**, **Terms of Use** and **Privacy Policy** are present and open the §3.2 URLs through `RecordingLinkLauncher`. With the store unavailable: the unavailable message and **no** buy buttons. |
| `widgets/results_test.dart` | The coin breakdown. "Watch an ad: +N coins" is disabled when the ad is not ready, and is absent after the double has been used. Continue calls the ad service, and the policy decides. |
| `widgets/settings_test.dart` | Controls options, units, camera, difficulty, Privacy choices tile, Restore, legal links, version. |
| `widgets/hud_test.dart` | Speed, position, lap, timer and nitro keys are present. The pause menu has no ad. |
| `i18n_test.dart`, `foldable_layout_test.dart` (kept) | The menus boot in every standard language and survive folds. |
| `identity/identity_test.dart` (rewritten) | The new palette contrast, the icon source, the storyboard, and the pubspec description. |
| `release_sanity_test.dart` (rewritten) | §6.4, plus a size check on `assets/` (≤ 15 MB). |

### 8.3 Simulator and device runs

These follow the office rule "build it and look at it".
- `integration_test/look_at_it_test.dart`, rewritten. On a fresh install it goes: launch → tutorial → map → a tier-C circuit (driven through the test seam) → results with coins → garage. Screenshots at each step go to `ai-office/projects/real-apps/evidence/RideZap/`.
- `integration_test/store_screenshots_test.dart`: §7.6.
- Run on the iPhone 17 Pro Max and iPad Pro 13" simulators (the portfolio's devices, per `store/apps/RideZap.json` review notes), and on an Android emulator in CI.
- **Device performance (§6.1)** must be measured on hardware. Until then it is reported as **not verified**.

### 8.4 Milestones

**M1: one drivable car, a piece of the map, one race.** Internal TestFlight / Play internal only; no store submission.
- Fare app removed (§6.4). Landscape. New palette, icon and splash (first pass).
- `lib/game/sim` (physics, checkpoints, clock), the Flame `RideZapGame` with chase camera, and touch and keyboard controls.
- A 2 km × 2 km slice of the map (Voltport plus part of Loop 8, 64 chunks) baked from `plan.svg`, with streaming.
- Pipsqueak drawn by code. Kenney tiles, objects and placeholder cars for the AI.
- One circuit with 5 AI rivals. HUD, minimap, pause, results (time and place; no coins yet).
- The home menu keeps the existing `AglAdBanner` setup. No interstitial, no rewarded, no IAP.
- **Done when:** the M1 rows of §8.1 pass (physics, collision, checkpoints, clock, chunk index, AI), `flutter analyze` is clean, every test passes, and simulator screenshots of the race and results are in the evidence folder.

**M2: the full game, without money.** Internal testing only.
- The whole 8 × 8 km world and all five regions; day/night and weather; all 40 events and 8 rivals.
- All 16 vehicles drawn by code (Kenney placeholders gone); bikes with lean and wipe-out.
- Garage, upgrades, liveries (preview, buy, apply); economy, save and migration; daily reward; free-roam tokens, speed traps, drift zones and fast travel; tutorial.
- Engine and sound-effect audio; the settings set.
- SHOULD: tilt steering and ambient traffic.
- **Done when:** every §8.1 test except monetization passes, plus the garage, livery, results (without the ad button), HUD and settings widget tests; size within budget; simulator look-at-it run.

**M3: ads, purchases and store.** Released only after R2, R4, R5 and R6.
- `AdPolicy` and the ad service: menu banners, the interstitial after a finished event, the four rewarded features.
- `agl_ads` changes: `maxAdContentRating`, and SHOULD `setInterstitialsEnabled`.
- `in_app_purchase`: four packs, Remove ads, the Pass, restore, the shop UI with the 3.1.2 items, entitlements.
- Updated privacy records, store copy, category, screenshots and review notes. Release-quality-gate.
- **Done when:** every test in §8 passes; a sandbox purchase of each product type succeeds on a real device or an StoreKit-configuration simulator run, with the output quoted; a Play licence-tester purchase succeeds; the Pass expiry check is confirmed (§3.2); the screenshot audit passes. **Submission is the founder's call** (R6).

---

## 9. Risks and open founder questions

### 9.1 Open questions

| # | Question | Office recommendation |
|---|---|---|
| **R1** | Game style: a) top-down Flame, b) pseudo-3D road racer, c) Unity 3D | **a.** This spec assumes it. See §0.2 for what b or c changes. |
| **R2** | Prices: a / b / c (approval request) | **a.** Placeholders are in §3.2. Under b, a 4th coin-pack price is needed, or the catalogue drops to three packs. |
| **R3** | The fare app is in Apple review (2026-10-14): let it run, or withdraw it | **b, withdraw.** A fare app that turns into a game earns bad reviews. |
| **R4** | Create the IAP products and subscription group, change the category to Games → Racing, redo the age rating | **Approve**, once the Paid Applications agreement is confirmed active (**not verified**). |
| **R5 (new)** | **Legal text.** The live RideZap privacy page says "no advertisements… no in-app purchases… no analytics and no crash reports". That is already untrue for the current app (`main.dart:35-46`). Terms §3 says "contains no purchases". Both must be rewritten before M3 ships. Use our own Terms, or Apple's standard EULA, as the Terms of Use? | Rewrite both pages, and use Apple's standard EULA as the Terms of Use unless the founder wants our own. Charter §6: founder approves the text. |
| **R6 (new)** | **Submission timing.** RideZap carries a 5.6 hold (`docs/store-holds.json:192-196`). Under MA-043 nothing is submitted while it stands. When may the game go to review? | Build M1–M3 now. The founder decides submission after the account-level 5.6 reply. |
| **R7 (new)** | Play **target audience**: include under-13s? | **No (13+).** Including them brings Play Families ad rules and child-directed AdMob settings. |
| **R8 (new)** | **Names:** sign off on "RideZap: Open Road Racing" (or the alternative), the 16 vehicle names, and the place names after store-compliance runs a trademark search (USPTO, classes 9/28 for games and 12 for vehicles). | Approve after the search. The office has **not** run any trademark search. |
| **R9 (new)** | **Test hardware:** there is no record of an iPhone 11-class or mid-range Android device for performance checks. Buy or borrow one? (money, Charter §3) | Borrow or buy one of each. Without them, §6.1 stays "not verified". |
| optional | ATT prompt for higher ad revenue | **No** for v1. Stay non-tracking (§7.2). |

### 9.2 Risks

| Risk | Mitigation |
|---|---|
| **Apple 4.3 for games.** A generic racer in a crowded category can still be called spam. | The identity in §1: a seamless five-region map, cars **and** bikes with different physics, layered liveries drawn by code, original vehicle art, and named AI rivals. Screenshots show all of these. |
| **Scope.** 140 km of road, 16 vehicles and 40 events is a lot for one developer. | The procedural road graph plus generated city grid and props keep the authoring small. Milestones ship internally. If M2 slips, cut to three regions and 24 events and say so; never ship placeholder screens (plan criterion 1). |
| **Performance on mid-range Android** with Impeller and many `Picture`s | Per-chunk `Picture` caching, sprite batches for props, the 30 fps battery saver, and measurement on a device (R9). |
| **IAP edge cases with no server**: refunds, fraud, Android subscription restore behaviour | Accepted for v1 (§3.2). Confirm Android restore in M3 with a licence tester. Server validation later. |
| **Ad policy.** Interstitial density, ads in a 4+ app. | `AdPolicy` tests; the package's 3-minute cap and warm-up; interstitials only after finished events, every 2nd one; rating G (§3.1). |
| **`agl_ads` suspension also kills rewarded ads** (`ads.dart:55-63`) | Gate in the app (§3.1). Never call `setSuspended` for paid tiers. |
| **The native plugins rewrite `Podfile.lock`**, which already has someone else's uncommitted edit | Coordinate before M1 (top of spec). |
| **Data loss for fare-app TestFlight testers**, if any | The fare app is not live on either store. The release notes for 2.0 say the app is now a game. |
| **Trademark** on names or vehicle shapes | R8 search. Generic silhouettes. The `ip_names_test` source check. |

### 9.3 Out of scope for v1

- Online multiplayer, leaderboards, cloud save, controllers.
- 3-D or elevation.
- Police chases or anything violent.
- Real brands, music (unless a CC0 track is verified), and server-side receipt validation.

---

## Evidence log (commands run for this spec, 2026-10-14)

- **Repo state:** `git -C RideZap rev-parse HEAD` → `f2b733c…`. `git status --short` → uncommitted fastlane and `Podfile.lock` edits. `git ls-files` layout (counts in §6.4).
- **Toolchain:** `/Users/spatchava/agl/.flutter-sdk/bin/flutter --version` → Flutter 3.44.2, Dart 3.12.2.
- **pub.dev** (`curl -s https://pub.dev/api/packages/<pkg>`):
  - flame 1.38.2 (Dart >=3.11, Flutter >=3.41); flame_audio 2.12.2 (audioplayers ^6.2.0); flame_tiled 3.1.2;
  - in_app_purchase 3.3.1; in_app_purchase_storekit 0.4.13+2, whose changelog has "StoreKit 2 is now the default" (0.4.0) and "Exposes expirationDate on SK2PurchaseDetails" (0.4.13);
  - google_mobile_ads 9.1.0; sensors_plus 7.1.1.
- **Kenney:**
  - `curl https://kenney.nl/assets/{racing-pack,pixel-vehicle-pack,roguelike-modern-city,ui-pack,impact-sounds,interface-sounds,digital-audio}` → each page shows "License Creative Commons CC0".
  - The Racing Pack zip was downloaded to `/tmp/kenney_dl_untrusted/`. `unzip -l` shows the contents and `License.txt` reads CC0. `sips` measured the sizes (cars 71×131, motorcycle 44×100, tiles 128×128).
- **Legal URLs:** `curl -w '%{http_code}'` → privacy, terms, support, delete-account and `/policy/ridezap/` all returned 200. The page text was read with `curl | sed`, quoted in §3.2.
- **Files read:**
  - `RideZap/mobile`: `pubspec.yaml`, `lib/main.dart`, `lib/app/{app,router,providers}.dart`, `lib/core/sources.dart`, `lib/services/ridezap_store.dart`, `ios/Runner/Info.plist`, `ios/Runner/PrivacyInfo.xcprivacy`, `android/app/src/main/AndroidManifest.xml`, `android/app/build.gradle.kts`, and the test names in `test/**` and `integration_test/**`.
  - `agl-manifest/packages/agl_ads/lib/**` and `agl_observability/lib/src/insights.dart`.
  - `store/apps/RideZap.json`, `store/privacy/RideZap.json`, `docs/{admob-ids.json, store-holds.json, APPLE_REQUIREMENTS.md, MANUAL_ACTIONS.md (MA-023), ios-ipa-evidence.json, build-evidence.json, deletion-urls.json}`.
- **Not verified:**
  - device performance;
  - Android subscription-restore semantics;
  - whether a StoreKit 2 silent restore prompts;
  - pitch behaviour of `audioplayers` playback rate;
  - whether Firebase Analytics logs purchase events;
  - the Paid Applications agreement;
  - trademark status of any proposed name;
  - Apple's current review state (taken from the approval request, not re-checked).
