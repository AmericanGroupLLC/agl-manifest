# Spec: RideZap — a low-poly 3D open-world racing game with cars and motorbikes

Author: product-manager (AI office), 2026-10-14. Revised for **R1 d (Godot 4)** by game-developer (AI office), 2026-10-14.
Project: real-apps (`../plan.md`, criteria 1–7). Approval request: `../../../reports/approvals/2026-10-14-ridezap-racing-game.md` (GitHub issue #46).
Replaces: `RideZap.md` (the fare-log spec). The fare app is removed at cut-over (§6.4).
Repo: `/Users/spatchava/agl/RideZap`. The fare app is Flutter in `mobile/`; **the game is a Godot project in a new top-level `game/`** (§0.4). Bundle id / package `com.americangroupllc.ridezap`. **Permanent: never changes** (`mobile/android/app/build.gradle.kts:32,45`).
Base: `main` @ `f2b733ccd10653a85bdbdaf7724279f53235bc36` (`git rev-parse HEAD`, `git branch --show-current` → `main`, run 2026-10-14).

> **Status: decided.** Decision log 2026-10-14 (`company/decision-log.md:23`): **R1 d** (stylized low-poly 3D open world in Godot 4), **R2 a** (coins $0.99 / $4.99 / $9.99 / $19.99; Pass $2.99 / month and $19.99 / year; Remove ads $4.99 once), **R3 b** (the fare-app submission is withdrawn), **R4** (the office creates the IAP products and subscription group, category Games → Racing, age rating redone). Under the charter as amended on 2026-10-14 the founder decides the product (racing game, cars **and** bikes, liveries, ads, rewarded ads, coin packs for premium vehicles, an ad-removal subscription); the office decides everything else and records it.

**Leave other people's work alone.** `git status --short` (2026-10-14) shows uncommitted edits to `mobile/fastlane/metadata/**`, `mobile/fastlane/screenshots/en-US/*`, `mobile/ios/Podfile.lock` and `mobile/ios/Runner.xcodeproj/project.pbxproj`. They belong to the fare-app submission (withdrawn under R3 b). The game lives in `game/` and **does not touch `mobile/`** until cut-over (§6.4), so these edits are not in the way. Commits are path-limited (`git add game/ …`), never `git add -A`.

---

## 0. Decisions, stack, and layout

### 0.1 Engine and toolchain (R1 d)

| Item | Pinned | Evidence (2026-10-14) | Why |
|---|---|---|---|
| Engine | **Godot 4.7.2-stable**, standard (non-.NET) build, MIT | `gh api repos/godotengine/godot/releases/latest` → `4.7.2-stable`, published 2026-08-18. `Godot --version` → `4.7.2.stable.official.ed1daf0bf` | No account, no licence fee, no revenue share. Headless CLI export fits CI. |
| macOS editor | `Godot_v4.7.2-stable_macos.universal.zip`, 170,622,178 bytes, SHA-512 `38aa16e5…bac69ca` | `shasum -a 512 -c` against the release's `SHA512-SUMS.txt` → `OK` | |
| Export templates | `Godot_v4.7.2-stable_export_templates.tpz`, 1,281,349,702 bytes, SHA-512 `ca4d71c4…cb84079` | same → `OK` | Only `ios.zip`, `macos.zip`, `android_*`, `icudt_godot.dat` and `version.txt` are extracted (≈ 0.78 GB); the other platforms are not needed. |
| Local install | `~/agl/.tools/godot/4.7.2-stable/` (`editor/Godot.app`, `export_templates/`, the zip, the tpz and `SHA512-SUMS.txt`). `~/Library/Application Support/Godot/export_templates/4.7.2.stable` is a symlink to `export_templates/`, which is where the editor looks for them. | `ls -la` | Nothing installed system-wide. |
| Language | **GDScript** | `which dotnet` → not found on this machine | C# needs the `.NET` editor build, a .NET SDK on every runner and a second export toolchain. GDScript needs nothing extra, and GUT tests run with the plain binary. Hot paths that ever need it move to a GDExtension, not to C#. |
| Renderer | `mobile` (Forward Mobile; Metal on Apple, Vulkan on Android) | | Built for tile-based mobile GPUs. `gl_compatibility` is evaluated in M2 as the fallback for low-end Android if Vulkan coverage or performance is poor. |
| Physics | Jolt (built into Godot 4.4+), set explicitly in `project.godot` | | Stable stacking and fast raycasts, which the raycast vehicle (§4.3) uses heavily. Physics tick 60 Hz, `max_physics_steps_per_frame = 4`. |

**Install, reproducible** (what the office ran; CI does the same on its runners with the Linux or macOS editor):

```bash
V=4.7.2-stable; D=~/agl/.tools/godot/$V; B=https://github.com/godotengine/godot/releases/download/$V
mkdir -p "$D" && cd "$D"
curl -fsSLO $B/SHA512-SUMS.txt
curl -fsSLO $B/Godot_v${V}_macos.universal.zip
curl -fsSLO $B/Godot_v${V}_export_templates.tpz
grep -E "  Godot_v${V}_(macos.universal.zip|export_templates.tpz)$" SHA512-SUMS.txt | shasum -a 512 -c -
unzip -q Godot_v${V}_macos.universal.zip -d editor
unzip -q Godot_v${V}_export_templates.tpz 'templates/ios.zip' 'templates/macos.zip' 'templates/android_*' \
  'templates/version.txt' 'templates/icudt_godot.dat' -d . && mv templates export_templates
ln -sfn "$D/export_templates" "$HOME/Library/Application Support/Godot/export_templates/4.7.2.stable"
```

Disk: the folder is ≈ 2.5 GB with the tpz kept. The machine had 45 GB free afterwards (`df -h`); the floor is 15 GB.

### 0.2 Plugins and third-party code (all MIT, all pinned)

| Purpose | Project | Pin | Evidence (2026-10-14) | Notes |
|---|---|---|---|---|
| Unit tests | `bitwes/Gut` | **v9.7.1** (2026-07-10), tarball SHA-256 `6da99c4e…964613385` | `addons/gut/LICENSE.md`: "The MIT License (MIT) Copyright (c) 2018 Tom "Butch" Wesley"; `plugin.cfg` `version="9.7.1"` | Vendored in `game/addons/gut/` with its licence. **Excluded from every export.** |
| AdMob: banner, interstitial, rewarded, **UMP consent** | `poingstudios/godot-admob-plugin` | **v5.1.0** (2026-09-13), with its `android-template-v4.7.2.zip` and `ios-template-v4.7.2.zip` assets | `gh api repos/poingstudios/godot-admob-plugin` → `license=MIT`, pushed 2026-10-13. README: Godot 4.5.0+, Banner / Interstitial / Rewarded / UMP Consent / Ad Inspector | **Not** `v5.2.0-nightly.*` (pre-release). Added in M3. |
| Google Play Billing | `godot-sdk-integrations/godot-google-play-billing` | **3.3.0** (2026-07-27), `godot-google-play-billing.zip` 43,050 bytes, Billing Library 9.1.0 | `license=MIT`; README: "The master branch supports Godot 4.2 and above" | **Not** 1.4.0 (2026-09-25): that is the Godot 3 `1.x` line ("help existing Godot 3.x projects"). M3. |
| App Store purchases | `godotengine/godot-ios-plugins`, plugin `inappstore` | **master @ `caafb2c7fbfb5c72a64f163c76449274fa49abaa`** (2026-07-10; "Fix build with Godot 4.5/4.6" is `c8b7182`) | `license=MIT`. The last binary release is `3.5-stable` (2022), so **for Godot 4 it must be built from source** (scons against the 4.7.2 headers) in the iOS CI job | `in_app_store.mm` uses **StoreKit 1** (`SKPaymentQueue` / `SKProductsRequest`, 16 references) and exposes **no subscription expiry**. Coin packs and Remove ads work with it. The Pass needs an expiry (§3.2), so M3 adds a small office-owned StoreKit 2 bridge (`Transaction.currentEntitlements`, a GDExtension) for the Pass state only. Risk logged in §9.2. |

Each plugin's licence file is kept next to its code and listed in `game/assets/LICENSES.md`.

### 0.3 What changed from the Flame draft (R1 a)

| Area | Flame draft | Godot 4 (this spec) |
|---|---|---|
| View | Top-down 2D | Third-person chase camera in 3D, low-poly flat-shaded art |
| Code | Dart in `mobile/lib/game/` | GDScript in `game/scripts/`; pure logic in `RefCounted` classes with no scene-tree dependency so GUT runs it headless |
| Vehicle physics | 2-D arcade integrator | Custom **raycast vehicle** on `RigidBody3D` (§4.3) |
| World | Baked `world.bin` from `plan.svg`, 2-D chunks | 3-D chunks of 256 m built at run time from a deterministic layout (§5); landmarks are hand-made scenes |
| Ads | `agl_ads` (Flutter) | poingstudios AdMob plugin; the `agl_ads` rules are re-implemented in `AdPolicy` (§3.1) |
| IAP | `in_app_purchase` | Play Billing plugin + `inappstore` + a StoreKit 2 Pass bridge (§3.2) |
| Tests | `flutter test` | GUT 9.7.1 headless (§8) |
| CI | the Flutter lanes | a new **Godot lane** in `ship.yml` (§10). The other 42 apps stay Flutter |
| Size | ≤ 45 MB IPA | ≤ 150 MB download (§6.1) |
| Out of scope before, now in | 3-D, elevation, police chases | 3-D with gentle elevation (M2); cartoon **pursuit / heat** (M2, §4.6); visual **damage** (M2, §4.7) |

### 0.4 Project layout

The Godot project is a **new top-level `game/`**. `mobile/` stays untouched until cut-over (§6.4).

```
game/
  project.godot              name "RideZap", main scene res://scenes/main.tscn, landscape, Jolt, mobile renderer
  export_presets.cfg         "iOS" and "Android" presets; no secrets (signing comes from env, §10)
  addons/gut/                GUT 9.7.1 (MIT, LICENSE.md kept) — excluded from export
  assets/
    LICENSES.md              every third-party file: source URL, date, bytes, SHA-256, licence
    kenney/car-kit/          License.txt + the GLB subset used + Textures/colormap.png
    kenney/city-kit-roads/   License.txt + the GLB subset used + Textures/colormap.png
  scenes/                    main.tscn, race/, ui/, vehicles/, landmarks/
  scripts/
    sim/                     pure logic: checkpoints, race clock, tyre model, surfaces (no Node dependency)
    world/                   layout (deterministic road grid), chunk builder, chunk streamer
    vehicle/                 raycast vehicle, vehicle specs, chase camera
    race/                    race director (wires sim to scene)
    ui/                      HUD, touch controls
    economy/  monetization/  M2 / M3
  test/unit/                 GUT unit tests (pure logic)
  test/smoke/                GUT headless scene smoke tests
  tools/capture/             frame capture and fps probe for "look at it" runs — excluded from export
```

Export filter (both presets): `exclude_filter="addons/gut/*, test/*, tools/*"`. A smoke test asserts that the presets carry this filter, so no test or capture code reaches a store build (honesty rule: no debug menu, no cheat path in any build).

---

## 0.5 Competitive bar — founder, 2026-10-14: "it has to be good and better"

The founder named the games RideZap must stand next to: CarX Street (open world), Asphalt Legends (arcade, nitro, stunts),
Drive Zone Online (open-world multiplayer), Need for Speed No Limits (street racing, police chases), GRID Autosport
(circuit realism), Wreckfest (damage and destruction), CarX Drift Racing 3 (drift), Rush Rally 3 (rally surfaces),
Traffic Rider (bike traffic weaving) and Mad Skills Motocross 3 (bike stunts). All of them except Mad Skills are **3D**.

**Consequence (decided, R1 d):** a top-down 2D game would not be judged against these titles at all. RideZap is a
**stylized low-poly 3D open world in Godot 4**. Photorealism is not the goal; readable, fast, good-looking low-poly art
that runs at 60 fps on older phones is.

**What RideZap can honestly beat them on.** It will not beat Asphalt or CarX on photorealism; that takes studio budgets.
It can beat them on fairness, size, offline play, variety and older phones:

| Founder's reference | Their strength we match | Where RideZap goes further |
| --- | --- | --- |
| CarX Street, Drive Zone | Free-roam city and highway map, tuning | Map regions are seamless and offline. No energy timers and no online requirement to roam |
| Asphalt Legends | Nitro, jumps, spectacle | Every vehicle earnable by play (§2). No random boxes |
| NFS No Limits | Police chases, street culture | Heat level and pursuit events in free roam, not menu-only (§4.6) |
| Wreckfest | Crashes and damage | Visual damage and flying debris on cars, wipe-outs on bikes (cartoon-level; age rating confirmed by the R4 questionnaire) (§4.7) |
| CarX Drift 3, Rush Rally 3 | Drift scoring, surfaces | Surface-grip table (§4.3): tarmac, gravel, dirt, sand, wet; drift and rally events in the same world |
| Traffic Rider, Mad Skills | Bikes, traffic weaving, stunts | Cars and bikes in one garage, with highway weaving events and trick ramps in the mountains |
| All of them | | Download target ≤ 150 MB (Asphalt-class games are multi-GB), 60 fps target on an iPhone 11-class device, ads never during a race |

Multiplayer (Drive Zone, Asphalt) is **out of v1**. It needs a realtime server we don't run. It is a candidate for v2 on
the existing Supabase project (Realtime); the office decides it later with its cost.

Claims about the competitors' features come from the founder's list and general knowledge, and were not checked on the
stores (store pages are blocked from this machine). Download sizes and pay-to-win claims are **not verified**.

## 1. Product identity (Apple 4.3 applies to games too)

**One sentence.** RideZap is a low-poly 3D open-world racer. One seamless map has five regions. You race **cars and motorbikes** that handle differently, in events you drive to, and you paint every vehicle your own way.

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
   - Bikes accelerate harder, lean into corners, slip through gaps (narrower body), have no drift, and **wipe out** on a hard hit (a 2 s respawn penalty).
   - Off-road machines (buggy, rally, desert truck, enduro, dirt bike) lose much less grip on dirt and sand.
3. **"Flavours" = liveries.** Paint (solid, metallic, pearl), patterns (stripes, chequer, flames, lightning, split, gradient…), decals and race numbers, car underglow (visible at night), and bike light trails and helmet colour.
   - A livery is a set of material parameters and a pattern mask applied by one shared vehicle shader (`shaders/livery.gdshader`), so a livery is real layered paint on the 3-D body, not a recoloured texture.
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
6. **Free-roam activities**: 300 **bolt tokens** to collect, speed traps, drift zones (cars only), trick ramps (bikes), and **heat** pursuits (§4.6).

**Fictional only (Apple 5.2.1, Play IP policy).**
- No real car or bike makes, models, logos or recognisable body shapes. No real places.
- No reference anywhere in the app, assets, store copy or screenshots to Forza, Horizon (as a title), The Crew, Motorfest, Test Drive, Solar Crown, or any other game.
- A source test enforces this (§8.1, `test_ip_names.gd`).
- The vehicle and place names in this spec are **proposals pending R8** (trademark check).
- The Kenney Car Kit models are generic low-poly shapes. Its `police.glb`, `taxi.glb` and service vehicles carry no real livery or brand; they are used as traffic and patrols only.

**Who it is for.** Phone players who want quick races (2–5 minutes) and a world to drive around. It runs offline, needs no account, and is playable one-handed with auto-accelerate.

**Honesty rules carried from the portfolio** (`../plan.md` criterion 5, `company/policies.md`):
- No fake player counts, ratings, "online rivals" or leaderboards. Every rival is an AI and is labelled "AI".
- No remote switches and no build-time feature flags. Everything in the binary is reachable by any user (this is what the 5.6 rejection was about).
- There is no debug or cheat menu in any build. Tests inject state through constructor arguments and GUT doubles only; capture tools live in `tools/` and are excluded from export (§0.4).

---

## 2. Core loop and economy

The economy numbers are unchanged from the Flame draft. The code is GDScript under `game/scripts/economy/` (pure `RefCounted` classes).

### 2.1 Loop

Drive in free roam → find an event → race → earn coins (+ an optional rewarded double) → garage: buy a vehicle, upgrade, or paint → unlock the next tier of events → repeat.

**One currency: coins.** Earned by play, or bought in packs (§3.3).
- Coins never expire (Apple 3.1.1).
- There is no second "premium" currency. The founder's "paid points for premium cars" is met by coin packs: premium (S-class) vehicles cost coins, and those coins can also be earned.
- **No loot boxes, no random rewards, no spins.** Every reward amount is fixed and shown before the user acts. So there is no odds disclosure (3.1.1) and no simulated-gambling rating.
- Seeded randomness is allowed **only** for weather and decorative props, never in `game/scripts/economy/` or `game/scripts/monetization/`. A source test enforces this.

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

The model lives in `game/scripts/economy/progression_model.gd` (pure GDScript), and the GUT tests pin it.

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

These figures informed R2 a. They are not claims to put in store copy.

**Tests pin the curve** (§8.1):
- first S vehicle ≥ 12 h and ≤ 25 h;
- full stock garage ≤ 70 h;
- no vehicle price above the largest coin pack.

Changing a number is fine. Breaking a bound is a product decision and goes back to the PM.

---
## 3. Monetization

The **rules** are the ones the portfolio's `agl_ads` package enforces for the Flutter apps (warm-up, 3-minute cap, consent fails closed, no ads in screenshots, rewarded only on a labelled tap). `agl_ads` is Flutter and cannot be used from Godot, so `game/scripts/monetization/ad_policy.gd` (pure GDScript) re-implements them and a GUT test pins each one. `ad_service.gd` is the only file that talks to the plugin.

### 3.1 AdMob through poingstudios/godot-admob-plugin v5.1.0 (M3)

**RideZap's AdMob records already exist** (`agl-manifest/docs/admob-ids.json`, RideZap entry):

| | Android | iOS |
|---|---|---|
| App id | `ca-app-pub-8528784688453695~6433412875` | `ca-app-pub-8528784688453695~2566320057` |
| Banner | `…/4780674991` | `…/3443367587` |
| Interstitial | `…/3467593323` | `…/9625632553` |
| Rewarded | `…/6268841478` | `…/5076188460` |

- The app ids go into the plugin's Android manifest / iOS `Info.plist` settings (the plugin's export plugin writes `GADApplicationIdentifier` and the Android `meta-data`). The iOS export also carries Google's 50 SKAdNetwork ids, copied from `mobile/ios/Runner/Info.plist:63-64` and following.
- Unit ids live in `game/scripts/monetization/ad_ids.gd` as constants: they are public identifiers, not secrets. Debug builds (`OS.is_debug_build()`) use Google's documented test unit ids, so no test traffic hits production units.
- **Consent first:** UMP (`ConsentInformation.update` → form if required) runs at launch before any `MobileAds.initialize`. Without consent the game requests no ads at all, and keeps working (fails closed, the `agl_ads` rule).
- **Content rating:** `RequestConfiguration.max_ad_content_rating = G` and the same ceiling in the AdMob console (a console action recorded as an office task).

**Placement rules.** These are MUST. `AdPolicy` decides; scenes ask it.

| Format | Allowed | Never |
|---|---|---|
| Banner | Home menu, garage list, world map / event list. Anchored to the bottom edge; the menu layout reserves the banner's height so it never covers a button. | Any driving (race, countdown, free roam), pause, loading, results, shop, settings, livery editor, onboarding |
| Interstitial | **Only** when the user taps **Continue** on a results screen after a **finished** event, only on every 2nd finished event of the session, never in the first 2 transitions of a session (warm-up), and at most once every 3 minutes. | During or before a race, on quit or restart, on DNF, from the shop or any purchase flow, from settings |
| Rewarded | Only from a button that states the reward. See below. | Automatically. Never as the only way to get anything. |

**Rewarded features.** All are deterministic, and the amount is printed on the button.
1. **"Watch an ad: +{N} coins"** on the results screen. N equals that event's payout, so the coins double.
   - Once per results screen. At most 10 rewarded views a day across all features.
2. **"Pit-stop bonus: watch an ad for +300 coins"** on the home menu.
   - Once every 4 hours, at most 4 a day.
3. **"Test drive: watch an ad to race {locked vehicle} in this event"** on the pre-race screen.
   - One event only. Payout is normal. Ownership does not change.
4. **"Try this livery for 24 h"** in the livery editor. It applies a locked paint or pattern for 24 hours, then reverts.

On each button:
- The button is disabled with "Ad not ready" until the rewarded ad has loaded.
- The reward is granted only from the plugin's user-earned-reward callback. If an ad fails to show, the user loses nothing: their coins are already banked and the button stays.
- The rewarded ad is preloaded when the results, home or pre-race screen opens.

**The ad-free gate.** For "Remove ads" or Pass owners, `AdPolicy` returns *no* for banners and interstitials and `ad_service` makes **no** banner or interstitial request at all. Rewarded stays available as opt-in.

**Store-screenshot builds** load no ads. The capture tool (`tools/capture/`, excluded from store exports) sets the ad service to "off" through its constructor. There is no build-time define in the game code.

### 3.2 In-app purchases (M3)

**Product catalogue (R2 a decided).**

| Product id (App Store and Play) | Type | Grants | Price (R2 a) |
|---|---|---|---|
| `com.americangroupllc.ridezap.coins.pocket` | consumable | 5,000 coins | $0.99 |
| `com.americangroupllc.ridezap.coins.stack` | consumable | 30,000 coins | $4.99 |
| `com.americangroupllc.ridezap.coins.vault` | consumable | 65,000 coins | $9.99 |
| `com.americangroupllc.ridezap.coins.garage` | consumable | 140,000 coins | $19.99 |
| `com.americangroupllc.ridezap.removeads` | non-consumable | No banners or interstitials, forever. Rewarded stays available as opt-in. | $4.99 |
| Subscription group **"RideZap Pass"**: `com.americangroupllc.ridezap.pass.monthly` and `.pass.yearly` | auto-renewing (iOS) | While active: no banners or interstitials, plus a **2,500-coin weekly bonus** claimed in-app (every 7 days since the last claim). Rewarded stays opt-in. | $2.99 / month · $19.99 / year |
| Play: subscription `ridezap_pass` with base plans `monthly` and `yearly` | Play subscription | same | same |

- The Pass benefit is ongoing (ad-free plus weekly coins), which subscriptions require.
- Coins already granted stay after the Pass lapses.
- R4: the office creates these products in both consoles in **M3**, not before.

**Plugins.**
- **Android:** `GodotGooglePlayBilling` 3.3.0 (Billing Library 9.1.0), loaded as an Android plugin v2 through the Gradle build. `queryProductDetails`, `purchase`, `acknowledgePurchase` / `consumePurchase`, `queryPurchases` on launch.
- **iOS:** `inappstore` (StoreKit 1) for the four packs and Remove ads, including `restore_purchases`. **The Pass** uses a small office-owned StoreKit 2 bridge (GDExtension, `Transaction.currentEntitlements` and `Product.SubscriptionInfo`), because `inappstore` exposes no expiry. If the bridge slips, the Pass is held back from the iOS shop rather than shipped without a correct entitlement.

**State machine.** `game/scripts/monetization/purchase_controller.gd` is pure logic over an injectable store facade (`store_facade.gd`, one implementation per platform plus a fake for tests). Per purchase:

`idle → pending → purchased → delivered → completed`, with side exits `canceled`, `error` and `restored`.

- **Deliver exactly once.** Before adding coins, check that the transaction id / purchase token is not already in the save's `delivered_transactions` set. Add it, write the save, **then** finish the transaction (`finish_transaction` on iOS, `consumePurchase` / `acknowledgePurchase` on Android). A crash between deliver and finish must not double-credit on replay.
- The purchase listener is connected at start-up (autoload), so purchases that completed while the game was closed are delivered on the next launch.
- `pending` (Ask to Buy, slow cards) shows "Waiting for approval" and grants nothing yet.

**Entitlements** (`entitlements.gd`):
- **Remove ads:** owned once seen as purchased or restored. Cached in the save.
- **Pass on iOS:** active while the StoreKit 2 expiry is after now. The cached expiry is honoured offline.
- **Pass on Android:** active while the subscription appears in the latest `queryPurchases` result. The cache is honoured for 72 h offline.
  - The claim that Play returns only active subscriptions comes from Play Billing documentation. **Not verified here; must be confirmed in M3 with a licence-tester purchase** that lapses.

**Shop UI: Apple 3.1.2 and 3.1.1 requirements.** These are MUST, and GUT scene tests check them.
- Prices come **only** from the store's localised price string. Nothing is hard-coded.
  - If the store is unavailable or a product id is not found, the shop shows "The store isn't available right now" and offers **no** buy buttons (the portfolio's MA-023 lesson, `docs/MANUAL_ACTIONS.md:971-993`).
- The subscription screen shows the subscription name, length and price per period ("$2.99 per month"); what it includes; "Renews automatically unless cancelled at least 24 hours before the end of the period"; how to cancel; links to **Terms of Use** and **Privacy Policy**.
- **Restore purchases** buttons appear in the shop and in Settings.
- **Links** (all returned HTTP 200 to `curl` on 2026-10-14): Privacy `https://www.americangroup.ai/policy/ridezap/privacy.html`, Terms `https://www.americangroup.ai/policy/ridezap/terms.html`, Support `https://www.americangroup.ai/policy/ridezap/support.html`. Opened with `OS.shell_open`.
- **Blocker, R5 (office-owned under the amended charter):** both pages are out of date and must be rewritten before M3 ships. Terms §3 says "The app is free to download and contains no purchases"; the privacy page says the app shows no ads, has no purchases and sends no analytics or crash reports.
- Interstitials never show from the shop. The shop never shows a banner.

**Receipt validation: the honest v1 approach.**
- No server. StoreKit verifies transactions on the device; Play Billing reports purchase state. We trust those.
- **Risks, accepted for v1:** coins can be faked on jailbroken or rooted devices; refunds and voided purchases are not taken back. Impact is low: single-player, no leaderboards, nothing traded.
- **Later:** a Supabase Edge Function that checks App Store Server API and Play Developer API tokens. Out of scope for v1.

**Store-side prerequisites (R4, office):** products and subscription group created in both consoles (M3); the Paid Applications agreement active (**not verified**; an Account Holder step if it is not); on Apple the IAP products are **submitted with the build** (`docs/APPLE_REQUIREMENTS.md:10`). **The shop must not ship in any build whose products are not created in both consoles.**

### 3.3 Crash reporting and analytics

The Flutter apps use Firebase Crashlytics and Analytics through `agl_observability`. Godot has no maintained first-party Firebase plugin, so **v1 of the game ships without analytics and without a third-party crash SDK**. Apple's and Google's built-in crash reports (Xcode Organizer, Play vitals) are the crash signal. This is simpler and makes the privacy records smaller (§7.1). Revisit in v1.1 with a pinned, licence-checked plugin if the office needs it.

---

## 4. Controls, camera, physics, AI, pursuit, damage, HUD

### 4.1 Orientation

**Landscape only** (left and right) on phone and iPad: `display/window/handheld/orientation = sensor_landscape`. The iOS export sets `UIRequiresFullScreen = true`, so iPad may be landscape-only without breaking the multitasking upload rules. iPad launch is checked on a simulator (2.1(a), `docs/APPLE_REQUIREMENTS.md:8`).

### 4.2 Controls (touch first)

**Default layout "Buttons"** (`scenes/ui/touch_controls.tscn`):
- Bottom-left: ◀ ▶ steering pads, each about 88 dp (scaled by `DisplayServer.screen_get_scale()`).
- Bottom-right: a large **throttle**, **brake/reverse** to its left, **nitro** above throttle, and **drift** (handbrake, cars only; on bikes this becomes "tuck", a small top-speed boost while going straight).
- Multi-touch: each pad tracks its own touch index, so steering and throttle can be held at the same time.
- Pads write to the same `InputMap` actions as the keyboard (`steer_left`, `steer_right`, `throttle`, `brake`, `nitro`, `drift`, `pause`) with `Input.action_press` / `action_release`, so the vehicle reads one input path.
- Steering is smoothed (rise 0.12 s, return 0.08 s) so digital pads still give progressive steering.

**Options in Settings:** tilt steering (SHOULD, M2; `Input.get_accelerometer()`, no permission prompt) with a sensitivity slider; **auto-accelerate**; **steering assist** (Easy default: mild pull toward the lane centre-line); haptics (`Input.vibrate_handheld`); swap left and right.

**Hardware keyboard and game controllers** come free with `InputMap`: arrows / WASD, Space = drift, Shift = nitro, Esc = pause; a standard gamepad maps to the same actions (M2, tested on desktop only).

### 4.3 Vehicle physics: a custom raycast vehicle on RigidBody3D

**Choice.** `VehicleBody3D` was considered and rejected:
- its single `wheel_friction_slip` value flips between full grip and sliding, so a controllable, scoreable arcade drift is hard to tune;
- it cannot balance a two-wheeled bike (the body falls over without a custom lean controller anyway);
- per-surface grip needs per-wheel friction from the ground under each wheel, which a raycast rig computes directly.

**Rig** (`scripts/vehicle/raycast_vehicle.gd`, extends `RigidBody3D`):
- One `RayCast3D`-style probe per wheel (4 for cars, 2 for bikes), cast down from the body each physics tick with `PhysicsDirectSpaceState3D.intersect_ray`.
- **Suspension:** a spring-damper force at each contact point: `F = k·compression − c·compression_velocity`, rest length and stiffness from the vehicle spec (`vehicle_spec.gd`).
- **Tyre forces** come from `scripts/sim/tire_model.gd`, a pure function that GUT tests directly:
  - longitudinal: `throttle × drive_force(v / v_max)` (falls off to zero at top speed); brake force per class; reverse capped at 25 km/h;
  - lateral: cancel the wheel's sideways velocity with a force limited by `grip = base_grip(class) × surface_grip × weather_grip`, the friction-circle clamp combining it with the longitudinal force;
  - aerodynamic drag `k·v²` with `k` set so terminal speed equals the table's top speed, plus surface rolling resistance.
- **Steering:** front-wheel angle = `steer × max_angle(v)`, keeping 35% of the low-speed angle at top speed.
- **Drift (cars):** starts when drift is held above 30 km/h, or full steer above 60% of v_max with a slip angle over 12°. While drifting, rear lateral grip × 0.45 and a yaw assist torque × 1.3. Ends when slip < 8° and drift is released. Drift zones score slip angle × speed × time.
- **Bikes:** roll is held upright by the rig (angular lock on the body's roll axis); the *visual* lean of the bike mesh is `clamp(steer × v / v_max × 45°, ±45°)`, and above 20° of lean, lateral grip + 10%. No drift. **Wipe-out:** an impact with a relative normal speed above 25 km/h, or more than 1.5 s on sand above 120 km/h on a non-sand bike, triggers a 2 s respawn at the nearest road node, facing along the road.
- **Nitro:** +35% drive force and +8% v_max while active. Capacity 3 s at stock, recharge 0.15 s per second while driving (faster while drifting, 2× for the electric S-class vehicles).
- **Anti-roll and downforce:** a small anti-roll torque and speed-squared downforce keep cars planted on kerbs and crests; tuned per class.
- **Stuck:** after 3 s below 2 km/h while throttling, a **Reset** button appears and puts the vehicle on the nearest road node.
- **Fixed step:** physics at 60 Hz, `max_physics_steps_per_frame = 4`; rendering uses physics interpolation (`physics/common/physics_interpolation = true`).

**Surface and weather multipliers.** Each ground collider carries a `surface` metadata key (M1 reads the surface from the deterministic layout, `WorldLayout.surface_at`, instead). A unit test pins this table.

| Surface | Grip | Top-speed cap | Off-road vehicles (dirt / sand specialists) |
|---|---|---|---|
| Asphalt, dry | 1.00 | 100% | same |
| Asphalt, wet (rain) | 0.80 | 100% | same |
| Kerb | 0.95 | 100% | same |
| Dirt | 0.70 | 90% | 0.90 grip, 100% |
| Grass | 0.65 | 80% | 0.80, 90% |
| Sand | 0.55 | 75% | 0.85, 95% |
| Sandstorm (desert, any surface) | × 0.90 | — | — |
| Fog | grip unchanged; visibility (fog density) 120 m | — | — |

**Collision:** Jolt handles body-vs-world and body-vs-body. Buildings, rocks and barriers are static boxes / convex hulls baked per chunk; guard-rails are boxes ≥ 1 m thick. Jolt's CCD is enabled on the player body (`continuous_cd = true`) so no tunnelling at 320 km/h (89 m/s, 1.48 m per tick). A smoke test drives into a wall at 100 m/s and asserts the body stays on the near side.

**The world edge** is the ocean (west) and impassable cliffs (the other three sides): real geometry, never invisible walls in open land.

### 4.4 Camera

- **Chase (default):** behind and above the vehicle, following its heading with a critically damped spring (0.25 s), looking at a point 0.4 s ahead of the vehicle.
- **FOV:** 70° at standstill widening to 82° at top speed and +6° with nitro (speed feel). "Reduce motion" turns the widening and shake off.
- **Bumper / hood camera** (M2) and a **free-orbit photo mode** in the garage (M2, for livery previews).
- **Collision shake:** at most 0.15 m for 150 ms; off with "Reduce motion".
- The camera casts a ray back to the vehicle and pulls in when a building would block the view.

### 4.5 AI rivals

- **Racing line:** each event has a `Curve3D` through its gates, built from the road layout (§5.2). Apexes are shifted toward the inside of each curve by up to 35% of the road half-width, in proportion to curvature.
- **Target speed** per sample: `min(v_max, sqrt(μ·g / κ))`, followed by a backward pass that limits deceleration to the vehicle's braking ability.
- **Driving:** pure-pursuit steering toward a look-ahead point (8 m + 0.4 s × speed); throttle and brake from a PI controller on `target_speed × skill`. Skill is 0.88 / 0.94 / 0.98 for Easy / Normal / Hard (§2.2).
- AI drives **the same raycast vehicle** as the player. There is no catch-up teleporting. Mild rubber-banding: ±4% skill at most.
- **Overtaking:** if a vehicle is less than 8 m ahead on the line and slower, the AI takes a lateral offset of ±half a lane for up to 3 s.
- **AI field:** rivals use vehicles of the event's class and type, in fixed liveries; duel opponents use their signature vehicle and livery, named by callsign only. There are no pedestrians anywhere.
- **Ambient traffic** (M2): up to 30 low-cost kinematic cars following lane curves in Voltport and on Loop 8 in free roam; they become rigid bodies only when hit. Not present during events, except "weaving" events (bikes) on Loop 8.

### 4.6 Pursuit and heat (M2)

Cartoon street-racing pursuit, matching what NFS No Limits players expect, without violence:
- **Heat 0–5** rises with speed-trap hits above the limit, contact with traffic or patrol cars, and driving the wrong way on Loop 8. It decays when no patrol has line of sight for 20 s.
- At heat ≥ 1, patrol cars (Kenney `police.glb`, generic, no real agency name) spawn ahead and behind, driven by the AI driver with an **intercept** target instead of a racing line. More patrols and road blocks (cones and barriers from the kits) at higher heat.
- **Escape:** break line of sight and stay out of the search radius until the heat timer runs out. Pays a fixed escape bonus by heat level (economy table in M2).
- **Busted:** stopped below 10 km/h inside a ring of patrols for 3 s. Consequence: the heat bonus is lost; **no coins are taken** and nothing is random.
- No weapons, no shooting, no arrests shown, no injury. Age-rating impact goes into the R4 questionnaire answers ("cartoon or fantasy violence: none").

### 4.7 Damage (M2)

- **Cars:** visual only plus a small handling cost. Impacts above 30 km/h relative speed detach a debris piece from the Kenney Car Kit (`debris-bumper`, `debris-door`, `debris-spoiler-*`, `debris-tire`, `debris-plate-*`) as a short-lived rigid body, and step the body material toward a scuffed variant (three damage levels). Each level costs 3% top speed (max −9%). Repaired at the end of every event and free in the garage.
- **Bikes:** no panel damage; the wipe-out rule (§4.3) applies.
- Debris bodies are pooled (max 12 alive) and removed after 8 s, so damage never costs frame time over budget.

### 4.8 Checkpoints and lap timing (`scripts/sim/checkpoints.gd`, `race_clock.gd`)

- A checkpoint is a gate: a segment on the ground plane (XZ) with a forward normal, and a visible arch.
- It counts when the vehicle's movement in one physics tick (previous → current position, projected to XZ) **crosses the gate segment in the forward direction**, and it is the **next expected** gate.
- A gate crossed out of order or backwards does nothing. If the vehicle gets more than 150 m beyond the next expected gate along the route without crossing it, the HUD shows "Missed checkpoint" and an arrow back. *(M1 shows the warning when a later gate is crossed while an earlier one is still expected; the 150 m distance rule and the arrow come in M2 with the route polyline.)*
- **Circuit:** gate 0 is start/finish. A lap counts on crossing gate 0 only after every other gate in that lap, in order. **Sprint:** finishing means crossing the last gate.
- **Timing uses physics ticks** (`tick × 1/60 s`), never the wall clock, so pause and frame drops do not change times. The race clock only advances while the race state is "running". Times are reported to 0.01 s. Best lap and best event time are saved per event and per vehicle type; split deltas against your best are shown at each gate.

### 4.9 HUD and minimap

The HUD is a `CanvasLayer` (`scenes/ui/hud.tscn`) whose nodes have stable names, so scene tests find them.
- Speed in km/h, or mph when the locale's region is US, GB or LR (unit changeable in Settings).
- Position "2 / 6", lap "1 / 3", event timer, split delta (green / red, with a text label for colour-blind players).
- Nitro gauge. Pause.
- In free roam: a token counter, the heat meter, and the nearest-event hint.
- **Minimap** (M2): a 140 dp circle, top-right, drawn from a `SubViewport` top-down orthographic camera rendering a simplified "map" visual layer (roads and markers only), rotating with the chase camera.
- **Pause:** resume, restart event, quit event (no coins), settings. No ads.

---

## 5. World build

### 5.1 Size

The world is 8 km × 8 km = 64 km², split into 32 × 32 = 1,024 chunks of 256 m. About a fifth of it is ocean along the west coast. The road network is **about 140 km**: Loop 8 ≈ 30 km, Voltport grid ≈ 40 km, region roads ≈ 50 km, trails ≈ 20 km. Crossing the map takes about 3 minutes at 150 km/h.

### 5.2 How the map is authored

- **Layout data** (`scripts/world/world_layout.gd` plus `assets/world/layout.json` in M2): the road graph (Loop 8, region roads, trails) as polylines, biome polygons, landmark positions and event routes. Small, versioned, reviewable.
- **Voltport's street grid** is generated: a seeded jittered grid of blocks inside the city polygon. In M1 the grid is regular (blocks of 128 m with 16 m roads) so the first race is easy to read.
- **Chunk builder** (`chunk_builder.gd`): for chunk `(cx, cz)` it deterministically produces the ground (one low-poly mesh per biome with gentle elevation from a seeded noise in M2; flat in M1), the road pieces, buildings, props and colliders. Same `(cx, cz, world_seed)` → same chunk, which a unit test asserts.
- **Roads:** Kenney City Kit Roads tiles (`road-straight`, `road-crossroad`, `road-intersection`, `road-bend`, `road-curve`, `road-side`, barriers, lights, signs) scaled to a 16 m tile, placed through one `MultiMeshInstance3D` per tile type per chunk (a few draw calls per chunk regardless of tile count). Open-road curves that the tile set cannot draw (Loop 8, coast road, switchbacks) are extruded meshes along a `Curve3D` with the same road texture (M2).
- **Buildings:** original low-poly blocks generated per city block (height bands by district, window strips via a shared emissive material that lights up at night). No third-party buildings.
- **Props** (trees, rocks, cacti, street lights, cones): a deterministic function of `(cx, cz, world_seed)` and the road mask; Kenney road props plus original low-poly trees and rocks.
- **Landmarks** (Lighthouse Point, Old Mine Pass, the wind farm, the harbour cranes) are hand-made scenes in `scenes/landmarks/`, placed by the layout.

### 5.3 Streaming (`chunk_streamer.gd`)

- Active set: the chunks within a 1-chunk ring of the player (3 × 3 = 768 m wide); preload ring 5 × 5 biased in the direction of travel; at most 25 chunks resident, least-recently-used eviction.
- Chunk geometry data (transforms, mesh arrays) is computed on `WorkerThreadPool`; node creation and `add_child` happen on the main thread under a **2 ms per frame budget**, spread across frames above that. *(M1 builds a whole chunk on the main thread, one preload chunk per frame at most: measured 15–113 ms per chunk on a loaded M1 Max, so the budget is not met yet; moving to `WorkerThreadPool` is an M2 item.)*
- Distance hiding: `visibility_range_end` on props (150 m) and buildings (500 m), plus depth fog, so the active set never shows a hard edge.
- An S-class vehicle at top speed crosses a chunk in about 2.9 s; preloading 2 chunks ahead gives at least 5 s.
- Chunk coordinates use floor division, so negative coordinates are correct. A unit test covers this.

### 5.4 Assets: verified CC0 or original only

**Kenney Car Kit 3.1** and **City Kit Roads 2.2**, CC0, verified 2026-10-14:

| Pack | URL (from the kenney.nl page) | Bytes | SHA-256 | `License.txt` |
|---|---|---|---|---|
| Car Kit 3.1 | `https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip` | 4,814,237 | `fac7daca…6ff0c4` | "Car Kit (3.1) … License: (Creative Commons Zero, CC0) http://creativecommons.org/publicdomain/zero/1.0/ … You can use this content for personal, educational, and commercial purposes." |
| City Kit Roads 2.2 | `https://kenney.nl/media/pages/assets/city-kit-roads/74288c9459-1791628607/kenney_city-kit-roads.zip` | 2,852,289 | `374a4552…a959` | "City Kit Roads (2.2) … License: (Creative Commons Zero, CC0) …" |

- Both pages show "License — Creative Commons CC0" (`curl https://kenney.nl/assets/{car-kit,city-kit-roads}`).
- Only the GLB files used are copied into `game/assets/kenney/<pack>/`, with the pack's `License.txt` **kept beside them unchanged** and recorded in `game/assets/LICENSES.md` (URL, date, bytes, SHA-256).
- The Car Kit vehicles (sedan, hatchback-sports, sedan-sports, race, race-future, suv, van, truck, police, taxi…) are the M1 player car, AI and traffic. **M2 adds original vehicle models** for the 16 named vehicles (cars and bikes; the kit has **no motorbikes**), built in Blender from simple primitives, so the garage is not a stock-asset garage (Apple 4.3). Kenney vehicles stay as traffic and patrols.

**Original, made by the office:** bike models and riders (helmeted, no faces), buildings, trees, rocks, terrain, water shader, sky, the livery shader, UI, icon. Engine audio is synthesised (`tools/audio/make_engine_audio.py`, four RPM loops per engine family, OGG Vorbis) and cross-faded by RPM with `AudioStreamPlayer3D.pitch_scale` for fine pitch (Godot pitch-shifting is native, unlike the Flame draft's concern). Kenney CC0 sound packs (`impact-sounds`, `interface-sounds`, `digital-audio`) for effects, each licence checked the same way before bundling. **Music:** none in v1 unless a verified CC0 track is found.

**Fonts:** Big Shoulders (display, racing HUD) and Schibsted Grotesk, both SIL OFL, copied from `mobile/` with their licence files.

---

## 6. Size, performance, save data, and removing the fare app

### 6.1 Size and performance budgets

| Item | Budget | Measured how |
|---|---|---|
| **Download size** | **≤ 150 MB** per platform (thinned iOS download, Play per-device download) | App Store Connect "App Store file sizes" and Play Console "App size" after M2 upload |
| Hard cap | 200 MB — the Play base-module limit without Play Asset Delivery (Play documentation, not re-checked today) | as above |
| Engine baseline | Godot 4.7 iOS / Android export with no game content (to be measured in M1/M2 and written here) | `du` on the exported `.ipa` / `.aab` |
| Game assets (`game/assets/`, imported) | ≤ 60 MB | a smoke test sums `.godot/imported` for the shipped resources |
| Frame rate | 60 fps. p95 frame time ≤ 16.7 ms, p99 ≤ 25 ms over a scripted 3-minute circuit with 6 vehicles at night in rain, on an **iPhone 11** and a **Pixel 6a / Galaxy A5x** class Android | `tools/capture/fps_probe.gd` on device |
| Draw calls | ≤ 300 per frame at the busiest Voltport view | `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME` |
| Visible triangles | ≤ 300 k | `Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME` |
| Chunk streaming | ≤ 2 ms of main-thread work per frame; no frame above 50 ms crossing chunk boundaries at top speed | fps probe at top speed on Loop 8 |
| Physics + AI | ≤ 4 ms per frame for 8 vehicles | `Performance.TIME_PHYSICS_PROCESS` |
| Memory | ≤ 500 MB resident on iPhone 11; ≤ 600 MB PSS on Android | Xcode / `dumpsys meminfo` |
| Cold start to home menu | ≤ 4 s on iPhone 11 | stopwatch on device |
| Battery | 60 fps cap (`application/run/max_fps = 60`); "Battery saver" caps at 30 fps | |

**Honest limit:** desktop and simulator frame times do not count. The office has no record of owning an iPhone 11 or a mid-range Android test device. **Device performance stays "not verified" until someone runs it on hardware (R9).**

### 6.2 Offline and accounts

- **Everything works offline.** Ads and the shop are simply absent offline: the shop shows its "store unavailable" state.
- **No account, no login, no Supabase.**
- The public delete-account page (`docs/deletion-urls.json:41`) stays as it is, for Play Data Safety.

### 6.3 Save data

- One file `user://ridezap_save_v1.json` (versioned JSON, target ≤ 50 KB), written atomically (write to `.tmp`, then `DirAccess.rename`).
- **Contents:** coins; owned vehicles; upgrades per vehicle; owned liveries; the livery applied per vehicle; event results and best times; rival wins; discovered landmarks and tokens collected; the daily-ladder state; Pass claim dates; `delivered_transactions`; cached entitlements (remove ads, Pass expiry); tutorial done; difficulty. Settings in `user://ridezap_settings_v1.json`.
- **When it is written:** after every finished event, purchase delivery, claim and garage change. Never mid-race.
- **Damage:** a save that cannot be read is renamed to `ridezap_save_v1.corrupt.json` and the game starts a new profile. Starters are owned and owned entitlements come back through restore. A GUT test covers this.
- **Migration** runs by `version` field, with a test for each version.
- **The fare data:** the Flutter app kept it in `shared_preferences` (`ridezap.places.v1`, `ridezap.trips.v1`, `ridezap.quotes.v1`, `ridezap.rides.v1`, `mobile/lib/services/ridezap_store.dart:61-64`). A Godot build replacing the Flutter build at the same bundle id does not read those keys; on iOS the old `NSUserDefaults` plist stays in the container until the app is deleted, on Android the old `FlutterSharedPreferences.xml` likewise. The fare app is not live on either store (Apple rejected it under 5.6; Play is `PRODUCTION_DRAFT_STAGED`), so no public user data is known to exist. M3 adds a one-time cleanup on first launch: iOS — remove the `flutter.ridezap.*` keys from `NSUserDefaults` via a tiny native call in the StoreKit bridge; Android — delete `shared_prefs/FlutterSharedPreferences.xml` from the app's data dir (`OS.get_user_data_dir()/../shared_prefs/`). Whether any TestFlight testers have data is **not verified**.
- **Cloud save** is out of scope for v1.

### 6.4 Cut-over: the fare app leaves, `game/` ships

The game is built in `game/` while `mobile/` stays as it is. Cut-over happens in **M3**, after the game passes M2 and the R3 b withdrawal is confirmed in App Store Connect:

1. `agl-manifest/apps.json`: RideZap gets `"engine": "godot"` and `"dir": "game"` (today `"dir": "mobile"`, `"flutter": true`). The Flutter lanes skip it; the Godot lane (§10) builds it.
2. Version: the game ships as **2.0.0**. iOS `CFBundleVersion` and Android `versionCode` continue above the highest existing build (the pipeline's preflight, `scripts/preflight_version_codes.py`, already enforces this for Play).
3. `mobile/` is removed in one commit that lists every removed path, together with the repo leftovers that the Flame draft flagged (`mobile-rn/` 24 files, `web/` 4, `extension/` 7, `tests_suite/` 5, root `app.json`, `eas.json`, `.env.example`; confirm with `git ls-files`). The uncommitted fastlane/Podfile edits are asked about first (they are someone else's).
4. Store metadata moves to `game/store/` (or stays in `agl-manifest/store/apps/RideZap.json`, which the release scripts read).

Plan criterion 6 ("no test deleted or skipped to go green") is respected because the Flutter tests go with the Flutter code they test; the commit pairs them.

---

## 7. Privacy, store listing and review

ATT stance, rating target and category carry over from the Flame draft. Data collected gets smaller, because the game ships without Firebase (§3.3).

### 7.1 Data collected

| Source | Data | Record to set in M3 |
|---|---|---|
| AdMob (poingstudios plugin, Google Mobile Ads SDK) | Device ID, advertising data. Third-party advertising, not linked. | Already declared: `store/privacy/RideZap.json` (`DEVICE_ID`, `ADVERTISING_DATA`). Keep. |
| Crash reports | The game has no Crashlytics (§3.3). Apple and Google's own crash reports are opt-in OS features, not app collection. | Remove `CRASH_DATA` unless a crash SDK is added later. |
| Analytics | None in the game (§3.3). | Remove the analytics and performance entries. |
| In-app purchases | Apple and Google process the payment; we run no server and no analytics, so no purchase events leave the device. | `"iap": false` (`store/privacy/RideZap.json:54`) becomes `true`. No "Purchase history" data type unless an analytics SDK is added. |

The Godot iOS export must carry a `PrivacyInfo.xcprivacy` (Godot generates one; the office adds the required-reason API entries the engine and the AdMob SDK need, checked by `scripts/apple_requirements.py` on the IPA).

- Game progress stays on the device and is not sent anywhere.
- No location, camera, microphone or contacts. Tilt uses the motion sensors, which need no permission prompt.
- The Android permissions stay `INTERNET` and `ACCESS_NETWORK_STATE` (`AndroidManifest.xml:8-9`).

### 7.2 App Tracking Transparency

**Keep the current non-tracking setup** (the Flutter app's, which the Godot export must reproduce):
- `mobile/ios/Runner/Info.plist:61-62`: "Non-tracking setup: no ATT prompt is requested". The game's iOS export has no `NSUserTrackingUsageDescription`.
- `mobile/ios/Runner/PrivacyInfo.xcprivacy:18-19` has `NSPrivacyTracking` set to `false`; the game's privacy manifest does the same.
- `store/privacy/RideZap.json:52` has `"att_prompt": false`.
- AdMob serves ads without the advertising id (IDFA).

**If the office ever adds ATT for ad revenue** (not in v1):
- Add `NSUserTrackingUsageDescription` and set `NSPrivacyTracking` to true.
- Show the prompt **before** any tracking, after the UMP consent form.
- Update both privacy records.
- Apple checks this (`docs/APPLE_REQUIREMENTS.md:11`, 2.1/5.1.2).

### 7.3 Age rating and category

**Age rating target: Apple 4+; IARC "Everyone" / PEGI 3.**
- No violence: vehicle contact only, no injury, no pedestrians. Pursuit (§4.6) is cartoon chase with no weapons and no arrests shown.
- No simulated gambling.
- No user-generated content.
- No web browsing apart from the legal links, which open externally.
- Questionnaire answers: IAP **yes**, ads **yes**, "unrestricted web access" **no**.
- The final rating is set by the questionnaire (R4). **Not verified.**

**Category:**
- Today: `TRAVEL` / `SHOPPING` (`store/apps/RideZap.json:46,48`, `fastlane/metadata/primary_category.txt`).
- Proposed: Apple **Games**, subcategories **Racing** and **Action**; Play **Game → Racing**. This is part of R4 (decided: the office makes the change).

**Play target audience: R7 (office decision): 13+.** Including under-13s would bring Play's Families policy: child-directed ads, and so on. Play may still judge a cartoon racer as "appealing to children". That is a risk.

### 7.4 Identity

Plan criterion 4 requires the app's own identity.
- **Palette "Night circuit":** asphalt `#14161B`, zap yellow `#FFD23F`, electric cyan `#2EC4F1`, signal red `#E5484D` (warnings only), chalk `#F2F4F7`.
  - Every text pair must reach 4.5:1 or better, measured in `test_identity.gd` (GUT).
  - Hex values are proposals for the developer to tune.
- **Icon and splash:** a yellow lightning-bolt road on asphalt, drawn by code (`game/tools/brand/draw_brand.py`), set as the Godot project icon, the iOS icon set and the Android adaptive icon, and as `application/boot_splash`.
- Menus are full-bleed 3-D garage and map scenes with sharp angled panels. No Material-style cards or pill chips.

### 7.5 Store listing proposals

These need store-compliance and the R8 name check. There are no trademarks and no other game names.

**Name (≤ 30 characters), one of:**
- "RideZap: Open Road Racing" (25)
- "RideZap - Car & Bike Racing" (27)

**Subtitle (≤ 30):** "Race cars and bikes, roam free" (30).

**Keywords (≤ 100):** `racing,car,bike,motorcycle,drift,open world,driving,rally,3d,nitro,garage,livery,road trip,chase` (96).

**Play short description (≤ 80):** "Race cars and motorbikes across one open map: city, coast, desert and mountains." (80).

**Description outline:** the open 3-D map and its five regions; cars vs bikes; liveries; day, night and weather; 40 events and 8 AI rivals; free-roam tokens, drift zones and heat pursuits; offline, no account.
- Then purchases, stated plainly: "Every vehicle can be earned by racing. Coin packs, Remove Ads and RideZap Pass are optional."
- Then the Pass terms paragraph, plus Terms of Use and Privacy links. Apple wants these in the metadata as well as in the app.
- **No** "#1", "best", ratings, player counts or comparisons with other games.

### 7.6 Screenshot plan

**Sizes:** landscape. iPhone 6.9" at 2868 × 1320, iPad 13" at 2752 × 2064, Play phone and 10" tablet.

**Capture method:**
- Taken by `game/tools/capture/` running the **real** game scenes: on the macOS runtime for framing work, and on iPhone / iPad simulators (and an Android emulator) for the store set, with `get_viewport().get_texture().get_image().save_png()` at the store sizes.
- The capture tool constructs the ad service in its "off" state, so no ads load. The tool is excluded from store exports (§0.4); nothing is added to the game code.
- The player vehicle is driven by the capture tool's autopilot (the AI driver's output fed into the player's input actions). The race, world and HUD are real.

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
- No placeholder art. After M2, the player's vehicles in screenshots are the original models; Kenney vehicles appear only as traffic and patrols.
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

**Do not submit while `docs/store-holds.json` carries the 5.6 hold for RideZap** (`store-holds.json:192-196`; Charter §1, MA-043). Under the amended charter submission is the office's call, recorded per submission in the decision log; while the 5.6 hold stands, nothing is submitted (R6).

---
## 8. Tests and acceptance criteria

All tests are **GUT 9.7.1** scripts under `game/test/`, run headless from the CLI with the pinned editor binary. No device is needed.

```bash
GODOT=~/agl/.tools/godot/4.7.2-stable/editor/Godot.app/Contents/MacOS/Godot   # CI: the Linux editor
$GODOT --headless --path game --import                                         # first run: builds .godot/
$GODOT --headless --path game -s addons/gut/gut_cmdln.gd \
       -gdir=res://test/unit,res://test/smoke -ginclude_subdirs -gexit \
       -gjunit_xml_file=<abs path>/gut-junit.xml
```

Verified on 2026-10-15 for M1: 48 tests, exit 0 (`evidence/RideZap/godot-m1/gut-output.txt`); a run with failing tests exited 1.

`-gexit` makes the process exit non-zero when any test fails, which is what CI keys on. The JUnit file is kept as the run's evidence.

### 8.1 Unit tests (`game/test/unit/`, pure logic, no scene tree)

| File | Must prove | Milestone |
|---|---|---|
| `test_checkpoints.gd` | Gates must be crossed in order. A backward crossing does not count. An out-of-order gate does nothing. A lap needs every gate. Sprint finish on the last gate. A crossing is caught when one tick moves 1.5 m across the gate (89 m/s). The missed-checkpoint state. | **M1** |
| `test_race_clock.gd` | Time = ticks / 60. Pause does not advance it. Lap times, best lap, splits. 0.01 s formatting (`1:02.35`). | **M1** |
| `test_tire_model.gd` | Drive force falls to 0 at top speed; terminal speed within ±2% of the spec on dry asphalt; surface table applied; drift grip multiplier; bike lean clamp ±45°. | M1 (basic), M2 (full) |
| `test_chunk_index.gd` | Floor division with negative coordinates. The resident set stays ≤ 25 chunks. The same `(cx, cz, seed)` gives the same chunk content. | **M1** |
| `test_world_layout.gd` | The M1 circuit's gates lie on road tiles; the 2 × 2 km slice is inside the world bounds. | **M1** |
| `test_payouts.gd` | The §2.2 tables exactly. The first-win bonus is paid once. Difficulty multipliers. DNF pays 0. Rounding to 10. | M2 |
| `test_catalog.gd` | Every vehicle has a coin price, and no vehicle is IAP-only. Prices are non-decreasing by class. The starters are free and owned on a new profile. Rival liveries are not for sale. | M2 |
| `test_upgrades.gd` | Costs equal 4/8/13% of the reference price, rounded to 100. A fully upgraded vehicle never reaches the next class's stock rating. | M2 |
| `test_progression_model.gd` | First S vehicle between 12 h and 25 h. Full stock garage ≤ 70 h. No vehicle costs more than the largest coin pack. | M2 |
| `test_daily_reward.gd` | The ladder values, one claim per day, missed days do not reset, it restarts after 7, the clock-rollback guard. | M2 |
| `test_no_randomness.gd` | Source check: no `randi(`, `randf(`, `RandomNumberGenerator` or `randomize(` anywhere under `scripts/economy/` or `scripts/monetization/`. | M2 |
| `test_ai_driver.gd` | Target speed follows `sqrt(μg/κ)`; the backward braking pass never asks for more than the braking limit. | M2 |
| `test_heat.gd` | Heat rises and decays by the rules in §4.6; busted takes no coins. | M2 |
| `test_save_store.gd` | Round trip. Migration per version. A corrupt save gives a new profile and keeps the corrupt copy. Atomic write. | M2 |
| `test_purchase_controller.gd` | Driven through the fake store facade: success delivers once; pending then purchased; cancel; error; **replaying the same transaction does not double-credit**; finish/consume is called exactly once and only after the save is written; restore re-grants Remove ads; Pass active and expired (iOS expiry; Android 72 h cache). | M3 |
| `test_ad_policy.gd` | No banner on any driving, results, shop, settings or editor screen. Interstitial only on results → Continue after a **finished** event, every 2nd one, after the 2-transition warm-up, at most once per 3 min. Never after DNF or quit. **With Remove ads or Pass: no banner and no interstitial request, but rewarded is still offered.** Rewarded caps (10 a day; pit-stop every 4 h, 4 a day). No ad request before consent. | M3 |
| `test_ip_names.gd` | Case-sensitive word-boundary check over `scripts/`, `scenes/`, text assets and store copy for other games' names (Forza, Motorfest, Solar Crown, Test Drive, The Crew) and real vehicle makes (Ferrari, Lamborghini, Porsche, BMW, Audi, Mercedes, Ford, Chevrolet, Toyota, Honda, Nissan, Subaru, Mazda, Tesla, Bugatti, McLaren, Ducati, Yamaha, Kawasaki, Suzuki, Harley, KTM, Triumph, Aprilia, …). | M1 |

### 8.2 Headless scene smoke tests (`game/test/smoke/`)

These instantiate real scenes under `--headless` (dummy renderer, real physics) and step them.

| File | Must prove | Milestone |
|---|---|---|
| `test_race_scene_smoke.gd` | `scenes/main.tscn` loads; after 120 physics frames of full throttle the player has moved forward > 5 m and is still upright and above the ground; the streamer has loaded the 3 × 3 set around the spawn; the HUD's `Speed`, `Lap` and `Timer` nodes exist and show non-placeholder text. | **M1** |
| `test_export_filter.gd` | Both export presets exclude `addons/gut/*`, `test/*` and `tools/*`. | **M1** |
| `test_hud_scene.gd`, `test_touch_controls.gd` | Pads press and release the right `InputMap` actions; multi-touch steering + throttle. | M1 |
| `test_shop_scene.gd` | With a fake store: prices from the store strings; the Pass shows price **and** period, the auto-renew text and cancel instructions; Restore, Terms and Privacy present. With the store unavailable: the message and **no** buy buttons. | M3 |
| `test_results_scene.gd` | The coin breakdown; "Watch an ad: +N coins" disabled until loaded, absent after use; Continue asks the policy. | M3 |

### 8.3 Look at it (simulator, desktop, device)

The office rule "build it and look at it":
- `tools/capture/capture_race.gd` (run with `--write-movie` or with its own `save_png` timer) drives a lap with the autopilot and saves frames to `agl-manifest/ai-office/projects/real-apps/evidence/RideZap/<milestone>/`. Every frame is opened and described in the evidence README.
- `tools/capture/fps_probe.gd` logs frame-time percentiles, draw calls and primitives.
- iOS simulator: Godot iOS export (Xcode project) → `xcodebuild -sdk iphonesimulator` → `simctl install / launch` → `simctl io screenshot`. **Found in M1:** the official 4.7.2 templates' simulator `libgodot.a` (debug and release) is **x86_64 only** (`lipo -info`), and the iOS 26.4 / 26.5 simulators on this machine refuse x86_64 apps ("Failed to find matching arch"). Simulator runs need an arm64 simulator template built from the 4.7.2 source (`scons platform=ios ios_simulator=yes arch=arm64`), cached by version like the other templates; until then iOS is checked on a device build.
- **Device performance (§6.1)** must be measured on hardware. Until then it is reported as **not verified**.

### 8.4 Milestones

**M1: a drivable car, a streamed 2 × 2 km slice, one race.** Internal only; no store submission.
- `game/` project: Godot 4.7.2, GDScript, Jolt, mobile renderer, landscape. GUT vendored.
- Raycast vehicle with a Kenney Car Kit body (placeholder for the original models in M2), chase camera, keyboard and **touch controls** (steer, throttle/brake, nitro).
- A streamed 2 × 2 km slice of Voltport (64 chunks of 256 m), Kenney City Kit Roads tiles on a 128 m block grid, generated low-poly buildings and props.
- One checkpoint circuit with lap timing. **HUD:** speed, lap, timer (and nitro). Results panel with lap times.
- 60 fps target (desktop measurement only; device not verified).
- **Done when:** the M1 rows of §8.1 and §8.2 pass headless from the CLI; frames from a desktop run are captured and described in `evidence/RideZap/godot-m1/`; iOS simulator export attempted and its result recorded.

**M2: the full game, without money.** Internal testing only.
- The whole 8 × 8 km world and all five regions with gentle elevation; curved open roads; day/night and weather; all 40 events and 8 rivals with the AI driver.
- All 16 vehicles as original models (cars **and** bikes); bikes with lean and wipe-out; damage; pursuit and heat; ambient traffic.
- Garage, upgrades, liveries (preview, buy, apply, shader); economy, save and migration; daily reward; tokens, speed traps, drift zones, trick ramps, fast travel; tutorial; minimap and world map.
- Engine and sound-effect audio; the settings set.
- **Done when:** every §8.1 / §8.2 test except monetization passes; size within budget; simulator look-at-it run with frames described; first TestFlight / Play internal build through the Godot lane.

**M3: ads, purchases, store and cut-over.**
- `AdPolicy` and the ad service (UMP, banners on menus, interstitial after a finished event, the four rewarded features).
- Purchases: four packs, Remove ads, the Pass (with the StoreKit 2 bridge on iOS), restore, the shop UI with the 3.1.2 items, entitlements.
- The office creates the store products (R4) and rewrites the legal pages (R5).
- Cut-over (§6.4); updated privacy records, store copy, category, screenshots and review notes; release-quality-gate.
- **Done when:** every test in §8 passes; a sandbox purchase of each product type succeeds on a real device or a StoreKit-configuration run, with the output quoted; a Play licence-tester purchase succeeds; the Pass expiry check is confirmed; the screenshot audit passes. Submission follows the 5.6 rule (R6).

---

## 9. Decisions, open questions and risks

### 9.1 Decisions and remaining questions

| # | Question | Decision / status |
|---|---|---|
| **R1** | Game style | **d — low-poly 3D open world in Godot 4** (decision log 2026-10-14). |
| **R2** | Prices | **a** (§3.2). |
| **R3** | The fare app in Apple review | **b, withdraw.** Confirmation in App Store Connect is a precondition for cut-over (§6.4). |
| **R4** | IAP products, subscription group, category, age rating | **Office does it in M3.** Paid Applications agreement: **not verified**; if inactive, it is an Account Holder step. |
| **R5** | Legal text (privacy and terms pages contradict ads, IAP and SDKs) | **Office-owned** under the amended charter. Rewrite both pages before M3 ships; Terms of Use may link Apple's standard EULA. |
| **R6** | Submission timing (5.6 hold, `docs/store-holds.json:192-196`, MA-043) | Build M1–M3 now. Submission is recorded in the decision log and does not happen while the hold stands. |
| **R7** | Play target audience | **13+** (office). |
| **R8** | Names: store name, 16 vehicle names, place names | Office runs the trademark search (USPTO, classes 9/28 and 12) before M3. **Not run yet.** |
| **R9** | Test hardware (iPhone 11-class, mid-range Android) | Needs money (office decision under the amended charter) and a physical device; until then §6.1 stays **not verified**. |
| optional | ATT prompt | **No** for v1 (§7.2). |

### 9.2 Risks

| Risk | Mitigation |
|---|---|
| **Apple 4.3 for games.** A generic racer in a crowded category can still be called spam. | §1 identity; original vehicle models in M2 (no stock-asset garage); liveries on a custom shader; named AI rivals; screenshots show all of these. |
| **Scope.** A 3-D open world, 16 vehicles and 40 events is a lot. | Procedural road grid, generated buildings and props, a small layout file; milestones ship internally. If M2 slips, cut to three regions and 24 events and say so; never ship placeholder screens (plan criterion 1). |
| **Mid-range Android GPU performance** on the mobile renderer | Draw-call budget with `MultiMesh`, visibility ranges, fog, a 30 fps battery saver, `gl_compatibility` fallback evaluated in M2, and measurement on a device (R9). |
| **`inappstore` has no Godot 4 binary release and uses StoreKit 1** | Built from source at a pinned SHA in CI; Pass state through an office-owned StoreKit 2 bridge; if the bridge slips the Pass is held back on iOS, not shipped wrong. |
| **Godot Android signing takes one password** (`GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD` is used for both the store and the key) | Check in the Godot lane that RideZap's `storePassword` equals its `keyPassword` in `ANDROID_KEYSTORE_CONFIG` (compare, never print). If they differ, the lane converts a temporary copy of the keystore with `keytool -keypasswd` inside `$RUNNER_TEMP`. **Not verified** (the office has not read the secret). |
| **No arm64 iOS simulator template** in the official 4.7.2 release (simulator slice is x86_64 only; found in M1) | Build the simulator template from source once per engine version and cache it; device builds through the signing path meanwhile. |
| **A second CI lane** (the other 42 apps are Flutter) | One job, reusing the existing signing secrets, `build_ipa.py`'s archive/export step, `run_batch.py` and `play_upload.py` unchanged (§10). |
| **IAP edge cases with no server**: refunds, fraud, Android subscription restore | Accepted for v1 (§3.2). Confirm Android restore in M3 with a licence tester. |
| **Ad policy** in a game | `AdPolicy` tests; interstitials only after finished events, every 2nd one, 3-minute cap; rating G (§3.1). |
| **Trademark** on names or vehicle shapes | R8 search; generic silhouettes; `test_ip_names.gd`. |

### 9.3 Out of scope for v1

- Online multiplayer, leaderboards, cloud save.
- Real brands, licensed music (unless a CC0 track is verified), server-side receipt validation.
- Analytics and third-party crash SDKs (§3.3).

---

## 10. CI: the Godot lane in `ship.yml` (described; `ship.yml` is not changed yet)

`ship.yml` today has Flutter jobs: `resolve` → `validate` → `gate` → `android` (ubuntu, `build_release.py`, keystores from `KEYSTORE_<APP>_BASE64` + `ANDROID_KEYSTORE_CONFIG` via `materialise_signing.py`) and `ios` (macos, `build_ipa.py`, ASC API key) → upload jobs (`play_upload.py`, `testflight/run_batch.py --prebuilt`). The Godot lane plugs into the same shape and **reuses every secret name**; the change lands with the cut-over (§6.4).

**Selection.** `apps.json` gets `"engine": "godot"` for RideZap. `resolve_matrix.py` puts `engine == godot` apps into a new `godot_android` / `godot_ios` matrix and leaves them out of the Flutter matrices. `materialise_signing.py --check-workflow` keeps requiring `KEYSTORE_RIDEZAP_BASE64` in the workflow (it is already on `ship.yml:334`).

**Toolchain step (both jobs).** Download the Godot 4.7.2-stable editor for the runner OS (`Godot_v4.7.2-stable_linux.x86_64.zip` on ubuntu, the macOS universal zip on macos) and the export templates tpz, verify both against `SHA512-SUMS.txt` with `sha512sum -c` / `shasum -a 512 -c`, extract only the needed templates, cache by version.

**`validate_godot`** (ubuntu): `godot --headless --path game --import`, then the GUT command in §8 with `-gexit`. Fails the app out of the run like the Flutter `validate` + `gate` jobs do.

**`godot_android`** (ubuntu, Java 17, Android SDK platform/build-tools as Godot 4.7 requires):
1. `python3 scripts/materialise_signing.py --apps RideZap --out "$RUNNER_TEMP" --godot-env "$RUNNER_TEMP/godot-signing.env"` — a new mode of the same script: same secrets (`KEYSTORE_RIDEZAP_BASE64`, `ANDROID_KEYSTORE_CONFIG["RideZap"]`), but instead of `android/key.properties` it writes `GODOT_ANDROID_KEYSTORE_RELEASE_PATH`, `GODOT_ANDROID_KEYSTORE_RELEASE_USER` (alias) and `GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD` to a `0600` env file in `$RUNNER_TEMP` (never the workspace), and fails if store and key passwords differ without the `keytool -keypasswd` conversion (§9.2).
2. Version: `scripts/preflight_version_codes.py --bump` result written into the preset's `version/code` and `version/name` with `sed` on a temporary copy of `export_presets.cfg` (or `--export-release` with the preset overridden) — the committed preset carries no version.
3. `godot --headless --path game --install-android-build-template` then `godot --headless --path game --export-release "Android" "$AGL_DIST/RideZap.aab"` (preset: `gradle_build/use_gradle_build=true`, `gradle_build/export_format=1` (AAB), arm64-v8a + armeabi-v7a).
4. Prove the signature like `build_release.py` does: compare the AAB's signing certificate (`keytool -printcert -jarfile`) with the upload keystore's; record it in `docs/build-evidence.json`.
5. Upload artefact; the existing upload job runs `play_upload.py RideZap` unchanged.

**`godot_ios`** (macos-latest, Xcode):
1. Build `inappstore` from `godot-ios-plugins@caafb2c` with scons against the 4.7.2 headers (cached by SHA), and the StoreKit 2 bridge; copy into `game/ios/plugins/` for the export only (not committed as binaries).
2. `godot --headless --path game --export-release "iOS" build/ios/RideZap.ipa` with the preset's `application/export_project_only=true` → an Xcode project `build/ios/RideZap.xcodeproj`. Team id `TLH7Z3G27A` (the one in `mobile/ios/Runner.xcodeproj/project.pbxproj`), bundle id `com.americangroupllc.ridezap`.
3. Archive unsigned and export with manual signing against the downloaded App Store profile — the same two `xcodebuild` steps `build_ipa.py` runs for Flutter apps (`build_ipa.py:109-145`). `build_ipa.py` gets a `--xcodeproj PATH --scheme RideZap` mode that skips its `flutter build ios` step; everything after it (CFBundleVersion override, `-exportArchive`, copy to `.dist`, `verify_ipa_signing.py`) is unchanged.
4. Upload artefact; the existing TestFlight job (`run_batch.py --prebuilt`) uploads it and confirms against App Store Connect as it does for every app.

Release gates that read Flutter sources (`predelivery.py`, `store_policy_audit.py`, `apple_requirements.py`) need an engine branch for RideZap: the IPA-level checks apply unchanged; source-level Flutter checks become `n/a` with the Godot equivalents (export filter test, GUT results). That work is part of M3.

---

## Evidence log (commands run for this revision, 2026-10-14)

- **Decision:** `company/decision-log.md:23` (RideZap R1 d, R2 a, R3 b, R4) and `:25` (charter amendment); `CHARTER.md` "Founder decides (amended 2026-10-14)".
- **Repo state:** `git -C RideZap status --short` → the uncommitted `mobile/fastlane/**`, `mobile/ios/Podfile.lock` and `project.pbxproj` edits listed at the top; `git branch --show-current` → `main`; HEAD `f2b733c`.
- **Godot:** `gh api repos/godotengine/godot/releases/latest` → `4.7.2-stable` (2026-08-18) with asset sizes; `curl -fsSL` of `SHA512-SUMS.txt`, the macOS universal zip and the export templates into `~/agl/.tools/godot/4.7.2-stable/`; `shasum -a 512 -c` → `Godot_v4.7.2-stable_macos.universal.zip: OK`, `Godot_v4.7.2-stable_export_templates.tpz: OK`; `Godot --version` → `4.7.2.stable.official.ed1daf0bf`; `export_templates/version.txt` → `4.7.2.stable`.
- **Plugins:** `gh api repos/<repo>` and `…/releases` for `bitwes/Gut`, `poingstudios/godot-admob-plugin`, `godot-sdk-integrations/godot-google-play-billing`, `godotengine/godot-ios-plugins` (licences, tags, dates, assets, release notes quoted in §0.2); GUT tarball downloaded to `/tmp/rz_dl/gut/`, SHA-256 and `LICENSE.md` read; `in_app_store.mm` grepped for StoreKit 1 symbols (16 matches); `godot-ios-plugins` latest commit `caafb2c`.
- **Kenney:** `curl https://kenney.nl/assets/{car-kit,city-kit-roads}` → "License — Creative Commons CC0" and the zip URLs; zips downloaded to `/tmp/rz_dl/{carkit,roads}/`, sizes and SHA-256 recorded, `License.txt` read (quoted in §5.4), GLB lists read (Car Kit: 50 GLB incl. debris parts and wheels, no motorbikes; City Kit Roads: 95 GLB).
- **Pipeline:** read `agl-manifest/scripts/materialise_signing.py`, `.github/workflows/ship.yml` (jobs, secrets, `KEYSTORE_RIDEZAP_BASE64` at `:334`), `scripts/build_ipa.py` header and its `xcodebuild` steps; `docs/admob-ids.json` RideZap entry; `apps.json` RideZap entry (`"dir": "mobile"`, `"flutter": true`).
- **Machine:** `which dotnet` → not found; `xcodebuild -version` → Xcode 27.1; `df -h` → 45 GB free after the downloads.
- **Not verified:**
  - device performance (no iPhone 11 / mid-range Android);
  - whether RideZap's upload keystore uses the same store and key password (secret not read);
  - that `inappstore@caafb2c` builds against 4.7.2 (not built yet);
  - Android subscription-restore semantics; the Paid Applications agreement;
  - the 200 MB Play base-module figure (from Play documentation, not re-checked today);
  - trademark status of any proposed name;
  - Apple's current review state for the withdrawn fare build.
